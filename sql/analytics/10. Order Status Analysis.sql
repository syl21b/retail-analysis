SELECT 
    s.order_status,
    COUNT(*) AS total_orders
FROM fact_orders f
JOIN status_table s ON f.status_code = s.status_code
GROUP BY s.order_status
ORDER BY total_orders DESC;