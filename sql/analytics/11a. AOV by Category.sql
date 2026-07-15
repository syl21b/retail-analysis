SELECT 
    ct.category_name AS category,
    ROUND(AVG(f.net_amount)::numeric, 2) AS avg_order_value
FROM fact_orders f
JOIN products_table p ON f.product_id = p.product_id
JOIN category_table ct ON p.category_code = ct.category_code
WHERE f.net_amount > 0
GROUP BY ct.category_name
ORDER BY avg_order_value DESC;