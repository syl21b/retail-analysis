-- Order value distribution
SELECT 
    CASE 
        WHEN total_amount < 500 THEN 'Low Value (<$500)'
        WHEN total_amount BETWEEN 500 AND 2000 THEN 'Mid Value ($500-$2000)'
        ELSE 'High Value (>$2000)'
    END AS order_value_bucket,
    COUNT(*) AS order_count,
    ROUND(AVG(total_amount), 2) AS average_order_value,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM fact_orders
GROUP BY 
    CASE 
        WHEN total_amount < 500 THEN 'Low Value (<$500)'
        WHEN total_amount BETWEEN 500 AND 2000 THEN 'Mid Value ($500-$2000)'
        ELSE 'High Value (>$2000)'
    END
ORDER BY order_value_bucket;

-- Order value statistics
SELECT 
    MAX(total_amount) AS max_order_value, 
    MIN(total_amount) AS min_order_value, 
    ROUND(AVG(total_amount), 2) AS avg_order_value,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_amount) AS median_order_value
FROM fact_orders;