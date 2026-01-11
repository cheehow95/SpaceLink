"""
Authentication Module for SpaceLink
Simple password-based authentication with optional API key support.
"""
import hashlib
import secrets
import time
from typing import Optional
from functools import wraps

# Configuration
AUTH_ENABLED = False  # Set to True to require authentication
PASSWORD_HASH = None  # Set via set_password()
API_KEYS = set()      # Valid API keys

# Session tokens (simple in-memory store)
_tokens = {}
TOKEN_EXPIRY = 3600 * 24  # 24 hours


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def set_password(password: str):
    """Set the server password."""
    global PASSWORD_HASH, AUTH_ENABLED
    PASSWORD_HASH = hash_password(password)
    AUTH_ENABLED = True
    print(f"[Auth] Password protection enabled")


def add_api_key(key: str):
    """Add a valid API key."""
    API_KEYS.add(key)
    print(f"[Auth] API key added: {key[:8]}...")


def generate_api_key() -> str:
    """Generate a new API key."""
    key = secrets.token_urlsafe(32)
    API_KEYS.add(key)
    return key


def verify_password(password: str) -> bool:
    """Verify a password against the stored hash."""
    if not AUTH_ENABLED or not PASSWORD_HASH:
        return True
    return hash_password(password) == PASSWORD_HASH


def verify_api_key(key: str) -> bool:
    """Verify an API key."""
    if not AUTH_ENABLED:
        return True
    return key in API_KEYS


def create_token(client_info: Optional[dict] = None) -> str:
    """Create a new authentication token."""
    token = secrets.token_urlsafe(32)
    _tokens[token] = {
        "created": time.time(),
        "client_info": client_info or {}
    }
    return token


def verify_token(token: str) -> bool:
    """Verify an authentication token."""
    if not AUTH_ENABLED:
        return True
    
    if token not in _tokens:
        return False
    
    token_data = _tokens[token]
    if time.time() - token_data["created"] > TOKEN_EXPIRY:
        del _tokens[token]
        return False
    
    return True


def revoke_token(token: str):
    """Revoke an authentication token."""
    if token in _tokens:
        del _tokens[token]


def cleanup_expired_tokens():
    """Remove expired tokens."""
    now = time.time()
    expired = [t for t, data in _tokens.items() 
               if now - data["created"] > TOKEN_EXPIRY]
    for t in expired:
        del _tokens[t]


def get_auth_status() -> dict:
    """Get current authentication status."""
    return {
        "enabled": AUTH_ENABLED,
        "password_set": PASSWORD_HASH is not None,
        "api_keys_count": len(API_KEYS),
        "active_tokens": len(_tokens)
    }


# FastAPI middleware support
def require_auth(func):
    """Decorator to require authentication for a route."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check for token in headers or query params
        request = kwargs.get("request")
        if request:
            token = request.headers.get("X-Auth-Token") or request.query_params.get("token")
            api_key = request.headers.get("X-API-Key")
            
            if AUTH_ENABLED:
                if not (verify_token(token) or verify_api_key(api_key)):
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=401,
                        content={"error": "Authentication required"}
                    )
        
        return await func(*args, **kwargs)
    return wrapper
