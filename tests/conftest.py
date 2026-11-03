
import pytest

from repositories.models import (
    Customer,
    Account,
    Complaint,
    ComplaintStatus,
    AccountStatus
)
from services.complaint_service import ComplaintService


# Reusable customer fixture
@pytest.fixture
def sample_customer():
    return Customer(
        customer_id="C001",
        first_name="John",
        last_name="Smith",
        email="john@example.com"
    )


# Reusable account fixture
@pytest.fixture
def sample_account():
    return Account(
        account_id="A001",
        customer_id="C001",
        account_type="Savings",
        status=AccountStatus.ACTIVE.value,
        current_balance=1000
    )


# Reusable complaint fixture
@pytest.fixture
def sample_complaint():
    return Complaint(
        complaint_id="CMP001",
        customer_id="C001",
        category="Billing",
        channel="Online",
        status=ComplaintStatus.OPEN.value,
        received_at=None
    )


# Fake repository for isolated service testing
class FakeComplaintRepository:

    def __init__(self):
        self.complaints = {}
        self.history = []

    def get_by_id(self, complaint_id):
        return self.complaints.get(complaint_id)

    def create(self, complaint):
        self.complaints[complaint.complaint_id] = complaint

    def create_history(self, event):
        self.history.append(event)

    def update_status(self, complaint_id, new_status):
        complaint = self.complaints[complaint_id]
        complaint.status = ComplaintStatus(new_status).value


# Reusable fake repository fixture
@pytest.fixture
def fake_complaint_repository():
    return FakeComplaintRepository()


# Reusable service fixture
@pytest.fixture
def complaint_service(fake_complaint_repository):
    return ComplaintService(fake_complaint_repository)
