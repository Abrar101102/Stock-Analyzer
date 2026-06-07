"""
STEP 3 — Generate the output thesis paragraph for each stock.

TWO MODES:
  a) rule_based  — instant, free, no API needed. Good enough to start.
  b) claude_api  — calls Claude claude-sonnet-4-20250514 to write a polished paragraph.
                   Uses the Anthropic API (you already have access via claude.ai).
                   Set ANTHROPIC_API_KEY in your environment first.

Run:
    python step3_write_outputs.py --mode rule_based
    python step3_write_outputs.py --mode claude_api

Input:  signals_labelled.json   (with verdicts already reviewed by you)
Output: signals_with_outputs.json
"""

import json
import sys
import time
import argparse
import os


# ── rule-based output writer ──────────────────────────────────────────────────

def fmt(val, decimals=2, suffix="") -> str:
    if val is None: return "N/A"
    try:   return f"{round(float(val), decimals)}{suffix}"
    except: return str(val)


def rule_based_thesis(s: dict) -> str:
    """
    Deterministic paragraph builder. Reads like a junior analyst note.
    Each sentence only fires when the data supports it.
    """
    name    = s.get("name", s.get("symbol"))
    verdict = s.get("verdict", "Hold")
    parts   = []

    # Opening — overall stance
    if verdict == "Buy":
        parts.append(
            f"{name} presents a compelling case for long-term investors, "
            f"supported by a composite score of {fmt(s.get('overall_score'))}/10."
        )
    elif verdict == "Hold":
        parts.append(
            f"{name} shows a mixed picture with a composite score of "
            f"{fmt(s.get('overall_score'))}/10 — neither a clear entry nor an exit."
        )
    else:
        parts.append(
            f"{name} raises concerns across multiple dimensions with a composite "
            f"score of {fmt(s.get('overall_score'))}/10, warranting caution."
        )

    # Valuation sentence
    pe  = s.get("pe_ratio")
    vl  = s.get("valuation_label", "")
    if pe:
        parts.append(
            f"At a PE of {fmt(pe)}, the stock is currently {vl.lower()}."
        )

    # Profitability sentence
    roe  = s.get("roe")
    roce = s.get("roce")
    rl   = s.get("roe_label", "")
    rcl  = s.get("roce_label", "")
    if roe and roce:
        parts.append(
            f"The company delivers {rl.lower()} profitability with ROE of {fmt(roe)}% "
            f"and ROCE of {fmt(roce)}%, indicating {rcl.lower()} capital efficiency."
        )

    # Growth sentence
    rev_g = s.get("revenue_growth_yoy")
    if rev_g is not None:
        if rev_g > 10:
            parts.append(
                f"Revenue growth of {fmt(rev_g)}% YoY signals healthy business momentum."
            )
        elif rev_g > 0:
            parts.append(
                f"Revenue growth is modest at {fmt(rev_g)}% YoY, suggesting a stable "
                f"but slow-expanding business."
            )
        else:
            parts.append(
                f"Revenue declined {fmt(abs(rev_g))}% YoY — a trend worth monitoring closely."
            )

    # Technical sentence
    rsi       = s.get("rsi")
    rsi_zone  = s.get("rsi_zone", "")
    sig_macd  = s.get("sig_macd", "")
    sma_label = s.get("sma_cross_label", "")
    if rsi:
        tech_parts = [f"RSI at {fmt(rsi)} ({rsi_zone.lower()})"]
        if sig_macd:
            tech_parts.append(f"MACD {sig_macd}")
        if sma_label:
            tech_parts.append(sma_label)
        parts.append(
            f"Technically, the stock shows {', '.join(tech_parts)}."
        )

    # Momentum
    mom   = s.get("momentum_30d_pct")
    moml  = s.get("momentum_label", "")
    if mom is not None:
        parts.append(
            f"Price momentum over the past month is {moml.lower()} "
            f"({fmt(mom)}% change)."
        )

    # Sentiment
    total_articles = s.get("total_articles", 0)
    sent_label     = s.get("sentiment_label", "neutral")
    pos_pct        = s.get("news_positive_pct", 0) or 0
    neg_pct        = s.get("news_negative_pct", 0) or 0
    if total_articles > 0:
        parts.append(
            f"News sentiment is {sent_label} "
            f"({int(pos_pct)}% positive, {int(neg_pct)}% negative "
            f"across {total_articles} articles)."
        )
    else:
        parts.append("No recent news articles were available for sentiment analysis.")

    # Closing call to action
    if verdict == "Buy":
        parts.append(
            "Overall, this stock appears suitable for investors with a long-term horizon "
            "and a moderate risk appetite."
        )
    elif verdict == "Hold":
        parts.append(
            "Existing holders may consider staying invested while watching for "
            "improvement in weak areas before adding more."
        )
    else:
        parts.append(
            "Investors are advised to wait for fundamental improvement or a significant "
            "price correction before considering entry."
        )

    return " ".join(parts)


# ── claude api output writer ──────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert financial analyst specialising in Indian equity markets.
Given structured financial data about a stock, write a concise, factual investment thesis
in 4-6 sentences.

Rules:
- Be specific — use the actual numbers given
- Be balanced — acknowledge both strengths and risks
- Use plain English — no jargon, no bullet points
- End with a clear stance: suitable for long-term investors / hold and watch / avoid for now
- Do NOT invent data that is not provided
- Do NOT use words like "robust", "stellar", or "impressive" — be neutral and precise"""


def claude_api_thesis(input_prompt: str, api_key: str) -> str:
    """Call Claude claude-sonnet-4-20250514 to write the thesis paragraph."""
    import urllib.request
    import urllib.error

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 400,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": input_prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
            "content-type":      "application/json",
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        return data["content"][0]["text"].strip()


# ── run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["rule_based", "claude_api"],
                        default="rule_based")
    args = parser.parse_args()

    api_key = None
    if args.mode == "claude_api":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("ERROR: set ANTHROPIC_API_KEY environment variable first.")
            sys.exit(1)

    with open("signals_labelled.json") as f:
        stocks = json.load(f)

    results = []
    for i, s in enumerate(stocks):
        sym = s.get("symbol", f"stock_{i}")
        try:
            if args.mode == "claude_api":
                output = claude_api_thesis(s["input_prompt"], api_key)
                time.sleep(1.0)   # gentle rate limiting
            else:
                output = rule_based_thesis(s)

            s["output_text"] = output
            results.append(s)
            print(f"  ✓ {sym}")
            # Print a preview so you can eyeball quality
            print(f"    {output[:120]}...")

        except Exception as e:
            print(f"  ✗ {sym}: {e}")
            s["output_text"] = rule_based_thesis(s)   # fallback
            results.append(s)

    with open("signals_with_outputs.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone → signals_with_outputs.json ({len(results)} stocks)")
    print("Next: run step4_build_jsonl.py to create the training file")