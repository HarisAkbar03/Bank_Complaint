from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class ComplaintStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class AccountStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    CLOSED = "Closed"


VALID_TRANSITIONS = {
    ComplaintStatus.OPEN: {ComplaintStatus.IN_PROGRESS},
    ComplaintStatus.IN_PROGRESS: {ComplaintStatus.RESOLVED},
    ComplaintStatus.RESOLVED: {ComplaintStatus.CLOSED},
    ComplaintStatus.CLOSED: set()
}


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
    status: AccountStatus
    current_balance: Decimal | None

    def __post_init__(self):
        object.__setattr__(
            self, "status", AccountStatus(self.status)
        )


@dataclass(frozen=True)
class Complaint:
    complaint_id: str
    customer_id: str
    category: str
    status: ComplaintStatus
    received_at: datetime | None

    def __post_init__(self):
        object.__setattr__(
            self, "status", ComplaintStatus(self.status)
        )

    def can_transition_to(self, new_status):
        new_status = ComplaintStatus(new_status)
        return new_status in VALID_TRANSITIONS[self.status]


@dataclass(frozen=True)
class StatusEvent:
    complaint_id: str
    old_status: ComplaintStatus
    new_status: ComplaintStatus
    changed_at: datetime

    def __post_init__(self):
        old = ComplaintStatus(self.old_status)
        new = ComplaintStatus(self.new_status)

        if new not in VALID_TRANSITIONS[old]:
            raise ValueError(
                f"Invalid transition: {old.value} to {new.value}"
            )

        object.__setattr__(self, "old_status", old)
        object.__setattr__(self, "new_status", new)