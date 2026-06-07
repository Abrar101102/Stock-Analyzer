"""
STEP 1 — Extract and flatten each stock JSON into a clean signal dict.

Drop this script in the same folder as your 50 JSON files and run:
    python step1_extract.py

Output: signals_raw.json  (one dict per stock, all signals flattened)
"""

import json
import os
import glob

# ── helpers ──────────────────────────────────────────────────────────────────

def safe(val, default=None):
    """Return val if it's a real number, else default."""
    if val is None:
        return default
    try:
        f = float(val)
        return None if (f != f) else f   # NaN check
    except (TypeError, ValueError):
        return default


def latest_indicator(data_list: list) -> dict:
    """Return the most recent row from the technical indicator time-series."""
    if not data_list:
        return {}
    return data_list[-1]


def price_change_pct(data_list: list, days: int = 30) -> float | None:
    """% price change over last `days` rows."""
    if not data_list or len(data_list) < days:
        return None
    old_close = safe(data_list[-days].get("close"))
    new_close = safe(data_list[-1].get("close"))
    if old_close and new_close and old_close != 0:
        return round((new_close - old_close) / old_close * 100, 2)
    return None


# ── main extractor ────────────────────────────────────────────────────────────

def extract_signals(filepath: str) -> dict | None:
    with open(filepath, encoding="utf-8", errors="replace") as f:
        data = json.load(f)

    symbol = data.get("symbol", os.path.basename(filepath).replace(".json", ""))
    eps    = data.get("endpoints", {})

    # ── screener ──────────────────────────────────────────────────────────────
    screener_ok   = eps.get("screener", {}).get("ok", False)
    screener_body = eps.get("screener", {}).get("body", {})
    screener_data = screener_body.get("data", {})
    items         = screener_data.get("items", [])
    item          = items[0] if items else {}
    metrics       = item.get("metrics", {})

    name              = item.get("name", symbol)
    sector            = item.get("sector", "Unknown")
    industry          = item.get("industry", "Unknown")
    market_cap        = safe(item.get("market_cap"))
    current_price     = safe(item.get("price"))
    pe_ratio          = safe(metrics.get("pe_ratio"))
    dividend_yield    = safe(metrics.get("dividend_yield"))
    roce              = safe(metrics.get("roce"))
    roe               = safe(metrics.get("roe"))
    revenue_growth_yoy = safe(metrics.get("revenue_growth_yoy"))
    high_low_52w      = safe(metrics.get("high_low"))

    # ── technical indicators ──────────────────────────────────────────────────
    tech_body      = eps.get("technical_indicators", {}).get("body", {})
    tech_data      = tech_body.get("data", [])
    tech_signals   = tech_body.get("signals", {})
    latest         = latest_indicator(tech_data)

    rsi            = safe(latest.get("rsi_14"))
    macd_line      = safe(latest.get("macd_line"))
    macd_signal    = safe(latest.get("macd_signal"))
    macd_hist      = safe(latest.get("macd_histogram"))
    sma_20         = safe(latest.get("sma_20"))
    sma_50         = safe(latest.get("sma_50"))
    sma_200        = safe(latest.get("sma_200"))
    bb_upper       = safe(latest.get("bb_upper"))
    bb_lower       = safe(latest.get("bb_lower"))
    bb_middle      = safe(latest.get("bb_middle"))
    support        = safe(latest.get("support_level"))
    resistance     = safe(latest.get("resistance_level"))
    vwap           = safe(latest.get("vwap"))

    sig_rsi        = tech_signals.get("rsi", "unknown")
    sig_macd       = tech_signals.get("macd", "unknown")
    sig_bollinger  = tech_signals.get("bollinger", "unknown")
    sig_sma        = tech_signals.get("sma_cross", "unknown")

    # ── price momentum ────────────────────────────────────────────────────────
    price_history  = eps.get("price_history", {}).get("body", {}).get("data", [])
    momentum_30d   = price_change_pct(price_history, 30)
    momentum_5d    = price_change_pct(price_history, 5)

    # price vs key MAs
    price_vs_sma20  = None
    price_vs_sma50  = None
    price_vs_vwap   = None
    if current_price and sma_20:
        price_vs_sma20 = round((current_price - sma_20) / sma_20 * 100, 2)
    if current_price and sma_50:
        price_vs_sma50 = round((current_price - sma_50) / sma_50 * 100, 2)
    if current_price and vwap:
        price_vs_vwap = round((current_price - vwap) / vwap * 100, 2)

    # ── news / sentiment ──────────────────────────────────────────────────────
    news_body         = eps.get("news", {}).get("body", {})
    sentiment_label   = news_body.get("overall_sentiment", "unknown")
    sentiment_score   = safe(news_body.get("overall_score"), 0.0)
    gauge             = news_body.get("gauge", {})
    news_positive_pct = safe(gauge.get("positive"), 0)
    news_neutral_pct  = safe(gauge.get("neutral"), 100)
    news_negative_pct = safe(gauge.get("negative"), 0)
    total_articles    = safe(news_body.get("total_results"), 0)

    # ── derived signals (rule-based, no extra endpoint needed) ───────────────
    # Valuation label
    if pe_ratio is None:
        valuation_label = "Unknown"
    elif pe_ratio < 15:
        valuation_label = "Undervalued"
    elif pe_ratio < 25:
        valuation_label = "Fairly Valued"
    elif pe_ratio < 40:
        valuation_label = "Moderately Expensive"
    else:
        valuation_label = "Expensive"

    # RSI zone
    if rsi is None:
        rsi_zone = "Unknown"
    elif rsi < 30:
        rsi_zone = "Oversold"
    elif rsi > 70:
        rsi_zone = "Overbought"
    else:
        rsi_zone = "Neutral"

    # ROCE quality
    if roce is None:
        roce_label = "Unknown"
    elif roce > 20:
        roce_label = "High"
    elif roce > 12:
        roce_label = "Moderate"
    else:
        roce_label = "Low"

    # ROE quality
    if roe is None:
        roe_label = "Unknown"
    elif roe > 20:
        roe_label = "Strong"
    elif roe > 12:
        roe_label = "Moderate"
    else:
        roe_label = "Weak"

    # SMA cross interpretation
    sma_cross_label = {
        "golden_cross": "Bullish (golden cross)",
        "death_cross":  "Bearish (death cross)",
    }.get(sig_sma, sig_sma.replace("_", " ").title() if sig_sma else "Unknown")

    # Momentum label
    if momentum_30d is None:
        momentum_label = "Unknown"
    elif momentum_30d > 10:
        momentum_label = "Strong Uptrend"
    elif momentum_30d > 2:
        momentum_label = "Mild Uptrend"
    elif momentum_30d > -2:
        momentum_label = "Sideways"
    elif momentum_30d > -10:
        momentum_label = "Mild Downtrend"
    else:
        momentum_label = "Strong Downtrend"

    # ── assemble ──────────────────────────────────────────────────────────────
    return {
        # identity
        "symbol":            symbol,
        "name":              name,
        "sector":            sector,
        "industry":          industry,

        # price
        "current_price":     current_price,
        "market_cap_cr":     market_cap,
        "high_52w":          high_low_52w,
        "momentum_30d_pct":  momentum_30d,
        "momentum_5d_pct":   momentum_5d,
        "momentum_label":    momentum_label,
        "price_vs_sma20_pct": price_vs_sma20,
        "price_vs_sma50_pct": price_vs_sma50,
        "price_vs_vwap_pct":  price_vs_vwap,

        # fundamentals
        "pe_ratio":          pe_ratio,
        "valuation_label":   valuation_label,
        "dividend_yield":    dividend_yield,
        "roce":              roce,
        "roce_label":        roce_label,
        "roe":               roe,
        "roe_label":         roe_label,
        "revenue_growth_yoy": revenue_growth_yoy,

        # technicals (values)
        "rsi":               rsi,
        "rsi_zone":          rsi_zone,
        "macd_line":         round(macd_line, 4) if macd_line else None,
        "macd_signal":       round(macd_signal, 4) if macd_signal else None,
        "macd_hist":         round(macd_hist, 4) if macd_hist else None,
        "sma_20":            round(sma_20, 2) if sma_20 else None,
        "sma_50":            round(sma_50, 2) if sma_50 else None,
        "sma_200":           round(sma_200, 2) if sma_200 else None,
        "support":           support,
        "resistance":        resistance,
        "bb_upper":          round(bb_upper, 2) if bb_upper else None,
        "bb_lower":          round(bb_lower, 2) if bb_lower else None,

        # technical signals (labels)
        "sig_rsi":           sig_rsi,
        "sig_macd":          sig_macd,
        "sig_bollinger":     sig_bollinger,
        "sig_sma_cross":     sig_sma,
        "sma_cross_label":   sma_cross_label,

        # news
        "sentiment_label":   sentiment_label,
        "sentiment_score":   sentiment_score,
        "news_positive_pct": news_positive_pct,
        "news_neutral_pct":  news_neutral_pct,
        "news_negative_pct": news_negative_pct,
        "total_articles":    int(total_articles) if total_articles else 0,
    }


# ── run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    JSON_FOLDER = "."          # ← change to your folder path if needed
    out_path    = "signals_raw.json"

    # Intermediate pipeline files to skip
    SKIP_NAMES = {
        "signals_raw.json", "signals_labelled.json",
        "signals_with_outputs.json", "thesis_train.jsonl", "thesis_val.jsonl"
    }
    json_files = glob.glob(os.path.join(JSON_FOLDER, "*.json"))
    json_files = [
        f for f in json_files
        if os.path.basename(f) not in SKIP_NAMES
        # Only include files that look like stock JSONs
        # (must contain "symbol" key at top level)
    ]

    results = []
    failed  = []

    for fp in sorted(json_files):
        sym = os.path.basename(fp).replace(".json", "")
        try:
            sig = extract_signals(fp)
            if sig:
                results.append(sig)
                print(f"  ✓ {sym}")
        except Exception as e:
            failed.append(sym)
            print(f"  ✗ {sym}: {e}")

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone. {len(results)} stocks extracted → {out_path}")
    if failed:
        print(f"Failed: {failed}")