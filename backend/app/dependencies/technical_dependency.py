from fastapi import Depends
from sqlalchemy.orm import Session
from app.dependencies.db_dependency import get_db
from app.dependencies.stock_dependencies import get_yahoo_market_data_provider
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.services.technical_persistance import TechnicalPersistanceService
from app.services.technical_orchestrator_service import TechnicalOrchestratorService
from app.dependencies.stock_dependencies import get_stock_service


def get_technical_orchestrator(
    db: Session = Depends(get_db),
    stock_service=Depends(get_stock_service),
):
    """
    Wires the full pipeline:
      MarketDataProvider → TechnicalAnalysisService → TechnicalPersistenceService
    All orchestrated by TechnicalOrchestratorService
    """
    return {
        "orchestrator": TechnicalOrchestratorService(
            stock_service=stock_service,
            analysis_service=TechnicalAnalysisService(),
            persistence_service=TechnicalPersistanceService(),
        ),
        "db": db,
    }