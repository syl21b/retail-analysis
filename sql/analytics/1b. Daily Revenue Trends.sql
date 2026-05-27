-- Daily revenue trends
SELECT 
    order_date AS order_day,
    SUM(total_amount) AS total_amount
FROM fact_orders
GROUP BY order_date
ORDER BY order_day DESC;