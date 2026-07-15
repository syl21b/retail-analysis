SELECT 
    pt.payment_method, 
    SUM(COALESCE(fo.total_amount, 0)) AS total_revenue,
    COUNT(DISTINCT fo.order_id) AS total_orders,
    ROUND(SUM(COALESCE(fo.total_amount, 0)) * 100.0 / NULLIF((SELECT SUM(COALESCE(total_amount, 0)) FROM fact_orders), 0), 2) AS revenue_percentage
FROM fact_orders fo
INNER JOIN payment_table pt ON fo.payment_code = pt.payment_code
GROUP BY pt.payment_method
ORDER BY total_revenue DESC;