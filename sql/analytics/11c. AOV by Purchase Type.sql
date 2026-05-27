WITH order_items AS (
    SELECT 
        order_id,
        COUNT(product_id) AS item_count
    FROM fact_orders
    GROUP BY order_id
)
SELECT 
    CASE 
        WHEN oi.item_count = 1 THEN 'Single Item'
        WHEN oi.item_count > 1 THEN 'Multiple Items'
    END AS purchase_type,
    ROUND(AVG(f.net_amount)::numeric, 2) AS avg_order_value
FROM fact_orders f
JOIN order_items oi ON f.order_id = oi.order_id
WHERE f.net_amount > 0
GROUP BY purchase_type
ORDER BY avg_order_value DESC;