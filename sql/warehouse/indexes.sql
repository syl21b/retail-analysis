-- FACT TABLE
CREATE INDEX idx_fact_order ON fact_orders(order_id);
CREATE INDEX idx_fact_customer ON fact_orders(customer_id);
CREATE INDEX idx_fact_product ON fact_orders(product_id);
CREATE INDEX idx_fact_date ON fact_orders(order_date);

-- HIGH VALUE INDEX
CREATE INDEX idx_fact_customer_date 
ON fact_orders(customer_id, order_date);

-- DIMENSIONS
CREATE INDEX idx_dim_location ON dim_location(city, state);
CREATE INDEX idx_dim_product_category ON dim_products(category);