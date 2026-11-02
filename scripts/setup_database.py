import csv
from pathlib import Path

from sqlalchemy import select, func
from database import SessionLocal
from repositories.models import Customer, Account, Complaint


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "Data"

MODELS = {
    "customers.csv": Customer,
    "accounts.csv": Account,
    "complaints.csv": Complaint
}


def read_csv(filename):
    path = DATA_DIR / filename

    with path.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def load_records(session, filename, model):
    rows = read_csv(filename)

    for row in rows:
        # Remove extra whitespace and convert empty values to None
        cleaned = {
            key: value.strip() if value and value.strip() else None
            for key, value in row.items()
        }

        # Convert the dictionary into an ORM object
        record = model(**cleaned)

        # Add the record to the current transaction
        session.add(record)

    session.flush()

    return len(rows)


def main():
    with SessionLocal.begin() as session:

        for filename, model in MODELS.items():
            count = load_records(session, filename, model)
            print(f"{filename}: {count} records loaded")

        for model in MODELS.values():
            count = session.scalar(
                select(func.count()).select_from(model)
            )
            print(f"{model.__tablename__}: {count} records")

    print("Database setup completed!")


if __name__ == "__main__":
    main()