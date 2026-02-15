from fastapi import Request
from app.core.rate_limiter import RateLimiter
from app.core.rate_limit_config import RATE_LIMITS

limiter = RateLimiter()

def rate_limit(rule_name:str):
    def dependency(request:Request):
        client_ip = request.client.host
        path = request.url.path

        rule = RATE_LIMITS[rule_name]

        key = f"{client_ip}:{path}"

        limiter.check(key = key, limit = rule["requests"],window=rule["window_seconds"])
    
    return dependency