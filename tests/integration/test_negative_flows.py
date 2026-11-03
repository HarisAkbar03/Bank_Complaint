
from repositories.models import Complaint
from sqlalchemy.exc import OperationalError
from dependencies import get_db
from main import app
from sqlalchemy import select
from repositories.models import ComplaintStatusHistory
def test_complaint_not_found(client, db_session):
    # Arrange: Use a complaint ID that doesn't exist
    complaint_id = "NONEXISTENT_CMP"

    # Act: Request the complaint
    response = client.get(
        f"/complaints/{complaint_id}"
    )

    # Assert: HTTP 404
    assert response.status_code == 404, response.text

    data = response.json()

    # Verify standardized API error response
    assert data["code"] == "NOT_FOUND"
    assert data["message"] == "Resource not found"
    assert "correlation_id" in data

    # Verify no complaint was created in PostgreSQL
    complaint = db_session.get(
        Complaint,
        complaint_id
    )

    assert complaint is None

def test_create_complaint_missing_required_field(
    client,
    db_session,
    seeded_customer
):
    complaint_id = "TEST_INVALID_CMP"

    # Arrange: Request without the required category field
    payload = {
        "complaint_id": complaint_id,
        "customer_id": seeded_customer.customer_id,
        "channel": "Online"
    }

    # Act: Send invalid request
    response = client.post(
        "/complaints",
        json=payload
    )

    # Assert: FastAPI rejects the request
    assert response.status_code == 422, response.text

    data = response.json()

    # Verify standardized validation error
    assert data["code"] == "VALIDATION_ERROR"
    assert "correlation_id" in data

    # Assert: No complaint was saved in PostgreSQL
    db_session.expire_all()

    complaint = db_session.get(
        Complaint,
        complaint_id
    )

    assert complaint is None

def test_invalid_status_transition(
    client,
    db_session,
    seeded_customer
):
    complaint_id = "TEST_INVALID_TRANSITION"

    # Arrange: Create a complaint with status Open
    payload = {
        "complaint_id": complaint_id,
        "customer_id": seeded_customer.customer_id,
        "category": "Billing",
        "channel": "Online"
    }

    create_response = client.post(
        "/complaints",
        json=payload
    )

    assert create_response.status_code == 201, create_response.text

    # Act: Attempt invalid transition Open -> Closed
    response = client.patch(
        f"/complaints/{complaint_id}/status",
        json={"status": "Closed"}
    )

    # Assert: API rejects the transition
    assert response.status_code == 409, response.text

    data = response.json()

    assert data["code"] == "CONFLICT"
    assert "correlation_id" in data

    # Assert: Complaint status remains Open
    db_session.expire_all()

    complaint = db_session.get(
        Complaint,
        complaint_id
    )

    assert complaint is not None
    assert complaint.status == "Open"

    # Assert: No additional history record was created
    history = db_session.scalars(
        select(ComplaintStatusHistory).where(
            ComplaintStatusHistory.complaint_id == complaint_id
        )
    ).all()

    assert len(history) == 1
    assert history[0].old_status is None
    assert history[0].new_status == "Open"

def test_database_unavailable(client):
    # Simulate a PostgreSQL connection failure
    def unavailable_db():
        raise OperationalError(
            "SELECT 1",
            {},
            Exception("Database connection unavailable")
        )
        yield

    # Temporarily replace the database dependency
    app.dependency_overrides[get_db] = unavailable_db

    try:
        response = client.get(
            "/complaints/TEST_CMP001"
        )

        assert response.status_code == 503, response.text

        data = response.json()

        assert data["code"] == "DATABASE_UNAVAILABLE"
        assert "correlation_id" in data

        # Internal database errors must not be exposed
        assert "Database connection unavailable" not in response.text

    finally:
        # Restore the original test database dependency
        app.dependency_overrides.pop(get_db, None)
