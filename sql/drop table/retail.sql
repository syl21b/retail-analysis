USE master;  -- or your actual database
GO

SELECT * FROM dbo.dim_customers;
SELECT * FROM dbo.dim_products;
SELECT * FROM dbo.dim_location;
SELECT * FROM dbo.dim_time;
SELECT * FROM dbo.fact_orders;