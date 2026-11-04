# Integration Test Report

**Project:** Banking Complaint Management System  
**Technology Stack:** Python 3.13, FastAPI, SQLAlchemy ORM, PostgreSQL, pytest  
**Test Database:** `banking_complaint_test`  
**Test Date:** November 3, 2026  
**Overall Result:** PASS

---

## 1. Objective

The purpose of integration testing was to verify that the Banking Complaint Management System correctly integrates its FastAPI endpoints, business logic, SQLAlchemy ORM, and PostgreSQL database.

The tests focused on:

- Database isolation and transaction rollback.
- Successful customer lookup, complaint creation, and status updates.
- Error handling for invalid requests and operations.
- Database state consistency.
- Test repeatability and order independence.

## 2. Test Environment

Integration tests were executed using a dedicated PostgreSQL database named `banking_complaint_test`, separate from the development database.

The test environment used:

- `pytest` for test execution.
- FastAPI `TestClient` for HTTP endpoint testing.
- SQLAlchemy sessions for database operations.
- FastAPI dependency overrides for database session injection.
- Database transactions and savepoints for test isolation.

The fixtures were implemented in `tests/integration/conftest.py`.

Each test used an isolated database transaction that was rolled back after execution, preventing test records from persisting.

## 3. Test Coverage and Results

### 3.1 Test Environment

| Test | Expected Result | Status |
|---|---|---|
| Database connection | PostgreSQL connection succeeds | PASS |
| Seeded customer | Test customer can be retrieved | PASS |
| Customer isolation — Run 1 | Transaction isolation works | PASS |
| Customer isolation — Run 2 | Transaction isolation works repeatedly | PASS |

**Result: 4/4 passed**

### 3.2 Positive Flows

| Test | Expected Result | Status |
|---|---|---|
| Customer lookup | HTTP 200 and correct customer data | PASS |
| Complaint creation | HTTP 201; complaint and initial history saved | PASS |
| Valid status update | HTTP 200; Open → In Progress | PASS |

**Result: 3/3 passed**

The positive tests also verified PostgreSQL records directly using SQLAlchemy ORM.

Complaint creation produced an initial history event with `old_status = NULL` and `new_status = Open`.

A valid status update changed the complaint to `In Progress` and created a second history event.

### 3.3 Negative Flows

| Test | Expected Result | Status |
|---|---|---|
| Complaint not found | HTTP 404 | PASS |
| Missing required field | HTTP 422 | PASS |
| Invalid status transition | HTTP 409 | PASS |
| Database unavailable | HTTP 503 | PASS |

**Result: 4/4 passed**

The negative tests confirmed that invalid requests were rejected appropriately.

The invalid transition test also verified that the complaint remained `Open` and no additional history record was created.

The database unavailability test simulated a connection failure and verified the application's standardized error response.

## 4. Repeatability and Order Independence

The complete integration test suite was executed three times.

| Execution | Tests Passed | Tests Failed | Result |
|---|---:|---:|---|
| First execution | 11 | 0 | PASS |
| Second execution | 11 | 0 | PASS |
| Reverse-order execution | 11 | 0 | PASS |

**Total: 33 successful test executions across three runs.**

The results demonstrate that the integration tests are repeatable and pass independently of their normal collection order.

## 5. Database Cleanup Verification

After execution, PostgreSQL was queried to check whether test records remained.

**Complaint cleanup query:**

```sql
SELECT complaint_id, status
FROM complaint
WHERE complaint_id LIKE 'TEST_%';
```

**Result:** 0 rows

**Customer cleanup query:**

```sql
SELECT customer_id
FROM customer
WHERE customer_id LIKE 'TEST_%';
```

**Result:** 0 rows

These results support successful cleanup of the test records matching the specified prefixes.

## 6. Defect Identified and Resolved

During complaint creation testing, PostgreSQL rejected the initial status history record because the `old_status` column had a `NOT NULL` constraint.

**Observed error:**

```text
null value in column "old_status"
violates not-null constraint
```

**Root cause:** The complaint creation service records an initial status history event with no previous status, but the database schema initially required a non-null value.

**Resolution:**

The SQLAlchemy model was updated to permit a nullable previous status:

```python
old_status: Mapped[str | None] = mapped_column(
    String,
    nullable=True
)
```

The corresponding PostgreSQL test database constraint was updated.

After the correction, complaint creation and all subsequent integration tests passed.

**Follow-up:** Ensure the same schema definition is consistently maintained through the project's database migration process.

## 7. Test Evidence

The following evidence was produced:

- Integration fixtures in `tests/integration/conftest.py`.
- Environment and isolation tests in `tests/integration/test_connection.py`.
- Positive flow tests in `tests/integration/test_positive_flows.py`.
- Negative flow tests in `tests/integration/test_negative_flows.py`.
- Two successful consecutive test suite executions.
- One successful reverse-order execution.
- PostgreSQL queries returning zero matching test records.

## 8. Conclusion

**Overall Status: PASS**

All 11 integration tests passed during the first run, second run, and reverse-order execution.

The results confirm that the tested API operations, business rules, and database interactions behave as expected under the covered scenarios.

The tests also demonstrated successful transaction isolation and repeatable execution.

**Final Outcome: 11/11 integration tests passed, with no failures across three executions.**

The integration testing exercise is complete.