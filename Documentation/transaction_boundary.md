# Complaint Creation Transaction Boundary

**Transaction:** Complaint creation

**Boundary:** The complaint record and its initial status history event must be created within one database transaction.

**Operations:**
1. Insert the complaint with status `Open`.
2. Insert the initial status history event.
3. Commit the transaction only if both operations succeed.
4. Roll back the entire transaction if either operation fails.

**Atomicity:** A complaint must never be committed without its initial status history event.

**Implementation:** Both operations use the same SQLAlchemy ORM session. The repository stages the writes, and the API endpoint controls the commit and rollback.