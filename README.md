# Banking Complaint Repository Layer

Python 3.10+ and PostgreSQL. Based on the `customer`, `account`, and `complaint` tables in the provided `.pgerd` diagram. The diagram contains schema, not actual records.

## Setup

```powershell
cd D:\FDM\Banking_Complaint\Bank_Complaint
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your local PostgreSQL settings. Never commit `.env`, log credentials, or include real passwords in screenshots. `.env` is excluded by `.gitignore`. Ensure your database tables already exist.

## Responsibilities

- `database_manager.py`: reads environment configuration, opens a connection, commits on success, rolls back on exception, and always closes an established connection.
- `repositories/*_repository.py`: owns parameterized SQL and converts query results to typed dataclass records.
- `repositories/models.py`: defines immutable return records.
- Service/business layer (your application): decides what operations are permitted and applies business rules. Do not put those decisions in repositories.
- UI, routes, and services must not contain SQL; SQL belongs in repositories (and separately maintained migration/schema files).

## Usage

```python
from database_manager import DatabaseManager
from repositories.customer_repository import CustomerRepository
from repositories.account_repository import AccountRepository
from repositories.complaint_repository import ComplaintRepository

db = DatabaseManager()
print(CustomerRepository(db).get_by_id("C001"))
print(AccountRepository(db).list_by_customer("C001"))
print(ComplaintRepository(db).list_by_customer("C001"))
```

Each call owns its transaction and closes its connection. For multi-repository atomic operations, refactor to pass a shared transaction/session instead of calling each independently.

## Tests

```powershell
python -m pytest -q test_repositories.py
```

Tests use mocked connections: no real database, no live credentials, and no production records. They verify found/missing records, parameter binding, rollback on query errors, connection failure, and closure. Add integration tests against a dedicated disposable PostgreSQL database before production use.

## Security

`%s` placeholders bind **values**, never interpolate user input into SQL. Table and column names are fixed in code. Use least-privilege DB accounts and do not expose exception details containing connection configuration to end users.
