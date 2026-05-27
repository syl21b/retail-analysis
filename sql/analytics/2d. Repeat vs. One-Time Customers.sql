SELECT 
    CASE 
        WHEN order_count = 1 THEN 'One-Time'
        WHEN order_count BETWEEN 2 AND 3 THEN 'Repeat (2-3)'
        WHEN order_count >= 4 THEN 'Loyal (4+)'
    END AS customer_type,
    COUNT(*) AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM (
    SELECT customer_id, COUNT(DISTINCT order_id) AS order_count
    FROM fact_orders
    GROUP BY customer_id
) t
WHERE order_count IS NOT NULL
GROUP BY 
    CASE 
        WHEN order_count = 1 THEN 'One-Time'
        WHEN order_count BETWEEN 2 AND 3 THEN 'Repeat (2-3)'
        WHEN order_count >= 4 THEN 'Loyal (4+)'
    END
ORDER BY customer_count DESC;