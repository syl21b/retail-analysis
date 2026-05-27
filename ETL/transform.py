def transform(customers, orders, order_items, products):
    # Example transformations
    customers.drop_duplicates(subset='customer_id', inplace=True)
    orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
    
    # Merge orders + order_items + products for fact table
    orders_fact = orders.merge(order_items, on='order_id')
    orders_fact = orders_fact.merge(products[['product_id','product_category_name']], on='product_id')
    
    return customers, orders_fact