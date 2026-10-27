# One-command banking database setup

This package is an **add-on** for the existing `Bank_Complaint` project. Copy `setup_database.py` into the project root. Keep the existing `database_manager.py`, `.env`, and `requirements.txt` if already configured.

## Prerequisites

- Python 3.10+, PostgreSQL database already created, and permission to create/insert records.
- `python -m pip install -r requirements.txt` (requires `psycopg` and `python-dotenv`).
- Copy `.env.example` to `.env`, set `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`; never commit `.env`.
- Existing SQL schema installed, **or** provide an ordered folder of schema scripts (`01_customer.sql`, `02_account.sql`, `03_complaint.sql`, etc.) with `--schema-dir SQL/schema`. SQL scripts are not bundled because the `.pgerd` diagram is not a complete executable schema migration.
- Place `customers.csv`, `accounts.csv`, `complaints.csv` under `seed_data/`. Any missing files must be supplied; do not invent banking records.
- CSV headers must match the **actual database column names**, not analysis aliases such as `date_opened` if the database uses `received_at`.

## One-command setup

From the project root, with schema already present:

```powershell
python setup_database.py
```

Or initialize schema first using your own numbered SQL files:

```powershell
python setup_database.py --schema-dir SQL/schema
```

To deliberately delete seed-table rows and reload (only in a disposable development database):

```powershell
python setup_database.py --reset --confirm-reset RESET-SEED-TABLES
```

The reset deletes only three seed tables in child-to-parent order; other dependent tables may prevent it, which is safer than cascading. **Never run reset against production.**

## Expected output

Logs for each schema/CSV stage, then `All stages completed and committed` and `Report: ...integrity_report.txt`. The report contains source/inserted/rejected counts, orphan checks, account/customer checks, and a commit/rollback status. Rejected noncritical CSV rows are skipped with line numbers; a SQL constraint or integrity failure rolls back the full transaction.

## Troubleshooting

- `Missing seed file`: add the missing CSV to `seed_data/`.
- `Missing required columns`: check header spelling; see the `REQUIRED` mapping in `setup_database.py`.
- `headers do not match database columns`: adjust CSV headers to the real PostgreSQL schema.
- `relation does not exist`: run your existing SQL schema first or use `--schema-dir` with ordered scripts.
- `foreign key violation` or `NOT NULL`: inspect the report; database transaction was rolled back.
- `duplicate key`: use an empty development database, or an explicit reset where safe. Duplicate CSV IDs are rejected with a reason.
- `permission denied`: verify your PostgreSQL user's permissions.
- Do not print database passwords or store credentials in reports.

## Responsibility and validation

`database_manager.py` owns connections, commits, rollback, and closure. `setup_database.py` performs ordered seeding and integrity checks. Repositories own application data-access SQL. Business decisions do not belong in repository SQL.

Ask a teammate who has not authored the project to follow this README on a fresh development database, record the command and outcome, and attach their feedback as separate evidence. **This independent check has not yet been performed.**

## Limitations

This is a project-specific starter, not a migration engine. Schema SQL must be reviewed; naive text screening does not guarantee that arbitrary scripts are safe. Source counts refer to CSV data rows, and database deltas count newly inserted rows. The script does not fabricate missing seed data. A live database was not available during package preparation, so the database has not been seeded or verified here.
