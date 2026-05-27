# run_full_pipeline.py
import psycopg2
from psycopg2 import sql
import pandas as pd
import logging
from datetime import datetime
import yaml

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RetailPipeline:
    def __init__(self, config_path='config.yaml'):
        self.conn = self.get_connection(config_path)
        self.cursor = self.conn.cursor()
        
    def get_connection(self, config_path):
        """Get database connection"""
        # Option 1: From config file
        # with open(config_path, 'r') as f:
        #     config = yaml.safe_load(f)
        
        # Option 2: From environment variables (recommended for deployment)
        import os
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'retail_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password'),
            port=os.getenv('DB_PORT', '5432')
        )
    
    def execute_sql_file(self, filepath, description):
        """Execute SQL file with error handling"""
        try:
            logger.info(f"Executing: {description}")
            with open(filepath, 'r') as f:
                sql_commands = f.read()
            
            # Split by semicolon and execute each command
            for command in sql_commands.split(';'):
                if command.strip():
                    self.cursor.execute(command)
            
            self.conn.commit()
            logger.info(f"✓ {description} completed")
            return True
        except Exception as e:
            logger.error(f"✗ Failed at {description}: {str(e)}")
            self.conn.rollback()
            return False
    
    def execute_stored_procedure(self, sp_name):
        """Execute stored procedure"""
        try:
            logger.info(f"Executing stored procedure: {sp_name}")
            self.cursor.execute(f"CALL {sp_name}();")
            self.conn.commit()
            logger.info(f"✓ {sp_name} completed")
            return True
        except Exception as e:
            logger.error(f"✗ Failed at {sp_name}: {str(e)}")
            self.conn.rollback()
            return False
    
    def run_staging(self):
        """Step 1: Create staging tables"""
        files = [
            ('sql/staging/create_stage_table.sql', 'Staging table creation')
        ]
        return all(self.execute_sql_file(f, d) for f, d in files)
    
    def run_warehouse(self):
        """Step 2: Create warehouse schema"""
        files = [
            ('sql/warehouse/create_dim_fact.sql', 'Dimension and Fact tables'),
            ('sql/warehouse/indexes.sql', 'Performance indexes')
        ]
        return all(self.execute_sql_file(f, d) for f, d in files)
    
    def run_etl_procedures(self):
        """Step 3: Execute ETL stored procedures in correct order"""
        procedures = [
            'sp_load_dim_time',           # Time dimension first (often referenced)
            'sp_load_dim_location',       # Location dimension
            'sp_load_dim_customers',      # Customer dimension
            'sp_load_dim_products',       # Product dimension  
            'sp_load_dim_payment',        # Payment dimension
            'sp_load_dim_status',         # Status dimension
            'sp_load_fact_orders'         # Fact table last (depends on all dims)
        ]
        
        # Execute master procedure if exists
        try:
            return self.execute_stored_procedure('sp_run_full_etl')
        except:
            # Otherwise run individually
            return all(self.execute_stored_procedure(sp) for sp in procedures)
    

    
    def run_full_pipeline(self):
        """Execute complete pipeline"""
        start_time = datetime.now()
        logger.info("=" * 50)
        logger.info("Starting Full Retail Analytics Pipeline")
        logger.info("=" * 50)
        
        steps = [
            (self.run_staging, "STAGING LAYER"),
            (self.run_warehouse, "WAREHOUSE LAYER"),
            (self.run_etl_procedures, "ETL PROCEDURES"),

        ]
        
        for step_func, step_name in steps:
            logger.info(f"\n--- {step_name} ---")
            if not step_func():
                logger.error(f"Pipeline failed at {step_name}")
                return False
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info("=" * 50)
        logger.info(f"✓ Pipeline completed successfully in {duration:.2f} seconds")
        logger.info("=" * 50)
        return True
    
    def close(self):
        self.cursor.close()
        self.conn.close()

# Main execution
if __name__ == "__main__":
    pipeline = RetailPipeline()
    try:
        success = pipeline.run_full_pipeline()
        if not success:
            exit(1)
    finally:
        pipeline.close()