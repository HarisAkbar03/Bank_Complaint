
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict, EmailStr

from dependencies import get_db
from repositories.models import Customer, Complaint, Account
from schemas.api import (
    CustomerResponse,
    ComplaintResponse,
    AccountResponse,
)


router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


# ---------------------------------------------
# Request schemas
# ---------------------------------------------

class CustomerCreate(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email: str | None = None


class CustomerUpdate(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None


# ---------------------------------------------
# GET ALL CUSTOMERS
# ---------------------------------------------

@router.get(
    "",
    response_model=list[CustomerResponse]
)
def get_all_customers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    customers = db.scalars(
        select(Customer)
        .order_by(Customer.customer_id)
        .offset(skip)
        .limit(limit)
    ).all()

    return customers


# ---------------------------------------------
# GET CUSTOMER BY ID
# ---------------------------------------------

@router.get(
    "/{customer_id}",
    response_model=CustomerResponse
)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db)
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return customer


# ---------------------------------------------
# GET CUSTOMER COMPLAINTS
# ---------------------------------------------

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


# ---------------------------------------------
# GET CUSTOMER ACCOUNTS
# ---------------------------------------------

@router.get(
    "/{customer_id}/accounts",
    response_model=list[AccountResponse]
)
def get_customer_accounts(
    customer_id: str,
    db: Session = Depends(get_db)
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    accounts = db.scalars(
        select(Account)
        .where(Account.customer_id == customer_id)
        .order_by(Account.account_id)
    ).all()

    return accounts


# ---------------------------------------------
# CREATE CUSTOMER
# ---------------------------------------------

@router.post(
    "",
    response_model=CustomerResponse,
    status_code=201
)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db)
):
    existing = db.get(Customer, data.customer_id)

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Customer already exists"
        )

    customer = Customer(
        customer_id=data.customer_id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email
    )

    try:
        db.add(customer)
        db.commit()
        db.refresh(customer)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Database constraint violation"
        )

    return customer


# ---------------------------------------------
# UPDATE CUSTOMER
# ---------------------------------------------

@router.put(
    "/{customer_id}",
    response_model=CustomerResponse
)
def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    db: Session = Depends(get_db)
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    customer.first_name = data.first_name
    customer.last_name = data.last_name
    customer.email = data.email

    try:
        db.commit()
        db.refresh(customer)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Database constraint violation"
        )

    return customer


# ---------------------------------------------
# DELETE CUSTOMER
# ---------------------------------------------

@router.delete(
    "/{customer_id}"
)
def delete_customer(
    customer_id: str,
    db: Session = Depends(get_db)
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    complaint_count = db.scalar(
        select(func.count())
        .select_from(Complaint)
        .where(Complaint.customer_id == customer_id)
    )

    account_count = db.scalar(
        select(func.count())
        .select_from(Account)
        .where(Account.customer_id == customer_id)
    )

    if complaint_count or account_count:
        raise HTTPException(
            status_code=409,
            detail=(
                "Customer has linked complaints or accounts "
                "and cannot be deleted"
            )
        )

    try:
        db.delete(customer)
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Customer is referenced by other records"
        )

    return {
        "message": "Customer deleted successfully",
        "customer_id": customer_id
    }
