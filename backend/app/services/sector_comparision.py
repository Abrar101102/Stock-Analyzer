from app.registry.stock_registry import StockRegistry
from app.core.exceptions import NotFoundError
from sqlalchemy.orm import Session
import statistics
from typing import Callable, Any, Optional
from datetime import datetime
from app.models.response.sector_comparison_model import (
    SectorComparisonResponse,
    MetricComparison,
    SectorThesisVerdict
)
from app.core.logging import trace

class SectorComparisionService:
  def __init__(self,valuation_service,trend_service):
    self.valuation_service = valuation_service
    self.trend_service = trend_service

  @trace
  def _compare_metric(self, db: Session, symbol: str, metric_getter: Callable[[Session, str], Any], higher_is_better: bool = False):
    try:
        peers = StockRegistry.get_peers(symbol, db)
    except Exception:
        return None
        
    values = []
    for peer in peers:
        try:
            val = metric_getter(db, peer.symbol)
            if val is not None:
                values.append((peer.symbol, val))
        except Exception:
            pass

    if not values:
        return None
    
    company_value = dict(values).get(symbol)
    if company_value is None:
        return None

    numbers = [v for _, v in values if v is not None]
    if not numbers:
        return None

    sector_avg = statistics.mean(numbers)
    ranked = sorted(values, key=lambda x: x[1], reverse=higher_is_better)
    rank = [s for s, _ in ranked].index(symbol) + 1

    below = len([v for v in numbers if v < company_value])
    percentile = below / len(numbers) * 100

    return {
        "company_value": round(company_value, 4) if isinstance(company_value, float) else company_value,
        "sector_average": round(sector_avg, 4),
        "rank": rank,
        "percentile": round(percentile, 2),
        "total_peers": len(numbers)
    }

  @trace
  def get_roe(self, db, s):
    try:
        trends = self.trend_service.get_trends(db, s, limit=2)
        if trends.years and len(trends.years) > 0:
            return getattr(trends.years[-1], 'roe', None)
    except Exception:
        pass
    return None

  @trace
  def get_revenue_growth(self, db, s):
    try:
        trends = self.trend_service.get_trends(db, s, limit=2)
        if trends.years and len(trends.years) > 0:
            return getattr(trends.years[-1], 'revenue_growth', None)
    except Exception:
        pass
    return None

  @trace
  def compare_pe_ratio(self,db:Session,symbol:str):
    res = self._compare_metric(db, symbol, self.valuation_service.get_pe_ratio, higher_is_better=False)
    if not res:
        raise NotFoundError(code="NO_PEERS_FOUND", message=f"No peer PE metrics found for symbol {symbol}")
    return res

  @trace
  def compare_ev_ebitda(self, db: Session, symbol: str):
      return self._compare_metric(db, symbol, self.valuation_service.get_ev_ebitda, higher_is_better=False)

  @trace
  def compare_price_to_book(self, db: Session, symbol: str):
      return self._compare_metric(db, symbol, self.valuation_service.get_price_to_book, higher_is_better=False)

  @trace
  def compare_roe(self, db: Session, symbol: str):
      return self._compare_metric(db, symbol, self.get_roe, higher_is_better=True)

  @trace
  def compare_revenue_growth(self, db: Session, symbol: str):
      return self._compare_metric(db, symbol, self.get_revenue_growth, higher_is_better=True)

  @trace
  def generate_sector_thesis(self, symbol: str, pe_cmp, ev_ebitda_cmp, pb_cmp, roe_cmp, rev_growth_cmp) -> SectorThesisVerdict:
      obs = []
      is_value = False
      is_growth = False
      is_quality = False
      
      expensive_count = 0
      cheap_count = 0

      # Valuation
      if pe_cmp and pe_cmp.get("percentile", 50) < 50:
          cheap_count += 1
          obs.append(f"P/E ratio trades better than median of peers.")
      elif pe_cmp:
          expensive_count += 1
          obs.append(f"P/E ratio trades at a premium.")

      if ev_ebitda_cmp and ev_ebitda_cmp.get("percentile", 50) < 50:
          cheap_count += 1
          obs.append(f"Attractive EV/EBITDA compared to peers.")
      elif ev_ebitda_cmp:
          expensive_count += 1

      is_value = cheap_count >= expensive_count and cheap_count > 0

      # Quality / Growth
      if roe_cmp and roe_cmp.get("percentile", 50) >= 50:
          is_quality = True
          obs.append(f"Strong ROE profile in the top half of peers.")
      
      if rev_growth_cmp and rev_growth_cmp.get("percentile", 50) >= 50:
          is_growth = True
          obs.append(f"Revenue growth outpaces sector median.")

      if is_value and (is_quality or is_growth):
          verdict = "Value Play with Quality"
          rationale = f"{symbol} trades at a relative discount while maintaining strong business fundamentals."
      elif not is_value and (is_quality or is_growth):
          verdict = "Growth at Premium"
          rationale = f"{symbol} commands a higher valuation, justified by its strong growth and quality metrics."
      elif not is_value and not is_quality and not is_growth:
          verdict = "Deteriorating Comps"
          rationale = f"{symbol} screens poorly on both valuation and fundamental momentum."
      else:
          verdict = "In-line with Sector"
          rationale = f"{symbol} shows average metrics balanced across valuation and growth."

      return SectorThesisVerdict(
          verdict=verdict,
          rationale=rationale,
          key_observations=obs
      )

  @trace
  def compare_all_metrics(self, db: Session, symbol: str) -> SectorComparisonResponse:
      try:
           pe = self.compare_pe_ratio(db, symbol)
      except NotFoundError:
           pe = None

      ev = self.compare_ev_ebitda(db, symbol)
      pb = self.compare_price_to_book(db, symbol)
      roe = self.compare_roe(db, symbol)
      rev = self.compare_revenue_growth(db, symbol)
      
      thesis = self.generate_sector_thesis(symbol, pe, ev, pb, roe, rev)

      return SectorComparisonResponse(
          symbol=symbol,
          pe_comparison=MetricComparison(**pe) if pe else None,
          ev_ebitda_comparison=MetricComparison(**ev) if ev else None,
          pb_comparison=MetricComparison(**pb) if pb else None,
          roe_comparison=MetricComparison(**roe) if roe else None,
          revenue_growth_comparison=MetricComparison(**rev) if rev else None,
          sector_thesis=thesis,
          generated_at=datetime.utcnow()
      )