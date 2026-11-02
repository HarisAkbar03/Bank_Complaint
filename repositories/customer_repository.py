from database import SessionLocal
from repositories.models import Customer


class CustomerRepository:

    def get_by_id(self, customer_id):
        with SessionLocal() as session:
            return session.get(Customer, customer_id)