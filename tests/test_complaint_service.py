
import pytest

from repositories.models import (
    Complaint,
    ComplaintStatus
)
from services.complaint_service import ComplaintService


class FakeComplaintRepository:

    def __init__(self):
        # Store test complaints in memory
        self.complaints = {}

        # Store status history events in memory
        self.history = []

    def get_by_id(self, complaint_id):
        return self.complaints.get(complaint_id)

    def create(self, complaint):
        self.complaints[complaint.complaint_id] = complaint

    def create_history(self, event):
        self.history.append(event)

    def update_status(self, complaint_id, new_status):
        complaint = self.complaints[complaint_id]

        # ORM objects are mutable
        complaint.status = ComplaintStatus(new_status).value


@pytest.fixture
def service():
    repository = FakeComplaintRepository()
    return ComplaintService(repository)


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


# Test 1: Creating a valid complaint
def test_create_complaint(service, sample_complaint):

    result = service.create_complaint(sample_complaint)

    assert result.complaint_id == "CMP001"
    assert result.status == ComplaintStatus.OPEN.value

    # Verify initial status history event was created
    assert len(service.repository.history) == 1

    event = service.repository.history[0]

    assert event.complaint_id == "CMP001"
    assert event.old_status is None
    assert event.new_status == ComplaintStatus.OPEN.value


# Test 2: New complaints cannot start as Closed
def test_invalid_creation_status(service, sample_complaint):

    sample_complaint.status = ComplaintStatus.CLOSED.value

    with pytest.raises(
        ValueError,
        match="New complaints must start as Open"
    ):
        service.create_complaint(sample_complaint)

    # Neither record should be staged
    assert service.repository.complaints == {}
    assert service.repository.history == []


# Test 3: Duplicate complaint IDs are rejected
def test_duplicate_complaint(service, sample_complaint):

    service.create_complaint(sample_complaint)

    with pytest.raises(
        ValueError,
        match="Complaint already exists"
    ):
        service.create_complaint(sample_complaint)

    assert len(service.repository.complaints) == 1
    assert len(service.repository.history) == 1


# Test 4: Valid status transition
def test_valid_status_transition(service, sample_complaint):

    service.create_complaint(sample_complaint)

    updated = service.update_status(
        "CMP001",
        ComplaintStatus.IN_PROGRESS
    )

    assert updated.status == ComplaintStatus.IN_PROGRESS.value


# Test 5: Invalid status transition
def test_invalid_status_transition(service, sample_complaint):

    service.create_complaint(sample_complaint)

    with pytest.raises(ValueError):
        service.update_status(
            "CMP001",
            ComplaintStatus.CLOSED
        )

    # Original status should remain unchanged
    assert (
        service.repository.get_by_id("CMP001").status
        == ComplaintStatus.OPEN.value
    )


# Test 6: Complaint does not exist
def test_missing_complaint(service):

    with pytest.raises(
        ValueError,
        match="Complaint not found"
    ):
        service.update_status(
            "UNKNOWN",
            ComplaintStatus.IN_PROGRESS
        )
