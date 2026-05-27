-- Monthly revenue trends
SELECT 
    TO_CHAR(order_date, 'YYYY-MM') AS year_month,
    SUM(total_amount) AS total_amount
FROM fact_orders
GROUP BY TO_CHAR(order_date, 'YYYY-MM')
ORDER BY year_month DESC;