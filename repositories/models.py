from datetime import datetime
from decimal import Decimal
from enum import Enum
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
from sqlalchemy import String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class ComplaintStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

    @classmethod
    def _missing_(cls,value):
        if isinstance(value,str):
            normalized = value.strip().casefold()

            for member in cls:
                if member.value.casefold() == normalized:
                    return member

        return None


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


class Customer(Base):
    __tablename__ = "customer"

    customer_id: Mapped[str] = mapped_column(
        String, primary_key=True
    )
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String, nullable=True)


class Account(Base):
    __tablename__ = "account"

    account_id: Mapped[str] = mapped_column(
        String, primary_key=True
    )
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customer.customer_id")
    )
    account_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    current_balance: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )


class Complaint(Base):
    __tablename__ = "complaint"
    channel: Mapped[str] = mapped_column(String, nullable=False)
    complaint_id: Mapped[str] = mapped_column(
        String, primary_key=True
    )
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customer.customer_id")
    )
    category: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    def can_transition_to(self, new_status):
        current = ComplaintStatus(self.status)
        new = ComplaintStatus(new_status)

        return new in VALID_TRANSITIONS[current]


class StatusEvent:
    def __init__(self, complaint_id, old_status, new_status, changed_at):
        old = ComplaintStatus(old_status)
        new = ComplaintStatus(new_status)

        if new not in VALID_TRANSITIONS[old]:
            raise ValueError(
                f"Invalid transition: {old.value} to {new.value}"
            )

        self.complaint_id = complaint_id
        self.old_status = old
        self.new_status = new
        self.changed_at = changed_at

class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"

    # Unique identifier for each status change
    history_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Complaint associated with the status change
    complaint_id: Mapped[str] = mapped_column(
        ForeignKey("complaint.complaint_id"),
        nullable=False
    )

    # Status before the update
    old_status: Mapped[str] = mapped_column(
        String,
        nullable=True
    )

    # Status after the update
    new_status: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    # When the status changed
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
