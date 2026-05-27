-- Status Distribution
SELECT 
    ds.order_status, 
    COUNT(*) AS order_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM warehouse.fact_orders), 2) AS status_percentage
FROM warehouse.fact_orders fo
INNER JOIN warehouse.dim_status ds ON fo.status_id = ds.status_id
GROUP BY ds.order_status
ORDER BY status_percentage DESC;