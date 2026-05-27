WITH rfm AS (
    SELECT 
        customer_id,
        DATEDIFF(DAY, MAX(order_date), GETDATE()) AS recency,
        COUNT(DISTINCT order_id) AS frequency,
        SUM(total_amount) AS monetary
    FROM fact_orders
    GROUP BY customer_id
)

SELECT *,
    CASE 
        WHEN monetary > 2000 AND frequency >= 10 THEN 'VIP'
        WHEN frequency >= 5 THEN 'Loyal'
        WHEN recency > 90 THEN 'Churn Risk'
        ELSE 'Regular'
    END AS segment
INTO customer_segments
FROM rfm;
