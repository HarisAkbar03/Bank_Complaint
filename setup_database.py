"""Transactional PostgreSQL seed loader for an EXISTING banking schema."""
import argparse
import csv
import logging
from collections import Counter
from pathlib import Path

from psycopg import sql
from database_manager import DatabaseManager

ROOT = Path(__file__).resolve().parent
TABLES = {
    'customer': ('customers.csv', 'customer_id', []),
    'account': ('accounts.csv', 'account_id', [('customer_id', 'customer', 'customer_id')]),
    'complaint': ('complaints.csv', 'complaint_id', [('customer_id', 'customer', 'customer_id'), ('account_id', 'account', 'account_id')]),
}
# Schema-specific required fields; other NOT NULL fields enforced by PostgreSQL.
REQUIRED = {
    'customer': {'customer_id', 'first_name', 'last_name'},
    'account': {'account_id', 'customer_id'},
    'complaint': {'complaint_id', 'customer_id'},
}


def run(args):
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    report = ['Banking database integrity report', '']
    rejected = []
    source = Counter()
    inserted = Counter()
    try:
        with DatabaseManager().session() as conn:
            with conn.cursor() as cur:
                # Schema scripts must be curated, ordered, and non-destructive.
                if args.schema_dir:
                    scripts = sorted(Path(args.schema_dir).glob('*.sql'))
                    if not scripts:
                        raise ValueError('No SQL schema scripts found')
                    for script in scripts:
                        content = script.read_text(encoding='utf-8')
                        if any(word in content.upper() for word in ('DROP TABLE', 'TRUNCATE', 'DROP SCHEMA', 'DELETE FROM')):
                            raise ValueError(f'Destructive SQL is not permitted in schema scripts: {script.name}')
                        logging.info('Schema stage: %s', script.name)
                        cur.execute(content)
                if args.reset:
                    if args.confirm_reset != 'RESET-SEED-TABLES':
                        raise ValueError('--reset requires --confirm-reset RESET-SEED-TABLES')
                    logging.warning('Resetting three seed tables (RESTRICT; dependent tables may block reset)')
                    # Child tables first. RESTRICT prevents deleting dependent data silently.
                    for table in ('complaint', 'account', 'customer'):
                        cur.execute(sql.SQL('DELETE FROM {}').format(sql.Identifier(table)))
                baseline = {}
                for table in TABLES:
                    cur.execute(sql.SQL('SELECT COUNT(*) FROM {}').format(sql.Identifier(table)))
                    baseline[table] = cur.fetchone()[0]
                known = {}
                for table, (_, pk, _) in TABLES.items():
                    cur.execute(sql.SQL('SELECT {} FROM {}').format(sql.Identifier(pk), sql.Identifier(table)))
                    known[table] = {str(row[0]) for row in cur.fetchall()}
                for table, (filename, pk, fks) in TABLES.items():
                    path = Path(args.data_dir) / filename
                    if not path.is_file():
                        raise FileNotFoundError(f'Missing seed file: {path}')
                    logging.info('Loading %s', filename)
                    with path.open(newline='', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        if not reader.fieldnames:
                            raise ValueError(f'{filename}: missing headers')
                        headers = [h.strip() for h in reader.fieldnames]
                        if len(headers) != len(set(headers)) or not REQUIRED[table].issubset(headers):
                            raise ValueError(f'{filename}: missing/duplicate headers; required {sorted(REQUIRED[table])}')
                        cur.execute('SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = %s', (table,))
                        db_cols = {r[0] for r in cur.fetchall()}
                        if not db_cols or not set(headers).issubset(db_cols):
                            raise ValueError(f'{filename}: headers do not match database columns: {sorted(set(headers) - db_cols)}')
                        for line, raw in enumerate(reader, start=2):
                            source[table] += 1
                            if None in raw:
                                rejected.append((filename, line, 'Extra CSV fields'))
                                continue
                            row = {k.strip(): (v.strip() if v else None) for k, v in raw.items()}
                            reason = None
                            if any(not row.get(c) for c in REQUIRED[table]):
                                reason = 'Missing required value'
                            elif row[pk] in known[table]:
                                reason = f'Duplicate {pk}'
                            else:
                                for col, parent, parent_pk in fks:
                                    if row.get(col) and row[col] not in known[parent]:
                                        reason = f'Invalid foreign key: {col}={row[col]}'
                                        break
                            if not reason and table == 'complaint' and row.get('account_id'):
                                cur.execute('SELECT customer_id FROM account WHERE account_id = %s', (row['account_id'],))
                                owner = cur.fetchone()
                                if owner and str(owner[0]) != row['customer_id']:
                                    reason = 'Account belongs to a different customer'
                            if reason:
                                rejected.append((filename, line, reason))
                                continue
                            columns = list(row)
                            statement = sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(
                                sql.Identifier(table),
                                sql.SQL(', ').join(map(sql.Identifier, columns)),
                                sql.SQL(', ').join(sql.Placeholder() for _ in columns),
                            )
                            # Any DB constraint failure is critical: session rolls back everything.
                            cur.execute(statement, [row[c] for c in columns])
                            known[table].add(row[pk])
                            inserted[table] += 1
                report.append('Table | Source | Inserted | Rejected | Database delta')
                for table in TABLES:
                    cur.execute(sql.SQL('SELECT COUNT(*) FROM {}').format(sql.Identifier(table)))
                    delta = cur.fetchone()[0] - baseline[table]
                    bad = sum(1 for name, _, _ in rejected if name == TABLES[table][0])
                    report.append(f'{table} | {source[table]} | {inserted[table]} | {bad} | {delta}')
                    if source[table] != inserted[table] + bad or delta != inserted[table]:
                        raise ValueError(f'Count integrity failure for {table}')
                report.append('\nOrphan checks:')
                for table, (_, _, fks) in TABLES.items():
                    for col, parent, parent_pk in fks:
                        query = sql.SQL('SELECT COUNT(*) FROM {} t LEFT JOIN {} p ON t.{} = p.{} WHERE t.{} IS NOT NULL AND p.{} IS NULL').format(
                            sql.Identifier(table), sql.Identifier(parent), sql.Identifier(col),
                            sql.Identifier(parent_pk), sql.Identifier(col), sql.Identifier(parent_pk))
                        cur.execute(query)
                        n = cur.fetchone()[0]
                        report.append(f'{table}.{col} -> {parent}: {n} orphans')
                        if n:
                            raise ValueError('Orphan integrity failure')
                for table in ('complaint',):
                    cur.execute(sql.SQL('SELECT COUNT(*) FROM {} t JOIN account a ON t.account_id = a.account_id WHERE t.customer_id <> a.customer_id').format(sql.Identifier(table)))
                    n = cur.fetchone()[0]
                    report.append(f'{table}: {n} account/customer mismatches')
                    if n:
                        raise ValueError('Account/customer integrity failure')
        report.append('\nSTATUS: COMMITTED')
        logging.info('All stages completed and committed')
    except Exception as exc:
        report.append('\nSTATUS: ROLLED BACK (or connection failed)')
        report.append(f'Error: {type(exc).__name__}: {exc}')
        logging.error('Setup failed; transaction rolled back: %s', exc)
        success = False
    else:
        success = True
    report.append('\nRejected rows (file, line, reason):')
    report += [f'{f}, line {n}: {why}' for f, n, why in rejected] or ['None']
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text('\n'.join(report) + '\n', encoding='utf-8')
    logging.info('Report: %s', args.report)
    return 0 if success else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Safely initialize and seed existing PostgreSQL schema')
    parser.add_argument('--data-dir', default=str(ROOT / 'Data'))
    parser.add_argument('--schema-dir', help='Optional directory of ordered, non-destructive .sql files')
    parser.add_argument('--report', default=str(ROOT / 'integrity_report.txt'))
    parser.add_argument('--reset', action='store_true', help='Delete seed rows explicitly')
    parser.add_argument('--confirm-reset', default='', help='Must equal RESET-SEED-TABLES')
    raise SystemExit(run(parser.parse_args()))
