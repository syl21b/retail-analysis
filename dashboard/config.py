import os
import sys
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32))
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    RATELIMIT_AI = int(os.environ.get('RATELIMIT_AI', 20))
    RATELIMIT_NLQ = int(os.environ.get('RATELIMIT_NLQ', 50))
    RATELIMIT_SIMULATE = int(os.environ.get('RATELIMIT_SIMULATE', 30))
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        sys.exit("DATABASE_URL environment variable not set.")
    
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5000').split(',')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    DISABLE_AUTH = os.environ.get('DISABLE_AUTH', 'true').lower() == 'true'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # Memory optimisation
    DATAFRAME_CACHE_SIZE = int(os.environ.get('DATAFRAME_CACHE_SIZE', 3))
    DATAFRAME_CACHE_TTL = int(os.environ.get('DATAFRAME_CACHE_TTL', 60))
    MAX_ROWS_PER_DATASET = int(os.environ.get('MAX_ROWS_PER_DATASET', 5000))