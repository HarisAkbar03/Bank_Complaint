
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
    customer = Customer("C001", "John", "Smith", "john@example.com")

    assert customer.customer_id == "C001"
    assert customer.first_name == "John"


# Test 2: Valid account
def test_valid_account():
    account = Account(
        "A001", "C001", "Savings", "Active", Decimal("1500.50")
    )

    assert account.status == AccountStatus.ACTIVE
    assert account.current_balance == Decimal("1500.50")


# Test 3: Invalid account status
def test_invalid_account_status():
    with pytest.raises(ValueError):
        Account("A001", "C001", "Savings", "Unknown", Decimal("100"))


# Test 4: Valid complaint
def test_valid_complaint():
    complaint = Complaint(
        "CP001", "C001", "Card Dispute", "Open", datetime.now()
    )

    assert complaint.status == ComplaintStatus.OPEN


# Test 5: Invalid complaint status
def test_invalid_complaint_status():
    with pytest.raises(ValueError):
        Complaint("CP001", "C001", "Card Dispute", "Unknown", None)


# Test 6: Valid status transition
def test_valid_transition():
    complaint = Complaint("CP001", "C001", "Card Dispute", "Open", None)

    assert complaint.can_transition_to("In Progress") is True


# Test 7: Invalid status transition
def test_invalid_transition():
    complaint = Complaint("CP001", "C001", "Card Dispute", "Open", None)

    assert complaint.can_transition_to("Closed") is False


# Test 8: Valid status event
def test_valid_status_event():
    event = StatusEvent(
        "CP001", "Open", "In Progress", datetime.now()
    )

    assert event.new_status == ComplaintStatus.IN_PROGRESS


# Test 9: Invalid status event
def test_invalid_status_event():
    with pytest.raises(ValueError):
        StatusEvent("CP001", "Open", "Closed", datetime.now())


# Test 10: Invalid frozen dataclass modification
def test_frozen_customer():
    from dataclasses import FrozenInstanceError

    customer = Customer("C001", "John", "Smith", None)

    with pytest.raises(FrozenInstanceError):
        customer.first_name = "Mike"
