CREATE OR ALTER PROCEDURE sp_load_dim_status
AS
BEGIN
    INSERT INTO dim_status (order_status)
    SELECT DISTINCT order_status
    FROM stg_orders s
    WHERE NOT EXISTS (
        SELECT 1 FROM dim_status d
        WHERE d.order_status = s.order_status
    );
END;