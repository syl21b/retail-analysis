import sys
from pathlib import Path

# Add the parent directory (the one containing 'dashboard') to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import os
import logging
import threading

sys.stdout.reconfigure(line_buffering=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

logger.info("🚀 Starting app.py")

from flask import Flask
from flask_cors import CORS
from flask_compress import Compress
from werkzeug.middleware.proxy_fix import ProxyFix
from dashboard.config import Config

logger.info("📦 Config imported")

from dashboard import database
logger.info("📦 Database module imported")

from dashboard.routes import register_routes
logger.info("📦 Routes module imported")

from dashboard.simulation import train_simulation_model
logger.info("📦 Simulation module imported")

from dashboard.sql_helpers import create_performance_indexes
logger.info("📦 SQL helpers imported")

# Init database
logger.info("🔗 Initialising database...")
database.init_db(Config.DATABASE_URL)
logger.info("✅ Database initialised")

# Pre-warm the extra metrics cache for AI (lightweight)
logger.info("⏳ Pre-loading extra metrics for AI...")
try:
    from dashboard.ai import get_cached_extra_metrics
    get_cached_extra_metrics()
    logger.info("✅ Extra metrics cached.")
except Exception as e:
    logger.warning(f"Could not pre-load metrics: {e}")

# --------------------------------------------------------------
#  No churn model loading/training here – will be done lazily
# --------------------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = Config.SECRET_KEY

CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
Compress(app)

logger.info("📡 Registering routes...")
register_routes(app)
logger.info("✅ Routes registered")

# ==============================================================
#  Startup tasks are now run in a background thread
#  (so the server binds to the port immediately)
# ==============================================================
def run_startup_tasks():
    """Run expensive startup tasks in a background thread."""
    with app.app_context():
        logger.info("⚙️ Running startup tasks in background...")
        try:
            logger.info("📊 Creating performance indexes...")
            create_performance_indexes(database.db)
            logger.info("📊 Indexes created.")

            logger.info("🧠 Training simulation model...")
            train_simulation_model()
            logger.info("✅ Simulation model trained.")

            logger.info("🧠 Churn model will be trained on first use (lazy loading).")
            logger.info("✅ All startup tasks completed.")
        except Exception as e:
            logger.error(f"⚠️ Startup tasks failed: {e}", exc_info=True)

if __name__ == '__main__':
    logger.info("🔥 Starting Flask development server on port 5001")
    
    # Start the heavy tasks in a background thread (daemon so it doesn't block exit)
    threading.Thread(target=run_startup_tasks, daemon=True).start()
    
    # Start the server immediately – this binds to the port quickly
    app.run(host='0.0.0.0', port=5001, debug=Config.DEBUG)