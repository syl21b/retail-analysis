USE master;
GO

-- ================================================================
-- Drop all existing tables (including staging)
-- ================================================================
IF OBJECT_ID('fact_orders', 'U') IS NOT NULL DROP TABLE fact_orders;
IF OBJECT_ID('time_table', 'U') IS NOT NULL DROP TABLE time_table;
IF OBJECT_ID('products_table', 'U') IS NOT NULL DROP TABLE products_table;
IF OBJECT_ID('customers_table', 'U') IS NOT NULL DROP TABLE customers_table;
IF OBJECT_ID('sub_category_table', 'U') IS NOT NULL DROP TABLE sub_category_table;
IF OBJECT_ID('category_table', 'U') IS NOT NULL DROP TABLE category_table;
IF OBJECT_ID('brand_table', 'U') IS NOT NULL DROP TABLE brand_table;
IF OBJECT_ID('city_table', 'U') IS NOT NULL DROP TABLE city_table;
IF OBJECT_ID('status_table', 'U') IS NOT NULL DROP TABLE status_table;
IF OBJECT_ID('payment_table', 'U') IS NOT NULL DROP TABLE payment_table;

-- Drop staging tables if they exist
IF OBJECT_ID('products_staging', 'U') IS NOT NULL DROP TABLE products_staging;
IF OBJECT_ID('orders_staging_full', 'U') IS NOT NULL DROP TABLE orders_staging_full;
IF OBJECT_ID('order_items_staging', 'U') IS NOT NULL DROP TABLE order_items_staging;
GO