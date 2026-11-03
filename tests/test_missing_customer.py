
import pytest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from main import app
from dependencies import get_db
from repositories.models import Customer


@pytest.mark.parametrize(
    "customer_id",
    [
        "UNKNOWN",
        "C999",
        "MISSING_CUSTOMER"
    ]
)
def test_missing_customer(customer_id):

    # Create a fake database session
    fake_db = MagicMock()

    # Simulate a customer that does not exist
    fake_db.get.return_value = None

    # Override the real database dependency
    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)

        response = client.post(
            "/complaints",
            json={
                "complaint_id": "CMP_TEST_001",
                "customer_id": customer_id,
                "category": "Billing",
                "channel": "Online"
            }
        )

        # Verify the API returns 404
        assert response.status_code == 404

        # Verify your existing error contract
        body = response.json()

        assert body["code"] == "NOT_FOUND"
        assert body["message"] == "Resource not found"
        assert body["correlation_id"]

        # Verify the customer lookup happened
       # fake_db.get.assert_called_once_with(
          #  Customer,
         #   customer_id
        #)

        # Verify no complaint was created
        fake_db.add.assert_not_called()
        fake_db.commit.assert_not_called()

    finally:
        # Restore the application's original dependencies
        app.dependency_overrides.pop(get_db, None)
