from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from dependencies import get_db


router = APIRouter(
    prefix="/health",
    tags=["Health"]
)


# Check whether FastAPI is running
@router.get("/live")
def liveness():
    return {"status": "alive"}


# Check whether PostgreSQL is accessible
@router.get("/ready")
def readiness(db: Session = Depends(get_db)):

    try:
        # Obtain a connection through the ORM session
        connection = db.connection()

        # Execute a lightweight database connectivity check
        connection.exec_driver_sql("SELECT 1")

        return {
            "status": "ready",
            "database": "connected"
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not ready",
                "database": "unavailable"
            }
        )