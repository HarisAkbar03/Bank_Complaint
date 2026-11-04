# Week 3 Release Notes

**Project:** Banking Complaint Management System  
**Version:** 1.0.0  
**Release status:** Pending final demo and tagging

## Features

- Customer and complaint retrieval.
- Complaint creation with initial Open status.
- Complaint status updates with enforced business rules.
- Complaint status history tracking.
- Standardized API error handling.
- Correlation ID tracking for requests.
- PostgreSQL persistence using SQLAlchemy ORM.

## Fixes

- Updated complaint history response validation to allow null previous statuses.
- Added case-insensitive complaint status matching using enum normalization.

## Testing and Verification

- Completed manual end-to-end complaint workflow verification.
- Executed unit and integration test suites.
- Generated automated test reports.
- Exported OpenAPI specification.

**Test result:** Record the actual passing, failing, and skipped test counts from the latest test report before release.

## Known Risks

- Database availability affects API operations.
- Database schema must remain consistent across environments.
- Concurrent status updates depend on correct transaction handling.
- Automated test coverage does not guarantee the absence of all defects.

## Release Evidence

- `reports/test_results.xml`
- `reports/openapi.json`
- End-to-end scenario screenshots
- Updated architecture documentation
- Updated README and specification

## Release Decision

Pending final demonstration, review of test results, and creation of the Week 3 Git tag.