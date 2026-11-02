from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from dependencies import get_db
from repositories.models import Customer, Complaint
from schemas.api import CustomerResponse, ComplaintResponse


router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):

    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return customer


@router.get(
    "/{customer_id}/complaints",
    response_model=list[ComplaintResponse]
)
def get_customer_complaints(
    customer_id: str,
    db: Session = Depends(get_db)
):

    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    complaints = db.scalars(
        select(Complaint)
        .where(Complaint.customer_id == customer_id)
        .order_by(Complaint.received_at)
    ).all()

    return complaints