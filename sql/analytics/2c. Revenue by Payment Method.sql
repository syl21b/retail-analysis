SELECT 
    dp.payment_method, 
    SUM(COALESCE(fo.total_amount, 0)) AS total_revenue,
    COUNT(DISTINCT fo.order_id) AS total_orders,
    ROUND(SUM(COALESCE(fo.total_amount, 0)) * 100.0 / NULLIF((SELECT SUM(COALESCE(total_amount, 0)) FROM warehouse.fact_orders), 0), 2) AS revenue_percentage
FROM warehouse.fact_orders fo
INNER JOIN warehouse.dim_payment dp ON fo.payment_id = dp.payment_id
GROUP BY dp.payment_method
ORDER BY total_revenue DESC;