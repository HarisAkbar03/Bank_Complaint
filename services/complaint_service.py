
from datetime import datetime, timezone

from repositories.models import (
    Complaint,
    ComplaintStatus,
    ComplaintStatusHistory
)


class ComplaintService:

    def __init__(self, complaint_repository):
        # Keep dependency injection
        self.repository = complaint_repository

    def create_complaint(self, complaint):

        if not isinstance(complaint, Complaint):
            raise ValueError("Invalid complaint object")

        if ComplaintStatus(complaint.status) != ComplaintStatus.OPEN:
            raise ValueError("New complaints must start as Open")

        if self.repository.get_by_id(complaint.complaint_id):
            raise ValueError("Complaint already exists")

        # First database operation
        self.repository.create(complaint)

        # Initial status history event
        event = ComplaintStatusHistory(
            complaint_id=complaint.complaint_id,
            old_status=None,
            new_status=ComplaintStatus.OPEN.value,
            changed_at=datetime.now(timezone.utc)
        )

        # Second database operation
        self.repository.create_history(event)

        # No commit here
        return complaint

    def update_status(self, complaint_id, new_status):

        complaint = self.repository.get_by_id(complaint_id)

        if complaint is None:
            raise ValueError("Complaint not found")

        new_status = ComplaintStatus(new_status)

        if not complaint.can_transition_to(new_status):
            raise ValueError("Invalid status transition")

        old_status = ComplaintStatus(complaint.status)

        # Update complaint
        self.repository.update_status(
            complaint_id,
            new_status.value
        )

        # Record the status change
        event = ComplaintStatusHistory(
            complaint_id=complaint_id,
            old_status=old_status.value,
            new_status=new_status.value,
            changed_at=datetime.now(timezone.utc)
        )

        self.repository.create_history(event)

        return complaint
