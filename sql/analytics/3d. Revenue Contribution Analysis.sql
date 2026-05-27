SELECT 
    customer_id,
    ROUND(total_revenue, 2) AS total_revenue,
    ROUND(SUM(total_revenue) OVER (ORDER BY total_revenue DESC), 2) AS cumulative_revenue,
    ROUND(SUM(total_revenue) OVER (), 2) AS total_revenue_all,
    ROUND(SUM(total_revenue) OVER (ORDER BY total_revenue DESC) * 100.0 / NULLIF(SUM(total_revenue) OVER (), 0), 2) AS cumulative_percentage
FROM (
    SELECT customer_id, SUM(COALESCE(total_amount, 0)) AS total_revenue
    FROM warehouse.fact_orders
    GROUP BY customer_id
) t
WHERE total_revenue > 0
ORDER BY total_revenue DESC;