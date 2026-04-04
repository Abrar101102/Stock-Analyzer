from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.stock import router as stock_router
from app.api.news import router as news_router
from app.api.metrics import router as metrics_router
from app.api.v1.fundamentals import router as fundamental_router
from app.api.internal.fundamental_persistance import router as ingest_router
from app.api.fundamental_read_routes import router as read_router
from app.api.derived_metrics_route import router as derived_metrics_router
from app.api.trend_route import router as trend_router
from app.api.quarterly import router as quarterly_router
from app.api.technical_analysis_route import router as technical_router
from app.api.screener import router as screener_router
from app.api.exception_handlers import domain_error_handler
from app.core.exceptions import DomainError
from app.core.logging import set_up_logging
from app.middleware.request_context import request_context_middleware
from app.middleware.metrics import metrics_middleware
from app.db.base_class import Base
from app.scheduler import start_scheduler
from app.db.session import engine
from app.core.lifespan import lifespan

Base.metadata.create_all(bind=engine)# Responsible for creating Table if not created

app = FastAPI(title="Stock Analyzer",lifespan=lifespan)

set_up_logging()
app.middleware("http")(request_context_middleware)
app.middleware("http")(metrics_middleware)
app.add_exception_handler(DomainError,domain_error_handler)
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

routes_under_api = [stock_router,news_router,fundamental_router,ingest_router,read_router,metrics_router,derived_metrics_router,trend_router,quarterly_router,technical_router,health_router,screener_router]
# app.include_router(health_router)
# app.include_router(stock_router,prefix="/api")
for route in routes_under_api:
  app.include_router(route,prefix="/api")

@app.on_event("startup")
def startup_event():
  start_scheduler()
# app.include_router(fundamental_router,prefix="/api")
# @app.get("/health")
# def health_check():
#   return {"status":"ok"}