CREATE OR ALTER PROCEDURE sp_load_dim_customers
AS
BEGIN
    INSERT INTO dim_customers (customer_id, full_name, gender, age, city, signup_date)
    SELECT DISTINCT
        customer_id,
        full_name,
        gender,
        age,
        city,
        signup_date
    FROM stg_customers s
    WHERE NOT EXISTS (
        SELECT 1 FROM dim_customers d
        WHERE d.customer_id = s.customer_id
    );
END;
