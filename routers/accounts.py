
from decimal import Decimal

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
    Account,
    Customer,
    AccountStatus,
)

from schemas.api import AccountResponse


router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"]
)


# ---------------------------------------------
# REQUEST SCHEMAS
# ---------------------------------------------

class AccountCreate(BaseModel):
    account_id: str
    customer_id: str
    account_type: str
    status: AccountStatus = AccountStatus.ACTIVE
    current_balance: Decimal | None = None


class AccountUpdate(BaseModel):
    account_type: str | None = None


class AccountStatusUpdate(BaseModel):
    status: AccountStatus


# ---------------------------------------------
# GET ALL ACCOUNTS
# ---------------------------------------------

@router.get(
    "",
    response_model=list[AccountResponse]
)
def get_all_accounts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    accounts = db.scalars(
        select(Account)
        .order_by(Account.account_id)
        .offset(skip)
        .limit(limit)
    ).all()

    return accounts


# ---------------------------------------------
# GET CUSTOMER ACCOUNTS
# ---------------------------------------------

@router.get(
    "/customer/{customer_id}",
    response_model=list[AccountResponse]
)
def get_customer_accounts(
    customer_id: str,
    db: Session = Depends(get_db)
):
    if db.get(Customer, customer_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    accounts = db.scalars(
        select(Account)
        .where(
            Account.customer_id == customer_id
        )
        .order_by(Account.account_id)
    ).all()

    return accounts


# ---------------------------------------------
# GET ACCOUNT BY ID
# ---------------------------------------------

@router.get(
    "/{account_id}",
    response_model=AccountResponse
)
def get_account(
    account_id: str,
    db: Session = Depends(get_db)
):
    account = db.get(Account, account_id)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    return account


# ---------------------------------------------
# CREATE ACCOUNT
# ---------------------------------------------

@router.post(
    "",
    response_model=AccountResponse,
    status_code=201
)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db)
):
    customer = db.get(
        Customer,
        data.customer_id
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    if db.get(Account, data.account_id):
        raise HTTPException(
            status_code=409,
            detail="Account already exists"
        )

    account = Account(
        account_id=data.account_id,
        customer_id=data.customer_id,
        account_type=data.account_type,
        status=data.status.value,
        current_balance=data.current_balance
    )

    try:
        db.add(account)
        db.commit()
        db.refresh(account)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Database constraint violation"
        )

    return account


# ---------------------------------------------
# UPDATE ACCOUNT DETAILS
# ---------------------------------------------

@router.patch(
    "/{account_id}",
    response_model=AccountResponse
)
def update_account(
    account_id: str,
    data: AccountUpdate,
    db: Session = Depends(get_db)
):
    account = db.get(Account, account_id)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    changes = data.model_dump(
        exclude_unset=True
    )

    if not changes:
        raise HTTPException(
            status_code=422,
            detail="No fields provided for update"
        )

    if "account_type" in changes:
        if not changes["account_type"]:
            raise HTTPException(
                status_code=422,
                detail="Account type cannot be empty"
            )

        account.account_type = changes[
            "account_type"
        ]

    try:
        db.commit()
        db.refresh(account)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Database constraint violation"
        )

    return account


# ---------------------------------------------
# UPDATE ACCOUNT STATUS
# ---------------------------------------------

@router.patch(
    "/{account_id}/status",
    response_model=AccountResponse
)
def update_account_status(
    account_id: str,
    data: AccountStatusUpdate,
    db: Session = Depends(get_db)
):
    account = db.scalar(
        select(Account)
        .where(Account.account_id == account_id)
        .with_for_update()
    )

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    current_status = AccountStatus(
        account.status
    )

    new_status = data.status

    if current_status == AccountStatus.CLOSED:
        raise HTTPException(
            status_code=409,
            detail="Closed accounts cannot change status"
        )

    if current_status == new_status:
        raise HTTPException(
            status_code=409,
            detail="Account already has this status"
        )

    account.status = new_status.value

    try:
        db.commit()
        db.refresh(account)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Database constraint violation"
        )

    return account
