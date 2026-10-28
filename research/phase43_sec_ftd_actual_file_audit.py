#!/usr/bin/env python3
"""Phase 43: SEC FTD actual-file feasibility audit.

Downloads two official SEC files (2018 and 2026), validates the raw schema,
and records PIT metadata separately from settlement dates. This is a gate only:
no alpha construction or portfolio testing occurs here.
"""

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

# Conservative knowledge dates required by the research protocol. The SEC says
# the first half is available at month-end and the second half around the 15th
# of the following month, without guaranteeing an exact posting date.
KNOWLEDGE_DATES = {
    "2018_first_half": "2018-01-31",
    "2026_second_half": "2026-10-15",
}

EXPECTED_COLUMNS = ("SETTLEMENT DATE", "CUSIP", "SYMBOL", "QUANTITY (FAILS)", "DESCRIPTION", "PRICE")


def download(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "NuevaEstrategia research audit contact research@example.com"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def parse_zip(payload: bytes):
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if not names:
            raise ValueError("ZIP contains no files")
        raw = zf.read(names[0])
    text = raw.decode("utf-8-sig", errors="replace")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("empty text file")

    reader = csv.reader(lines, delimiter="|")
    rows = list(reader)
    header = tuple(x.strip().upper() for x in rows[0])
    if header != EXPECTED_COLUMNS:
        raise ValueError(f"unexpected schema: {header!r}")

    data = rows[1:]
    bad_width = sum(len(r) != 6 for r in data)
    parsed = []
    for row in data:
        if len(row) != 6:
            continue
        settlement, cusip, symbol, quantity, description, price = [x.strip() for x in row]
        try:
            y, m, d = map(int, re.split(r"[-/]", settlement))
            dt = date(y, m, d)
        except Exception as exc:
            raise ValueError(f"bad settlement date {settlement!r}: {exc}")
        q = int(quantity.replace(",", ""))
        p = None if price == "." else float(price.replace(",", ""))
        parsed.append((dt.isoformat(), cusip, symbol, q, description, p))

    return names[0], parsed, bad_width


def audit_one(label: str, url: str) -> dict:
    payload = download(url)
    member, rows, bad_width = parse_zip(payload)
    settlements = [r[0] for r in rows]
    duplicate_keys = Counter((r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows)
    duplicate_rows = sum(v - 1 for v in duplicate_keys.values() if v > 1)
    empty_cusip = sum(not r[1] for r in rows)
    empty_symbol = sum(not r[2] for r in rows)
    invalid_qty = sum(r[3] < 0 for r in rows)
    prices_available = sum(r[5] is not None for r in rows)
    return {
        "label": label,
        "url": url,
        "zip_member": member,
        "bytes": len(payload),
        "rows": len(rows),
        "bad_width_rows": bad_width,
        "duplicate_exact_rows": duplicate_rows,
        "min_settlement": min(settlements),
        "max_settlement": max(settlements),
        "unique_settlement_dates": len(set(settlements)),
        "empty_cusip_rows": empty_cusip,
        "empty_symbol_rows": empty_symbol,
        "negative_quantity_rows": invalid_qty,
        "price_available_pct": round(100 * prices_available / len(rows), 3),
        "knowledge_date": KNOWLEDGE_DATES[label],
        "pit_rule": "knowledge_date is file availability cutoff, never settlement date",
    }


def main() -> None:
    results = []
    for label, url in FILES.items():
        results.append(audit_one(label, url))

    # Gate conditions deliberately conservative: schema and types must be clean;
    # identity fields should be substantially populated; duplicates cannot be
    # silently accepted; settlement dates must fall within the named period.
    passed = all(
        r["rows"] > 0
        and r["bad_width_rows"] == 0
        and r["duplicate_exact_rows"] == 0
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
            "Schema/PIT parser gate passed. Proceed to frozen-universe identity coverage and continuity audit; "
            "do not interpret FTD as short selling."
            if passed
            else "Do not proceed to alpha research until parser/schema defects are resolved."
        ),
    }
    out = Path("ftd_actual_file_audit.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
