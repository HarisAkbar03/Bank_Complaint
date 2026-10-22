--
SELECT
    category,
    COUNT(*) AS complaint_count
FROM Complaint
GROUP BY category
ORDER BY complaint_count DESC;


--
SELECT
    status,
    COUNT(*) AS complaint_count
FROM Complaint
GROUP BY status
ORDER BY complaint_count DESC;

--
SELECT
    DATE_TRUNC('month', received_at) AS complaint_month,
    COUNT(*) AS complaint_count
FROM Complaint
GROUP BY DATE_TRUNC('month', received_at)
ORDER BY complaint_month;

--
SELECT
    category,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM Complaint
GROUP BY category;


--STEP 2 --
SELECT
    c.category,
    AVG(csh.changed_at - c.received_at) AS avg_resolution_days
FROM complaint c
JOIN complaint_status_history csh
    ON c.complaint_id = csh.complaint_id
WHERE csh.new_status = 'CLOSED'
GROUP BY c.category;


--STEP 3--
SELECT
    CURRENT_DATE AS calculation_date,
    'All Complaints' AS grouping,
    'Total Complaints' AS metric_name,
    COUNT(*) AS metric_value
FROM Complaint

UNION ALL

SELECT
    CURRENT_DATE,
    'All Complaints',
    'Distinct Customers',
    COUNT(DISTINCT customer_id)
FROM Complaint;

