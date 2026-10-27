from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass(frozen=True)
class Customer:
    customer_id: str
    first_name: str
    last_name: str
    email: str | None

@dataclass(frozen=True)
class Account:
    account_id: str
    customer_id: str
    account_type: str
    status: str
    current_balance: Decimal | None

@dataclass(frozen=True)
class Complaint:
    complaint_id: str
    customer_id: str
    category: str
    status: str
    received_at: datetime | None
