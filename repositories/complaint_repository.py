
from sqlalchemy import text
from repositories.models import Complaint
from database import engine


class ComplaintRepository:

    def get_by_id(self, complaint_id):
        # Open a database connection
        with engine.connect() as conn:

            # Execute a parameterized SELECT query
            result = conn.execute(
                text("""
                    SELECT complaint_id, customer_id, category,
                           status, received_at
                    FROM complaint
                    WHERE complaint_id = :complaint_id
                """),
                {"complaint_id": complaint_id}
            )

            # Retrieve the first matching row
            row = result.first()

            # Convert the row into a Complaint object
            return Complaint(*row) if row else None

    def list_by_customer(self, customer_id):
        with engine.connect() as conn:

            result = conn.execute(
                text("""
                    SELECT complaint_id, customer_id, category,
                           status, received_at
                    FROM complaint
                    WHERE customer_id = :customer_id
                    ORDER BY complaint_id
                """),
                {"customer_id": customer_id}
            )

            return [
                Complaint(*row)
                for row in result.fetchall()
            ]

    def create(self, complaint):
        # Begin a transaction
        with engine.begin() as conn:

            # Insert a new complaint
            conn.execute(
                text("""
                    INSERT INTO complaint
                    (complaint_id, customer_id, category,
                     status, received_at)
                    VALUES
                    (:complaint_id, :customer_id, :category,
                     :status, :received_at)
                """),
                {
                    "complaint_id": complaint.complaint_id,
                    "customer_id": complaint.customer_id,
                    "category": complaint.category,
                    "status": complaint.status.value,
                    "received_at": complaint.received_at
                }
            )

    def update_status(self, complaint_id, new_status):
        # Begin a transaction
        with engine.begin() as conn:

            # Update complaint status
            result = conn.execute(
                text("""
                    UPDATE complaint
                    SET status = :new_status
                    WHERE complaint_id = :complaint_id
                """),
                {
                    "complaint_id": complaint_id,
                    "new_status": new_status
                }
            )

            if result.rowcount == 0:
                raise ValueError("Complaint not found")
