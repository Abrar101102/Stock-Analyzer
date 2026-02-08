import time
from fastapi import Request
from app.core.metrics import REQUEST_COUNT,REQUEST_LATENCY,ERROR_COUNT

async def metrics_middleware(request:Request,call_next):
  start = time.time()
  path = request.url.path

  REQUEST_COUNT[path] += 1

  try:
    response = await call_next(request)
    return response
  
  except Exception:
    ERROR_COUNT[path] +=1
    raise
  finally:
    duration = time.time() - start
    REQUEST_LATENCY[path].append(duration )
