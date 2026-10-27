from repositories.models import Complaint

class ComplaintRepository:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, record_id):
        with self.db.session() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT complaint_id, customer_id, category, status, received_at FROM complaint WHERE complaint_id = %s",
                    (record_id,)
                )
                row = cursor.fetchone()
                return Complaint(*row) if row else None

    def list_by_customer(self, customer_id):
        with self.db.session() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT complaint_id, customer_id, category, status, received_at FROM complaint WHERE customer_id = %s ORDER BY complaint_id",
                    (customer_id,)
                )
                return [Complaint(*row) for row in cursor.fetchall()]
