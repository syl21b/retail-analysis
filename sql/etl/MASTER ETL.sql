CREATE OR ALTER PROCEDURE sp_run_full_etl
AS
BEGIN
    EXEC sp_load_dim_customers;
    EXEC sp_load_dim_products;
    EXEC sp_load_dim_payment;
    EXEC sp_load_dim_status;
    EXEC sp_load_dim_location;
    EXEC sp_load_dim_time;
    EXEC sp_load_fact_orders;
END;