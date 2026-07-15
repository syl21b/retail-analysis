SELECT 
    ct.category_name AS category,
    SUM(COALESCE(fo.total_amount, 0)) AS revenue
FROM fact_orders fo
JOIN products_table p ON fo.product_id = p.product_id
JOIN category_table ct ON p.category_code = ct.category_code
GROUP BY ct.category_name
ORDER BY revenue DESC;