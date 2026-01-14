from fastapi import APIRouter

router = APIRouter(prefix="/stock",tags=["Stock"])

@router.get("/ping")
def ping():
  return {"message":"Stock endpoint is reachable"}