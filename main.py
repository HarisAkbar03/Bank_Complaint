from fastapi import FastAPI
from routers.health import router as health_router

app = FastAPI(
    title="Banking Complaint Management API",
    version="1.0.0",
    description="API for the Banking Complaint Management System"
)

app.include_router(health_router)


@app.get("/")
def root():
    return {"message": "Banking Complaint API is running"}