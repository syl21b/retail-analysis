SELECT name 
FROM sys.procedures
WHERE name LIKE 'sp_load%';


-- Check row counts in dimension tables
SELECT 'dim_customers' as table_name, COUNT(*) as row_count FROM dim_customers
UNION ALL SELECT 'dim_products', COUNT(*) FROM dim_products
UNION ALL SELECT 'dim_location', COUNT(*) FROM dim_location
UNION ALL SELECT 'dim_time', COUNT(*) FROM dim_time
UNION ALL SELECT 'dim_payment', COUNT(*) FROM dim_payment
UNION ALL SELECT 'dim_status', COUNT(*) FROM dim_status;

-- Check fact table volume
SELECT COUNT(*) as fact_orders_count, 
       COUNT(DISTINCT order_id) as unique_orders
FROM fact_orders;

-- Validate referential integrity
SELECT COUNT(*) as orphaned_records
FROM fact_orders f
LEFT JOIN dim_customers c ON f.customer_id = c.customer_id
WHERE c.customer_id IS NULL;