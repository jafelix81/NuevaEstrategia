#!/usr/bin/env python3
"""Phase 44: SEC FTD fixed-snapshot identity/coverage audit.

This is a data-feasibility gate only. The 335-name input is a fixed research
snapshot, not a date-appropriate historical active universe. No return or
directional inference is performed.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

FILES = {
    "2018_first_half": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails201801a.zip",
    "2026_second_half": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails202609b.zip",
}
KNOWLEDGE_DATES = {
    "2018_first_half": "2018-01-31",
    "2026_second_half": "2026-10-15",
}
EXPECTED_COLUMNS = (
    "SETTLEMENT DATE", "CUSIP", "SYMBOL", "QUANTITY (FAILS)", "DESCRIPTION", "PRICE"
)
UNIVERSE_PATH = Path("research/phase44_frozen_universe_335_tickers.csv")
OUTPUT_PATH = Path("ftd_universe_coverage_audit.json")


def require_user_agent(value: str | None = None) -> str:
    """Return a monitored SEC User-Agent without ever logging its value."""
    candidate = (value if value is not None else os.environ.get("SEC_USER_AGENT", "")).strip()
    if not candidate or "@" not in candidate:
        raise RuntimeError(
            "SEC_USER_AGENT is required and must include a monitored contact email; "
            "configure it as a GitHub Actions secret."
        )
    return candidate


def download(url: str, user_agent: str | None = None) -> bytes:
    ua = require_user_agent(user_agent)
    request = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def parse_zip(payload: bytes) -> dict:
    """Parse one SEC pipe-delimited FTD ZIP and preserve identity exceptions."""
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [name for name in archive.namelist() if not name.endswith("/")]
        if len(members) != 1:
            raise ValueError(f"expected one data member, found {len(members)}")
        raw = archive.read(members[0])

    rows = [
        row for row in csv.reader(io.StringIO(raw.decode("latin-1")), delimiter="|")
        if any(cell.strip() for cell in row)
    ]
    if not rows:
        raise ValueError("empty FTD file")
    header = tuple(cell.strip().upper() for cell in rows[0])
    if header != EXPECTED_COLUMNS:
        raise ValueError(f"unexpected FTD schema: {header!r}")

    by_symbol: dict[str, set[str]] = defaultdict(set)
    cusip_only: set[str] = set()
    identity_missing_rows = 0
    economic_rows = 0
    duplicate_rows = 0
    seen_rows: set[tuple[str, ...]] = set()

    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != 6:
            raise ValueError(f"row {row_number}: expected 6 columns, got {len(row)}")
        settlement_date, cusip, symbol, quantity, description, price = (
            cell.strip() for cell in row
        )
        # SEC trailer/summary records do not carry an eight-digit settlement date.
        if not re.fullmatch(r"\d{8}", settlement_date):
            continue
        datetime.strptime(settlement_date, "%Y%m%d")
        try:
            qty = int(quantity.replace(",", ""))
        except ValueError as exc:
            raise ValueError(f"row {row_number}: invalid FTD quantity") from exc
        if qty < 0:
            raise ValueError(f"row {row_number}: negative FTD quantity")

        normalized = (
            settlement_date, cusip.upper(), symbol.upper(), str(qty), description, price
        )
        economic_rows += 1
        if normalized in seen_rows:
            duplicate_rows += 1
        seen_rows.add(normalized)

        normalized_cusip = cusip.upper()
        normalized_symbol = symbol.upper()
        if normalized_symbol:
            by_symbol[normalized_symbol].add(normalized_cusip)
        elif normalized_cusip:
            cusip_only.add(normalized_cusip)
        else:
            identity_missing_rows += 1

    return {
        "member": members[0],
        "symbols": {symbol: sorted(cusips) for symbol, cusips in by_symbol.items()},
        "cusip_only_rows": len(cusip_only),
        "cusip_only_cusips": sorted(cusip_only),
        "identity_missing_rows": identity_missing_rows,
        "economic_rows": economic_rows,
        "exact_duplicate_rows": duplicate_rows,
    }


def load_universe(path: Path = UNIVERSE_PATH) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["Ticker"]:
            raise ValueError(f"unexpected universe columns: {reader.fieldnames!r}")
        tickers = [
            row["Ticker"].strip().upper()
            for row in reader
            if row.get("Ticker") and row["Ticker"].strip()
        ]
    if len(tickers) != 335 or len(set(tickers)) != 335:
        raise ValueError(f"expected 335 unique frozen symbols, got {len(tickers)}")
    return tickers


def build_report(universe: list[str], parsed_files: dict[str, dict]) -> dict:
    universe_set = set(universe)
    by_file: dict[str, dict] = {}
    covered_sets: dict[str, set[str]] = {}

    for label, parsed in parsed_files.items():
        symbols = parsed["symbols"]
        present = sorted(universe_set & set(symbols))
        missing = sorted(universe_set - set(symbols))
        multi_cusip = {
            ticker: sorted(cusips for cusips in symbols[ticker] if cusips)
            for ticker in present
            if len({cusip for cusip in symbols[ticker] if cusip}) > 1
        }
        covered_sets[label] = set(present)
        by_file[label] = {
            "knowledge_date": KNOWLEDGE_DATES[label],
            "universe_size": len(universe),
            "covered_symbols": len(present),
            "coverage_pct": round(100 * len(present) / len(universe), 3),
            "missing_symbols": missing,
            "multi_cusip_symbols": multi_cusip,
            "distinct_ftd_cusips": len({
                cusip for ticker in present for cusip in symbols[ticker] if cusip
            }),
            "economic_rows": parsed["economic_rows"],
            "cusip_only_rows": parsed["cusip_only_rows"],
            "identity_missing_rows": parsed["identity_missing_rows"],
            "exact_duplicate_rows": parsed["exact_duplicate_rows"],
            "pit_rule": (
                "symbol/CUSIP observations are usable only after the file knowledge date; "
                "settlement date is not the knowledge date"
            ),
        }

    both = sorted(covered_sets["2018_first_half"] & covered_sets["2026_second_half"])
    either = sorted(covered_sets["2018_first_half"] | covered_sets["2026_second_half"])
    return {
        "phase": "44",
        "status": "PASS_FIXED_SNAPSHOT_IDENTITY_COVERAGE_ONLY",
        "universe_source": (
            "Phase 21C signal-panel ticker snapshot; fixed audit input, not a "
            "date-appropriate historical active universe"
        ),
        "universe_size": len(universe),
        "active_universe_gate_passed": False,
        "files": by_file,
        "coverage_intersection": {
            "covered_in_both_representative_files": len(both),
            "covered_in_both_pct": round(100 * len(both) / len(universe), 3),
            "covered_in_either": len(either),
            "covered_in_either_pct": round(100 * len(either) / len(universe), 3),
            "symbols_covered_in_both": both,
        },
        "interpretation": (
            "Identity/coverage gate only. The denominator is a fixed 335-name snapshot, "
            "not the set of securities active/listed on each historical knowledge date. "
            "Missing symbols are not zero FTD. FTD is an outstanding settlement-fails "
            "balance, not daily short-sale flow or evidence of informed direction."
        ),
        "next_gate": (
            "Build an effective-dated active-universe and deterministic CUSIP/ticker "
            "crosswalk by signal date; distinguish not-active, active-zero, active-positive "
            "and unresolved identity before any return test."
        ),
        "signal_eligible": False,
        "alpha_test_authorized": False,
        "baseline": "F80_TOP20_PARTIAL50_BASELINE_C20",
        "baseline_changed": False,
    }


def main() -> None:
    user_agent = require_user_agent()
    universe = load_universe()
    parsed = {
        label: parse_zip(download(url, user_agent))
        for label, url in FILES.items()
    }
    report = build_report(universe, parsed)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
