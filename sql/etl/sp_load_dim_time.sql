CREATE OR ALTER PROCEDURE sp_load_dim_time
AS
BEGIN
    INSERT INTO dim_time (date, year, month, month_name)
    SELECT DISTINCT
        order_date,
        YEAR(order_date),
        MONTH(order_date),
        DATENAME(MONTH, order_date)
    FROM stg_orders s
    WHERE NOT EXISTS (
        SELECT 1 FROM dim_time d
        WHERE d.date = s.order_date
    );
END;