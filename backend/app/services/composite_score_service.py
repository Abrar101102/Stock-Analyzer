from __future__ import annotations

from typing import Dict
from app.core.config import settings


class CompositeScoreService:
  def __init__(self, weights: Dict[str, float] | None = None) -> None:
    default_weights = {
      "fundamental": getattr(settings, "COMPOSITE_WEIGHT_FUNDAMENTAL", 0.25),
      "technical": getattr(settings, "COMPOSITE_WEIGHT_TECHNICAL", 0.25),
      "sentiment": getattr(settings, "COMPOSITE_WEIGHT_SENTIMENT", 0.25),
      "valuation": getattr(settings, "COMPOSITE_WEIGHT_VALUATION", 0.25),
    }
    self.weights = weights or default_weights

  def compute(self, signals: Dict[str, str] | None) -> float:
    if signals is None:
      signals = {}

    label_scores = {
      "positive": 1,
      "bullish": 1,
      "cheap": 1,
      "neutral": 0,
      "fair": 0,
      "negative": -1,
      "bearish": -1,
      "expensive": -1,
      "unknown": 0,
    }

    subscores = {}
    for dimension in ["fundamental", "technical", "sentiment", "valuation"]:
      label = signals.get(dimension, "neutral")
      raw = label_scores.get(label, 0)
      subscores[dimension] = (raw + 1) * 50

    total_weight = sum(self.weights.values()) or 1.0
    normalized = {k: v / total_weight for k, v in self.weights.items()}

    composite = sum(subscores[k] * normalized.get(k, 0) for k in subscores.keys())
    if composite < 0:
      composite = 0.0
    if composite > 100:
      composite = 100.0
    return round(composite, 2)
