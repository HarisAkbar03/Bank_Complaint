# Banking Complaint Management System — Test Plan

## 1. Objective

Verify that the Banking Complaint Management System correctly handles complaint creation, status transitions, input validation, missing customer records, and escalation indicators.

Testing will use pytest, reusable fixtures, fake repositories, and parametrization to verify business behavior without requiring a live PostgreSQL connection.

## 2. Happy Path Test Cases

| ID | Test scenario | Expected result |
|---|---|---|
| HP-01 | Create a complaint with valid data | Complaint is created with Open status |
| HP-02 | Transition from Open to In Progress | Transition succeeds |
| HP-03 | Transition from In Progress to Resolved | Transition succeeds |
| HP-04 | Transition from Resolved to Closed | Transition succeeds |
| HP-05 | Create complaint status history | Initial history event is recorded |
| HP-06 | Retrieve an existing complaint | Correct complaint is returned |

## 3. Boundary Test Cases

| ID | Test scenario | Expected result |
|---|---|---|
| BC-01 | Attempt transition from Closed to another status | Transition is rejected |
| BC-02 | Create a complaint with an existing complaint ID | Duplicate is rejected |
| BC-03 | Create a complaint without an optional received date | Accepted if the domain permits it |
| BC-04 | Attempt transition to the current status | Transition is rejected if self-transitions are not allowed |
| BC-05 | Check escalation at its configured threshold | Behavior matches the escalation rule |

## 4. Failure Test Cases

| ID | Test scenario | Expected result |
|---|---|---|
| FL-01 | Create complaint with invalid starting status | Validation error |
| FL-02 | Transition directly from Open to Closed | Rejected |
| FL-03 | Update nonexistent complaint | Not-found error |
| FL-04 | Create complaint for nonexistent customer | Customer is rejected |
| FL-05 | Provide invalid complaint status | Validation error |
| FL-06 | Simulate repository failure | Error is propagated or handled appropriately |
| FL-07 | Evaluate escalation indicators for nonqualifying complaints | No escalation indicator |

## 5. Testing Strategy

- **Framework:** pytest
- **Database layer:** SQLAlchemy ORM
- **Isolation:** Fake repositories and mocks
- **Fixtures:** Reusable customer, account, complaint, and repository objects
- **Parametrization:** Multiple input scenarios tested using `@pytest.mark.parametrize`
- **Assertions:** Focus on observable behavior and business rules rather than internal implementation details

## 6. Completion Criteria

- All implemented test cases pass.
- Status transitions follow the defined workflow.
- Invalid inputs and missing records are handled correctly.
- Escalation tests reflect the actual business rules.
- Existing tests continue to pass.
- Test execution evidence is saved.

## 7. Execution

Run all tests using:

`python -m pytest -v`

Record the final number of passing and failing tests in `Documentation/test_review.md`.

**Note:** Customer existence checks and escalation indicators require confirmation of their implementation before their expected results can be fully verified.