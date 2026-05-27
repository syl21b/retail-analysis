SELECT 
    dp.sub_category,
    SUM(COALESCE(fo.total_amount, 0)) AS revenue
FROM warehouse.fact_orders fo
INNER JOIN warehouse.dim_products dp ON fo.product_id = dp.product_id
GROUP BY dp.sub_category
ORDER BY revenue DESC;