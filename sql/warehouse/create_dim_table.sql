USE master;
GO

-- Drop fact table first due to FK dependencies
IF OBJECT_ID('fact_orders', 'U') IS NOT NULL DROP TABLE fact_orders;
GO

-- Drop existing dimensions
IF OBJECT_ID('dim_payment', 'U') IS NOT NULL DROP TABLE dim_payment;
IF OBJECT_ID('dim_status', 'U') IS NOT NULL DROP TABLE dim_status;
IF OBJECT_ID('dim_location', 'U') IS NOT NULL DROP TABLE dim_location;
IF OBJECT_ID('dim_products', 'U') IS NOT NULL DROP TABLE dim_products;
IF OBJECT_ID('dim_customers', 'U') IS NOT NULL DROP TABLE dim_customers;
IF OBJECT_ID('dim_time', 'U') IS NOT NULL DROP TABLE dim_time;
GO

-- ==========================================
-- New Dimension: Payment Method
-- ==========================================
CREATE TABLE dim_payment (
    payment_id INT IDENTITY(1,1) PRIMARY KEY,
    payment_method VARCHAR(50) UNIQUE
);

-- ==========================================
-- New Dimension: Order Status
-- ==========================================
CREATE TABLE dim_status (
    status_id INT IDENTITY(1,1) PRIMARY KEY,
    order_status VARCHAR(50) UNIQUE
);

-- Existing Dimensions (Optimized)
CREATE TABLE dim_customers (
    customer_id INT PRIMARY KEY,
    full_name VARCHAR(100),
    gender VARCHAR(10),
    age TINYINT,
    city VARCHAR(100),
    signup_date DATE
);

CREATE TABLE dim_products (
    product_id INT PRIMARY KEY,
    brand VARCHAR(100),
    category VARCHAR(100),
    sub_category VARCHAR(100),
    mrp DECIMAL(10,2)
);

CREATE TABLE dim_location (
    location_id INT IDENTITY(1,1) PRIMARY KEY,
    city VARCHAR(100),
    state VARCHAR(100)
);

CREATE TABLE dim_time (
    date DATE PRIMARY KEY,
    year INT,
    month INT,
    month_name VARCHAR(20)
);

-- ==========================================
-- Updated Fact Table (Using IDs instead of Strings)
-- ==========================================
CREATE TABLE fact_orders (
    order_id VARCHAR(50),
    customer_id INT,
    product_id INT,
    order_date DATE,
    location_id INT,
    payment_id INT, -- New FK
    status_id INT,  -- New FK
    quantity INT,
    unit_price DECIMAL(10,2),
    discount DECIMAL(10,2),
    net_amount DECIMAL(10,2), 
    total_amount DECIMAL(10,2),

    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id),
    FOREIGN KEY (payment_id) REFERENCES dim_payment(payment_id),
    FOREIGN KEY (status_id) REFERENCES dim_status(status_id),
    FOREIGN KEY (order_date) REFERENCES dim_time(date)
);
GO