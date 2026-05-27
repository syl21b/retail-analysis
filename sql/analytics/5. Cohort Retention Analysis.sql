SELECT 
    TO_CHAR(cohort_month, 'YYYY-MM') AS cohort_month,
    month_number,
    COUNT(DISTINCT customer_id) AS customers,
    ROUND(COUNT(DISTINCT customer_id) * 100.0 / FIRST_VALUE(COUNT(DISTINCT customer_id)) OVER (PARTITION BY cohort_month ORDER BY month_number), 2) AS retention_rate
FROM (
    SELECT 
        customer_id,
        DATE_TRUNC('month', MIN(order_date) OVER (PARTITION BY customer_id)) AS cohort_month,
        EXTRACT(MONTH FROM AGE(DATE_TRUNC('month', order_date), DATE_TRUNC('month', MIN(order_date) OVER (PARTITION BY customer_id)))) AS month_number
    FROM fact_orders
    WHERE order_date IS NOT NULL
) t
WHERE month_number IS NOT NULL AND month_number <= 12
GROUP BY cohort_month, month_number
ORDER BY cohort_month, month_number;