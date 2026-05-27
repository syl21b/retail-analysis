CREATE OR ALTER PROCEDURE sp_load_dim_products
AS
BEGIN
    INSERT INTO dim_products (product_id, brand, category, sub_category, mrp)
    SELECT DISTINCT
        product_id,
        brand,
        category,
        sub_category,
        mrp
    FROM stg_products s
    WHERE NOT EXISTS (
        SELECT 1 FROM dim_products d
        WHERE d.product_id = s.product_id
    );
END;