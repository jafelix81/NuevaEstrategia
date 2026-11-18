#!/usr/bin/env python3
"""Phase 473: metadata-only re-audit of Phase 20C price-provider responses.

No OHLCV values or raw provider bodies are persisted. The diagnostic is
feasibility-only and never authorizes a mixed-provider price panel.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

import requests

START = "2016-10-24"
END_EXCLUSIVE = "2026-10-24"
MISSING = ("AVB", "EA", "EQR", "LPRO", "ROKU", "WBD", "WBS")
CONTROLS = ("AAPL", "MSFT", "NVDA", "SPY")
TICKERS = MISSING + CONTROLS
TIMEOUT = 25


def epoch(day: str) -> int:
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def clean_text(value: Any, limit: int = 180) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text[:limit] if text else None


def date_from_epoch(value: Any) -> str | None:
    try:
        return datetime.fromtimestamp(int(value), timezone.utc).date().isoformat()
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def request_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; NuevaEstrategia/Phase473; research)",
        "Accept": "application/json,text/csv,text/plain,*/*",
    })
    return session


def base_record(ticker: str, provider: str) -> dict[str, Any]:
    return {
        "ticker": ticker,
        "provider": provider,
        "status": "not_run",
        "http_status": None,
        "content_type": None,
        "response_bytes": None,
        "schema_valid": False,
        "rows": 0,
        "first_date": None,
        "last_date": None,
        "error_class": None,
    }


def fetch_yahoo(ticker: str, host: str) -> dict[str, Any]:
    provider = f"yahoo_{host}"
    out = base_record(ticker, provider)
    url = f"https://{host}/v8/finance/chart/{ticker}"
    params = {
        "period1": epoch(START),
        "period2": epoch(END_EXCLUSIVE),
        "interval": "1d",
        "events": "div,splits",
    }
    try:
        response = request_session().get(url, params=params, timeout=TIMEOUT)
        out["http_status"] = response.status_code
        out["content_type"] = response.headers.get("Content-Type")
        out["response_bytes"] = len(response.content)
        response.raise_for_status()
        payload = response.json()
        chart = payload.get("chart") or {}
        error = chart.get("error")
        result = chart.get("result")
        out.update({
            "chart_error_code": clean_text((error or {}).get("code")),
            "chart_error_description": clean_text((error or {}).get("description")),
            "result_present": bool(result),
        })
        if not result:
            out["status"] = "chart_error" if error else "empty_result"
            return out
        item = result[0]
        timestamps = item.get("timestamp") or []
        dates = sorted({d for d in (date_from_epoch(x) for x in timestamps) if d})
        meta = item.get("meta") or {}
        out.update({
            "status": "ok" if dates else "empty_chart",
            "schema_valid": True,
            "rows": len(dates),
            "first_date": dates[0] if dates else None,
            "last_date": dates[-1] if dates else None,
            "chart_symbol": clean_text(meta.get("symbol"), 32),
            "exchange_name": clean_text(meta.get("exchangeName"), 64),
            "instrument_type": clean_text(meta.get("instrumentType"), 32),
            "first_trade_date": date_from_epoch(meta.get("firstTradeDate")),
            "regular_market_time": date_from_epoch(meta.get("regularMarketTime")),
            "price_hint": meta.get("priceHint"),
            "valid_ranges": [clean_text(x, 20) for x in (meta.get("validRanges") or [])[:20]],
        })
        return out
    except Exception as exc:
        out["status"] = "request_or_parse_error"
        out["error_class"] = type(exc).__name__
        return out


def fetch_stooq(ticker: str) -> dict[str, Any]:
    out = base_record(ticker, "stooq")
    url = "https://stooq.com/q/d/l/"
    params = {
        "s": ticker.lower() + ".us",
        "d1": START.replace("-", ""),
        "d2": END_EXCLUSIVE.replace("-", ""),
        "i": "d",
    }
    try:
        response = request_session().get(url, params=params, timeout=TIMEOUT)
        out["http_status"] = response.status_code
        out["content_type"] = response.headers.get("Content-Type")
        out["response_bytes"] = len(response.content)
        response.raise_for_status()
        reader = csv.reader(StringIO(response.text))
        header = next(reader, [])
        columns = [clean_text(x, 32) for x in header]
        out["columns"] = columns[:20]
        normalized = {str(x).strip().lower() for x in header}
        if not {"date", "close"}.issubset(normalized):
            out["status"] = "unexpected_csv_schema"
            out["schema_valid"] = False
            return out
        date_idx = next(i for i, x in enumerate(header) if str(x).strip().lower() == "date")
        close_idx = next(i for i, x in enumerate(header) if str(x).strip().lower() == "close")
        dates = []
        for row in reader:
            if len(row) <= max(date_idx, close_idx):
                continue
            date_value = clean_text(row[date_idx], 16)
            close_value = clean_text(row[close_idx], 32)
            if date_value and close_value:
                dates.append(date_value)
        dates = sorted(set(dates))
        out.update({
            "status": "ok" if dates else "empty_csv",
            "schema_valid": True,
            "rows": len(dates),
            "first_date": dates[0] if dates else None,
            "last_date": dates[-1] if dates else None,
        })
        return out
    except Exception as exc:
        out["status"] = "request_or_parse_error"
        out["error_class"] = type(exc).__name__
        return out


def fetch_nasdaq(ticker: str) -> dict[str, Any]:
    out = base_record(ticker, "nasdaq")
    session = request_session()
    session.headers.update({
        "Origin": "https://www.nasdaq.com",
        "Referer": f"https://www.nasdaq.com/market-activity/stocks/{ticker.lower()}/historical",
    })
    url = f"https://api.nasdaq.com/api/quote/{ticker}/historical"
    params = {
        "assetclass": "stocks",
        "fromdate": "10/24/2016",
        "limit": "5000",
        "todate": "10/24/2026",
    }
    try:
        response = session.get(url, params=params, timeout=TIMEOUT)
        out["http_status"] = response.status_code
        out["content_type"] = response.headers.get("Content-Type")
        out["response_bytes"] = len(response.content)
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") or {}
        table = data.get("tradesTable") or {}
        rows = table.get("rows")
        out.update({
            "api_status": clean_text(payload.get("status")),
            "api_message": clean_text(payload.get("message")),
            "root_keys": sorted(str(k) for k in payload.keys())[:30],
            "data_keys": sorted(str(k) for k in data.keys())[:30],
            "trades_table_keys": sorted(str(k) for k in table.keys())[:30],
            "total_records": table.get("totalRecords"),
            "schema_valid": isinstance(rows, list),
        })
        if not isinstance(rows, list):
            out["status"] = "unexpected_json_schema"
            return out
        dates = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            value = row.get("date") or row.get("Date")
            if value:
                dates.append(clean_text(value, 32))
        dates = sorted(set(x for x in dates if x))
        out.update({
            "status": "ok" if dates else "empty_rows",
            "rows": len(dates),
            "first_date": dates[0] if dates else None,
            "last_date": dates[-1] if dates else None,
        })
        return out
    except Exception as exc:
        out["status"] = "request_or_parse_error"
        out["error_class"] = type(exc).__name__
        return out


def classify_provider(records: list[dict[str, Any]], provider: str) -> dict[str, Any]:
    subset = [x for x in records if x.get("provider") == provider]
    controls = [x for x in subset if x.get("ticker") in CONTROLS]
    missing = [x for x in subset if x.get("ticker") in MISSING]
    control_nonempty = sum(int(x.get("rows") or 0) > 0 for x in controls)
    missing_nonempty = sum(int(x.get("rows") or 0) > 0 for x in missing)
    method_valid = control_nonempty >= 3
    if not method_valid:
        disposition = "PROVIDER_METHOD_UNVALIDATED_CONTROLS_INSUFFICIENT"
    elif missing_nonempty == 0:
        disposition = "VALID_CONTROLS_BUT_MISSING_SYMBOL_RESPONSES_EMPTY"
    else:
        disposition = "VALID_CONTROLS_AND_SOME_MISSING_SYMBOL_HISTORY"
    return {
        "provider": provider,
        "control_count": len(controls),
        "control_nonempty_count": control_nonempty,
        "missing_symbol_count": len(missing),
        "missing_symbol_nonempty_count": missing_nonempty,
        "method_validated_by_controls": method_valid,
        "disposition": disposition,
    }


def build_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    providers = sorted({str(x.get("provider")) for x in records})
    return {
        "phase": 473,
        "audit_time_utc": datetime.now(timezone.utc).isoformat(),
        "price_window_start": START,
        "price_window_end_exclusive": END_EXCLUSIVE,
        "controls": list(CONTROLS),
        "missing_tickers": list(MISSING),
        "provider_summary": [classify_provider(records, p) for p in providers],
        "records": records,
        "raw_price_data_retained": False,
        "raw_provider_response_bodies_retained": False,
        "forward_returns_used": False,
        "fallback_accepted": False,
        "alpha_test_authorized": False,
        "f80_changed": False,
        "production_changed": False,
        "research_disposition": "PROVIDER_RESPONSE_CLASSIFICATION_ONLY_NO_FALLBACK_ADMITTED",
    }


def run_probe() -> dict[str, Any]:
    tasks = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for ticker in TICKERS:
            tasks.extend([
                pool.submit(fetch_yahoo, ticker, "query1.finance.yahoo.com"),
                pool.submit(fetch_yahoo, ticker, "query2.finance.yahoo.com"),
                pool.submit(fetch_stooq, ticker),
                pool.submit(fetch_nasdaq, ticker),
            ])
        records = [future.result() for future in as_completed(tasks)]
    records.sort(key=lambda x: (x["provider"], x["ticker"]))
    return build_summary(records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase473_output")
    args = parser.parse_args()
    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    summary = run_probe()
    target = outdir / "summary.json"
    target.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print("PHASE473_PROVIDER_RESPONSE_AUDIT=", summary["research_disposition"])
    for item in summary["provider_summary"]:
        print(
            "PROVIDER=", item["provider"],
            "CONTROL_NONEMPTY=", item["control_nonempty_count"],
            "MISSING_NONEMPTY=", item["missing_symbol_nonempty_count"],
            "DISPOSITION=", item["disposition"],
        )
    print("RAW_PRICE_DATA_RETAINED=False")
    print("RAW_RESPONSE_BODIES_RETAINED=False")
    print("FALLBACK_ACCEPTED=False")
    if summary["raw_price_data_retained"] or summary["raw_provider_response_bodies_retained"] or summary["fallback_accepted"]:
        raise SystemExit("Phase 473 research-only guard violated")


if __name__ == "__main__":
    main()
