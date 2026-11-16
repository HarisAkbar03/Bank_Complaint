
from sqlalchemy import inspect

from database import SessionLocal
from repositories.customer_repository import CustomerRepository
from repositories.account_repository import AccountRepository
from repositories.complaint_repository import ComplaintRepository
from rag.retrieval import retrieve


def to_dict(record):
    """Convert an ORM object to a JSON-compatible dictionary."""
    if record is None:
        return None

    return {
        column.key: getattr(record, column.key)
        for column in inspect(record).mapper.column_attrs
    }


def get_customer_service(customer_id: str):
    customer = CustomerRepository().get_by_id(customer_id)
    return to_dict(customer)


def get_accounts_service(customer_id: str):
    accounts = AccountRepository().list_by_customer(customer_id)

    return [
        to_dict(account)
        for account in accounts
    ]


def get_complaint_service(complaint_id: str):
    with SessionLocal() as session:
        repo = ComplaintRepository(session)
        complaint = repo.get_by_id(complaint_id)

        return to_dict(complaint)


def search_policy_service(**kwargs):
    return retrieve(**kwargs)
