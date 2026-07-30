import hashlib
import secrets
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
from flask import request, jsonify
import jwt
from .config import Config

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
    def is_allowed(self, key, limit, window_seconds):
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_seconds)
        self.requests[key] = [ts for ts in self.requests[key] if ts > cutoff]
        if len(self.requests[key]) >= limit:
            return False
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter()

def rate_limit(limit, window=3600, by_ip=True):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key = request.remote_addr if by_ip else request.headers.get('Authorization', 'anonymous')
            if not rate_limiter.is_allowed(key, limit, window):
                return jsonify({'error': f'Rate limit exceeded. Max {limit} requests per {window//60} minutes.'}), 429
            return f(*args, **kwargs)
        return decorated
    return decorator

class AuthManager:
    def __init__(self):
        self.api_keys = {}
    def generate_api_key(self, user_id, role='analyst'):
        key = secrets.token_urlsafe(32)
        hashed = hashlib.sha256(key.encode()).hexdigest()
        self.api_keys[hashed] = {'user_id': user_id, 'role': role, 'created_at': datetime.utcnow()}
        return key
    def verify_api_key(self, api_key):
        hashed = hashlib.sha256(api_key.encode()).hexdigest()
        return self.api_keys.get(hashed)
    def generate_jwt(self, user_id, role):
        payload = {'user_id': user_id, 'role': role, 'exp': datetime.utcnow() + timedelta(hours=1)}
        return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')

auth_manager = AuthManager()

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if Config.DISABLE_AUTH:
            request.current_user = {'user_id': 'dev_user', 'role': 'admin'}
            return f(*args, **kwargs)
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing authorization header'}), 401
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                return jsonify({'error': 'Invalid auth scheme'}), 401
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

def require_role(roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if Config.DISABLE_AUTH:
                return f(*args, **kwargs)
            if not hasattr(request, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401
            if request.current_user.get('role') not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator