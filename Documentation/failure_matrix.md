# API Failure Testing Matrix

## Banking Complaint Management System

**Objective:** Verify that the FastAPI application returns consistent error responses with HTTP status codes, error messages, and correlation IDs.

| Test Scenario | Expected HTTP Status | Actual HTTP Status | Error Code | Result |
|---|---|---|---|---|
| Missing customer | 404 | 404 | NOT_FOUND | PASS |
| Invalid complaint request | 422 | 422 | VALIDATION_ERROR | PASS |
| Database unavailable | 503 | 503 | DATABASE_UNAVAILABLE | PASS |
| Unexpected application error | 500 | 500 | INTERNAL_ERROR | PASS |

## Test Details

### Test 1 — Missing Resource
- Requested a customer that does not exist.
- API returned HTTP 404.
- Response included `NOT_FOUND`, a message, and a correlation ID.

### Test 2 — Invalid Request
- Submitted an empty JSON object to `POST /complaints`.
- API returned HTTP 422.
- Response included `VALIDATION_ERROR`.

### Test 3 — Database Unavailable
- Simulated a database connection failure using a FastAPI dependency override.
- API returned HTTP 503.
- Pytest confirmed the expected error response and matching correlation ID.

### Test 4 — Unexpected Error
- Simulated an unexpected `RuntimeError` in a test endpoint.
- API returned HTTP 500.
- Pytest confirmed the `INTERNAL_ERROR` response and matching correlation ID.

## Logging and Security

Structured logs record the request operation, outcome, duration, and correlation ID.

API error responses do not expose stack traces, database credentials, or sensitive complaint narratives.

## Conclusion

All four required failure scenarios passed. The application returns standardized error responses and supports request tracing through correlation IDs.