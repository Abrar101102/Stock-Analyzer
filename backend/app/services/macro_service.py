import requests
import logging
from typing import Dict, Optional
from app.core.config import settings
from app.core.cache import redis_cache
from app.core.logging import trace

logger = logging.getLogger(__name__)

class MacroService:
    """
    Fetches macroeconomic data using the FRED API.
    """
    
    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    @redis_cache(expire_seconds=86400) # cache for 24h as macro data updates daily/monthly
    @trace
    def get_macro_signals(self) -> Dict[str, Optional[float]]:
        if not hasattr(settings, 'FRED_API_KEY') or not settings.FRED_API_KEY:
            logger.warning("FRED_API_KEY is not configured. Macro signals disabled.")
            return {"interest_rate": None, "inflation": None}

        signals = {}
        # Fetch latest Fed Funds Rate (Interest Rate)
        signals["interest_rate"] = self._fetch_latest_fred_series("FEDFUNDS")
        
        # Fetch latest CPIAUCSL (Inflation Proxy - CPI)
        # We fetch YoY% change for CPI
        signals["inflation"] = self._fetch_latest_fred_series("CPIAUCSL", units="pc1")

        return signals
    

    @trace
    def _fetch_latest_fred_series(self, series_id: str, units: str = "lin") -> Optional[float]:
        try:
            params = {
                "series_id": series_id,
                "api_key": settings.FRED_API_KEY,
                "file_type": "json",
                "units": units,
                "sort_order": "desc",
                "limit": 1
            }
            res = requests.get(self.BASE_URL, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            observations = data.get("observations", [])
            if observations:
                val = observations[0].get("value")
                if val and val != ".":
                    return round(float(val), 2)
            return None
        except Exception as e:
            logger.error(f"Error fetching FRED series {series_id}: {e}")
            return None
