from sqlalchemy.orm import Session
from repositories.models import Employee


class EmployeeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Employee).all()

    def get_by_id(self, employee_id: str):
        return (
            self.db.query(Employee)
            .filter(Employee.employee_id == employee_id)
            .first()
        )