CREATE OR ALTER PROCEDURE sp_load_fact_orders
AS
BEGIN
    INSERT INTO fact_orders (
        order_id,
        customer_id,
        product_id,
        order_date,
        location_id,
        payment_id,
        status_id,
        quantity,
        unit_price,
        discount,
        net_amount,
        total_amount
    )
    SELECT
        o.order_id,
        o.customer_id,
        oi.product_id,
        o.order_date,
        l.location_id,
        p.payment_id,
        s.status_id,
        oi.quantity,
        oi.unit_price,
        oi.discount,
        oi.net_amount,
        o.total_amount
    FROM stg_orders o
    JOIN stg_order_items oi 
        ON o.order_id = oi.order_id

    JOIN dim_location l 
        ON o.city = l.city AND o.state = l.state

    JOIN dim_payment p 
        ON o.payment_method = p.payment_method

    JOIN dim_status s 
        ON o.order_status = s.order_status

    WHERE NOT EXISTS (
        SELECT 1 FROM fact_orders f
        WHERE f.order_id = o.order_id
        AND f.product_id = oi.product_id
    );
END;