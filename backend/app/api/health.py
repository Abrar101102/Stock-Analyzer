from fastapi import APIRouter

router = APIRouter(prefix="/health" , tags=["Health"])

@router.get("", summary="Health Check")
def health_check():
  return {
    "status":"UP",
    "service":"Stock Analyzer API"
  }