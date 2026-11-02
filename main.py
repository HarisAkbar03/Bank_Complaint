from fastapi import FastAPI

from routers.health import router as health_router
from routers.customers import router as customers_router
from routers.complaints import router as complaints_router


app = FastAPI(
    title="Banking Complaint Management API",
    version="1.0.0"
)

app.include_router(health_router)
app.include_router(customers_router)
app.include_router(complaints_router)


@app.get("/")
def root():
    return {"message": "Banking Complaint API is running"}