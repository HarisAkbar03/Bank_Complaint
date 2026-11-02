from fastapi import FastAPI
from middleware import correlation_middleware
from routers.health import router as health_router
from routers.customers import router as customers_router
from routers.complaints import router as complaints_router
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import OperationalError

from exception_handler import (
    http_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    unexpected_exception_handler
)

app = FastAPI(
    title="Banking Complaint Management API",
    version="1.0.0"
)
app.add_exception_handler(
    HTTPException,
    http_exception_handler
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)

app.add_exception_handler(
    OperationalError,
    database_exception_handler
)

app.add_exception_handler(
    Exception,
    unexpected_exception_handler
)
app.middleware("http")(correlation_middleware)
app.include_router(health_router)
app.include_router(customers_router)
app.include_router(complaints_router)


@app.get("/")
def root():
    return {"message": "Banking Complaint API is running"}