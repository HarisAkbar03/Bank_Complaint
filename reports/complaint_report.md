# Complaint Analysis Report

**Total complaints:** 120
**Skipped rows:** 0

## Highest-volume category

Mortgage Servicing: 31 complaints (25.83%)

## Status counts

| Status | Count |
| --- | --- |
| Closed | 34 |
| Escalated | 30 |
| In Review | 32 |
| Open | 24 |

## Category counts

| Category | Count | Percentage |
| --- | --- | --- |
| Mortgage Servicing | 31 | 25.83% |
| Card or Transaction Dispute | 25 | 20.83% |
| Service Quality | 21 | 17.50% |
| Digital Banking | 19 | 15.83% |
| Fees | 15 | 12.50% |
| Account Access | 9 | 7.50% |

## Closed-case resolution

| Category | Total | Closed | Measured | Unmeasurable | Average hours |
| --- | --- | --- | --- | --- | --- |
| Mortgage Servicing | 31 | 9 | 9 | 0 | 226.67 |
| Card or Transaction Dispute | 25 | 4 | 4 | 0 | 270.0 |
| Service Quality | 21 | 6 | 6 | 0 | 148.0 |
| Digital Banking | 19 | 4 | 4 | 0 | 198.0 |
| Fees | 15 | 6 | 6 | 0 | 248.0 |
| Account Access | 9 | 5 | 5 | 0 | 388.8 |

## Methodology

- Each valid CSV row represents one complaint.
- Incomplete rows and invalid received dates are skipped.
- Closed cases are identified by status 'Closed'.
- Resolution time = closed_at minus received_at.
- Missing, negative, or incompatible durations are excluded.
- Average resolution uses closed cases with valid durations.
- Category percentages use total valid complaints.