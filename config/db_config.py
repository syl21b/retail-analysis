# config/db_config.py
import os
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your Neon PostgreSQL connection string
NEON_DB_URL = "postgresql://neondb_owner:npg_4vjDeG0qHypE@ep-twilight-dawn-ankobhm8-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

class NeonDBConnection:
    def __init__(self):
        self.db_url = NEON_DB_URL
        self.connection = None
        self.engine = None
    
    def get_connection(self):
        """Get psycopg2 connection for raw SQL"""
        try:
            self.connection = psycopg2.connect(self.db_url)
            return self.connection
        except Exception as e:
            logger.error(f"Failed to connect to Neon DB: {str(e)}")
            raise
    
    def get_cursor(self, dict_cursor=True):
        """Get database cursor"""
        conn = self.get_connection()
        if dict_cursor:
            return conn.cursor(cursor_factory=RealDictCursor)
        return conn.cursor()
    
    def get_sqlalchemy_engine(self):
        """Get SQLAlchemy engine for pandas operations"""
        if not self.engine:
            self.engine = create_engine(self.db_url)
        return self.engine
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return cur.fetchall()
                conn.commit()
                return cur.rowcount
        finally:
            conn.close()
    
    def execute_sql_file(self, filepath):
        """Execute SQL from file"""
        with open(filepath, 'r') as f:
            sql = f.read()
        
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Split by semicolon and execute each statement
                for statement in sql.split(';'):
                    if statement.strip():
                        cur.execute(statement)
                conn.commit()
            logger.info(f"Successfully executed {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error executing {filepath}: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()

# Singleton instance
db = NeonDBConnection()