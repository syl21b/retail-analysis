import logging
from .churn_model import load_model

logger = logging.getLogger(__name__)

_model_loaded = False

def ensure_model_loaded():
    """Load the churn model from disk. Do not train."""
    global _model_loaded
    if not _model_loaded:
        logger.info("Loading churn model...")
        if load_model():
            _model_loaded = True
            logger.info("Churn model loaded successfully.")
        else:
            logger.error("Churn model files not found.")
            # We do not raise here; the endpoints will return empty/error
    return _model_loaded