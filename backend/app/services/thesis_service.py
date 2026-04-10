from datetime import datetime,timezone
from typing import Any
from app.models.response.thesis_model import ThesisResponseModel

class ThesisService:
  def __init__(self,llm_provider=None):
    self.llm_provider = llm_provider

  def generate(self,symbol:str)-> dict[str,Any]:
    #TODO replace with real upstream service calls
    signals = {
      "fundamental":"posetive",
      "technical":"neutral",
      "sentiment":"negative",
      "valuation":"expensive"
    }
    verdict = self._rule_based_verdict(signals)
    summary = self._fallback_summary(symbol,signals,verdict)

    if self.llm_provider:
      try:
        prompt = self._build_prompt(symbol,signals)
        raw = self.llm_provider.generate(prompt)
        mapped = self._map_verdict(raw)
        if mapped :
          verdict = mapped
        summary = self._clean_summary(raw) or summary
      
      except Exception as e:
        return e
      
      return ThesisResponseModel(
        symbol = symbol,
        verdict = verdict,
        summary = summary,
        signals = signals,
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00","Z") 

      )
    
  def _build_prompt(self,symbol:str,signals:dict[str,Any])->str:
      
      return f"Symbol : {symbol}. Signals:{signals}. Return 1 Short thesis paragraph and a verdict."
  
  def _rule_based_verdict(self,symbol:str,signals:dict[str,Any])->str:
    score_map = {
      "posetive":1,
      "neutral":0,
      "negative":-1,
      "cheap":1,
      "fair":0,
      "expensive":-1,
      "unknown":0
    }

    score = sum(score_map.get(v,0)for v in signals.vales())

    if score >= 2:
      return "Buy"
    elif score <= -2:
      return "Avoid"
    return "Hold"
  
  def _map_verdict(self,raw:str)->str|None:
    t = raw.lower()
    if "buy" in t:
      return "Buy"
    if "avoid" in t or "sell" in t:
      return "Avoid"
    if "hold" in t:
      return "Hold"
    return None
  
  def _clean_summary(self,raw:str)->str:
    return raw.strip()
  
  def _fallback_summary(self,symbol:str,signals:dict[str,str],verdict:str)->str:
    return f"{symbol.upper()} shows {signals['fundamentals']} fundamentals, {signals['technical']} technicals, {signals['sentiment']} sentiment, and {signals['valuation']} valuation; overall stance is {verdict}."
    
