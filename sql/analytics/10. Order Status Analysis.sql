SELECT 
    s.order_status,
    COUNT(*) AS total_orders
FROM fact_orders f
JOIN dim_status s ON f.status_id = s.status_id
GROUP BY s.order_status
ORDER BY total_orders DESC;