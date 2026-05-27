-- RFM Segmentation - PostgreSQL Version
WITH rfm_calc AS (
    SELECT 
        customer_id,
        EXTRACT(DAY FROM (CURRENT_DATE - MAX(order_date))) AS recency_days,
        COUNT(DISTINCT order_id) AS frequency,
        SUM(COALESCE(net_amount, 0)) AS monetary
    FROM warehouse.fact_orders
    WHERE order_date IS NOT NULL
    GROUP BY customer_id
)
SELECT 
    c.customer_id,
    c.full_name,
    COALESCE(r.recency_days, 999) AS recency_days,
    COALESCE(r.frequency, 0) AS frequency,
    COALESCE(ROUND(CAST(r.monetary AS numeric), 2), 0) AS monetary,
    CASE 
        WHEN COALESCE(r.monetary, 0) = 0 THEN 'Inactive'
        WHEN COALESCE(r.recency_days, 999) <= 30 AND COALESCE(r.frequency, 0) >= 5 THEN 'Champions'
        WHEN COALESCE(r.recency_days, 999) <= 60 AND COALESCE(r.frequency, 0) >= 3 THEN 'Loyal'
        WHEN COALESCE(r.recency_days, 999) <= 90 THEN 'Active'
        WHEN COALESCE(r.recency_days, 999) <= 180 THEN 'At Risk'
        ELSE 'Lost'
    END AS segment
FROM warehouse.dim_customers c
LEFT JOIN rfm_calc r ON c.customer_id = r.customer_id
WHERE COALESCE(r.monetary, 0) > 0  -- Only show customers with purchases
ORDER BY monetary DESC;