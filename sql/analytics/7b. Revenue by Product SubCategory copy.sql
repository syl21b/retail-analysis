SELECT 
    sct.sub_category_name AS sub_category,
    COALESCE(SUM(fo.total_amount), 0) AS revenue
FROM sub_category_table sct
LEFT JOIN products_table p ON sct.sub_category_code = p.sub_category_code
LEFT JOIN fact_orders fo ON p.product_id = fo.product_id
GROUP BY sct.sub_category_name
ORDER BY revenue DESC;