WITH cohort_data AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', order_date) AS order_month,
        DATE_TRUNC('month', MIN(order_date) OVER (PARTITION BY customer_id)) AS cohort_month
    FROM fact_orders
    WHERE order_date IS NOT NULL
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id) AS total_customers
    FROM cohort_data
    GROUP BY cohort_month
),
retention_by_cohort_month AS (
    SELECT
        c.cohort_month,
        EXTRACT(YEAR FROM AGE(c.order_month, c.cohort_month)) * 12 + 
        EXTRACT(MONTH FROM AGE(c.order_month, c.cohort_month)) AS month_number,
        COUNT(DISTINCT c.customer_id) AS retained_customers
    FROM cohort_data c
    GROUP BY c.cohort_month, month_number
)
SELECT
    TO_CHAR(r.cohort_month, 'YYYY-MM') AS cohort_month,
    r.month_number,
    ROUND((r.retained_customers * 100.0) / cs.total_customers, 2) AS retention_rate
FROM retention_by_cohort_month r
JOIN cohort_sizes cs ON r.cohort_month = cs.cohort_month
WHERE r.month_number <= 12
ORDER BY r.cohort_month, r.month_number;