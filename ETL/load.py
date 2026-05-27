from sqlalchemy import create_engine

def load(customers, orders_fact):
    engine = create_engine("postgresql://postgres:password@localhost:5432/retail")
    customers.to_sql("dim_customers", engine, if_exists="replace", index=False)
    orders_fact.to_sql("fact_orders", engine, if_exists="replace", index=False)