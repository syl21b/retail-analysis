import re
import time 

def sanitize_output(data):
    if isinstance(data, str):
        return re.sub(r'<[^>]*>', '', data)
    elif isinstance(data, dict):
        return {k: sanitize_output(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_output(item) for item in data]
    return data

def validate_nlq_input(question):
    if len(question) > 1000:
        return False, "Query too long"
    if not re.match(r'^[a-zA-Z0-9\s.,?!\-:;()"\'/]+$', question):
        return False, "Input contains disallowed characters"
    return True, ""

def add_schema_prefix(sql_query, schema='public'):
    tables = ['fact_orders', 'customers_table', 'products_table', 'location_table',
              'payment_table', 'status_table', 'category_table', 'sub_category_table']
    for table in tables:
        pattern = rf'(?<![\.\w]){table}\b(?!\.)'
        sql_query = re.sub(pattern, f'{schema}.{table}', sql_query, flags=re.IGNORECASE)
    return sql_query

def fix_date_extract(sql_query):
    sql_query = re.sub(r'EXTRACT\(DAY\s+FROM\s+\(CURRENT_DATE\s*-\s*MAX\(([^)]+)\)\)\)',
                       r'(CURRENT_DATE - MAX(\1))', sql_query, flags=re.IGNORECASE)
    sql_query = re.sub(r'EXTRACT\(DAY\s+FROM\s+\(MAX\(([^)]+)\)\s*-\s*MIN\(([^)]+)\)\)\)',
                       r'(MAX(\1) - MIN(\2))', sql_query, flags=re.IGNORECASE)
    sql_query = re.sub(r'EXTRACT\(DAY\s+FROM\s+\(([^)]+)\)\)', r'(\1)', sql_query, flags=re.IGNORECASE)
    return sql_query

def clean_sql(sql_content):
    lines = []
    for line in sql_content.split('\n'):
        if '--' in line:
            line = line[:line.index('--')]
        line = line.strip()
        if line:
            lines.append(line)
    sql = '\n'.join(lines).strip()
    if sql.endswith(';'):
        sql = sql[:-1].strip()
    return sql

def create_performance_indexes(db):
    for attempt in range(3):
        try:
            with db.get_cursor() as cur:
                index_queries = [
                    "CREATE INDEX IF NOT EXISTS idx_fact_orders_order_date ON public.fact_orders(order_date);",
                    "CREATE INDEX IF NOT EXISTS idx_fact_orders_customer_id ON public.fact_orders(customer_id);",
                    "CREATE INDEX IF NOT EXISTS idx_fact_orders_net_amount ON public.fact_orders(net_amount);"
                ]
                for sql in index_queries:
                    cur.execute(sql)
                return
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                raise