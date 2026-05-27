SELECT * FROM fact_orders 
JOIN dim_customers ON fact_orders.customer_id = dim_customers.customer_id
WHERE dim_customers.customer_id = 868685;
