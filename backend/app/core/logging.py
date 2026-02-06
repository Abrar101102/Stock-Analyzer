import logging
import sys

LOG_FORMAT = (
  "%(asctime)s | "
  "%(levelname)s | "
  "%(name)s | "
  "%(message)s"
)

def set_up_logging(level=logging.info):
  logging.basicConfig(
    level=level,
    format=LOG_FORMAT,
    handlers=[
      logging.StreamHandler(sys.stdout)
    ]
  )
