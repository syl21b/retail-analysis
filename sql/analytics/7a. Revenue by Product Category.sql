SELECT 
    dp.category,
    SUM(COALESCE(fo.total_amount, 0)) AS revenue
FROM warehouse.fact_orders fo
INNER JOIN warehouse.dim_products dp ON fo.product_id = dp.product_id
GROUP BY dp.category
ORDER BY revenue DESC;