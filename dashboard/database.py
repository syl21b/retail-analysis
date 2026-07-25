import logging
import time
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class SecureDatabase:
    def __init__(self, db_url, min_conn=2, max_conn=20):
        if '?' in db_url:
            db_url += '&sslmode=require'
        else:
            db_url += '?sslmode=require'
        keepalive_params = [
            'keepalives_idle=60',
            'keepalives_interval=10',
            'keepalives_count=5',
            'connect_timeout=10',
            'tcp_user_timeout=10000'
        ]
        for p in keepalive_params:
            db_url += f'&{p}'
        self.pool = SimpleConnectionPool(min_conn, max_conn, db_url)

    def get_connection(self):
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        except Exception:
            self.pool.putconn(conn, close=True)
            conn = self.pool.getconn()
        return conn

    def put_connection(self, conn):
        self.pool.putconn(conn)

    @contextmanager
    def get_cursor(self):
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                yield cur
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                self.put_connection(conn)

    def execute_query(self, query, params=None, retries=3):
        last_exception = None
        for attempt in range(retries + 1):
            try:
                with self.get_cursor() as cur:
                    cur.execute(query, params)
                    if query.strip().upper().startswith(('SELECT', 'WITH')):
                        return cur.fetchall()
                    return cur.rowcount
            except Exception as e:
                last_exception = e
                if 'connection' in str(e).lower() or 'closed' in str(e).lower():
                    logger.warning(f"Query failed (attempt {attempt+1}): {e}. Retrying in 0.5s...")
                    if attempt < retries:
                        time.sleep(0.5)
                        continue
                raise
        raise last_exception

# Global db instance (initialised after config)
db = None

def init_db(db_url):
    global db
    db = SecureDatabase(db_url)
    return db