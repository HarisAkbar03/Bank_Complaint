from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from dependencies import get_db
from repositories.models import Employee
from schemas.api import EmployeeResponse

router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)


@router.get("", response_model=list[EmployeeResponse])
def get_all_employees(
    db: Session = Depends(get_db)
):
    employees = db.scalars(
        select(Employee)
    ).all()

    return employees


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: str,
    db: Session = Depends(get_db)
):
    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return employee