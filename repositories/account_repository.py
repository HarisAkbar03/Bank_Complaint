from sqlalchemy import select
from database import SessionLocal
from repositories.models import Account


class AccountRepository:

    # Initialize the repository with a session factory
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    # Find an account using its account ID
    def get_by_id(self, record_id):

        # Open a SQLAlchemy ORM session
        with self.session_factory() as session:

            # Retrieve an account using its primary key
            account = session.get(Account, record_id)

            # Return the Account object or None
            return account

    # Get all accounts belonging to a customer
    def list_by_customer(self, customer_id):

        # Open a SQLAlchemy ORM session
        with self.session_factory() as session:

            # Build an ORM query to filter accounts by customer ID
            statement = (
                select(Account)
                .where(Account.customer_id == customer_id)
                .order_by(Account.account_id)
            )

            # Execute the query and retrieve Account objects
            accounts = session.scalars(statement).all()

            # Return the list of accounts
            return accounts