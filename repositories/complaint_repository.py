from database import SessionLocal
from repositories.models import Complaint, ComplaintStatus


class ComplaintRepository:

    def create(self, complaint):
        with SessionLocal.begin() as session:
            session.add(complaint)

    def get_by_id(self, complaint_id):
        with SessionLocal() as session:
            return session.get(Complaint, complaint_id)

    def update_status(self, complaint_id, new_status):
        with SessionLocal.begin() as session:
            complaint = session.get(Complaint, complaint_id)

            if complaint is None:
                raise ValueError("Complaint not found")

            complaint.status = ComplaintStatus(new_status).value