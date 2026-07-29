import re
import logging
import threading
import time
from pathlib import Path
from functools import cached_property
import pandas as pd
import numpy as np
from cachetools import TTLCache
from config import Config
from . import database
from sql_helpers import clean_sql, add_schema_prefix, fix_date_extract

logger = logging.getLogger(__name__)

class LazyDataFrame:
    def __init__(self, loader, sql_key):
        self.loader = loader
        self.sql_key = sql_key
    def _get_df(self):
        return self.loader.get_dataframe(self.sql_key)
    def __getitem__(self, key):
        return self._get_df().__getitem__(key)
    def __setitem__(self, key, value):
        self._get_df()[key] = value
    def __getattr__(self, name):
        return getattr(self._get_df(), name)
    def __len__(self):
        return len(self._get_df())
    def __bool__(self):
        return bool(self._get_df())
    def __contains__(self, key):
        return key in self._get_df()
    def to_dict(self, orient='records'):
        return self._get_df().to_dict(orient=orient)
    def copy(self):
        return self._get_df().copy()

class DataLoader:
    def __init__(self):
        self.sql_folder = None
        self.sql_files = {}
        self._cache = TTLCache(maxsize=Config.DATAFRAME_CACHE_SIZE, ttl=Config.DATAFRAME_CACHE_TTL)
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            try:
                self.sql_folder = self._find_sql_folder()
                self._index_sql_files()
            except Exception as e:
                logger.error(f"Error loading SQL files: {e}")
            finally:
                self._loaded = True

    def _find_sql_folder(self):
        possible = [Path('sql/analytics'), Path('../sql/analytics'), Path('Retail_Analytics/sql/analytics')]
        for p in possible:
            if p.exists():
                return p
        logger.warning("SQL folder not found. Charts may be empty.")
        return None

    def _index_sql_files(self):
        if not self.sql_folder:
            return
        for sql_file in self.sql_folder.glob('*.sql'):
            name = re.sub(r'[^\w\-_]', '_', sql_file.stem)
            self.sql_files[name] = sql_file
        logger.info(f"Loaded {len(self.sql_files)} SQL files")

    def _execute_sql_file(self, sql_path):
          try:
               with open(sql_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
               sql_content = clean_sql(sql_content)
               if not sql_content:
                    return None
               sql_content = add_schema_prefix(sql_content)
               sql_content = fix_date_extract(sql_content)
               sql_content = re.sub(r'\s+LIMIT\s+\d+', '', sql_content, flags=re.IGNORECASE)
               sql_content = sql_content.rstrip(';').strip()
               if sql_content.strip().upper().startswith('SELECT'):
                    sql_content += f" LIMIT {Config.MAX_ROWS_PER_DATASET}"
               result = database.db.execute_query(sql_content)   # <-- fix: use database.db
               if result and isinstance(result, list) and len(result) > 0:
                    df = pd.DataFrame(result)
                    df = self._convert_decimal_to_float(df)
                    if len(df) > Config.MAX_ROWS_PER_DATASET:
                         logger.warning(f"Truncating {sql_path.name} from {len(df)} to {Config.MAX_ROWS_PER_DATASET} rows")
                         df = df.head(Config.MAX_ROWS_PER_DATASET)
                    for col in df.select_dtypes(include=['float']).columns:
                         df[col] = pd.to_numeric(df[col], downcast='float')
                    for col in df.select_dtypes(include=['integer']).columns:
                         df[col] = pd.to_numeric(df[col], downcast='integer')
                    return df
               return None
          except Exception as e:
               logger.error(f"Error in {sql_path.name}: {e}")
               return None
    def _convert_decimal_to_float(self, df):
        for col in df.columns:
            try:
                sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if sample is not None and hasattr(sample, 'as_tuple'):
                    df[col] = df[col].astype(float)
            except Exception:
                pass
        return df

    def get_dataframe(self, sql_key):
        self._ensure_loaded()
        if sql_key in self._cache:
            return self._cache[sql_key]
        sql_path = self.sql_files.get(sql_key)
        if not sql_path:
            return pd.DataFrame()
        df = self._execute_sql_file(sql_path)
        if df is None:
            df = pd.DataFrame()
        self._cache[sql_key] = df
        return df

    def clear_cache(self):
        self._cache.clear()
        logger.info("DataLoader cache cleared manually")

    @cached_property
    def friendly_data(self):
        self._ensure_loaded()
        mapping = {
            '1a_Customer_Lifetime_Value__CLV_': 'Customer Lifetime Value',
            '1b_Daily_Revenue_Trends': 'Daily Revenue Trends',
            '1c_Monthly_Revenue_Trends': 'Monthly Revenue Trends',
            '1d_Top_Cities_by_Revenue': 'Top Cities by Revenue',
            '2a_Order_Fulfillment_Performance': 'Order Fulfillment Performance',
            '2b_Order_Status_Distribution': 'Order Status Distribution',
            '2c_Revenue_by_Payment_Method': 'Revenue by Payment Method',
            '2d_Repeat_vs_One-Time_Customers': 'Repeat vs One-Time Customers',
            '3a_Cohort_Analysis__Customer_Retention_Over_Time_': 'Cohort Analysis',
            '3b_Customer_Segmentation_using_Revenue___Behavior': 'Customer Segmentation',
            '3c_Order_Value_Distribution___Basket_Analysis': 'Order Value Distribution',
            '3d_Revenue_Contribution_Analysis': 'Revenue Contribution Analysis',
            '3e_Time-to-Purchase_Behavior': 'Time to Purchase Behavior',
            '4_RFM_Segmentation': 'RFM Segmentation',
            '5_Cohort_Retention_Analysis': 'Cohort Retention Analysis',
            '6_Churn_Detection': 'Churn Detection',
            '7a_Revenue_by_Product_Category': 'Revenue by Product Category',
            '7b_Revenue_by_Product_SubCategory': 'Revenue by Product SubCategory',
            '8_Revenue_by_Location': 'Revenue by Location',
            '9_Payment_Method_Analysis': 'Payment Method Analysis',
            '10_Order_Status_Analysis': 'Order Status Analysis'
        }
        fd = {}
        for key, value in mapping.items():
            for res_name in self.sql_files:
                if key in res_name or res_name.startswith(key.split('_')[0]):
                    fd[value] = LazyDataFrame(self, res_name)
                    break
            if value not in fd:
                for res_name in self.sql_files:
                    if value.lower().replace(' ', '_') in res_name.lower():
                        fd[value] = LazyDataFrame(self, res_name)
                        break
            if value not in fd:
                fd[value] = pd.DataFrame()
        return fd

    def to_dict(self, df):
        if df is None or df.empty:
            return []
        return df.replace({np.nan: None}).to_dict(orient='records')

loader = DataLoader()
friendly_data = loader.friendly_data

def get_dataset(name):
    return loader.to_dict(friendly_data.get(name, pd.DataFrame()))

# Cache clear thread
def schedule_cache_clear():
    while True:
        time.sleep(300)
        loader.clear_cache()
threading.Thread(target=schedule_cache_clear, daemon=True).start()