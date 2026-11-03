
import pytest

from repositories.models import ComplaintStatus


# Test valid status transitions
@pytest.mark.parametrize(
    "current_status, new_status",
    [
        (ComplaintStatus.OPEN, ComplaintStatus.IN_PROGRESS),
        (ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED),
        (ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED),
    ]
)
def test_valid_status_transitions(
    sample_complaint,
    current_status,
    new_status
):
    sample_complaint.status = current_status.value

    assert sample_complaint.can_transition_to(new_status) is True


# Test invalid status transitions
@pytest.mark.parametrize(
    "current_status, new_status",
    [
        (ComplaintStatus.OPEN, ComplaintStatus.RESOLVED),
        (ComplaintStatus.OPEN, ComplaintStatus.CLOSED),
        (ComplaintStatus.IN_PROGRESS, ComplaintStatus.CLOSED),
        (ComplaintStatus.CLOSED, ComplaintStatus.OPEN),
        (ComplaintStatus.CLOSED, ComplaintStatus.IN_PROGRESS),
        (ComplaintStatus.CLOSED, ComplaintStatus.RESOLVED),
    ]
)
def test_invalid_status_transitions(
    sample_complaint,
    current_status,
    new_status
):
    sample_complaint.status = current_status.value

    assert sample_complaint.can_transition_to(new_status) is False


# ---------------------------------------
# Parametrized Validation Tests
# ---------------------------------------

# Test 10-12: New complaints must start as Open
@pytest.mark.parametrize(
    "starting_status",
    [
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.RESOLVED,
        ComplaintStatus.CLOSED,
    ]
)
def test_invalid_starting_status(
    complaint_service,
    sample_complaint,
    starting_status
):
    sample_complaint.status = starting_status.value

    with pytest.raises(
        ValueError,
        match="New complaints must start as Open"
    ):
        complaint_service.create_complaint(sample_complaint)


# Test 13: Duplicate complaint ID
def test_duplicate_complaint_id(
    complaint_service,
    sample_complaint
):
    complaint_service.create_complaint(sample_complaint)

    with pytest.raises(
        ValueError,
        match="Complaint already exists"
    ):
        complaint_service.create_complaint(sample_complaint)


# Test 14-16: Invalid complaint status values
@pytest.mark.parametrize(
    "invalid_status",
    [
        "Pending",
        "Cancelled",
        "Unknown",
    ]
)
def test_invalid_complaint_status(invalid_status):

    with pytest.raises(ValueError):
        ComplaintStatus(invalid_status)
