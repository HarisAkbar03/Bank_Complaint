
from repositories.models import Complaint


class ComplaintRepository:

    def __init__(self, db):
        # Store the database manager
        self.db = db

    def get_by_id(self, record_id):
        # Find a complaint using its ID
        with self.db.session() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT complaint_id, customer_id, category,
                           status, received_at
                    FROM complaint
                    WHERE complaint_id = %s
                    """,
                    (record_id,)
                )

                row = cursor.fetchone()

                # Convert the database row into a Complaint object
                return Complaint(*row) if row else None

    def list_by_customer(self, customer_id):
        # Retrieve all complaints for a customer
        with self.db.session() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT complaint_id, customer_id, category,
                           status, received_at
                    FROM complaint
                    WHERE customer_id = %s
                    ORDER BY complaint_id
                    """,
                    (customer_id,)
                )

                return [
                    Complaint(*row)
                    for row in cursor.fetchall()
                ]

    def create(self, complaint):
        # Insert a new complaint into PostgreSQL
        with self.db.session() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO complaint
                    (complaint_id, customer_id, category,
                     status, received_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        complaint.complaint_id,
                        complaint.customer_id,
                        complaint.category,
                        complaint.status.value,
                        complaint.received_at
                    )
                )

    def update_status(self, complaint_id, new_status):
        # Update the complaint's status in PostgreSQL
        with self.db.session() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE complaint
                    SET status = %s
                    WHERE complaint_id = %s
                    """,
                    (new_status, complaint_id)
                )
