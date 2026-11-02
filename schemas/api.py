from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    first_name: str
    last_name: str
    email: str | None


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: str
    customer_id: str
    category: str
    status: str
    received_at: datetime | None


class ComplaintCreate(BaseModel):
    complaint_id: str
    customer_id: str
    category: str
    channel: str
    received_at: datetime | None = None

class StatusUpdate(BaseModel):
    status: str


class StatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: str
    old_status: str
    new_status: str
    changed_at: datetime