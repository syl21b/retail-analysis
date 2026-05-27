-- Example inserts (optional)
USE master
GO

INSERT INTO stg_customers VALUES
(1, 'Male', 'John', 'Doe', 'John Doe', 30, 'Houston', '2022-01-01', '30-40');

INSERT INTO stg_products VALUES
(101, 'Nike', 'Clothing', 'Shoes', 120.00, '100-200');

INSERT INTO stg_orders VALUES
('ORD1', 1, '2024-01-01', GETDATE(), 'Houston', 'TX', 'Credit Card', 'Delivered', 120.00);

INSERT INTO stg_order_items VALUES
('ORD1', 101, 1, 120.00, 0, 120.00);