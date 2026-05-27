# run_etl_pipeline.py
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from db_config import db
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RetailETLPipeline:
    def __init__(self):
        self.db = db
        self.steps = []
        
    def create_schemas(self):
        """Create all necessary schemas"""
        logger.info("Creating database schemas...")
        queries = [
            "CREATE SCHEMA IF NOT EXISTS staging;",
            "CREATE SCHEMA IF NOT EXISTS warehouse;",
            "CREATE SCHEMA IF NOT EXISTS analytics;",
            "CREATE SCHEMA IF NOT EXISTS etl;"
        ]
        for query in queries:
            self.db.execute_query(query)
        logger.info("✓ Schemas created")
    
    def run_staging(self):
        """Step 1: Create and populate staging tables"""
        logger.info("=" * 60)
        logger.info("STEP 1: STAGING LAYER")
        logger.info("=" * 60)
        
        # Create staging tables
        staging_sql = """
        -- Drop existing tables if they exist (for clean runs)
        DROP TABLE IF EXISTS staging.customers CASCADE;
        DROP TABLE IF EXISTS staging.orders CASCADE;
        DROP TABLE IF EXISTS staging.order_items CASCADE;
        DROP TABLE IF EXISTS staging.products CASCADE;
        
        -- Create staging customers table
        CREATE TABLE staging.customers (
            customer_id INTEGER PRIMARY KEY,
            gender VARCHAR(10),
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            full_name VARCHAR(100),
            age INTEGER,
            city VARCHAR(100),
            signup_date DATE,
            age_range VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create staging orders table
        CREATE TABLE staging.orders (
            order_id VARCHAR(50) PRIMARY KEY,
            customer_id INTEGER,
            order_date DATE,
            order_ts TIMESTAMP,
            city VARCHAR(100),
            state VARCHAR(100),
            payment_method VARCHAR(50),
            order_status VARCHAR(50),
            total_amount DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create staging order_items table
        CREATE TABLE staging.order_items (
            order_item_id SERIAL PRIMARY KEY,
            order_id VARCHAR(50),
            product_id INTEGER,
            quantity INTEGER,
            unit_price DECIMAL(10,2),
            discount DECIMAL(10,2),
            net_amount DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create staging products table
        CREATE TABLE staging.products (
            product_id INTEGER PRIMARY KEY,
            brand VARCHAR(100),
            category VARCHAR(100),
            sub_category VARCHAR(100),
            mrp DECIMAL(10,2),
            mrp_range VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        self.db.execute_query(staging_sql)
        logger.info("✓ Staging tables created")
        
        # Load data from CSV files (if they exist)
        self.load_csv_to_staging()
    
    def load_csv_to_staging(self):
        """Load CSV data into staging tables using pandas"""
        data_dir = Path('data/cleaned')
        
        if not data_dir.exists():
            logger.warning(f"Data directory {data_dir} not found. Creating sample data...")
            self.generate_sample_data()
        
        # Load customers with date conversion
        customers_file = data_dir / 'customers.csv'
        if customers_file.exists():
            logger.info(f"Loading customers from {customers_file}")
            df = pd.read_csv(customers_file)
            # Convert date columns to datetime
            if 'signup_date' in df.columns:
                df['signup_date'] = pd.to_datetime(df['signup_date']).dt.date
            engine = self.db.get_sqlalchemy_engine()
            df.to_sql('customers', engine, schema='staging', if_exists='replace', index=False)
            logger.info(f"✓ Loaded {len(df)} customers")
        
        # Load orders with date conversion
        orders_file = data_dir / 'orders.csv'
        if orders_file.exists():
            logger.info(f"Loading orders from {orders_file}")
            df = pd.read_csv(orders_file)
            # Convert date columns
            if 'order_date' in df.columns:
                df['order_date'] = pd.to_datetime(df['order_date']).dt.date
            if 'order_ts' in df.columns:
                df['order_ts'] = pd.to_datetime(df['order_ts'])
            engine = self.db.get_sqlalchemy_engine()
            df.to_sql('orders', engine, schema='staging', if_exists='replace', index=False)
            logger.info(f"✓ Loaded {len(df)} orders")
        
        # Load order_items
        order_items_file = data_dir / 'order_items.csv'
        if order_items_file.exists():
            logger.info(f"Loading order items from {order_items_file}")
            df = pd.read_csv(order_items_file)
            engine = self.db.get_sqlalchemy_engine()
            df.to_sql('order_items', engine, schema='staging', if_exists='replace', index=False)
            logger.info(f"✓ Loaded {len(df)} order items")
        
        # Load products
        products_file = data_dir / 'products.csv'
        if products_file.exists():
            logger.info(f"Loading products from {products_file}")
            df = pd.read_csv(products_file)
            engine = self.db.get_sqlalchemy_engine()
            df.to_sql('products', engine, schema='staging', if_exists='replace', index=False)
            logger.info(f"✓ Loaded {len(df)} products")
    
    def generate_sample_data(self):
        """Generate sample data for testing"""
        logger.info("Generating sample data...")
        from faker import Faker
        import random
        
        fake = Faker()
        
        # Create data directory if it doesn't exist
        Path('data/cleaned').mkdir(parents=True, exist_ok=True)
        
        # Generate customers
        customers = []
        for i in range(1000):
            first_name = fake.first_name()
            last_name = fake.last_name()
            customers.append({
                'customer_id': i + 1,
                'gender': random.choice(['M', 'F']),
                'first_name': first_name,
                'last_name': last_name,
                'full_name': f"{first_name} {last_name}",
                'age': random.randint(18, 80),
                'city': fake.city(),
                'signup_date': fake.date_between(start_date='-2y', end_date='today'),
                'age_range': random.choice(['18-25', '26-35', '36-50', '51+'])
            })
        
        pd.DataFrame(customers).to_csv('data/cleaned/customers.csv', index=False)
        logger.info(f"  ✓ Generated {len(customers)} customers")
        
        # Generate orders
        orders = []
        cities_states = [('New York', 'NY'), ('Los Angeles', 'CA'), ('Chicago', 'IL'), ('Houston', 'TX'), ('Phoenix', 'AZ')]
        for i in range(5000):
            city, state = random.choice(cities_states)
            orders.append({
                'order_id': f'ORD{i+1:06d}',
                'customer_id': random.randint(1, 1000),
                'order_date': fake.date_between(start_date='-2y', end_date='today'),
                'order_ts': fake.date_time_between(start_date='-2y', end_date='today'),
                'city': city,
                'state': state,
                'payment_method': random.choice(['Credit Card', 'PayPal', 'Bank Transfer', 'Cash']),
                'order_status': random.choice(['Completed', 'Pending', 'Shipped', 'Cancelled']),
                'total_amount': round(random.uniform(20, 1000), 2)
            })
        
        pd.DataFrame(orders).to_csv('data/cleaned/orders.csv', index=False)
        logger.info(f"  ✓ Generated {len(orders)} orders")
        
        # Generate products
        products = []
        categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']
        for i in range(500):
            mrp = round(random.uniform(20, 1000), 2)
            products.append({
                'product_id': i + 1,
                'brand': fake.company(),
                'category': random.choice(categories),
                'sub_category': fake.word(),
                'mrp': mrp,
                'mrp_range': f"{int(mrp/100)*100}-{int(mrp/100)*100+99}" if mrp < 1000 else '1000+'
            })
        
        pd.DataFrame(products).to_csv('data/cleaned/products.csv', index=False)
        logger.info(f"  ✓ Generated {len(products)} products")
        
        # Generate order items
        order_items = []
        for i in range(15000):
            unit_price = round(random.uniform(20, 1000), 2)
            quantity = random.randint(1, 5)
            discount = round(random.uniform(0, 0.3), 2)
            net_amount = round(unit_price * quantity * (1 - discount), 2)
            order_items.append({
                'order_item_id': i + 1,
                'order_id': f"ORD{random.randint(1, 5000):06d}",
                'product_id': random.randint(1, 500),
                'quantity': quantity,
                'unit_price': unit_price,
                'discount': discount,
                'net_amount': net_amount
            })
        
        pd.DataFrame(order_items).to_csv('data/cleaned/order_items.csv', index=False)
        logger.info(f"  ✓ Generated {len(order_items)} order items")
        
        logger.info("✓ Sample data generation complete!")
    
    def create_warehouse(self):
        """Step 2: Create dimensional model in warehouse"""
        logger.info("=" * 60)
        logger.info("STEP 2: WAREHOUSE LAYER")
        logger.info("=" * 60)
        
        warehouse_sql = """
        -- Drop existing tables in reverse order of dependencies
        DROP TABLE IF EXISTS warehouse.fact_orders CASCADE;
        DROP TABLE IF EXISTS warehouse.dim_time CASCADE;
        DROP TABLE IF EXISTS warehouse.dim_location CASCADE;
        DROP TABLE IF EXISTS warehouse.dim_payment CASCADE;
        DROP TABLE IF EXISTS warehouse.dim_status CASCADE;
        DROP TABLE IF EXISTS warehouse.dim_customers CASCADE;
        DROP TABLE IF EXISTS warehouse.dim_products CASCADE;
        
        -- Create dimension tables
        CREATE TABLE warehouse.dim_customers (
            customer_id INTEGER PRIMARY KEY,
            full_name VARCHAR(100),
            gender VARCHAR(10),
            age INTEGER,
            city VARCHAR(100),
            signup_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE warehouse.dim_products (
            product_id INTEGER PRIMARY KEY,
            brand VARCHAR(100),
            category VARCHAR(100),
            sub_category VARCHAR(100),
            mrp DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE warehouse.dim_location (
            location_id SERIAL PRIMARY KEY,
            city VARCHAR(100),
            state VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE warehouse.dim_payment (
            payment_id SERIAL PRIMARY KEY,
            payment_method VARCHAR(50) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE warehouse.dim_status (
            status_id SERIAL PRIMARY KEY,
            order_status VARCHAR(50) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE warehouse.dim_time (
            date DATE PRIMARY KEY,
            year INTEGER,
            month INTEGER,
            month_name VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create fact table
        CREATE TABLE warehouse.fact_orders (
            order_id VARCHAR(50),
            customer_id INTEGER,
            product_id INTEGER,
            order_date DATE,
            location_id INTEGER,
            payment_id INTEGER,
            status_id INTEGER,
            quantity INTEGER,
            unit_price DECIMAL(10,2),
            discount DECIMAL(10,2),
            net_amount DECIMAL(10,2),
            total_amount DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (order_id, product_id),
            FOREIGN KEY (customer_id) REFERENCES warehouse.dim_customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES warehouse.dim_products(product_id),
            FOREIGN KEY (location_id) REFERENCES warehouse.dim_location(location_id),
            FOREIGN KEY (payment_id) REFERENCES warehouse.dim_payment(payment_id),
            FOREIGN KEY (status_id) REFERENCES warehouse.dim_status(status_id),
            FOREIGN KEY (order_date) REFERENCES warehouse.dim_time(date)
        );
        
        -- Create indexes
        CREATE INDEX idx_fact_customer ON warehouse.fact_orders(customer_id);
        CREATE INDEX idx_fact_product ON warehouse.fact_orders(product_id);
        CREATE INDEX idx_fact_date ON warehouse.fact_orders(order_date);
        CREATE INDEX idx_fact_location ON warehouse.fact_orders(location_id);
        CREATE INDEX idx_fact_payment ON warehouse.fact_orders(payment_id);
        CREATE INDEX idx_fact_status ON warehouse.fact_orders(status_id);
        """
        
        self.db.execute_query(warehouse_sql)
        logger.info("✓ Warehouse schema created")
    
    def run_etl_procedures(self):
          """Step 3: Execute ETL procedures to populate warehouse"""
          logger.info("=" * 60)
          logger.info("STEP 3: ETL PROCEDURES")
          logger.info("=" * 60)
          
          # Create stored procedures based on your SQL Server example (adapted for PostgreSQL)
          procedures_sql = """
          -- Procedure to load customers
          CREATE OR REPLACE PROCEDURE etl.load_dim_customers()
          LANGUAGE plpgsql
          AS $$
          BEGIN
               INSERT INTO warehouse.dim_customers (customer_id, full_name, gender, age, city, signup_date)
               SELECT DISTINCT
                    s.customer_id,
                    s.full_name,
                    s.gender,
                    s.age,
                    s.city,
                    s.signup_date::DATE
               FROM staging.customers s
               WHERE NOT EXISTS (
                    SELECT 1 FROM warehouse.dim_customers d
                    WHERE d.customer_id = s.customer_id
               );
               
               RAISE NOTICE 'Loaded customers: %', (SELECT COUNT(*) FROM staging.customers);
          END;
          $$;
          
          -- Procedure to load products
          CREATE OR REPLACE PROCEDURE etl.load_dim_products()
          LANGUAGE plpgsql
          AS $$
          BEGIN
               INSERT INTO warehouse.dim_products (product_id, brand, category, sub_category, mrp)
               SELECT DISTINCT
                    s.product_id,
                    s.brand,
                    s.category,
                    s.sub_category,
                    s.mrp
               FROM staging.products s
               WHERE NOT EXISTS (
                    SELECT 1 FROM warehouse.dim_products d
                    WHERE d.product_id = s.product_id
               );
               
               RAISE NOTICE 'Loaded products: %', (SELECT COUNT(*) FROM staging.products);
          END;
          $$;
          
          -- Procedure to load location
          CREATE OR REPLACE PROCEDURE etl.load_dim_location()
          LANGUAGE plpgsql
          AS $$
          BEGIN
               INSERT INTO warehouse.dim_location (city, state)
               SELECT DISTINCT s.city, s.state
               FROM staging.orders s
               WHERE NOT EXISTS (
                    SELECT 1 FROM warehouse.dim_location d
                    WHERE d.city = s.city AND d.state = s.state
               );
               
               RAISE NOTICE 'Loaded locations';
          END;
          $$;
          
          -- Procedure to load payment methods
          CREATE OR REPLACE PROCEDURE etl.load_dim_payment()
          LANGUAGE plpgsql
          AS $$
          BEGIN
               INSERT INTO warehouse.dim_payment (payment_method)
               SELECT DISTINCT s.payment_method
               FROM staging.orders s
               WHERE NOT EXISTS (
                    SELECT 1 FROM warehouse.dim_payment d
                    WHERE d.payment_method = s.payment_method
               );
               
               RAISE NOTICE 'Loaded payment methods';
          END;
          $$;
          
          -- Procedure to load status
          CREATE OR REPLACE PROCEDURE etl.load_dim_status()
          LANGUAGE plpgsql
          AS $$
          BEGIN
               INSERT INTO warehouse.dim_status (order_status)
               SELECT DISTINCT s.order_status
               FROM staging.orders s
               WHERE NOT EXISTS (
                    SELECT 1 FROM warehouse.dim_status d
                    WHERE d.order_status = s.order_status
               );
               
               RAISE NOTICE 'Loaded order statuses';
          END;
          $$;
          
          -- Procedure to load time dimension
          CREATE OR REPLACE PROCEDURE etl.load_dim_time()
          LANGUAGE plpgsql
          AS $$
          BEGIN
               INSERT INTO warehouse.dim_time (date, year, month, month_name)
               SELECT DISTINCT
                    s.order_date::DATE,
                    EXTRACT(YEAR FROM s.order_date)::INTEGER,
                    EXTRACT(MONTH FROM s.order_date)::INTEGER,
                    TO_CHAR(s.order_date, 'Month')
               FROM staging.orders s
               WHERE NOT EXISTS (
                    SELECT 1 FROM warehouse.dim_time d
                    WHERE d.date = s.order_date
               );
               
               RAISE NOTICE 'Loaded time dimension';
          END;
          $$;
          
          -- Procedure to load fact orders (with proper joins and missing key handling)
          CREATE OR REPLACE PROCEDURE etl.load_fact_orders()
          LANGUAGE plpgsql
          AS $$
          BEGIN
               -- First, clean up any orphaned records in staging.order_items
               -- Delete order items where product_id doesn't exist in staging.products
               DELETE FROM staging.order_items 
               WHERE product_id NOT IN (SELECT product_id FROM staging.products);
               
               -- Delete order items where order_id doesn't exist in staging.orders
               DELETE FROM staging.order_items 
               WHERE order_id NOT IN (SELECT order_id FROM staging.orders);
               
               -- Now insert valid records
               INSERT INTO warehouse.fact_orders (
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
               FROM staging.orders o
               INNER JOIN staging.order_items oi ON o.order_id = oi.order_id
               INNER JOIN warehouse.dim_location l ON o.city = l.city AND o.state = l.state
               INNER JOIN warehouse.dim_payment p ON o.payment_method = p.payment_method
               INNER JOIN warehouse.dim_status s ON o.order_status = s.order_status
               INNER JOIN warehouse.dim_products dp ON oi.product_id = dp.product_id
               INNER JOIN warehouse.dim_customers dc ON o.customer_id = dc.customer_id
               INNER JOIN warehouse.dim_time dt ON o.order_date = dt.date
               WHERE NOT EXISTS (
                    SELECT 1 FROM warehouse.fact_orders f
                    WHERE f.order_id = o.order_id AND f.product_id = oi.product_id
               );
               
               RAISE NOTICE 'Loaded fact orders: %', (SELECT COUNT(*) FROM staging.order_items);
          END;
          $$;
          
          -- Master procedure to run all ETL
          CREATE OR REPLACE PROCEDURE etl.run_full_etl()
          LANGUAGE plpgsql
          AS $$
          BEGIN
               RAISE NOTICE 'Starting full ETL pipeline...';
               CALL etl.load_dim_customers();
               CALL etl.load_dim_products();
               CALL etl.load_dim_location();
               CALL etl.load_dim_payment();
               CALL etl.load_dim_status();
               CALL etl.load_dim_time();
               CALL etl.load_fact_orders();
               RAISE NOTICE 'ETL pipeline completed successfully!';
          END;
          $$;
          """
          
          self.db.execute_query(procedures_sql)
          logger.info("✓ Stored procedures created")
          
          # Execute the ETL procedures
          logger.info("Executing ETL procedures...")
          
          logger.info("  Loading customers...")
          self.db.execute_query("CALL etl.load_dim_customers();")
          logger.info("  ✓ Customers loaded")
          
          logger.info("  Loading products...")
          self.db.execute_query("CALL etl.load_dim_products();")
          logger.info("  ✓ Products loaded")
          
          logger.info("  Loading locations...")
          self.db.execute_query("CALL etl.load_dim_location();")
          logger.info("  ✓ Locations loaded")
          
          logger.info("  Loading payment methods...")
          self.db.execute_query("CALL etl.load_dim_payment();")
          logger.info("  ✓ Payment methods loaded")
          
          logger.info("  Loading order statuses...")
          self.db.execute_query("CALL etl.load_dim_status();")
          logger.info("  ✓ Order statuses loaded")
          
          logger.info("  Loading time dimension...")
          self.db.execute_query("CALL etl.load_dim_time();")
          logger.info("  ✓ Time dimension loaded")
          
          logger.info("  Loading fact orders...")
          self.db.execute_query("CALL etl.load_fact_orders();")
          logger.info("  ✓ Fact orders loaded")
    
    
    def create_analytics_views(self):
        """Step 4: Create analytics views for dashboard"""
        logger.info("=" * 60)
        logger.info("STEP 4: ANALYTICS LAYER")
        logger.info("=" * 60)
        
        analytics_sql = """
        -- Core metrics view
        CREATE OR REPLACE VIEW analytics.core_metrics AS
        SELECT 
            DATE_TRUNC('day', order_date) as metric_date,
            COUNT(DISTINCT order_id) as total_orders,
            COUNT(DISTINCT customer_id) as active_customers,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as average_order_value
        FROM warehouse.fact_orders
        GROUP BY DATE_TRUNC('day', order_date)
        ORDER BY metric_date DESC;
        
        -- Payment method analysis
        CREATE OR REPLACE VIEW analytics.payment_analysis AS
        SELECT 
            dp.payment_method,
            COUNT(DISTINCT fo.order_id) as total_orders,
            SUM(fo.total_amount) as total_revenue,
            AVG(fo.total_amount) as avg_order_value
        FROM warehouse.fact_orders fo
        JOIN warehouse.dim_payment dp ON fo.payment_id = dp.payment_id
        GROUP BY dp.payment_method
        ORDER BY total_revenue DESC;
        
        -- Product performance
        CREATE OR REPLACE VIEW analytics.product_performance AS
        SELECT 
            dp.product_id,
            dp.brand,
            dp.category,
            COUNT(DISTINCT fo.order_id) as total_orders,
            SUM(fo.quantity) as units_sold,
            SUM(fo.total_amount) as total_revenue,
            AVG(fo.total_amount) as avg_order_value
        FROM warehouse.fact_orders fo
        JOIN warehouse.dim_products dp ON fo.product_id = dp.product_id
        GROUP BY dp.product_id, dp.brand, dp.category
        ORDER BY total_revenue DESC;
        
        -- Location analysis
        CREATE OR REPLACE VIEW analytics.location_analysis AS
        SELECT 
            dl.city,
            dl.state,
            COUNT(DISTINCT fo.order_id) as total_orders,
            SUM(fo.total_amount) as total_revenue,
            COUNT(DISTINCT fo.customer_id) as unique_customers
        FROM warehouse.fact_orders fo
        JOIN warehouse.dim_location dl ON fo.location_id = dl.location_id
        GROUP BY dl.city, dl.state
        ORDER BY total_revenue DESC;
        """
        
        self.db.execute_query(analytics_sql)
        logger.info("✓ Analytics views created")
    
    def validate_pipeline(self):
        """Validate that all data loaded correctly"""
        logger.info("=" * 60)
        logger.info("PIPELINE VALIDATION")
        logger.info("=" * 60)
        
        validation_queries = [
            ("Customers in warehouse", "SELECT COUNT(*) as count FROM warehouse.dim_customers"),
            ("Products in warehouse", "SELECT COUNT(*) as count FROM warehouse.dim_products"),
            ("Orders in fact table", "SELECT COUNT(*) as count FROM warehouse.fact_orders"),
            ("Locations", "SELECT COUNT(*) as count FROM warehouse.dim_location"),
            ("Payment methods", "SELECT COUNT(*) as count FROM warehouse.dim_payment"),
            ("Order statuses", "SELECT COUNT(*) as count FROM warehouse.dim_status"),
            ("Days in time dimension", "SELECT COUNT(*) as count FROM warehouse.dim_time"),
            ("Total revenue", "SELECT SUM(total_amount) as total FROM warehouse.fact_orders")
        ]
        
        for name, query in validation_queries:
            result = self.db.execute_query(query)
            if result and len(result) > 0:
                count = result[0].get('count') if 'count' in result[0] else result[0].get('total', 0)
                logger.info(f"  ✓ {name}: {count}")
            else:
                logger.info(f"  ✓ {name}: 0")
    
    def run_full_pipeline(self):
        """Execute the complete ETL pipeline"""
        start_time = datetime.now()
        logger.info("🚀 Starting Retail Analytics ETL Pipeline")
        logger.info(f"📅 Start time: {start_time}")
        logger.info(f"🗄️  Database: Neon PostgreSQL")
        
        try:
            # Run all steps
            self.create_schemas()
            self.run_staging()
            self.create_warehouse()
            self.run_etl_procedures()
            self.create_analytics_views()
            self.validate_pipeline()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 60)
            logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY!")
            logger.info(f"⏱️  Total duration: {duration:.2f} seconds")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            raise

if __name__ == "__main__":
    pipeline = RetailETLPipeline()
    pipeline.run_full_pipeline()