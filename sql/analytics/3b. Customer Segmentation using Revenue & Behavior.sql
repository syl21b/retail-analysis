SELECT customer_id, full_name, total_revenue
FROM (
    SELECT 
        f.customer_id, 
        c.full_name,
        SUM(f.total_amount) AS total_revenue,
        COUNT(DISTINCT f.order_id) AS total_orders,
        ROW_NUMBER() OVER (ORDER BY SUM(f.total_amount) DESC) AS revenue_rank
    FROM fact_orders f
    JOIN dim_customers c ON f.customer_id = c.customer_id
    GROUP BY f.customer_id, c.full_name
) AS ranked_customers;
--WHERE revenue_rank <= 100;