-- Order Fulfillment Performance Analysis - PostgreSQL Version
WITH processing_time AS (
    SELECT 
        customer_id, 
        MAX(order_date) AS latest_order_date, 
        MIN(order_date) AS first_order_date,
        (MAX(order_date) - MIN(order_date)) AS fulfillment_days
    FROM warehouse.fact_orders
    WHERE order_date IS NOT NULL
    GROUP BY customer_id
)
SELECT 
    COUNT(*) AS total_customers,
    COUNT(CASE WHEN fulfillment_days > 30 THEN 1 END) AS customers_over_30d,
    ROUND(
        CAST(COUNT(CASE WHEN fulfillment_days > 30 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) AS numeric),
        2
    ) AS customers_with_long_gaps_pct
FROM processing_time
WHERE fulfillment_days IS NOT NULL;