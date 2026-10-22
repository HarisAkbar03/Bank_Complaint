# Advanced SQL Explanation

## 1. CTE Analysis

Common Table Expressions (CTEs) organize complex SQL queries into readable stages.

- **ComplaintCounts:** Calculates the total number of complaints for each customer.
- **RepeatComplaints:** Identifies customers who submitted more than one complaint.
- **EscalationContext:** Counts escalated complaints for each customer.

The final query combines repeat complaint counts with escalation information.

## 2. Window Functions

**ROW_NUMBER():** Assigns a unique sequential number to rows based on the specified ordering.

**PARTITION BY:** Divides records into separate customer groups so that numbering restarts for each customer.

**ORDER BY:** Determines the sequence of records within each partition or ranking.

**Tie handling:** Uses complaint_id or customer_id as an additional sorting column to ensure deterministic results, assuming these IDs are unique.

## 3. Boundaries and Expected Grain

- CTE analysis includes customers with more than one complaint.
- Escalation analysis assumes escalation_level greater than zero indicates escalation.
- Latest-status analysis returns one record per customer.
- Customer ranking returns one record per customer.
- Latest status is determined using last_updated, with complaint_id as the tie-breaker.
- Complaint counts include all records unless additional date or status filters are applied.


## 4. Validation

1. Verify complaint counts using COUNT(*) and GROUP BY.
2. Confirm repeat customers have more than one complaint.
3. Check that escalated complaints do not exceed total complaints.
4. Confirm the latest-status query returns exactly one row per customer.
5. Verify customers with equal complaint counts are ordered consistently.
6. Check for missing customer IDs and timestamps that could affect results.

## Conclusion

CTEs improve query readability by separating business logic into stages. Window functions identify the latest customer status and rank customers by complaint volume. Deterministic ordering ensures consistent results when ties occur.