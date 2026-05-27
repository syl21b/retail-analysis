CREATE OR ALTER PROCEDURE sp_load_dim_payment
AS
BEGIN
    INSERT INTO dim_payment (payment_method)
    SELECT DISTINCT payment_method
    FROM stg_orders s
    WHERE NOT EXISTS (
        SELECT 1 FROM dim_payment d
        WHERE d.payment_method = s.payment_method
    );
END;