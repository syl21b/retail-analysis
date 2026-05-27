SELECT 
    customer_id,
    order_date,
    previous_order_date,
    (order_date - previous_order_date) AS days_between_orders
FROM (
    SELECT 
        customer_id, 
        order_date,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS previous_order_date
    FROM fact_orders
    WHERE order_date IS NOT NULL
) t
WHERE previous_order_date IS NOT NULL
ORDER BY days_between_orders DESC;