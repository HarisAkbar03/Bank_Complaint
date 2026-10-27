from repositories.models import Account

class AccountRepository:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, record_id):
        with self.db.session() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT account_id, customer_id, account_type, status, current_balance FROM account WHERE account_id = %s",
                    (record_id,)
                )
                row = cursor.fetchone()
                return Account(*row) if row else None

    def list_by_customer(self, customer_id):
        with self.db.session() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT account_id, customer_id, account_type, status, current_balance FROM account WHERE customer_id = %s ORDER BY account_id",
                    (customer_id,)
                )
                return [Account(*row) for row in cursor.fetchall()]
