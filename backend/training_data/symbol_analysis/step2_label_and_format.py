"""
STEP 2 — Auto-label each stock with Buy / Hold / Avoid
and format it into the exact input string the model will see.

Run after step1:
    python step2_label_and_format.py

Input:  signals_raw.json
Output: signals_labelled.json   (signals + verdict + formatted input string)

After this step you review the verdicts manually and correct any that
look wrong — that's your only manual task in the whole pipeline.
"""

import json


# ── scoring ───────────────────────────────────────────────────────────────────
# Each dimension returns a score 0–10. We then weight and sum.
# All thresholds are tuned for Indian large-cap/mid-cap stocks.

def score_valuation(s: dict) -> float:
    pe = s.get("pe_ratio")
    if pe is None:
        return 5.0   # neutral if unknown
    if pe < 15:   return 9.0
    if pe < 20:   return 8.0
    if pe < 28:   return 6.5
    if pe < 40:   return 4.5
    if pe < 60:   return 3.0
    return 1.5


def score_profitability(s: dict) -> float:
    roe  = s.get("roe")  or 0
    roce = s.get("roce") or 0
    avg  = (roe + roce) / 2
    if avg > 25:  return 9.5
    if avg > 18:  return 8.0
    if avg > 12:  return 6.5
    if avg > 7:   return 4.5
    return 2.5


def score_growth(s: dict) -> float:
    g = s.get("revenue_growth_yoy")
    if g is None:
        return 5.0
    if g > 20:   return 9.5
    if g > 12:   return 8.0
    if g > 6:    return 6.5
    if g > 0:    return 5.0
    if g > -5:   return 3.5
    return 2.0


def score_technical(s: dict) -> float:
    scores = []
    # RSI
    rsi_map = {"oversold": 8.5, "neutral": 6.0, "overbought": 3.5, "unknown": 5.0}
    scores.append(rsi_map.get(s.get("sig_rsi", "unknown"), 5.0))
    # MACD
    macd_map = {"bullish": 8.0, "bearish": 3.0, "neutral": 5.5, "unknown": 5.0}
    scores.append(macd_map.get(s.get("sig_macd", "unknown"), 5.0))
    # Bollinger
    bb_map = {"oversold": 8.0, "overbought": 3.0, "neutral": 6.0, "unknown": 5.0}
    scores.append(bb_map.get(s.get("sig_bollinger", "unknown"), 5.0))
    # SMA cross
    sma_map = {"golden_cross": 8.5, "death_cross": 2.5, "unknown": 5.0}
    scores.append(sma_map.get(s.get("sig_sma_cross", "unknown"), 5.0))
    return round(sum(scores) / len(scores), 2)


def score_momentum(s: dict) -> float:
    mom = s.get("momentum_30d_pct")
    if mom is None:
        return 5.0
    if mom > 15:   return 8.5
    if mom > 8:    return 7.5
    if mom > 2:    return 6.0
    if mom > -2:   return 5.0
    if mom > -8:   return 3.5
    return 2.0


def score_sentiment(s: dict) -> float:
    if s.get("total_articles", 0) == 0:
        return 5.0   # no data — neutral
    label = s.get("sentiment_label", "neutral")
    pos   = s.get("news_positive_pct", 0) or 0
    neg   = s.get("news_negative_pct", 0) or 0
    if label == "positive" or pos > 60:   return 8.0
    if label == "negative" or neg > 60:   return 3.0
    return 5.5


def composite_score(s: dict) -> dict:
    val   = score_valuation(s)
    prof  = score_profitability(s)
    grow  = score_growth(s)
    tech  = score_technical(s)
    mom   = score_momentum(s)
    sent  = score_sentiment(s)

    # Weights — fundamentals matter most for thesis
    weighted = (
        val   * 0.25 +
        prof  * 0.20 +
        grow  * 0.20 +
        tech  * 0.15 +
        mom   * 0.10 +
        sent  * 0.10
    )

    return {
        "score_valuation":      round(val, 2),
        "score_profitability":  round(prof, 2),
        "score_growth":         round(grow, 2),
        "score_technical":      round(tech, 2),
        "score_momentum":       round(mom, 2),
        "score_sentiment":      round(sent, 2),
        "overall_score":        round(weighted, 2),
    }


def verdict(overall: float) -> str:
    if overall >= 7.0:  return "Buy"
    if overall >= 5.0:  return "Hold"
    return "Avoid"


# ── prompt formatter ──────────────────────────────────────────────────────────

def fmt(val, decimals=2, suffix="") -> str:
    """Format a number cleanly, or return 'N/A'."""
    if val is None:
        return "N/A"
    try:
        return f"{round(float(val), decimals)}{suffix}"
    except Exception:
        return str(val)


def build_input_prompt(s: dict, scores: dict) -> str:
    """
    Build the exact input string that will be fed to the model at inference.
    Keep it dense but human-readable — the model learns the pattern from this.
    """
    return f"""Analyse the following stock and write an investment thesis.

Symbol: {s['symbol']}
Company: {s['name']}
Sector: {s['sector']} | Industry: {s['industry']}
Market Cap: ₹{fmt(s.get('market_cap_cr'), 0)} Cr | Current Price: ₹{fmt(s.get('current_price'), 1)}

VALUATION (score {scores['score_valuation']}/10)
  PE Ratio: {fmt(s.get('pe_ratio'))} → {s.get('valuation_label', 'N/A')}
  Dividend Yield: {fmt(s.get('dividend_yield'))}%
  52W High: ₹{fmt(s.get('high_52w'), 1)}

PROFITABILITY (score {scores['score_profitability']}/10)
  ROE: {fmt(s.get('roe'))}% → {s.get('roe_label', 'N/A')}
  ROCE: {fmt(s.get('roce'))}% → {s.get('roce_label', 'N/A')}
  Revenue Growth YoY: {fmt(s.get('revenue_growth_yoy'))}%

TECHNICAL SIGNALS (score {scores['score_technical']}/10)
  RSI (14): {fmt(s.get('rsi'))} → {s.get('rsi_zone', 'N/A')}
  MACD Signal: {s.get('sig_macd', 'N/A').title()}
  Bollinger: {s.get('sig_bollinger', 'N/A').title()}
  SMA Cross: {s.get('sma_cross_label', 'N/A')}
  Price vs SMA20: {fmt(s.get('price_vs_sma20_pct'))}%
  Price vs SMA50: {fmt(s.get('price_vs_sma50_pct'))}%
  Support: ₹{fmt(s.get('support'), 1)} | Resistance: ₹{fmt(s.get('resistance'), 1)}

MOMENTUM (score {scores['score_momentum']}/10)
  30-Day Price Change: {fmt(s.get('momentum_30d_pct'))}% → {s.get('momentum_label', 'N/A')}
  5-Day Price Change: {fmt(s.get('momentum_5d_pct'))}%

NEWS & SENTIMENT (score {scores['score_sentiment']}/10)
  Overall Sentiment: {s.get('sentiment_label', 'N/A').title()}
  Positive: {fmt(s.get('news_positive_pct'), 0)}% | Neutral: {fmt(s.get('news_neutral_pct'), 0)}% | Negative: {fmt(s.get('news_negative_pct'), 0)}%
  Articles Analysed: {s.get('total_articles', 0)}

COMPOSITE SCORE: {scores['overall_score']}/10
AUTO VERDICT: {verdict(scores['overall_score'])}"""


# ── run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with open("signals_raw.json") as f:
        stocks = json.load(f)

    labelled = []
    for s in stocks:
        scores  = composite_score(s)
        v       = verdict(scores["overall_score"])
        prompt  = build_input_prompt(s, scores)

        labelled.append({
            **s,
            **scores,
            "verdict":      v,
            "input_prompt": prompt,
            "output_text":  None,    # ← you fill this in step 3
        })
        print(f"  {s['symbol']:15s}  overall={scores['overall_score']}  → {v}")

    with open("signals_labelled.json", "w") as f:
        json.dump(labelled, f, indent=2)

    buy   = sum(1 for x in labelled if x["verdict"] == "Buy")
    hold  = sum(1 for x in labelled if x["verdict"] == "Hold")
    avoid = sum(1 for x in labelled if x["verdict"] == "Avoid")
    print(f"\nDone → signals_labelled.json")
    print(f"  Buy: {buy}  Hold: {hold}  Avoid: {avoid}")
    print(f"\nNext: open signals_labelled.json, review the verdicts,")
    print(f"correct any that look wrong, then run step3_write_outputs.py")