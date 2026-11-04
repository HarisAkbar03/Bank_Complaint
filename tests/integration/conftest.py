
import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session
from repositories.models import Customer
from config import settings
from database import Base
from dependencies import get_db
from main import app

# Import models so SQLAlchemy knows about the tables
import repositories.models


TEST_DATABASE_NAME = "banking_complaint_test"

# Safety check: never use the development database
if settings.DB_NAME == TEST_DATABASE_NAME:
    raise RuntimeError(
        "Development and test database names must differ"
    )

TEST_DATABASE_URL = URL.create(
    "postgresql+psycopg",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=TEST_DATABASE_NAME
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 3}
)


@pytest.fixture(scope="session")
def integration_schema():
    # Create tables in the isolated test database.
    # Do not drop tables automatically.
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def db_session(integration_schema):
    # Start a database connection and outer transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # join_transaction_mode="create_savepoint" keeps
    # API commits inside the test's outer transaction.
    session = Session(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint"
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(
    app,
    raise_server_exceptions=False
) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def seeded_customer(db_session):
    customer = Customer(
        customer_id="TEST_C001",
        first_name="Test",
        last_name="Customer",
        email="test.customer@example.com"
    )

    db_session.add(customer)
    db_session.flush()

    return customer
