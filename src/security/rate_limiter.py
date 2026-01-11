"""
Rate Limiter for SpaceLink
Provides simple rate limiting for API endpoints.
"""
import time
from collections import defaultdict
from functools import wraps


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_second: int = 10, burst: int = 20):
        self.rps = requests_per_second
        self.burst = burst
        self.tokens = defaultdict(lambda: burst)
        self.last_update = defaultdict(float)
    
    def is_allowed(self, key: str = "default") -> bool:
        """Check if a request is allowed for the given key."""
        now = time.time()
        elapsed = now - self.last_update[key]
        self.last_update[key] = now
        
        # Replenish tokens
        self.tokens[key] = min(
            self.burst,
            self.tokens[key] + elapsed * self.rps
        )
        
        # Check if request is allowed
        if self.tokens[key] >= 1:
            self.tokens[key] -= 1
            return True
        return False
    
    def get_remaining(self, key: str = "default") -> int:
        """Get remaining tokens for the given key."""
        return int(self.tokens[key])


# Global rate limiters
command_limiter = RateLimiter(requests_per_second=30, burst=50)  # For control commands
api_limiter = RateLimiter(requests_per_second=10, burst=20)      # For API calls


def rate_limit(limiter: RateLimiter = None, key_func=None):
    """Decorator to rate limit an endpoint."""
    if limiter is None:
        limiter = api_limiter
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get key from request if available
            request = kwargs.get("request")
            if key_func and request:
                key = key_func(request)
            elif request:
                key = request.client.host if request.client else "unknown"
            else:
                key = "default"
            
            if not limiter.is_allowed(key):
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": 1
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_command_rate(ip: str = "default") -> bool:
    """Check if a command is allowed (for WebSocket commands)."""
    return command_limiter.is_allowed(ip)


def get_rate_status() -> dict:
    """Get rate limiter status."""
    return {
        "command_limiter": {
            "rps": command_limiter.rps,
            "burst": command_limiter.burst
        },
        "api_limiter": {
            "rps": api_limiter.rps,
            "burst": api_limiter.burst
        }
    }
