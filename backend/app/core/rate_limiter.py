import time
import logging
from fastapi import Request, HTTPException
from collections import defaultdict

logger = logging.getLogger(__name__)

class RateLimiter:
  def __init__(self):
    self.requests = defaultdict(list)

  def check(self,key:str,limit:int,window:int):
    now = time.time()
    timestamps = self.requests[key]

    self.requests[key] = [t for t in timestamps if now - t < window]

    if len(self.requests[key]) >= limit:
      logger.warning(
        "Rate Limit Exceeded",
        extra={
          "Key":key,
          "limit":limit,
          "window":window
        }
      )

      raise HTTPException(
        status_code = 429,
        detail = "Rate limit Exceeded"
      )


