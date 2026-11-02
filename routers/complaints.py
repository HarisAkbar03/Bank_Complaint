from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from repositories.models import ComplaintStatusHistory
from schemas.api import StatusUpdate, StatusHistoryResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from dependencies import get_db
from repositories.models import Customer, Complaint, ComplaintStatus
from schemas.api import ComplaintCreate, ComplaintResponse


router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.get("/{complaint_id}", response_model=ComplaintResponse)
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


@router.post(
    "",
    status_code=status.HTTP_201_CREATED
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

    if db.get(Complaint, data.complaint_id) is not None:
        raise HTTPException(
            status_code=409,
            detail="Complaint ID already exists"
        )

    complaint = Complaint(
        complaint_id=data.complaint_id,
        customer_id=data.customer_id,
        category=data.category,
        status=ComplaintStatus.OPEN.value,
        received_at=data.received_at or datetime.now(timezone.utc)
    )

    try:
        db.add(complaint)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Complaint could not be created due to a database constraint"
        )

    return {
        "message": "Complaint created successfully",
        "complaint_id": complaint.complaint_id
    }

@router.patch("/{complaint_id}/status")
def update_complaint_status(
    complaint_id: str,
    data: StatusUpdate,
    db: Session = Depends(get_db)
):

    # Lock the complaint row during the status change
    complaint = db.scalar(
        select(Complaint)
        .where(Complaint.complaint_id == complaint_id)
        .with_for_update()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    try:
        new_status = ComplaintStatus(data.status)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid complaint status"
        )

    if not complaint.can_transition_to(new_status):
        raise HTTPException(
            status_code=409,
            detail="Invalid status transition"
        )

    old_status = ComplaintStatus(complaint.status)

    complaint.status = new_status.value

    event = ComplaintStatusHistory(
        complaint_id=complaint_id,
        old_status=old_status.value,
        new_status=new_status.value,
        changed_at=datetime.now(timezone.utc)
    )

    db.add(event)
    db.commit()

    return {
        "complaint_id": complaint_id,
        "old_status": old_status.value,
        "new_status": new_status.value,
        "message": "Status updated successfully"
    }
@router.get(
    "/{complaint_id}/history",
    response_model=list[StatusHistoryResponse]
)
def get_status_history(
    complaint_id: str,
    db: Session = Depends(get_db)
):

    if db.get(Complaint, complaint_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return db.scalars(
        select(ComplaintStatusHistory)
        .where(ComplaintStatusHistory.complaint_id == complaint_id)
        .order_by(ComplaintStatusHistory.changed_at)
    ).all()