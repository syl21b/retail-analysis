SELECT 
    lt.state_name AS state,
    SUM(COALESCE(fo.total_amount, 0)) AS revenue
FROM fact_orders fo
INNER JOIN location_table lt ON fo.city_code = lt.city_code
GROUP BY lt.state_name
ORDER BY revenue DESC;