from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from main import app
from dependencies import get_db


def failing_db():
    # Simulate PostgreSQL being unavailable
    raise OperationalError(
        "Simulated connection failure",
        {},
        Exception("Database unavailable")
    )
    yield


def test_database_unavailable():

    # Temporarily replace the database dependency
    app.dependency_overrides[get_db] = failing_db

    try:
        with TestClient(app) as client:
            response = client.get("/health/ready")

        print("\nHTTP Status:", response.status_code)
        print("Response:", response.json())

        assert response.status_code == 503
        assert response.json()["code"] == "DATABASE_UNAVAILABLE"

        assert "correlation_id" in response.json()

        assert (
            response.headers["x-correlation-id"]
            == response.json()["correlation_id"]
        )

    finally:
        # Restore normal database dependency
        app.dependency_overrides.pop(get_db, None)
        