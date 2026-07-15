SELECT 
    lt.city_name AS city,
    SUM(COALESCE(f.total_amount, 0)) AS total_revenue
FROM fact_orders f
INNER JOIN location_table lt ON f.city_code = lt.city_code
GROUP BY lt.city_name
ORDER BY total_revenue DESC;