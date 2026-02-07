import uuid
import logging
from fastapi import Request
from app.core.logging_filter import request_id_ctx_var

logger = logging.getLogger(__name__)

async def request_context_middleware(request:Request,call_next):
  request_id = str(uuid.uuid4())
  request.state.request_id = request_id
  request_id_ctx_var.set(request_id)

  logger.info(
    "Incoming Request",
    extra={
      "path":request.url.path,
      "method":request.method
    }
  )

  response = await call_next(request)
  response.headers["X-Request-ID"] = request_id
  return response