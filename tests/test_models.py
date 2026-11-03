
import pytest
from datetime import datetime
from decimal import Decimal

from repositories.models import (
    Customer,
    Account,
    Complaint,
    StatusEvent,
    ComplaintStatus,
    AccountStatus
)


# Test 1: Valid customer
def test_valid_customer():
    customer = Customer(
        customer_id="C001",
        first_name="John",
        last_name="Smith",
        email="john@example.com"
    )

    assert customer.customer_id == "C001"
    assert customer.first_name == "John"


# Test 2: Valid account
def test_valid_account():
    account = Account(
        account_id="A001",
        customer_id="C001",
        account_type="Savings",
        status=AccountStatus.ACTIVE.value,
        current_balance=Decimal("1500.50")
    )

    assert account.status == AccountStatus.ACTIVE.value
    assert account.current_balance == Decimal("1500.50")


# Test 3: Invalid account status
def test_invalid_account_status():
    # Explicitly validate the status using the Enum
    with pytest.raises(ValueError):
        AccountStatus("Unknown")


# Test 4: Valid complaint
def test_valid_complaint():
    complaint = Complaint(
        complaint_id="CP001",
        customer_id="C001",
        category="Card Dispute",
        channel="Online",
        status=ComplaintStatus.OPEN.value,
        received_at=datetime.now()
    )

    assert complaint.status == ComplaintStatus.OPEN.value


# Test 5: Invalid complaint status
def test_invalid_complaint_status():
    # Explicitly validate the status using the Enum
    with pytest.raises(ValueError):
        ComplaintStatus("Unknown")


# Test 6: Valid status transition
def test_valid_transition():
    complaint = Complaint(
        complaint_id="CP001",
        customer_id="C001",
        category="Card Dispute",
        channel="Online",
        status=ComplaintStatus.OPEN.value,
        received_at=None
    )

    assert complaint.can_transition_to("In Progress") is True


# Test 7: Invalid status transition
def test_invalid_transition():
    complaint = Complaint(
        complaint_id="CP001",
        customer_id="C001",
        category="Card Dispute",
        channel="Online",
        status=ComplaintStatus.OPEN.value,
        received_at=None
    )

    assert complaint.can_transition_to("Closed") is False


# Test 8: Valid status event
def test_valid_status_event():
    event = StatusEvent(
        complaint_id="CP001",
        old_status="Open",
        new_status="In Progress",
        changed_at=datetime.now()
    )

    assert event.new_status == ComplaintStatus.IN_PROGRESS


# Test 9: Invalid status event
def test_invalid_status_event():
    with pytest.raises(ValueError):
        StatusEvent(
            complaint_id="CP001",
            old_status="Open",
            new_status="Closed",
            changed_at=datetime.now()
        )


# Test 10: ORM customer modification
def test_customer_modification():
    customer = Customer(
        customer_id="C001",
        first_name="John",
        last_name="Smith",
        email=None
    )

    # SQLAlchemy ORM models are mutable
    customer.first_name = "Mike"

    assert customer.first_name == "Mike"
