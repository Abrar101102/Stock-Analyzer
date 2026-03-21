from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from app.fundamentals.data_providers.screener_provider import ScreenerFundamentalProvider
from app.utils.json_sanitize import sanitize_json_floats

router = APIRouter(prefix="/screener", tags=["Screener"])

@router.get("")
def get_screener_data(
    symbol: str = Query(..., description="Stock symbol to screen")
):
    try:
        # Instantiate your existing provider directly
        provider = ScreenerFundamentalProvider()
        
        # Call the new method we just added
        item = provider.get_company_overview(symbol)
        
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