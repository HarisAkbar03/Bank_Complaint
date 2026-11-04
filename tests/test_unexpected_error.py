from fastapi.testclient import TestClient

from main import app


def test_unexpected_error():

    # Temporary test-only endpoint
    async def failing_endpoint():
        raise RuntimeError("Simulated unexpected error")

    app.add_api_route(
        "/test/unexpected-error",
        failing_endpoint,
        methods=["GET"]
    )

    # Prevent TestClient from re-raising server exceptions
    with TestClient(
        app,
        raise_server_exceptions=False
    ) as client:
        response = client.get("/test/unexpected-error")

    print("\nHTTP Status:", response.status_code)
    print("Response:", response.json())

    assert response.status_code == 500

    assert response.json()["code"] == "INTERNAL_ERROR"

    assert response.json()["message"] == (
        "An unexpected error occurred"
    )

    assert "correlation_id" in response.json()

    assert (
        response.headers["x-correlation-id"]
        == response.json()["correlation_id"]
    )