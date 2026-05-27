import pandas as pd

def extract():
    customers = pd.read_csv("../data/cleaned/customers.csv")
    orders = pd.read_csv("../data/cleaned/orders.csv")
    order_items = pd.read_csv("../data/cleaned/order_items.csv")
    products = pd.read_csv("../data/cleaned/products.csv")
    return customers, orders, order_items, products