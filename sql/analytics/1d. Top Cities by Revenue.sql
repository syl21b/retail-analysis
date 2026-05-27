SELECT l.city, SUM(COALESCE(f.total_amount, 0)) AS total_revenue
FROM warehouse.fact_orders f
INNER JOIN warehouse.dim_location l ON f.location_id = l.location_id
GROUP BY l.city
ORDER BY total_revenue DESC;