
from repositories.models import (
    Complaint,
    ComplaintStatus,
    ComplaintStatusHistory
)


class ComplaintRepository:

    def __init__(self, session):
        # Receive the shared SQLAlchemy session
        self.session = session

    def create(self, complaint):
        # Stage the complaint for insertion
        # Do not commit here
        self.session.add(complaint)

    def create_history(self, event):
        # Stage the status history event
        # Do not commit here
        self.session.add(event)

    def get_by_id(self, complaint_id):
        # Find complaint using its primary key
        return self.session.get(Complaint, complaint_id)

    def update_status(self, complaint_id, new_status):
        # Retrieve the complaint
        complaint = self.get_by_id(complaint_id)

        if complaint is None:
            raise ValueError("Complaint not found")

        # Change the ORM object's status
        complaint.status = ComplaintStatus(new_status).value

        # Do not commit here
        return complaint
