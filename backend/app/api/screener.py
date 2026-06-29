from fastapi import APIRouter, HTTPException, Query
from app.core.logging import trace
from datetime import datetime
from app.fundamentals.data_providers.screener_provider import ScreenerFundamentalProvider
from app.utils.json_sanitize import sanitize_json_floats

router = APIRouter(prefix="/screener", tags=["Screener"])

@router.get("")
@trace
def get_screener_data(
    symbol: str = Query(..., description="Stock symbol to screen")
):
    try:
        # Instantiate your existing provider directly
        provider = ScreenerFundamentalProvider()

        item = provider.get_company_overview(symbol)

        # Add Revenue Growth YoY from latest two annual revenue points.
        income_statements = provider.get_income_statements(symbol, period="annual", limit=2)
        if len(income_statements) >= 2:
            latest_revenue = income_statements[0].total_revenue
            previous_revenue = income_statements[1].total_revenue
            if latest_revenue is not None and previous_revenue not in (None, 0):
                growth_yoy = ((latest_revenue - previous_revenue) / previous_revenue) * 100
                item.setdefault("metrics", {})["revenue_growth_yoy"] = round(growth_yoy, 2)
        
        # Format response for the Angular UI
        response = {
            "symbol": symbol,
            "provider": "screener.in",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "ok",
            "data": {
                "count": 1,
                "items": [item]
            }
        }
        
        return sanitize_json_floats(response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))