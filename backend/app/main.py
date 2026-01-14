from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.stock import router as stock_router

app = FastAPI(title="Stock Analyzer")
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(stock_router,prefix="/api")
# @app.get("/health")
# def health_check():
#   return {"status":"ok"}