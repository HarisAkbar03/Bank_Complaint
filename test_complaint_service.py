
import pytest
from dataclasses import replace

from repositories.models import Complaint, ComplaintStatus
from services.complaint_service import ComplaintService


class FakeComplaintRepository:

    def __init__(self):
        self.complaints = {}

    def get_by_id(self, complaint_id):
        return self.complaints.get(complaint_id)

    def create(self, complaint):
        self.complaints[complaint.complaint_id] = complaint

    def update_status(self, complaint_id, new_status):
        complaint = self.complaints[complaint_id]
        self.complaints[complaint_id] = replace(
            complaint,
            status=new_status
        )


@pytest.fixture
def service():
    repo = FakeComplaintRepository()
    return ComplaintService(repo)


@pytest.fixture
def sample_complaint():
    return Complaint(
        complaint_id="CMP001",
        customer_id="C001",
        category="Billing",
        status=ComplaintStatus.OPEN,
        received_at=None
    )


# Test 1: Creating a valid complaint
def test_create_complaint(service, sample_complaint):
    result = service.create_complaint(sample_complaint)

    assert result.complaint_id == "CMP001"
    assert result.status == ComplaintStatus.OPEN


# Test 2: New complaints cannot start as Closed
def test_invalid_creation_status(service, sample_complaint):
    closed = replace(
        sample_complaint,
        status=ComplaintStatus.CLOSED
    )

    with pytest.raises(ValueError):
        service.create_complaint(closed)


# Test 3: Duplicate complaint IDs are rejected
def test_duplicate_complaint(service, sample_complaint):
    service.create_complaint(sample_complaint)

    with pytest.raises(ValueError):
        service.create_complaint(sample_complaint)


# Test 4: Valid status transition
def test_valid_status_transition(service, sample_complaint):
    service.create_complaint(sample_complaint)

    updated = service.update_status(
        "CMP001",
        ComplaintStatus.IN_PROGRESS
    )

    assert updated.status == ComplaintStatus.IN_PROGRESS


# Test 5: Invalid status transition
def test_invalid_status_transition(service, sample_complaint):
    service.create_complaint(sample_complaint)

    with pytest.raises(ValueError):
        service.update_status(
            "CMP001",
            ComplaintStatus.CLOSED
        )

    # Ensure the original status remains unchanged
    assert service.repository.get_by_id("CMP001").status == ComplaintStatus.OPEN


# Test 6: Complaint does not exist
def test_missing_complaint(service):
    with pytest.raises(ValueError):
        service.update_status(
            "UNKNOWN",
            ComplaintStatus.IN_PROGRESS
        )
