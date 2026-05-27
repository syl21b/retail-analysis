SELECT 
    p.category,
    ROUND(AVG(f.net_amount)::numeric, 2) AS avg_order_value
FROM fact_orders f
JOIN dim_products p ON f.product_id = p.product_id
WHERE f.net_amount > 0
GROUP BY p.category
ORDER BY avg_order_value DESC;