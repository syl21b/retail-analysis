WITH rfm_seg AS (
    SELECT 
        customer_id,
        CASE 
            WHEN EXTRACT(DAY FROM (CURRENT_DATE - MAX(order_date))) <= 30 
                 AND COUNT(DISTINCT order_id) >= 5 THEN 'Champions'
            WHEN EXTRACT(DAY FROM (CURRENT_DATE - MAX(order_date))) <= 60 
                 AND COUNT(DISTINCT order_id) >= 3 THEN 'Loyal'
            WHEN EXTRACT(DAY FROM (CURRENT_DATE - MAX(order_date))) <= 90 THEN 'Active'
            WHEN EXTRACT(DAY FROM (CURRENT_DATE - MAX(order_date))) <= 180 THEN 'At Risk'
            ELSE 'Lost'
        END AS segment
    FROM fact_orders
    GROUP BY customer_id
)
SELECT 
    rs.segment,
    ROUND(AVG(f.net_amount)::numeric, 2) AS avg_order_value
FROM fact_orders f
JOIN rfm_seg rs ON f.customer_id = rs.customer_id
WHERE f.net_amount > 0
GROUP BY rs.segment
ORDER BY avg_order_value DESC;