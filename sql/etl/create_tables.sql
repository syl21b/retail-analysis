USE master;
GO

-- ================================================================
-- Drop all existing tables (including staging)
-- ================================================================
IF OBJECT_ID('fact_orders', 'U') IS NOT NULL DROP TABLE fact_orders;
IF OBJECT_ID('products_table', 'U') IS NOT NULL DROP TABLE products_table;
IF OBJECT_ID('customers_table', 'U') IS NOT NULL DROP TABLE customers_table;
IF OBJECT_ID('sub_category_table', 'U') IS NOT NULL DROP TABLE sub_category_table;
IF OBJECT_ID('category_table', 'U') IS NOT NULL DROP TABLE category_table;
IF OBJECT_ID('brand_table', 'U') IS NOT NULL DROP TABLE brand_table;
IF OBJECT_ID('location_table', 'U') IS NOT NULL DROP TABLE location_table;
IF OBJECT_ID('status_table', 'U') IS NOT NULL DROP TABLE status_table;
IF OBJECT_ID('payment_table', 'U') IS NOT NULL DROP TABLE payment_table;

-- Drop staging tables if they exist
IF OBJECT_ID('products_staging', 'U') IS NOT NULL DROP TABLE products_staging;
IF OBJECT_ID('orders_staging_full', 'U') IS NOT NULL DROP TABLE orders_staging_full;
IF OBJECT_ID('order_items_staging', 'U') IS NOT NULL DROP TABLE order_items_staging;
GO

-- ================================================================
-- Create dimension tables
-- ================================================================

CREATE TABLE payment_table (
    payment_method VARCHAR(255),
    payment_code INT PRIMARY KEY
);

CREATE TABLE status_table (
    order_status VARCHAR(255),
    status_code INT PRIMARY KEY
);

-- Updated location_table: now includes state_code and state_name
CREATE TABLE location_table (
    city_code INT PRIMARY KEY,
    city_name VARCHAR(255),
    state_code INT,
    state_name VARCHAR(255)
);

CREATE TABLE brand_table (
    brand_name VARCHAR(255),
    brand_code INT PRIMARY KEY
);

CREATE TABLE category_table (
    category_name VARCHAR(255),
    category_code INT PRIMARY KEY
);

CREATE TABLE sub_category_table (
    sub_category_name VARCHAR(255),
    sub_category_code INT PRIMARY KEY
);

CREATE TABLE customers_table (
    customer_id INT PRIMARY KEY,
    gender_code INT,
    full_name VARCHAR(255),
    age INT,
    city_code INT,
    signup_date DATE,
    FOREIGN KEY (city_code) REFERENCES location_table(city_code)
);

CREATE TABLE products_table (
    product_id INT PRIMARY KEY,
    brand_code INT,
    category_code INT,
    sub_category_code INT,
    mrp DECIMAL(10,2),
    FOREIGN KEY (brand_code) REFERENCES brand_table(brand_code),
    FOREIGN KEY (category_code) REFERENCES category_table(category_code),
    FOREIGN KEY (sub_category_code) REFERENCES sub_category_table(sub_category_code)
);



CREATE TABLE fact_orders (
    order_id INT,
    customer_id INT,
    product_id INT,
    order_date DATE,
    city_code INT,
    payment_code INT,
    status_code INT,
    quantity INT,
    unit_price DECIMAL(10,2),
    discount DECIMAL(10,2),
    net_amount DECIMAL(10,2),
    total_amount DECIMAL(10,2),

    FOREIGN KEY (customer_id) REFERENCES customers_table(customer_id),
    FOREIGN KEY (product_id) REFERENCES products_table(product_id),
    FOREIGN KEY (city_code) REFERENCES location_table(city_code),
    FOREIGN KEY (payment_code) REFERENCES payment_table(payment_code),
    FOREIGN KEY (status_code) REFERENCES status_table(status_code)
);
GO

-- ================================================================
-- BULK INSERT – mapping tables (dimensions)
-- ================================================================

BULK INSERT payment_table
FROM '/var/opt/mssql/data/payment_method.csv'
WITH (DATAFILETYPE = 'char', FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a', FIRSTROW = 2, TABLOCK);
GO

BULK INSERT status_table
FROM '/var/opt/mssql/data/order_status.csv'
WITH (DATAFILETYPE = 'char', FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a', FIRSTROW = 2, TABLOCK);
GO

-- Now loading from location.csv (contains city_code, city_name, state_code, state_name)
BULK INSERT location_table
FROM '/var/opt/mssql/data/location.csv'
WITH (DATAFILETYPE = 'char', FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a', FIRSTROW = 2, TABLOCK);
GO

BULK INSERT brand_table
FROM '/var/opt/mssql/data/brand.csv'
WITH (DATAFILETYPE = 'char', FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a', FIRSTROW = 2, TABLOCK);
GO

BULK INSERT category_table
FROM '/var/opt/mssql/data/category.csv'
WITH (DATAFILETYPE = 'char', FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a', FIRSTROW = 2, TABLOCK);
GO

BULK INSERT sub_category_table
FROM '/var/opt/mssql/data/sub_category.csv'
WITH (DATAFILETYPE = 'char', FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a', FIRSTROW = 2, TABLOCK);
GO

-- ================================================================
-- Load customers
-- ================================================================
BULK INSERT customers_table
FROM '/var/opt/mssql/data/customers.csv'
WITH (DATAFILETYPE = 'char', FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a', FIRSTROW = 2, TABLOCK);
GO

-- ================================================================
-- Load products using staging (extra columns are ignored)
-- ================================================================
CREATE TABLE products_staging (
    product_id INT,
    brand_code INT,
    category_code INT,
    sub_category_code INT,
    mrp DECIMAL(10,2)
);

BULK INSERT products_staging
FROM '/var/opt/mssql/data/products.csv'
WITH (DATAFILETYPE = 'char', FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a', FIRSTROW = 2, TABLOCK);

INSERT INTO products_table (product_id, brand_code, category_code, sub_category_code, mrp)
SELECT product_id, brand_code, category_code, sub_category_code, mrp
FROM products_staging;

DROP TABLE products_staging;
GO

-- ================================================================
-- Staging for orders (matches CSV columns exactly)
-- ================================================================
CREATE TABLE orders_staging_full (
    order_id INT,
    customer_id INT,
    order_date DATE,
    city_code INT,
    state VARCHAR(10),          -- extra column not used in fact, but kept
    payment_code INT,
    status_code INT,
    total_amount DECIMAL(10,2),
    order_time TIME
);

BULK INSERT orders_staging_full
FROM '/var/opt/mssql/data/orders.csv'
WITH (DATAFILETYPE = 'char', FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a', FIRSTROW = 2, TABLOCK);
GO

-- ================================================================
-- Staging for order items (matches CSV columns exactly)
-- ================================================================
CREATE TABLE order_items_staging (
    order_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10,2),
    discount DECIMAL(10,2),
    net_amount DECIMAL(10,2)
);

BULK INSERT order_items_staging
FROM '/var/opt/mssql/data/order_items.csv'
WITH (DATAFILETYPE = 'char', FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a', FIRSTROW = 2, TABLOCK);
GO



-- ================================================================
-- Insert into fact_orders (with foreign key validation)
-- ================================================================
INSERT INTO fact_orders (
    order_id, customer_id, product_id, order_date, city_code,
    payment_code, status_code, quantity, unit_price,
    discount, net_amount, total_amount
)
SELECT
    o.order_id,
    o.customer_id,
    oi.product_id,
    o.order_date,
    o.city_code,
    o.payment_code,
    o.status_code,
    oi.quantity,
    oi.unit_price,
    oi.discount,
    oi.net_amount,
    oi.unit_price * oi.quantity AS total_amount
FROM orders_staging_full o
JOIN order_items_staging oi ON o.order_id = oi.order_id
WHERE EXISTS (SELECT 1 FROM products_table p WHERE p.product_id = oi.product_id)
  AND EXISTS (SELECT 1 FROM customers_table c WHERE c.customer_id = o.customer_id)
  AND EXISTS (SELECT 1 FROM location_table ct WHERE ct.city_code = o.city_code)
  AND EXISTS (SELECT 1 FROM payment_table pm WHERE pm.payment_code = o.payment_code)
  AND EXISTS (SELECT 1 FROM status_table s WHERE s.status_code = o.status_code);
GO

-- ================================================================
-- Clean up staging tables
-- ================================================================
DROP TABLE orders_staging_full, order_items_staging;
GO

-- ================================================================
-- Verify row counts
-- ================================================================
SELECT 'payment_table' AS TableName, COUNT(*) AS Rows FROM payment_table
UNION ALL
SELECT 'status_table', COUNT(*) FROM status_table
UNION ALL
SELECT 'location_table', COUNT(*) FROM location_table
UNION ALL
SELECT 'brand_table', COUNT(*) FROM brand_table
UNION ALL
SELECT 'category_table', COUNT(*) FROM category_table
UNION ALL
SELECT 'sub_category_table', COUNT(*) FROM sub_category_table
UNION ALL
SELECT 'customers_table', COUNT(*) FROM customers_table
UNION ALL
SELECT 'products_table', COUNT(*) FROM products_table
UNION ALL
SELECT 'fact_orders', COUNT(*) FROM fact_orders;
GO