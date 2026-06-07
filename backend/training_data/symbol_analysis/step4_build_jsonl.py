"""
STEP 4 — Augment to 200+ examples and build the final JSONL training file.

50 stocks × 4 augmentations = 200 examples.
Augmentation = slight random variation in numbers to teach the model
to reason about ranges, not memorise exact figures.

Run:
    python step4_build_jsonl.py

Input:  signals_with_outputs.json
Output: thesis_training.jsonl   ← this is your final training file for Colab
"""

import json
import random

random.seed(42)   # reproducible


def jitter(val, pct=0.08):
    """Nudge a number by ±pct (default 8%). Returns None if val is None."""
    if val is None:
        return None
    return round(val * (1 + random.uniform(-pct, pct)), 2)


def vary_signals(sig: str, choices: list, flip_prob=0.15) -> str:
    """Occasionally flip a signal label to an adjacent one."""
    if random.random() < flip_prob and len(choices) > 1:
        others = [c for c in choices if c != sig]
        return random.choice(others)
    return sig


RSI_SIGNALS   = ["neutral", "oversold", "overbought"]
MACD_SIGNALS  = ["bullish", "bearish", "neutral"]
BB_SIGNALS    = ["neutral", "oversold", "overbought"]
SMA_SIGNALS   = ["golden_cross", "death_cross", "unknown"]
SENT_LABELS   = ["positive", "neutral", "negative"]


def augment_stock(s: dict, augment_id: int) -> dict:
    """Create one augmented variant of a stock's signal dict."""
    aug = dict(s)   # shallow copy is fine — all values are scalars

    if augment_id == 0:
        # Original — no changes
        return aug

    # Jitter numeric fields
    for field in [
        "pe_ratio", "roe", "roce", "dividend_yield",
        "revenue_growth_yoy", "rsi", "macd_line", "macd_signal",
        "momentum_30d_pct", "momentum_5d_pct",
        "price_vs_sma20_pct", "price_vs_sma50_pct",
    ]:
        aug[field] = jitter(aug.get(field))

    # Occasionally vary signal labels (makes model robust to edge cases)
    aug["sig_rsi"]       = vary_signals(aug.get("sig_rsi", "neutral"), RSI_SIGNALS)
    aug["sig_macd"]      = vary_signals(aug.get("sig_macd", "neutral"), MACD_SIGNALS)
    aug["sig_bollinger"] = vary_signals(aug.get("sig_bollinger", "neutral"), BB_SIGNALS)

    # Re-derive zone labels from jittered values
    rsi = aug.get("rsi")
    if rsi is not None:
        if rsi < 30:   aug["rsi_zone"] = "Oversold"
        elif rsi > 70: aug["rsi_zone"] = "Overbought"
        else:          aug["rsi_zone"] = "Neutral"

    pe = aug.get("pe_ratio")
    if pe is not None:
        if pe < 15:   aug["valuation_label"] = "Undervalued"
        elif pe < 25: aug["valuation_label"] = "Fairly Valued"
        elif pe < 40: aug["valuation_label"] = "Moderately Expensive"
        else:         aug["valuation_label"] = "Expensive"

    return aug


def rebuild_prompt(s: dict, scores: dict) -> str:
    """Rebuild the input prompt from (potentially augmented) signal values."""
    def fmt(val, d=2, sfx=""):
        if val is None: return "N/A"
        try:   return f"{round(float(val), d)}{sfx}"
        except: return str(val)

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
AUTO VERDICT: {s.get('verdict', 'Hold')}"""


def score_fields(s: dict) -> dict:
    """Re-extract score fields from the dict (they're stored from step 2)."""
    return {
        "score_valuation":     s.get("score_valuation", 5),
        "score_profitability": s.get("score_profitability", 5),
        "score_growth":        s.get("score_growth", 5),
        "score_technical":     s.get("score_technical", 5),
        "score_momentum":      s.get("score_momentum", 5),
        "score_sentiment":     s.get("score_sentiment", 5),
        "overall_score":       s.get("overall_score", 5),
    }


# ── run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with open("signals_with_outputs.json") as f:
        stocks = json.load(f)

    # Filter out any stocks where output_text is still None
    stocks = [s for s in stocks if s.get("output_text")]
    print(f"Building dataset from {len(stocks)} labelled stocks...")

    examples = []
    for s in stocks:
        for aug_id in range(4):   # original + 3 augmentations
            aug     = augment_stock(s, aug_id)
            scores  = score_fields(aug)
            prompt  = rebuild_prompt(aug, scores) if aug_id > 0 else s["input_prompt"]
            output  = s["output_text"]   # same output for all augmentations

            # This is the exact format SFTTrainer expects
            example = {
                "messages": [
                    {
                        "role":    "system",
                        "content": (
                            "You are a financial analyst specialising in Indian equity markets. "
                            "Given structured financial data, write a concise investment thesis."
                        )
                    },
                    {
                        "role":    "user",
                        "content": prompt
                    },
                    {
                        "role":    "assistant",
                        "content": output
                    }
                ]
            }
            examples.append(example)

    # Shuffle so the model doesn't overfit to stock order
    random.shuffle(examples)

    # 90% train / 10% validation split
    split     = int(len(examples) * 0.9)
    train_set = examples[:split]
    val_set   = examples[split:]

    with open("thesis_train.jsonl", "w") as f:
        for ex in train_set:
            f.write(json.dumps(ex) + "\n")

    with open("thesis_val.jsonl", "w") as f:
        for ex in val_set:
            f.write(json.dumps(ex) + "\n")

    print(f"\nDone!")
    print(f"  Training examples:   {len(train_set)}  → thesis_train.jsonl")
    print(f"  Validation examples: {len(val_set)}   → thesis_val.jsonl")
    print(f"\nUpload both files to Google Colab and run the fine-tuning notebook.")