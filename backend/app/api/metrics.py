from fastapi import APIRouter
from app.core.metrics import REQUEST_COUNT,REQUEST_LATENCY,ERROR_COUNT

router = APIRouter(tags= ["METRICS"])

router.get("/metrics")
def metrics():
  return {
    "request":dict(REQUEST_COUNT),
    "error":dict(ERROR_COUNT),
    "latency_avg":{
      path: sum(times) / len(times)
      for path,times in REQUEST_LATENCY.items()
      if times
    }
  }