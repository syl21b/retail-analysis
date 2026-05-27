-- Bulk load CSV files into tables
-- Adjust file paths to match your environment
USE master;  -- or your actual database
GO

BULK INSERT stg_customers
FROM '/var/opt/mssql/data/customers.csv'
WITH (FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '\n');

BULK INSERT stg_products
FROM '/var/opt/mssql/data/products.csv'
WITH (FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '\n');

BULK INSERT stg_orders
FROM '/var/opt/mssql/data/orders.csv'
WITH (FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '\n');

BULK INSERT stg_order_items
FROM '/var/opt/mssql/data/order_items.csv'
WITH (FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '\n');


