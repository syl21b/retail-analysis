import logging
from .churn_model import load_model, train_model

logger = logging.getLogger(__name__)

_model_loaded = False

def ensure_model_loaded():
    """Load or train the churn model only when needed."""
    global _model_loaded
    if not _model_loaded:
        logger.info("Loading churn model...")
        if not load_model():
            logger.info("No saved churn model found. Training a new one...")
            train_model()
        _model_loaded = True
        logger.info("Churn model ready.")