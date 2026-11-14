#!/usr/bin/env python3
"""Phase 393: retest Nasdaq historical endpoint with ISO dates.

Provider feasibility only. Raw prices are held in memory for diagnostics and
never written to the artifact or repository.
"""
from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

START = "2016-10-24"
END_EXCLUSIVE = "2026-10-24"
MISSING = ("AVB", "EA", "EQR", "LPRO", "ROKU", "WBD", "WBS")
CONTROLS = ("AAPL", "MSFT", "NVDA", "SPY")
TICKERS = MISSING + CONTROLS
TIMEOUT = 35
PAGE_LIMIT = 5000
MAX_PAGES = 4


def validate_iso_window(start: str = START, end: str = END_EXCLUSIVE) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", start)
                and re.fullmatch(r"\d{4}-\d{2}-\d{2}", end)
                and start < end)


def new_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; NuevaEstrategia/Phase393; research)",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.nasdaq.com",
        "Referer": "https://www.nasdaq.com/",
    })
    return session


def _close_value(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(str(value).replace("$", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return result if np.isfinite(result) and result > 0 else None


def _date_value(value: Any) -> str | None:
    if value is None:
        return None
    parsed = pd.to_datetime(str(value).strip(), errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date().isoformat()


def parse_nasdaq_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") or {}
    table = data.get("tradesTable") or {}
    rows = table.get("rows") or []
    parsed: list[tuple[str, float]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        day = _date_value(row.get("date") or row.get("Date"))
        close = _close_value(
            row.get("close") or row.get("Close/Last") or row.get("closePrice")
        )
        if day and close is not None:
            parsed.append((day, close))
    parsed.sort(key=lambda item: item[0])
    return {
        "series": {day: close for day, close in parsed},
        "payload_keys": sorted(str(k) for k in payload.keys()),
        "data_keys": sorted(str(k) for k in data.keys()) if isinstance(data, dict) else [],
        "table_keys": sorted(str(k) for k in table.keys()) if isinstance(table, dict) else [],
        "total_records": table.get("totalRecords") if isinstance(table, dict) else None,
        "response_message": (
            payload.get("message") or payload.get("status")
            or (data.get("message") if isinstance(data, dict) else None)
        ),
        "reported_row_count": len(rows),
    }


def fetch_nasdaq(ticker: str) -> dict[str, Any]:
    session = new_session()
    url = f"https://api.nasdaq.com/api/quote/{ticker}/historical"
    all_series: dict[str, float] = {}
    diagnostics: dict[str, Any] = {
        "ticker": ticker,
        "provider": "nasdaq_public_quote_historical",
        "status": "failed",
        "http_status": None,
        "content_type": None,
        "payload_keys": [],
        "data_keys": [],
        "table_keys": [],
        "total_records": None,
        "reported_row_count": 0,
        "pages_requested": 0,
        "rows": 0,
        "first_date": None,
        "last_date": None,
        "error_class": None,
        "response_message": None,
    }
    try:
        for page in range(MAX_PAGES):
            params = {
                "assetclass": "stocks",
                "fromdate": START,
                "todate": END_EXCLUSIVE,
                "limit": str(PAGE_LIMIT),
                "offset": str(page * PAGE_LIMIT),
            }
            response = session.get(url, params=params, timeout=TIMEOUT)
            diagnostics["pages_requested"] += 1
            diagnostics["http_status"] = response.status_code
            diagnostics["content_type"] = response.headers.get("Content-Type", "").split(";")[0]
            response.raise_for_status()
            payload = response.json()
            parsed = parse_nasdaq_payload(payload)
            if page == 0:
                for key in ("payload_keys", "data_keys", "table_keys",
                            "total_records", "response_message"):
                    diagnostics[key] = parsed[key]
            diagnostics["reported_row_count"] += parsed["reported_row_count"]
            all_series.update(parsed["series"])
            total = parsed["total_records"]
            if parsed["reported_row_count"] < PAGE_LIMIT:
                break
            if total is not None:
                try:
                    if page * PAGE_LIMIT + parsed["reported_row_count"] >= int(total):
                        break
                except (TypeError, ValueError):
                    pass
            time.sleep(0.25)
        ordered = sorted(all_series)
        diagnostics["rows"] = len(all_series)
        diagnostics["first_date"] = ordered[0] if ordered else None
        diagnostics["last_date"] = ordered[-1] if ordered else None
        diagnostics["status"] = "ok" if all_series else "empty"
        diagnostics["_series"] = all_series
    except Exception as exc:
        diagnostics["error_class"] = type(exc).__name__
        diagnostics["status"] = "failed"
        diagnostics["_series"] = all_series
    finally:
        session.close()
    return diagnostics


def fetch_yahoo_control(ticker: str) -> dict[str, Any]:
    session = new_session()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    period1 = int(datetime.strptime(START, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    ).timestamp())
    period2 = int(datetime.strptime(END_EXCLUSIVE, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    ).timestamp())
    result: dict[str, Any] = {
        "ticker": ticker,
        "provider": "yahoo_query1_control",
        "status": "failed",
        "http_status": None,
        "rows": 0,
        "first_date": None,
        "last_date": None,
        "error_class": None,
        "_series": {},
    }
    try:
        response = session.get(
            url,
            params={"period1": period1, "period2": period2,
                    "interval": "1d", "events": "div,splits"},
            timeout=TIMEOUT,
        )
        result["http_status"] = response.status_code
        response.raise_for_status()
        payload = response.json().get("chart", {})
        items = payload.get("result") or []
        if not items:
            result["status"] = "empty"
            result["error_class"] = "EmptyChartResult"
            return result
        item = items[0]
        timestamps = item.get("timestamp") or []
        quote = (item.get("indicators") or {}).get("quote", [{}])[0]
        closes = quote.get("close") or []
        series: dict[str, float] = {}
        for stamp, close in zip(timestamps, closes):
            value = _close_value(close)
            if value is None:
                continue
            day = datetime.fromtimestamp(stamp, timezone.utc).date().isoformat()
            series[day] = value
        ordered = sorted(series)
        result["rows"] = len(series)
        result["first_date"] = ordered[0] if ordered else None
        result["last_date"] = ordered[-1] if ordered else None
        result["status"] = "ok" if series else "empty"
        result["_series"] = series
    except Exception as exc:
        result["error_class"] = type(exc).__name__
    finally:
        session.close()
    return result


def compare_daily_returns(left: dict[str, float], right: dict[str, float]) -> dict[str, Any]:
    common = sorted(set(left) & set(right))
    left_returns: list[float] = []
    right_returns: list[float] = []
    for previous, current in zip(common, common[1:]):
        l0, l1 = left[previous], left[current]
        r0, r1 = right[previous], right[current]
        if min(l0, l1, r0, r1) <= 0:
            continue
        left_returns.append(l1 / l0 - 1.0)
        right_returns.append(r1 / r0 - 1.0)
    if len(left_returns) < 30:
        return {
            "common_dates": len(common), "return_pairs": len(left_returns),
            "return_corr": None, "median_abs_return_diff": None,
            "p95_abs_return_diff": None, "max_abs_return_diff": None,
        }
    a = np.asarray(left_returns, dtype=float)
    b = np.asarray(right_returns, dtype=float)
    difference = np.abs(a - b)
    correlation = float(np.corrcoef(a, b)[0, 1]) if np.std(a) and np.std(b) else None
    return {
        "common_dates": len(common),
        "return_pairs": len(a),
        "return_corr": correlation,
        "median_abs_return_diff": float(np.median(difference)),
        "p95_abs_return_diff": float(np.quantile(difference, 0.95)),
        "max_abs_return_diff": float(np.max(difference)),
    }


def public_record(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if not key.startswith("_")}


def run_audit() -> dict[str, Any]:
    if not validate_iso_window():
        raise ValueError("The fixed historical window must use ISO YYYY-MM-DD dates")
    nasdaq: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch_nasdaq, ticker): ticker for ticker in TICKERS}
        for future in as_completed(futures):
            ticker = futures[future]
            nasdaq[ticker] = future.result()

    controls: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(fetch_yahoo_control, ticker): ticker for ticker in CONTROLS}
        for future in as_completed(futures):
            ticker = futures[future]
            controls[ticker] = future.result()

    control_validation = all(
        nasdaq[ticker]["rows"] >= 220 and controls[ticker]["rows"] >= 220
        for ticker in CONTROLS
    )
    concordance = []
    for ticker in CONTROLS:
        concordance.append({
            "ticker": ticker,
            **compare_daily_returns(
                nasdaq[ticker].get("_series", {}),
                controls[ticker].get("_series", {}),
            ),
        })

    missing_assessment = []
    for ticker in MISSING:
        rows = nasdaq[ticker]["rows"]
        if not control_validation:
            disposition = "UNRESOLVED_ENDPOINT_NOT_VALIDATED_BY_CONTROLS"
        elif rows >= 220:
            disposition = "COVERAGE_CANDIDATE_REQUIRES_IDENTITY_AND_PRICE_RECONCILIATION"
        else:
            disposition = "NO_220_ROW_COVERAGE_IN_FIXED_WINDOW"
        missing_assessment.append({
            "ticker": ticker,
            "nasdaq_rows": rows,
            "first_date": nasdaq[ticker]["first_date"],
            "last_date": nasdaq[ticker]["last_date"],
            "disposition": disposition,
        })

    candidate_count = sum(item["nasdaq_rows"] >= 220 for item in missing_assessment)
    return {
        "phase": 393,
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "price_window_start": START,
        "price_window_end_exclusive": END_EXCLUSIVE,
        "nasdaq_request_date_format": "YYYY-MM-DD",
        "nasdaq_endpoint_control_validated": control_validation,
        "nasdaq_records": [public_record(nasdaq[t]) for t in TICKERS],
        "yahoo_control_records": [public_record(controls[t]) for t in CONTROLS],
        "control_daily_return_concordance": concordance,
        "missing_symbol_assessment": missing_assessment,
        "missing_symbols_with_at_least_220_nasdaq_rows": candidate_count,
        "fallback_accepted": False,
        "raw_prices_retained": False,
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_changed": False,
        "production_changed": False,
        "research_disposition": (
            "NASDAQ_ENDPOINT_VALIDATED_CANDIDATE_COVERAGE_FOUND"
            if control_validation and candidate_count == len(MISSING)
            else "PROVIDER_DIAGNOSTIC_ONLY_NO_FALLBACK_ADMITTED"
        ),
        "acceptance_rule": (
            "All four controls must return >=220 rows; missing names must meet "
            "listing-date-appropriate coverage; independent daily-return "
            "concordance, corporate-action treatment, identity and delisting "
            "gates must pass before any fallback is admitted."
        ),
    }


def main() -> None:
    output = Path("phase393_finra_nasdaq_iso_date_provider_retest")
    output.mkdir(parents=True, exist_ok=True)
    result = run_audit()
    (output / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    print("PHASE393_DISPOSITION=", result["research_disposition"])
    print("NASDAQ_CONTROLS_VALIDATED=", result["nasdaq_endpoint_control_validated"])
    print("MISSING_SYMBOLS_WITH_220_ROWS=", result["missing_symbols_with_at_least_220_nasdaq_rows"])
    print("RAW_PRICES_RETAINED=False")
    print("FALLBACK_ACCEPTED=False")
    if any(result[key] for key in (
        "raw_prices_retained", "forward_returns_used", "alpha_test_authorized",
        "holdout_used", "f80_changed", "production_changed", "fallback_accepted"
    )):
        raise SystemExit("Phase 393 research-only controls violated")


if __name__ == "__main__":
    main()
