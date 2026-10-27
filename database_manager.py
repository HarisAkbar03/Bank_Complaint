import os
from contextlib import contextmanager
import psycopg
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self, connect=None):
        self.connect = connect or psycopg.connect

    @contextmanager
    def session(self):
        # Never print connection parameters: they may contain secrets.
        connection = self.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
        )
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
