SELECT 
    dl.state,
    SUM(COALESCE(fo.total_amount, 0)) AS revenue
FROM warehouse.fact_orders fo
INNER JOIN warehouse.dim_location dl ON fo.location_id = dl.location_id
GROUP BY dl.state
ORDER BY revenue DESC;