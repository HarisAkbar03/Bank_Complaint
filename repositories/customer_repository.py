from repositories.models import Customer

class CustomerRepository:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, record_id):
        with self.db.session() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT customer_id, first_name, last_name, email FROM customer WHERE customer_id = %s",
                    (record_id,)
                )
                row = cursor.fetchone()
                return Customer(*row) if row else None
