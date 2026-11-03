
from sqlalchemy import text


def test_database_connection(db_session):
    result = db_session.execute(
        text("SELECT 1")
    ).scalar_one()

    assert result == 1


from repositories.models import Customer


def test_seeded_customer(db_session, seeded_customer):
    customer = db_session.get(
        Customer,
        "TEST_C001"
    )

    assert customer is not None
    assert customer.customer_id == "TEST_C001"
    assert customer.first_name == "Test"



import pytest


@pytest.mark.parametrize("run_number", [1, 2])
def test_customer_isolation(db_session, run_number):
    assert db_session.get(Customer, "TEST_ISOLATION") is None

    customer = Customer(
        customer_id="TEST_ISOLATION",
        first_name="Isolation",
        last_name="Test"
    )

    db_session.add(customer)
    db_session.flush()

    assert db_session.get(Customer, "TEST_ISOLATION") is not None
