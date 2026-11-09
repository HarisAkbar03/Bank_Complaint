
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from dependencies import get_db

from repositories.models import (
    Customer,
    Complaint,
    ComplaintStatus,
    ComplaintStatusHistory,
)

from repositories.complaint_repository import (
    ComplaintRepository
)

from services.complaint_service import (
    ComplaintService
)

from schemas.api import (
    ComplaintCreate,
    ComplaintResponse,
    StatusUpdate,
    StatusHistoryResponse,
)


router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"]
)


# ---------------------------------------------
# REQUEST SCHEMA
# ---------------------------------------------

class ComplaintUpdate(BaseModel):
    category: str | None = None
    channel: str | None = None


# ---------------------------------------------
# GET ALL COMPLAINTS WITH FILTERS
# ---------------------------------------------

@router.get(
    "",
    response_model=list[ComplaintResponse]
)
def get_all_complaints(
    status: str | None = None,
    category: str | None = None,
    customer_id: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = select(Complaint)

    if status is not None:
        try:
            selected_status = ComplaintStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Invalid complaint status"
            )

        query = query.where(
            Complaint.status == selected_status.value
        )

    if category is not None:
        query = query.where(
            Complaint.category == category
        )

    if customer_id is not None:
        query = query.where(
            Complaint.customer_id == customer_id
        )

    query = (
        query
        .order_by(Complaint.received_at.desc())
        .offset(skip)
        .limit(limit)
    )

    complaints = db.scalars(query).all()

    return complaints


# ---------------------------------------------
# GET COMPLAINT BY ID
# ---------------------------------------------

@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse
)
def get_complaint(
    complaint_id: str,
    db: Session = Depends(get_db)
):
    complaint = db.get(Complaint, complaint_id)

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return complaint


# ---------------------------------------------
# CREATE COMPLAINT
# ---------------------------------------------

@router.post(
    "",
    status_code=201
)
def create_complaint(
    data: ComplaintCreate,
    db: Session = Depends(get_db)
):
    if db.get(Customer, data.customer_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    existing = db.get(
        Complaint,
        data.complaint_id
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Complaint already exists"
        )

    complaint = Complaint(
        complaint_id=data.complaint_id,
        customer_id=data.customer_id,
        category=data.category,
        channel=data.channel,
        status=ComplaintStatus.OPEN.value,
        received_at=(
            data.received_at
            or datetime.now(timezone.utc)
        )
    )

    repository = ComplaintRepository(db)
    service = ComplaintService(repository)

    try:
        service.create_complaint(complaint)

        db.flush()
        db.commit()

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=str(error)
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Database constraint violation"
        )

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Complaint created successfully",
        "complaint_id": complaint.complaint_id
    }


# ---------------------------------------------
# UPDATE COMPLAINT DETAILS
# ---------------------------------------------

@router.put(
    "/{complaint_id}",
    response_model=ComplaintResponse
)
def update_complaint(
    complaint_id: str,
    data: ComplaintUpdate,
    db: Session = Depends(get_db)
):
    complaint = db.get(
        Complaint,
        complaint_id
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    changes = data.model_dump(
        exclude_unset=True
    )

    if not changes:
        raise HTTPException(
            status_code=422,
            detail="No fields provided for update"
        )

    if "category" in changes:
        if not changes["category"]:
            raise HTTPException(
                status_code=422,
                detail="Category cannot be empty"
            )

        complaint.category = changes["category"]

    if "channel" in changes:
        if not changes["channel"]:
            raise HTTPException(
                status_code=422,
                detail="Channel cannot be empty"
            )

        complaint.channel = changes["channel"]

    try:
        db.commit()
        db.refresh(complaint)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Database constraint violation"
        )

    return complaint


# ---------------------------------------------
# UPDATE COMPLAINT STATUS
# ---------------------------------------------

@router.patch(
    "/{complaint_id}/status"
)
def update_complaint_status(
    complaint_id: str,
    data: StatusUpdate,
    db: Session = Depends(get_db)
):
    complaint = db.scalar(
        select(Complaint)
        .where(
            Complaint.complaint_id == complaint_id
        )
        .with_for_update()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    try:
        new_status = ComplaintStatus(
            data.status
        )

    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid complaint status"
        )

    if not complaint.can_transition_to(
        new_status
    ):
        raise HTTPException(
            status_code=409,
            detail="Invalid status transition"
        )

    old_status = ComplaintStatus(
        complaint.status
    )

    complaint.status = new_status.value

    event = ComplaintStatusHistory(
        complaint_id=complaint_id,
        old_status=old_status.value,
        new_status=new_status.value,
        changed_at=datetime.now(
            timezone.utc
        )
    )

    try:
        db.add(event)
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Database constraint violation"
        )

    return {
        "complaint_id": complaint_id,
        "old_status": old_status.value,
        "new_status": new_status.value,
        "message": "Status updated successfully"
    }


# ---------------------------------------------
# GET COMPLAINT STATUS HISTORY
# ---------------------------------------------

@router.get(
    "/{complaint_id}/history",
    response_model=list[StatusHistoryResponse]
)
def get_status_history(
    complaint_id: str,
    db: Session = Depends(get_db)
):
    if db.get(
        Complaint,
        complaint_id
    ) is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    history = db.scalars(
        select(ComplaintStatusHistory)
        .where(
            ComplaintStatusHistory.complaint_id
            == complaint_id
        )
        .order_by(
            ComplaintStatusHistory.changed_at
        )
    ).all()

    return history
