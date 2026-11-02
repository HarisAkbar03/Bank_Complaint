from sqlalchemy import inspect
from database import engine

try:
    inspector = inspect(engine)

    tables = inspector.get_table_names()

    print("Connected to PostgreSQL!")
    print("Available tables:", tables)

except Exception as error:
    print("Connection failed:", error)