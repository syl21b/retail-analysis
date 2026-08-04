import logging
import time
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
import psycopg2

logger = logging.getLogger(__name__)

class SecureDatabase:
    def __init__(self, db_url, min_conn=2, max_conn=20):
        # Add keepalives and timeouts to the URL
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
        self.db_url = db_url
        self.min_conn = min_conn
        self.max_conn = max_conn
        self.pool = None
        self._init_pool()

    def _init_pool(self):
        """Initialize or reinitialize the connection pool."""
        if self.pool:
            try:
                self.pool.closeall()
            except Exception:
                pass
        self.pool = SimpleConnectionPool(
            self.min_conn, self.max_conn, self.db_url,
            keepalives_idle=60,
            keepalives_interval=10,
            keepalives_count=5,
            connect_timeout=10
        )

    def get_connection(self):
        """Get a connection from the pool, with retry on failure."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                conn = self.pool.getconn()
                # Test the connection
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                return conn
            except Exception as e:
                logger.warning(f"Connection attempt {attempt+1} failed: {e}")
                if attempt < max_attempts - 1:
                    # Reinitialize the pool and retry
                    self._init_pool()
                    time.sleep(0.5)
                else:
                    raise
        raise Exception("Failed to get database connection after retries")

    def put_connection(self, conn):
        """Return connection to the pool, closing if broken."""
        try:
            self.pool.putconn(conn, close=True)
        except Exception:
            pass

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
                try:
                    conn.rollback()
                except Exception:
                    pass
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
                # If connection error, we retry after reinitializing pool
                if 'connection' in str(e).lower() or 'closed' in str(e).lower() or 'SSL' in str(e):
                    logger.warning(f"Query failed (attempt {attempt+1}): {e}. Retrying...")
                    if attempt < retries:
                        self._init_pool()
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