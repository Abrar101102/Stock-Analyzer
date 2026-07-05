import asyncio
import json
import logging
from functools import wraps
from typing import Callable, Any
import redis
import pandas as pd
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception as e:
    logger.warning(f"Failed to connect to Redis: {e}. Caching will be disabled.")
    redis_client = None

def redis_cache(expire_seconds: int = 3600, returns_df: bool = False):
    def decorator(func: Callable) -> Callable:

        def _build_key(args, kwargs):
            cache_args = args[1:] if args and hasattr(args[0], '__dict__') else args
            key_parts = [func.__module__, func.__name__, str(cache_args), str(kwargs)]
            return "cache:" + ":".join(key_parts)

        def _read_cached(cached_val):
            if returns_df:
                return pd.read_json(cached_val, orient='records')
            return json.loads(cached_val)

        def _write_cache(cache_key, result):
            if result is not None:
                if returns_df and type(result).__name__ == "DataFrame":
                    redis_client.setex(cache_key, expire_seconds, result.to_json(date_format='iso', orient='records'))
                else:
                    redis_client.setex(cache_key, expire_seconds, json.dumps(result))

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if redis_client is None:
                return await func(*args, **kwargs)        # ← await here

            try:
                cache_key = _build_key(args, kwargs)
                cached_val = redis_client.get(cache_key)
                if cached_val:
                    logger.debug(f"Cache hit for {cache_key}")
                    return _read_cached(cached_val)
            except Exception as e:
                logger.warning(f"Redis cache retrieval failed: {e}")
                return await func(*args, **kwargs)        # ← await here

            result = await func(*args, **kwargs)          # ← await here

            try:
                _write_cache(cache_key, result)
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if redis_client is None:
                return func(*args, **kwargs)

            try:
                cache_key = _build_key(args, kwargs)
                cached_val = redis_client.get(cache_key)
                if cached_val:
                    logger.debug(f"Cache hit for {cache_key}")
                    return _read_cached(cached_val)
            except Exception as e:
                logger.warning(f"Redis cache retrieval failed: {e}")
                return func(*args, **kwargs)

            result = func(*args, **kwargs)

            try:
                _write_cache(cache_key, result)
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")

            return result

        # ← automatically pick the right wrapper based on the function type
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator