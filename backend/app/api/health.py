from fastapi import APIRouter
from app.core.logging import trace

router = APIRouter(prefix="/health" , tags=["Health"])

@router.get("", summary="Health Check")
@trace
def health_check():
  return {
    "status":"UP",
    "service":"Stock Analyzer API"
  }

