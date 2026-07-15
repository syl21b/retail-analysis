SELECT 
    dp.payment_method,
    COUNT(DISTINCT fo.order_id) AS total_orders,
    SUM(COALESCE(fo.total_amount, 0)) AS revenue,
    ROUND(AVG(COALESCE(fo.total_amount, 0)), 2) AS avg_order_value,
    COUNT(DISTINCT fo.customer_id) AS unique_customers
FROM fact_orders fo
INNER JOIN payment_table dp ON fo.payment_code = dp.payment_code
GROUP BY dp.payment_method
ORDER BY revenue DESC;