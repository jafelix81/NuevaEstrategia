#!/usr/bin/env python3
"""Phase 43: SEC FTD actual-file feasibility audit."""

from __future__ import annotations

import csv
import io
import json
import re
import urllib.request
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path

FILES = {
    "2018_first_half": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails201801a.zip",
    "2026_second_half": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails202609b.zip",
}

KNOWLEDGE_DATES = {
    "2018_first_half": "2018-01-31",
    "2026_second_half": "2026-10-15",
}

SETTLEMENT_WINDOWS = {
    "2018_first_half": (date(2018, 1, 1), date(2018, 1, 15)),
    "2026_second_half": (date(2026, 9, 15), date(2026, 9, 30)),
}

EXPECTED_COLUMNS = ("SETTLEMENT DATE", "CUSIP", "SYMBOL", "QUANTITY (FAILS)", "DESCRIPTION", "PRICE")
TRAILER_COUNT_RE = re.compile(r"^Trailer record count\s+(\d+)\s*$", re.I)
TRAILER_QTY_RE = re.compile(r"^Trailer total quantity of shares\s+(\d+)\s*$", re.I)


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "NuevaEstrategia research audit contact research@example.com"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def parse_settlement_date(value: str) -> date:
    value = value.strip()
    if re.fullmatch(r"\d{8}", value):
        return date(int(value[:4]), int(value[4:6]), int(value[6:8]))
    parts = re.split(r"[-/]", value)
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        return date(*map(int, parts))
    raise ValueError(f"unsupported settlement date format: {value!r}")


def parse_zip(payload: bytes):
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if not names:
            raise ValueError("ZIP contains no files")
        raw = zf.read(names[0])
    text = raw.decode("utf-8-sig", errors="replace")
    lines = [line for line in text.splitlines() if line.strip()]
    reader = csv.reader(lines, delimiter="|")
    rows = list(reader)
    header = tuple(x.strip().upper() for x in rows[0])
    if header != EXPECTED_COLUMNS:
        raise ValueError(f"unexpected schema: {header!r}")

    data = rows[1:]
    parsed = []
    malformed = []
    trailer_count = None
    trailer_total_quantity = None
    for i, row in enumerate(data, start=2):
        if len(row) == 1:
            text_row = row[0].strip()
            m_count = TRAILER_COUNT_RE.match(text_row)
            m_qty = TRAILER_QTY_RE.match(text_row)
            if m_count:
                trailer_count = int(m_count.group(1))
                continue
            if m_qty:
                trailer_total_quantity = int(m_qty.group(1))
                continue
        if len(row) != 6:
            malformed.append((i, row))
            continue
        settlement, cusip, symbol, quantity, description, price = [x.strip() for x in row]
        dt = parse_settlement_date(settlement)
        q = int(quantity.replace(",", ""))
        p = None if price == "." else float(price.replace(",", ""))
        parsed.append((dt.isoformat(), cusip, symbol, q, description, p))
    return names[0], parsed, malformed, trailer_count, trailer_total_quantity


def audit_one(label: str, url: str) -> dict:
    payload = download(url)
    member, rows, malformed, trailer_count, trailer_total_quantity = parse_zip(payload)
    settlements = [date.fromisoformat(r[0]) for r in rows]
    lo, hi = SETTLEMENT_WINDOWS[label]
    outside_window = sum(not (lo <= dt <= hi) for dt in settlements)
    duplicate_keys = Counter((r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows)
    duplicate_rows = sum(v - 1 for v in duplicate_keys.values() if v > 1)
    empty_cusip = sum(not r[1] for r in rows)
    empty_symbol = sum(not r[2] for r in rows)
    invalid_qty = sum(r[3] < 0 for r in rows)
    prices_available = sum(r[5] is not None for r in rows)
    quantity_sum = sum(r[3] for r in rows)
    return {
        "label": label,
        "url": url,
        "zip_member": member,
        "bytes": len(payload),
        "rows": len(rows),
        "bad_width_rows": len(malformed),
        "bad_width_samples": [{"line_number": n, "fields": row} for n, row in malformed[:10]],
        "trailer_record_count": trailer_count,
        "trailer_total_quantity": trailer_total_quantity,
        "trailer_count_matches_rows": trailer_count == len(rows) if trailer_count is not None else False,
        "trailer_quantity_matches_rows": trailer_total_quantity == quantity_sum if trailer_total_quantity is not None else False,
        "duplicate_exact_rows": duplicate_rows,
        "min_settlement": min(r[0] for r in rows),
        "max_settlement": max(r[0] for r in rows),
        "unique_settlement_dates": len(set(r[0] for r in rows)),
        "outside_expected_settlement_window_rows": outside_window,
        "empty_cusip_rows": empty_cusip,
        "empty_symbol_rows": empty_symbol,
        "negative_quantity_rows": invalid_qty,
        "price_available_pct": round(100 * prices_available / len(rows), 3),
        "knowledge_date": KNOWLEDGE_DATES[label],
        "pit_rule": "knowledge_date is file availability cutoff, never settlement date",
    }


def main() -> None:
    results = [audit_one(label, url) for label, url in FILES.items()]
    passed = all(
        r["rows"] > 0
        and r["bad_width_rows"] == 0
        and r["trailer_count_matches_rows"]
        and r["trailer_quantity_matches_rows"]
        and r["duplicate_exact_rows"] == 0
        and r["outside_expected_settlement_window_rows"] == 0
        and r["empty_cusip_rows"] == 0
        and r["empty_symbol_rows"] == 0
        and r["negative_quantity_rows"] == 0
        for r in results
    )
    report = {
        "phase": "43",
        "status": "PASS_ACTUAL_FILE_SCHEMA_GATE" if passed else "FAIL_ACTUAL_FILE_SCHEMA_GATE",
        "generated_on": date.today().isoformat(),
        "files": results,
        "interpretation": (
            "Schema/PIT parser gate passed. Trailer metadata is explicitly validated. Proceed to frozen-universe identity coverage and continuity audit; do not interpret FTD as short selling."
            if passed else
            "Do not proceed to alpha research until parser/schema defects are resolved. Recognized SEC trailer metadata is retained as validation; unexpected malformed rows remain blocking."
        ),
    }
    Path("ftd_actual_file_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
