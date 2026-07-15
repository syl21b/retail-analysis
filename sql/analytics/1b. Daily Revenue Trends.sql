SELECT 
    f.order_date AS order_day,
    EXTRACT(YEAR FROM f.order_date) AS year,
    TO_CHAR(f.order_date, 'Month') AS month_name,  
    SUM(f.total_amount) AS total_amount
FROM fact_orders f
GROUP BY f.order_date, EXTRACT(YEAR FROM f.order_date), TO_CHAR(f.order_date, 'Month')
ORDER BY f.order_date DESC;