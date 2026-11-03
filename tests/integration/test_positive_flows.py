
from repositories.models import Customer

from sqlalchemy import select
from repositories.models import (
    Complaint,
    ComplaintStatus,
    ComplaintStatusHistory
)
def test_customer_lookup(client, db_session, seeded_customer):

    response = client.get(
        f"/customers/{seeded_customer.customer_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == seeded_customer.customer_id
    assert data["first_name"] == "Test"

    # Verify the customer exists in PostgreSQL
    customer = db_session.get(
        Customer,
        seeded_customer.customer_id
    )

    assert customer is not None
    assert customer.first_name == "Test"

def test_create_complaint(
    client,
    db_session,
    seeded_customer
):
    # Arrange: Prepare a valid complaint request
    complaint_id = "TEST_CMP001"

    payload = {
        "complaint_id": complaint_id,
        "customer_id": seeded_customer.customer_id,
        "category": "Billing",
        "channel": "Online"
    }

    # Act: Create complaint through FastAPI
    response = client.post(
        "/complaints",
        json=payload
    )

    # Assert: HTTP response
    assert response.status_code == 201, response.text

    data = response.json()

    assert data["complaint_id"] == complaint_id
    assert data["message"] == "Complaint created successfully"

    # Assert: Complaint was saved in PostgreSQL
    db_session.expire_all()

    complaint = db_session.get(
        Complaint,
        complaint_id
    )

    assert complaint is not None
    assert complaint.customer_id == seeded_customer.customer_id
    assert complaint.category == "Billing"
    assert complaint.status == ComplaintStatus.OPEN.value

    # Assert: Initial history event was saved
    history = db_session.scalars(
        select(ComplaintStatusHistory).where(
            ComplaintStatusHistory.complaint_id == complaint_id
        )
    ).all()

    assert len(history) == 1
    assert history[0].old_status is None
    assert history[0].new_status == ComplaintStatus.OPEN.value


def test_valid_status_update(client, db_session, seeded_customer):
    complaint_id = "TEST_CMP002"

    # Arrange: Create a complaint through the API
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

    # Act: Update status from Open to In Progress
    response = client.patch(
        f"/complaints/{complaint_id}/status",
        json={"status": "In Progress"}
    )

    # Assert: API response
    assert response.status_code == 200, response.text

    data = response.json()

    assert data["complaint_id"] == complaint_id
    assert data["old_status"] == "Open"
    assert data["new_status"] == "In Progress"

    # Assert: PostgreSQL complaint state
    db_session.expire_all()

    complaint = db_session.get(Complaint, complaint_id)

    assert complaint is not None
    assert complaint.status == ComplaintStatus.IN_PROGRESS.value

    # Assert: Both history events exist
    history = db_session.scalars(
        select(ComplaintStatusHistory)
        .where(ComplaintStatusHistory.complaint_id == complaint_id)
        .order_by(ComplaintStatusHistory.history_id)
    ).all()

    assert len(history) == 2

    assert history[0].old_status is None
    assert history[0].new_status == "Open"

    assert history[1].old_status == "Open"
    assert history[1].new_status == "In Progress"
