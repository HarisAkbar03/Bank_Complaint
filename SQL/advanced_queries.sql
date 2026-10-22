
SELECT
    CASE
        WHEN CURRENT_DATE - received_at::date <= 7 THEN '0-7 Days'
        WHEN CURRENT_DATE - received_at::date <= 30 THEN '8-30 Days'
        ELSE '31+ Days'
    END AS age_bucket,
    COUNT(*) AS complaint_count
FROM complaint
GROUP BY age_bucket;

--
WITH ComplaintCounts AS (
    SELECT
        customer_id,
        COUNT(*) AS total_complaints
    FROM complaint
    GROUP BY customer_id
),
RepeatComplaints AS (
    SELECT
        customer_id,
        total_complaints
    FROM ComplaintCounts
    WHERE total_complaints > 1
),
EscalationContext AS (
    SELECT
        c.customer_id,
        COUNT(DISTINCT c.complaint_id)
            AS complaints_with_reviews
    FROM complaint c
    JOIN review_request r
        ON c.complaint_id = r.complaint_id
    GROUP BY c.customer_id
)
SELECT
    r.customer_id,
    r.total_complaints,
    COALESCE(e.complaints_with_reviews, 0)
        AS complaints_with_reviews
FROM RepeatComplaints r
LEFT JOIN EscalationContext e
    ON r.customer_id = e.customer_id
ORDER BY r.total_complaints DESC, r.customer_id;

--
WITH LatestStatus AS (
    SELECT
        complaint_id,
        new_status,
        changed_at,
        ROW_NUMBER() OVER (
            PARTITION BY complaint_id
            ORDER BY changed_at DESC,
                     history_id DESC
        ) AS rn
    FROM complaint_status_history
)
SELECT
    complaint_id,
    new_status AS latest_status,
    changed_at
FROM LatestStatus
WHERE rn = 1;

WITH ComplaintCounts AS (
    SELECT
        customer_id,
        COUNT(*) AS total_complaints
    FROM complaint
    GROUP BY customer_id
)
SELECT
    customer_id,
    total_complaints,
    ROW_NUMBER() OVER (
        ORDER BY total_complaints DESC,
                 customer_id ASC
    ) AS customer_rank
FROM ComplaintCounts;