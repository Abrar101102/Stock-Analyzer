import asyncio
import functools
import logging
import sys
from app.core.logging_filter import RequestIDFilter

LOG_FORMAT = (
  "%(asctime)s | "
  "%(levelname)s | "
  "%(name)s | "
  "%(request_id)s | "
  "%(message)s"
)

def set_up_logging(level=logging.INFO):
  root_logger = logging.getLogger()
  root_logger.setLevel(level)

  handler = logging.StreamHandler(sys.stdout)
  handler.setFormatter(logging.Formatter(LOG_FORMAT))
  handler.addFilter(RequestIDFilter())

  root_logger.addHandler(handler)
  logging.basicConfig(
    level=level,
    format=LOG_FORMAT,
    handlers=[
      logging.StreamHandler(sys.stdout)
    ]
  )

def trace(func):
  """Decorator to log function entry and exit with arguments and return value."""
  logger = logging.getLogger(func.__module__)

  @functools.wraps(func)
  async def async_wrapper(*args, **kwargs):
      logger.debug(f"Entering {func.__qualname__} with args: {args}, kwargs: {kwargs}")
      try:
         result = await func(*args, **kwargs)
         logger.debug(f"Exiting {func.__qualname__} returned with result: {result}")
         return result
      except Exception as e:
         logger.exception(f"Exception in {func.__qualname__}: {e}")
         raise
  
  @functools.wraps(func)
  def sync_wrapper(*args, **kwargs):
      logger.debug(f"Entering {func.__qualname__} with args: {args}, kwargs: {kwargs}")
      try:
         result = func(*args, **kwargs)
         logger.debug(f"Exiting {func.__qualname__} returned with result: {result}")
         return result
      except Exception as e:
         logger.exception(f"Exception in {func.__qualname__}: {e}")
         raise
  
  return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper