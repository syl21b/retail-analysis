USE master;
GO

-- 1. Load Unique Payment Methods
INSERT INTO dim_payment (payment_method)
SELECT DISTINCT payment_method FROM stg_orders WHERE payment_method IS NOT NULL;

-- 2. Load Unique Order Statuses
INSERT INTO dim_status (order_status)
SELECT DISTINCT order_status FROM stg_orders WHERE order_status IS NOT NULL;

-- 3. Load other dimensions (Customers, Products, Location, Time) as before...
INSERT INTO dim_customers SELECT customer_id, full_name, gender, CAST(age AS TINYINT), city, signup_date FROM stg_customers;
INSERT INTO dim_products SELECT product_id, brand, category, sub_category, mrp FROM stg_products;
INSERT INTO dim_location (city, state) SELECT DISTINCT city, state FROM stg_orders;
INSERT INTO dim_time SELECT DISTINCT order_date, YEAR(order_date), MONTH(order_date), DATENAME(MONTH, order_date) FROM stg_orders;

-- 4. Load Fact Table with Lookups
WITH fact_dedup AS (
    SELECT
        o.order_id,
        o.customer_id,
        oi.product_id,
        o.order_date,
        l.location_id,
        dp.payment_id, -- Lookup ID
        ds.status_id,  -- Lookup ID
        oi.quantity,
        oi.unit_price,
        oi.discount,
        oi.net_amount,
        o.total_amount,
        ROW_NUMBER() OVER (PARTITION BY o.order_id, oi.product_id ORDER BY (SELECT NULL)) AS rn
    FROM dbo.stg_orders o
    JOIN dbo.stg_order_items oi ON o.order_id = oi.order_id
    JOIN dbo.dim_location l ON o.city = l.city AND o.state = l.state
    JOIN dbo.dim_payment dp ON o.payment_method = dp.payment_method -- Join for ID
    JOIN dbo.dim_status ds ON o.order_status = ds.order_status      -- Join for ID
    JOIN dbo.dim_customers c ON o.customer_id = c.customer_id
    JOIN dbo.dim_products p ON oi.product_id = p.product_id
    JOIN dbo.dim_time t ON o.order_date = t.date
)
INSERT INTO dbo.fact_orders (
    order_id, customer_id, product_id, order_date, location_id, 
    payment_id, status_id, quantity, unit_price, discount, net_amount, total_amount
)
SELECT 
    order_id, customer_id, product_id, order_date, location_id, 
    payment_id, status_id, quantity, unit_price, discount, net_amount, total_amount
FROM fact_dedup 
WHERE rn = 1;
GO