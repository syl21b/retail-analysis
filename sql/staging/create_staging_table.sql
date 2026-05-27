USE master;
GO


-- Drop dimension tables
IF OBJECT_ID('stg_order_items', 'U') IS NOT NULL
    DROP TABLE stg_order_items;
GO

IF OBJECT_ID('stg_orders', 'U') IS NOT NULL
    DROP TABLE stg_orders;
GO

IF OBJECT_ID('stg_products', 'U') IS NOT NULL
    DROP TABLE stg_products;
GO

IF OBJECT_ID('stg_customers', 'U') IS NOT NULL
    DROP TABLE stg_customers;
GO

-- =========================
-- Create tables
-- =========================

CREATE TABLE stg_customers (
    customer_id INT,
    gender VARCHAR(10),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    full_name VARCHAR(100),
    age INT,
    city VARCHAR(100),
    signup_date DATE,
    age_range VARCHAR(20)
);

CREATE TABLE stg_products (
    product_id INT,
    brand VARCHAR(100),
    category VARCHAR(100),
    sub_category VARCHAR(100),
    mrp DECIMAL(10,2),
    mrp_range VARCHAR(20) 
);

CREATE TABLE stg_orders (
    order_id VARCHAR(50),
    customer_id INT,
    order_date DATE,
    order_ts DATETIME,
    city VARCHAR(100),
    state VARCHAR(100),
    payment_method VARCHAR(50),
    order_status VARCHAR(50),
    total_amount DECIMAL(10,2)
);

CREATE TABLE stg_order_items (
    order_id VARCHAR(50),
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10,2),
    discount DECIMAL(10,2),
    net_amount DECIMAL(10,2)
);