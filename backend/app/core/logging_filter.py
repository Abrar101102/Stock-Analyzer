import logging
from contextvars import ContextVar

request_id_ctx_var: ContextVar[str|None] = ContextVar("request_id",default=None)

class RequestIDFilter(logging.Filter):
  def filter(self,record:logging.LogRecord) -> bool:
    record.request_id = request_id_ctx_var.get()
    return True