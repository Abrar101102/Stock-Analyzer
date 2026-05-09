from datetime import datetime, timezone
from typing import Any
import logging
from sqlalchemy.orm import Session
from app.models.response.thesis_model import ThesisResponseModel
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.services.news_service import NewsService
from app.services.valuation_service import ValuationService
from app.services.fundamental_read_service import FundamentalReadService
from app.services.composite_score_service import CompositeScoreService
from app.data_sources.market_data_source import MarketDataSource
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)

class ThesisService:
  def __init__(
    self,
    llm_provider=None,
    db: Session = None,
    technical_service: TechnicalAnalysisService = None,
    news_service: NewsService = None,
    valuation_service: ValuationService = None,
    fundamental_service: FundamentalReadService = None,
    composite_score_service: CompositeScoreService = None,
  ):
    self.llm_provider = llm_provider
    self.db = db
    self.technical_service = technical_service or TechnicalAnalysisService()
    self.news_service = news_service
    self.valuation_service = valuation_service
    self.fundamental_service = fundamental_service or FundamentalReadService()
    self.composite_score_service = composite_score_service or CompositeScoreService()
    self.market_data_source = MarketDataSource()

  def generate(self, symbol: str) -> dict[str, Any]:
    """Generate thesis with real signals from upstream services."""
    try:
      signals = self._gather_signals(symbol)
    except Exception as e:
      logger.warning(f"Failed to gather signals for {symbol}: {e}")
      signals = self._fallback_signals()

    metrics = self._extract_metrics_for_prompt(symbol, signals)
    verdict = self._rule_based_verdict(signals)
    composite_score = self.composite_score_service.compute(signals)
    summary = self._fallback_summary(symbol, signals, verdict)

    if self.llm_provider:
      try:
        prompt = self._build_prompt(symbol, signals, metrics)
        raw = self.llm_provider.generate(prompt)
        mapped = self._map_verdict(raw)
        if mapped:
          verdict = mapped
        summary = self._clean_summary(raw) or summary
      except Exception as e:
        logger.warning(f"LLM generation failed: {e}")
        summary = self._fallback_summary(symbol, signals, verdict)

    return ThesisResponseModel(
      symbol=symbol,
      verdict=verdict,
      composite_score=composite_score,
      summary=summary,
      signals=signals,
      generated_at=datetime.now(timezone.utc)
    )

  def _gather_signals(self, symbol: str) -> dict[str, str]:
    """Assemble signals from all upstream services."""
    signals = {}

    # Technical signal from price history
    try:
      df = self.market_data_source.fetch_history(symbol, period="1y")
      if df is not None and not df.empty:
        technical_signals = self.technical_service.get_signals(df)
        signals["technical"] = self._map_technical_signal(technical_signals)
      else:
        signals["technical"] = "neutral"
    except Exception as e:
      logger.warning(f"Failed to fetch technical signals for {symbol}: {e}")
      signals["technical"] = "neutral"

    # News sentiment signal
    if self.news_service:
      try:
        news_result = self.news_service.get_news_and_sentiment(symbol, limit=10)
        sentiment_label = news_result.get("overall_sentiment", "neutral")
        signals["sentiment"] = sentiment_label
      except Exception as e:
        logger.warning(f"Failed to fetch news sentiment for {symbol}: {e}")
        signals["sentiment"] = "neutral"
    else:
      signals["sentiment"] = "neutral"

    # Valuation signal
    if self.valuation_service and self.db:
      try:
        valuation = self.valuation_service.get_valuation(self.db, symbol)
        pe_ratio = valuation.pe_ratio
        signals["valuation"] = self._map_valuation_signal(pe_ratio)
      except Exception as e:
        logger.warning(f"Failed to fetch valuation for {symbol}: {e}")
        signals["valuation"] = "fair"
    else:
      signals["valuation"] = "fair"

    # Fundamental signal
    if self.db:
      try:
        from datetime import datetime as dt
        current_year = dt.now().year
        snapshot = self.fundamental_service.get_snapshot(
          self.db, symbol, fiscal_year=current_year
        )
        if snapshot:
          signals["fundamental"] = self._map_fundamental_signal(snapshot)
        else:
          signals["fundamental"] = "neutral"
      except Exception as e:
        logger.warning(f"Failed to fetch fundamentals for {symbol}: {e}")
        signals["fundamental"] = "neutral"
    else:
      signals["fundamental"] = "neutral"

    return signals

  def _fallback_signals(self) -> dict[str, str]:
    """Return neutral signals when data retrieval fails."""
    return {
      "fundamental": "neutral",
      "technical": "neutral",
      "sentiment": "neutral",
      "valuation": "fair"
    }

  def _map_technical_signal(self, technical_signals: dict) -> str:
    """Map technical indicators to bullish/neutral/bearish."""
    if not technical_signals:
      return "neutral"
    # Simple heuristic: count bullish vs bearish signals
    bullish_count = sum(
      1 for sig in technical_signals.values()
      if sig in ["golden_cross", "bullish", "oversold"]
    )
    bearish_count = sum(
      1 for sig in technical_signals.values()
      if sig in ["death_cross", "bearish", "overbought"]
    )
    if bullish_count > bearish_count:
      return "bullish"
    elif bearish_count > bullish_count:
      return "bearish"
    return "neutral"

  def _map_valuation_signal(self, pe_ratio: float | None) -> str:
    """Map P/E ratio to cheap/fair/expensive."""
    if pe_ratio is None:
      return "fair"
    if pe_ratio < 15:
      return "cheap"
    elif pe_ratio > 25:
      return "expensive"
    return "fair"

  def _map_fundamental_signal(self, snapshot) -> str:
    """Map fundamental metrics (net margin, ROE) to positive/neutral/negative."""
    if not snapshot:
      return "neutral"
    # Extract key metrics
    total_revenue = snapshot.total_revenue
    net_income = snapshot.net_income
    equity = snapshot.shareholders_equity

    if not total_revenue or not net_income or not equity:
      return "neutral"

    net_margin = net_income / total_revenue if total_revenue != 0 else 0
    roe = net_income / equity if equity != 0 else 0

    # Simple scoring: positive if both metrics are healthy
    margin_good = net_margin > 0.1  # > 10% net margin
    roe_good = roe > 0.15  # > 15% ROE

    if margin_good and roe_good:
      return "positive"
    elif margin_good or roe_good:
      return "neutral"
    else:
      return "negative"

  def _extract_metrics_for_prompt(self, symbol: str, signals: dict) -> dict[str, Any]:
    """Extract quantitative metrics for enriched LLM prompt."""
    metrics = {}
    try:
      # Technical metrics
      df = self.market_data_source.fetch_history(symbol, period="1y")
      if df is not None and not df.empty:
        latest = df.iloc[-1]
        metrics["rsi"] = latest.get("rsi_14")
        metrics["macd_histogram"] = latest.get("macd_histogram")
    except:
      pass

    try:
      # Valuation metrics
      if self.valuation_service and self.db:
        valuation = self.valuation_service.get_valuation(self.db, symbol)
        metrics["pe_ratio"] = valuation.pe_ratio
        metrics["price_to_book"] = valuation.price_to_book
    except:
      pass

    try:
      # News sentiment score
      if self.news_service:
        news_result = self.news_service.get_news_and_sentiment(symbol, limit=5)
        metrics["sentiment_score"] = news_result.get("overall_score")
    except:
      pass

    try:
      # Fundamental metrics
      if self.db:
        from datetime import datetime as dt
        current_year = dt.now().year
        snapshot = self.fundamental_service.get_snapshot(
          self.db, symbol, fiscal_year=current_year
        )
        if snapshot:
          if snapshot.total_revenue and snapshot.net_income:
            metrics["net_margin"] = round(
              (snapshot.net_income / snapshot.total_revenue) * 100, 2
            )
          if snapshot.shareholders_equity and snapshot.net_income:
            metrics["roe"] = round(
              (snapshot.net_income / snapshot.shareholders_equity) * 100, 2
            )
    except:
      pass

    return metrics
    
  def _build_prompt(self, symbol: str, signals: dict[str, Any], metrics: dict[str, Any] = None) -> str:
    """Build enriched prompt with both signal labels and quantitative metrics."""
    if metrics is None:
      metrics = {}

    # Format metrics into readable text
    metrics_text = ""
    if metrics.get("pe_ratio") is not None:
      metrics_text += f"P/E Ratio: {metrics['pe_ratio']}, "
    if metrics.get("net_margin") is not None:
      metrics_text += f"Net Margin: {metrics['net_margin']}%, "
    if metrics.get("roe") is not None:
      metrics_text += f"ROE: {metrics['roe']}%, "
    if metrics.get("rsi") is not None:
      metrics_text += f"RSI: {metrics['rsi']}, "
    if metrics.get("sentiment_score") is not None:
      metrics_text += f"Sentiment Score: {metrics['sentiment_score']}, "

    return f"""Analyze stock {symbol} and generate investment thesis.

Signals:
- Fundamental: {signals.get('fundamental', 'unknown')}
- Technical: {signals.get('technical', 'unknown')}
- Sentiment: {signals.get('sentiment', 'unknown')}
- Valuation: {signals.get('valuation', 'unknown')}

Key Metrics:
{metrics_text if metrics_text else 'No metrics available.'}

Provide a concise 1-2 sentence thesis paragraph and a clear verdict (Buy/Hold/Sell)."""
  
  def _rule_based_verdict(self, signals: dict[str, Any]) -> str:
    """Generate verdict based on signal scores. Fixed typo: 'posetive' -> 'positive'."""
    score_map = {
      "positive": 1,
      "bullish": 1,
      "cheap": 1,
      "neutral": 0,
      "fair": 0,
      "negative": -1,
      "bearish": -1,
      "expensive": -1,
      "unknown": 0
    }

    score = sum(score_map.get(v, 0) for v in signals.values())

    if score >= 2:
      return "Buy"
    elif score <= -2:
      return "Sell"
    return "Hold"
  
  def _map_verdict(self, raw: str) -> str | None:
    """Extract verdict from LLM response."""
    t = raw.lower()
    if "buy" in t:
      return "Buy"
    if "avoid" in t or "sell" in t:
      return "Sell"
    if "hold" in t:
      return "Hold"
    return None

  def _clean_summary(self, raw: str) -> str:
    """Extract thesis summary from LLM response."""
    return raw.strip()

  def _fallback_summary(self, symbol: str, signals: dict[str, str], verdict: str) -> str:
    """Generate summary when LLM is unavailable."""
    return f"{symbol.upper()} shows {signals.get('fundamental', 'unknown')} fundamentals, {signals.get('technical', 'unknown')} technicals, {signals.get('sentiment', 'unknown')} sentiment, and {signals.get('valuation', 'unknown')} valuation; overall stance is {verdict}."
    
