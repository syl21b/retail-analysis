from dotenv import load_dotenv
load_dotenv()

import os
import sys
import logging

sys.stdout.reconfigure(line_buffering=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

logger.info("🚀 Starting app1.py")

from flask import Flask
from flask_cors import CORS
from flask_compress import Compress
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import Config   # ✅ relative import

logger.info("📦 Config imported")

from . import database       # ✅ relative import (was: import database)
logger.info("📦 Database module imported")

from .routes import register_routes   # ✅ relative import (was: from routes import register_routes)
logger.info("📦 Routes module imported")

from .simulation import train_simulation_model   # ✅ relative import
logger.info("📦 Simulation module imported")

from .sql_helpers import create_performance_indexes   # ✅ relative import
logger.info("📦 SQL helpers imported")

# Init database
logger.info("🔗 Initialising database...")
database.init_db(Config.DATABASE_URL) 
logger.info("✅ Database initialised")

# Pre-warm the extra metrics cache for AI
logger.info("⏳ Pre-loading extra metrics for AI...")
try:
    from .ai import get_cached_extra_metrics
    get_cached_extra_metrics()
    logger.info("✅ Extra metrics cached.")
except Exception as e:
    logger.warning(f"Could not pre-load metrics: {e}")


from .churn_model import load_model, train_model

# Load or train churn model
if not load_model():
    logger.info("No saved churn model found. Training a new one...")
    train_model()
    
app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = Config.SECRET_KEY

CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
Compress(app)

logger.info("📡 Registering routes...")
register_routes(app)
logger.info("✅ Routes registered")

# Startup tasks
_startup_done = False

@app.before_request
def run_startup_tasks():
    global _startup_done
    if not _startup_done:
        logger.info("⚙️ Running startup tasks...")
        try:
            logger.info("📊 Creating performance indexes...")
            create_performance_indexes(database.db)   # <-- pass database.db
            logger.info("📊 Indexes created.")
            logger.info("🧠 Training simulation model...")
            with app.app_context():
                train_simulation_model()
            logger.info("✅ Startup tasks completed.")
        except Exception as e:
            logger.error(f"⚠️ Startup tasks failed: {e}", exc_info=True)
        _startup_done = True

if __name__ == '__main__':
    logger.info("🔥 Starting Flask development server on port 5001")
    with app.app_context():
        train_simulation_model()
    app.run(host='0.0.0.0', port=5001, debug=Config.DEBUG)