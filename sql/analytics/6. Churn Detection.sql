SELECT 
    c.customer_id,
    c.full_name,
    lo.last_order_date,
    (CURRENT_DATE - lo.last_order_date) AS days_since_last_order,
    lo.total_orders,
    CASE 
        WHEN (CURRENT_DATE - lo.last_order_date) > 90 THEN 'Churned'
        WHEN (CURRENT_DATE - lo.last_order_date) > 60 THEN 'At Risk'
        WHEN (CURRENT_DATE - lo.last_order_date) > 30 THEN 'Engaged'
        ELSE 'Active'
    END AS churn_status
FROM (
    SELECT 
        customer_id,
        MAX(order_date) AS last_order_date,
        COUNT(*) AS total_orders
    FROM fact_orders
    WHERE order_date IS NOT NULL
    GROUP BY customer_id
) lo
JOIN dim_customers c ON lo.customer_id = c.customer_id
WHERE (CURRENT_DATE - lo.last_order_date) > 30
ORDER BY days_since_last_order DESC;