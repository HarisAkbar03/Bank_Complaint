
from dataclasses import replace

from repositories.models import Complaint, ComplaintStatus


class ComplaintService:

    def __init__(self, complaint_repository):
        # Dependency injection
        self.repository = complaint_repository

    def create_complaint(self, complaint):
        # Validate the complaint object
        if not isinstance(complaint, Complaint):
            raise ValueError("Invalid complaint object")

        # New complaints must start as Open
        if complaint.status != ComplaintStatus.OPEN:
            raise ValueError("New complaints must start as Open")

        # Check whether the complaint already exists
        if self.repository.get_by_id(complaint.complaint_id):
            raise ValueError("Complaint already exists")

        # Save through the repository
        self.repository.create(complaint)

        return complaint

    def update_status(self, complaint_id, new_status):
        # Retrieve the complaint
        complaint = self.repository.get_by_id(complaint_id)

        if complaint is None:
            raise ValueError("Complaint not found")

        # Convert the requested status to an Enum
        new_status = ComplaintStatus(new_status)

        # Validate the transition
        if not complaint.can_transition_to(new_status):
            raise ValueError("Invalid status transition")

        # Save the new status
        self.repository.update_status(
            complaint_id,
            new_status.value
        )

        # Return a new Complaint object because it is frozen
        return replace(complaint, status=new_status)
