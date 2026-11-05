#!/usr/bin/env python3
"""Phase 111: audit OCC ONN daily account-type history using public batch endpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ENDPOINT = "https://marketdata.theocc.com/onn-volume-download"
DATES = ("20160531", "20190531", "20231103", "20261103")
EXCHANGE_CODES = set("ABCDEFGHIJKLM PQRSTUVWXZ".replace(" ", ""))
EXPECTED_WIDTH = 40


def parse_report_header(line: str) -> tuple[str | None, str | None]:
    if len(line) < 31:
        return None, None
    start_raw = line[8:17].strip()
    end_raw = line[23:31].strip()
    if start_raw.startswith("H"):
        start_raw = start_raw[1:]
    if re.fullmatch(r"\d{8}", start_raw) and re.fullmatch(r"\d{8}", end_raw):
        return start_raw, end_raw
    return None, None


def parse_fixed_width(payload: bytes) -> dict[str, Any]:
    text = payload.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    header_start = None
    header_end = None
    rows: list[dict[str, Any]] = []
    malformed: list[str] = []
    unknown_exchange: list[str] = []
    bad_numeric: list[str] = []

    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        start, end = parse_report_header(line)
        if start and end:
            header_start, header_end = start, end
            continue
        if len(line) < EXPECTED_WIDTH:
            malformed.append(f"line_{line_no}:width_{len(line)}")
            continue

        group = line[0:6].strip()
        symbol = line[6:12].strip()
        exchange = line[12:13].strip()
        if not group or not symbol:
            malformed.append(f"line_{line_no}:blank_group_or_symbol")
            continue
        if exchange not in EXCHANGE_CODES:
            unknown_exchange.append(f"line_{line_no}:{exchange}")
            continue

        numeric_segments = (line[13:22], line[22:31], line[31:40])
        values: list[int] = []
        numeric_ok = True
        for segment in numeric_segments:
            raw = segment.strip()
            if not raw:
                values.append(0)
            elif re.fullmatch(r"-?\d+", raw):
                values.append(int(raw))
            else:
                numeric_ok = False
                break
        if not numeric_ok:
            bad_numeric.append(f"line_{line_no}:invalid_volume")
            continue

        rows.append(
            {
                "group": group,
                "symbol": symbol,
                "exchange": exchange,
                "customer_volume": values[0],
                "firm_volume": values[1],
                "market_maker_volume": values[2],
            }
        )

    keys = [(r["group"], r["symbol"], r["exchange"]) for r in rows]
    duplicate_count = len(keys) - len(set(keys))
    negative_count = sum(
        1
        for row in rows
        for field in ("customer_volume", "firm_volume", "market_maker_volume")
        if row[field] < 0
    )

    return {
        "header_start": header_start,
        "header_end": header_end,
        "rows": rows,
        "row_count": len(rows),
        "unique_symbols": len({r["symbol"] for r in rows}),
        "unique_groups": sorted({r["group"] for r in rows}),
        "unique_exchanges": sorted({r["exchange"] for r in rows}),
        "duplicate_key_count": duplicate_count,
        "unknown_exchange_rows": unknown_exchange,
        "malformed_rows": malformed,
        "bad_numeric_rows": bad_numeric,
        "negative_volume_count": negative_count,
        "customer_volume_sum": sum(r["customer_volume"] for r in rows),
        "firm_volume_sum": sum(r["firm_volume"] for r in rows),
        "market_maker_volume_sum": sum(r["market_maker_volume"] for r in rows),
        "non_data_lines": len(lines) - len(rows) - (1 if header_start else 0),
    }


def fetch_one(session: requests.Session, report_date: str, out_dir: Path) -> dict[str, Any]:
    params = {
        "productKind": "options",
        "reportType": "D",
        "reportDate": report_date,
        "reportFormat": "volume",
        "issues": "all",
        "reportView": "raw",
    }
    attempts = []
    response = None
    for attempt in range(1, 4):
        try:
            response = session.get(ENDPOINT, params=params, timeout=90)
            attempts.append(
                {
                    "attempt": attempt,
                    "status": response.status_code,
                    "bytes": len(response.content),
                    "content_type": response.headers.get("Content-Type"),
                }
            )
            if response.status_code == 200:
                break
            if response.status_code not in (429, 500, 502, 503, 504):
                break
        except requests.RequestException as exc:
            attempts.append({"attempt": attempt, "error": type(exc).__name__})
        if attempt < 3:
            time.sleep(attempt * 2)

    record: dict[str, Any] = {
        "report_date": report_date,
        "request_url": response.url if response is not None else None,
        "attempts": attempts,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if response is None:
        record.update({"http_status": None, "available": False, "error": "request_failed"})
        return record

    payload = response.content
    record.update(
        {
            "http_status": response.status_code,
            "content_type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("Last-Modified"),
            "etag": response.headers.get("ETag"),
            "byte_count": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    )

    raw_path = out_dir / f"occ_onn_volume_{report_date}.txt"
    raw_path.write_bytes(payload)
    record["raw_file"] = raw_path.name

    if response.status_code != 200:
        record.update({"available": False, "error": f"http_{response.status_code}"})
        return record

    parsed = parse_fixed_width(payload)
    expected_date_match = (
        parsed["header_start"] == report_date and parsed["header_end"] == report_date
    )
    record.update(
        {
            "available": parsed["row_count"] > 0,
            "header_start": parsed["header_start"],
            "header_end": parsed["header_end"],
            "header_matches_requested_date": expected_date_match,
            "row_count": parsed["row_count"],
            "unique_symbols": parsed["unique_symbols"],
            "unique_groups": parsed["unique_groups"],
            "unique_exchanges": parsed["unique_exchanges"],
            "duplicate_key_count": parsed["duplicate_key_count"],
            "unknown_exchange_count": len(parsed["unknown_exchange_rows"]),
            "malformed_row_count": len(parsed["malformed_rows"]),
            "bad_numeric_row_count": len(parsed["bad_numeric_rows"]),
            "negative_volume_count": parsed["negative_volume_count"],
            "customer_volume_sum": parsed["customer_volume_sum"],
            "firm_volume_sum": parsed["firm_volume_sum"],
            "market_maker_volume_sum": parsed["market_maker_volume_sum"],
            "non_data_lines": parsed["non_data_lines"],
        }
    )
    record["diagnostics"] = {
        "unknown_exchange_rows": parsed["unknown_exchange_rows"][:20],
        "malformed_rows": parsed["malformed_rows"][:20],
        "bad_numeric_rows": parsed["bad_numeric_rows"][:20],
    }
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase111_occ_output")
    parser.add_argument("--dates", nargs="*", default=list(DATES))
    args = parser.parse_args()

    output = Path(args.output)
    raw_dir = output / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "NuevaEstrategia-Research/Phase111",
            "Accept": "text/plain,text/csv,application/octet-stream,*/*",
        }
    )

    results = []
    for index, report_date in enumerate(args.dates):
        results.append(fetch_one(session, report_date, raw_dir))
        if index + 1 < len(args.dates):
            time.sleep(1.0)

    successful = [
        r for r in results
        if r.get("available")
        and r.get("header_matches_requested_date")
        and r.get("duplicate_key_count") == 0
        and r.get("unknown_exchange_count") == 0
        and r.get("malformed_row_count") == 0
        and r.get("bad_numeric_row_count") == 0
        and r.get("negative_volume_count") == 0
    ]
    summary = {
        "phase": 111,
        "endpoint": ENDPOINT,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_dates": list(args.dates),
        "successful_dates": len(successful),
        "results": results,
        "data_gate": "PASS_SAMPLED_DATES" if len(successful) == len(args.dates) else "INCOMPLETE_OR_FAILED",
        "limitations": [
            "No explicit historical publication timestamp was established.",
            "Customer/Firm/Market Maker are account-type categories, not beneficial-owner identities.",
            "The report does not contain buyer/seller initiation or opening/closing status.",
            "A four-date sample does not establish continuous historical coverage.",
        ],
    }
    (output / "phase111_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
