CREATE OR ALTER PROCEDURE sp_load_dim_location
AS
BEGIN
    INSERT INTO dim_location (city, state)
    SELECT DISTINCT city, state
    FROM staging_orders s
    WHERE NOT EXISTS (
        SELECT 1 FROM dim_location d
        WHERE d.city = s.city AND d.state = s.state
    );
END;