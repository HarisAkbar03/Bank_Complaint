
--Create core joins--
SELECT
    c.complaint_id,
    c.status,
    c.received_at,
    cu.customer_id,
    cu.first_name,
    cu.last_name,
    a.account_id,
    a.account_number
FROM Complaint c
INNER JOIN Customer cu
    ON c.customer_id = cu.customer_id
LEFT JOIN Account a
    ON c.account_id = a.account_id;

--Detect duplication --
SELECT COUNT(*) AS complaint_count
FROM Complaint;

SELECT COUNT(*) AS joined_count
FROM Complaint c
INNER JOIN Customer cu
    ON c.customer_id = cu.customer_id
LEFT JOIN Account a
    ON c.account_id = a.account_id;

-- analyst view --
SELECT COUNT(DISTINCT c.complaint_id) AS distinct_complaints
FROM Complaint c
INNER JOIN Customer cu
    ON c.customer_id = cu.customer_id
LEFT JOIN Account a
    ON c.account_id = a.account_id;

-- missing account --
SELECT
    c.complaint_id,
    COUNT(*) AS row_count
FROM Complaint c
INNER JOIN Customer cu
    ON c.customer_id = cu.customer_id
LEFT JOIN Account a
    ON c.account_id = a.account_id
GROUP BY c.complaint_id
HAVING COUNT(*) > 1;