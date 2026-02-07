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
