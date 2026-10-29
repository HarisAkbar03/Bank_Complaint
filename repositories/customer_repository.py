
from sqlalchemy import text
from repositories.models import Customer
from database import engine


class CustomerRepository:

    # Find a customer using their customer ID
    def get_by_id(self, record_id):

        # Open a database connection
        with engine.connect() as conn:

            # Execute a parameterized SQL query
            result = conn.execute(
                text("""
                    SELECT customer_id, first_name, last_name, email
                    FROM customer
                    WHERE customer_id = :customer_id
                """),
                {"customer_id": record_id}
            )

            # Get the first matching row
            row = result.first()

            # Return a Customer object if found, otherwise None
            return Customer(*row) if row else None
