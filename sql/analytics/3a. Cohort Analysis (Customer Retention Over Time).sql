SELECT 
    customer_id, 
    MIN(order_date) AS first_order_date,
    EXTRACT(MONTH FROM age(CURRENT_DATE, MIN(order_date))) AS months_since_first_order
FROM fact_orders
GROUP BY customer_id
HAVING EXTRACT(MONTH FROM age(CURRENT_DATE, MIN(order_date))) <= 12
ORDER BY first_order_date;