"""Collect analysis API responses per symbol into single JSON files.

This script calls the same backend endpoints used by the dashboard symbol analysis
flow and stores all responses for each symbol in one file.

Example:
  python collect_symbol_analysis_data.py --symbols TCS INFY RELIANCE

Output:
  training_data/symbol_analysis/TCS.json
  training_data/symbol_analysis/INFY.json
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class EndpointSpec:
    name: str
    path_template: str
    query: dict[str, str | int]


# These are the APIs currently used in the frontend dashboard symbol analysis flow.
CORE_ENDPOINTS: tuple[EndpointSpec, ...] = (
    EndpointSpec(
        name="price_history",
        path_template="/stock/{symbol}/price-history/",
        query={"period": "6mo"},
    ),
    EndpointSpec(
        name="technical_indicators",
        path_template="/technical/{symbol}/indicators",
        query={"period": "6mo"},
    ),
    EndpointSpec(
        name="screener",
        path_template="/screener",
        query={"symbol": "{symbol}"},
    ),
    EndpointSpec(
        name="signals",
        path_template="/technical/{symbol}/signals",
        query={"period": "6mo"},
    ),
    EndpointSpec(
        name="news",
        path_template="/news/{symbol}",
        query={"limit": 8},
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Call symbol-analysis APIs and store one consolidated JSON file per symbol."
        )
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Space-separated list of symbols, e.g. TCS INFY RELIANCE",
    )
    parser.add_argument(
        "--symbols-from-seed",
        action="store_true",
        help="Load symbols from app/data/nifty50_seed.py (NIFTY50_STOCKS).",
    )
    parser.add_argument(
        "--seed-file",
        default="app/data/nifty50_seed.py",
        help="Path to seed file that contains NIFTY50_STOCKS.",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000/api",
        help="Backend API base URL. Default: http://127.0.0.1:8000/api",
    )
    parser.add_argument(
        "--output-dir",
        default="training_data/symbol_analysis",
        help="Directory where symbol JSON files are written.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="HTTP timeout in seconds for each endpoint call.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help=(
            "Continue to next endpoint/symbol when a call fails. "
            "Without this flag, first failure stops execution."
        ),
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Write pretty-formatted JSON output instead of compact JSON.",
    )
    return parser.parse_args()


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_symbol(raw: str) -> str:
    symbol = raw.strip().upper()
    if not symbol:
        raise ValueError("Empty symbol provided")
    if not re.fullmatch(r"[A-Z0-9.\-]{1,15}", symbol):
        raise ValueError(f"Invalid symbol format: {raw!r}")
    return symbol


def load_symbols_from_seed_file(seed_file: Path) -> list[str]:
    if not seed_file.exists():
        raise ValueError(f"Seed file not found: {seed_file}")

    source = seed_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(seed_file))

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue

        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "NIFTY50_STOCKS" not in targets:
            continue

        data = ast.literal_eval(node.value)
        if not isinstance(data, list):
            raise ValueError("NIFTY50_STOCKS must be a list")

        symbols: list[str] = []
        for item in data:
            if isinstance(item, dict) and "symbol" in item:
                symbols.append(normalize_symbol(str(item["symbol"])))

        if not symbols:
            raise ValueError("No symbols found in NIFTY50_STOCKS")

        # Preserve list order while dropping accidental duplicates.
        return list(dict.fromkeys(symbols))

    raise ValueError("NIFTY50_STOCKS assignment not found in seed file")


def build_url(base_url: str, spec: EndpointSpec, symbol: str) -> str:
    path = spec.path_template.format(symbol=symbol)
    query: dict[str, str | int] = {}
    for key, value in spec.query.items():
        query[key] = value.format(symbol=symbol) if isinstance(value, str) else value

    root = base_url.rstrip("/")
    if query:
        return f"{root}{path}?{urlencode(query)}"
    return f"{root}{path}"


def fetch_json(url: str, timeout_seconds: float) -> dict[str, Any]:
    request = Request(url=url, headers={"Accept": "application/json"}, method="GET")

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body_text = response.read().decode("utf-8", errors="replace")
            try:
                body_json = json.loads(body_text)
            except json.JSONDecodeError:
                body_json = {"raw_text": body_text}

            return {
                "ok": True,
                "status_code": response.getcode(),
                "url": url,
                "body": body_json,
                "error": None,
                "fetched_at": now_iso_utc(),
            }

    except HTTPError as exc:
        raw_text = exc.read().decode("utf-8", errors="replace")
        try:
            error_body = json.loads(raw_text)
        except json.JSONDecodeError:
            error_body = {"raw_text": raw_text}

        return {
            "ok": False,
            "status_code": exc.code,
            "url": url,
            "body": error_body,
            "error": f"HTTPError: {exc.reason}",
            "fetched_at": now_iso_utc(),
        }

    except URLError as exc:
        return {
            "ok": False,
            "status_code": None,
            "url": url,
            "body": None,
            "error": f"URLError: {exc.reason}",
            "fetched_at": now_iso_utc(),
        }


def write_symbol_file(
    output_dir: Path,
    symbol: str,
    payload: dict[str, Any],
    pretty: bool,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{symbol}.json"

    with target.open("w", encoding="utf-8") as handle:
        if pretty:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        else:
            json.dump(payload, handle, separators=(",", ":"), ensure_ascii=False)

    return target


def collect_for_symbol(
    symbol: str,
    base_url: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    endpoint_results: dict[str, Any] = {}

    for spec in CORE_ENDPOINTS:
        url = build_url(base_url=base_url, spec=spec, symbol=symbol)
        endpoint_results[spec.name] = fetch_json(url=url, timeout_seconds=timeout_seconds)

    return {
        "symbol": symbol,
        "base_url": base_url.rstrip("/"),
        "generated_at": now_iso_utc(),
        "endpoints": endpoint_results,
    }


def main() -> int:
    args = parse_args()

    try:
        symbols: list[str] = []

        if args.symbols_from_seed:
            symbols.extend(load_symbols_from_seed_file(Path(args.seed_file)))

        if args.symbols:
            symbols.extend(normalize_symbol(item) for item in args.symbols)

        symbols = list(dict.fromkeys(symbols))
        if not symbols:
            raise ValueError(
                "Provide --symbols and/or use --symbols-from-seed to load symbols"
            )
    except ValueError as exc:
        print(f"Invalid input: {exc}")
        return 2

    output_dir = Path(args.output_dir)

    for symbol in symbols:
        payload = collect_for_symbol(
            symbol=symbol,
            base_url=args.base_url,
            timeout_seconds=args.timeout_seconds,
        )

        failures = [
            name for name, result in payload["endpoints"].items() if not result.get("ok")
        ]
        target = write_symbol_file(
            output_dir=output_dir,
            symbol=symbol,
            payload=payload,
            pretty=args.pretty,
        )

        if failures:
            print(f"{symbol}: wrote {target} with failed endpoints: {', '.join(failures)}")
            if not args.continue_on_error:
                return 1
        else:
            print(f"{symbol}: wrote {target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
