
import time
from uuid import UUID, uuid4

from fastapi import Request
from fastapi.responses import JSONResponse

from logging_config import log_operation


async def correlation_middleware(request: Request, call_next):

    # Get incoming correlation ID
    incoming_id = request.headers.get("X-Correlation-ID")

    try:
        correlation_id = (
            str(UUID(incoming_id))
            if incoming_id
            else str(uuid4())
        )
    except (ValueError, AttributeError):
        correlation_id = str(uuid4())

    # Store correlation ID for exception handlers
    request.state.correlation_id = correlation_id

    # Start measuring request duration
    start_time = time.perf_counter()
    status_code = 500

    try:
        # Process the API request
        response = await call_next(request)
        status_code = response.status_code

    except Exception:
        # Handle unexpected errors safely
        response = JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "correlation_id": correlation_id
            }
        )

    finally:
        # Calculate execution time
        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        # Log request details
        log_operation(
            operation=f"{request.method} {request.url.path}",
            outcome=(
                "success" if status_code < 400
                else "failure"
            ),
            duration_ms=duration_ms,
            correlation_id=correlation_id
        )

    # Include correlation ID in response headers
    response.headers["X-Correlation-ID"] = correlation_id

    return response
