import json
import logging
from functools import wraps
from typing import Callable, Any
import redis
import pandas as pd
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize a global Redis connection
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception as e:
    logger.warning(f"Failed to connect to Redis: {e}. Caching will be disabled.")
    redis_client = None

def redis_cache(expire_seconds: int = 3600, returns_df: bool = False):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if redis_client is None:
                return func(*args, **kwargs)

            try:
                cache_args = args[1:] if args and hasattr(args[0], '__dict__') else args
                key_parts = [func.__module__, func.__name__, str(cache_args), str(kwargs)]
                cache_key = "cache:" + ":".join(key_parts)
                
                cached_val = redis_client.get(cache_key)
                if cached_val:
                    logger.debug(f"Cache hit for {cache_key}")
                    if returns_df:
                        return pd.read_json(cached_val, orient='records')
                    return json.loads(cached_val)
                    
            except Exception as e:
                logger.warning(f"Redis cache key generation/retrieval failed: {e}")
                return func(*args, **kwargs)

            result = func(*args, **kwargs)

            try:
                if result is not None:
                    if returns_df and type(result).__name__ == "DataFrame":
                        redis_client.setex(cache_key, expire_seconds, result.to_json(date_format='iso', orient='records'))
                    else:
                        redis_client.setex(cache_key, expire_seconds, json.dumps(result))
            except Exception as e:
                logger.warning(f"Redis cache set failed for {cache_key}: {e}")

            return result

        return wrapper
    return decorator
