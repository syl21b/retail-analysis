-- Customer Lifetime Value (CLV) Analysis - PostgreSQL Version
WITH cte_customer_revenue AS (
    SELECT 
        f.customer_id, 
        c.full_name,
        SUM(COALESCE(f.net_amount, 0)) AS total_net_amount
    FROM warehouse.fact_orders f
    JOIN warehouse.dim_customers c 
        ON f.customer_id = c.customer_id
    GROUP BY f.customer_id, c.full_name
)
SELECT * FROM (
    SELECT 
        customer_id, 
        full_name, 
        ROUND(CAST(total_net_amount AS numeric), 2) AS total_net_amount, 
        'Highest' AS category
    FROM cte_customer_revenue
    WHERE total_net_amount IS NOT NULL
    ORDER BY total_net_amount DESC
    LIMIT 5
) t

UNION ALL

SELECT * FROM (
    SELECT 
        customer_id, 
        full_name, 
        ROUND(CAST(total_net_amount AS numeric), 2) AS total_net_amount, 
        'Lowest' AS category
    FROM cte_customer_revenue
    WHERE total_net_amount IS NOT NULL
    ORDER BY total_net_amount ASC
    LIMIT 5
) u;