#!/usr/bin/env python3
"""Phase 44: SEC FTD frozen-universe identity and continuity audit.

This is a data gate only. It does not test returns or infer direction from FTD.
The frozen 335-symbol universe is a snapshot recovered from the Phase 21C signal
panel and is treated as an audit input, not a change to the production baseline.
"""
from __future__ import annotations

import csv
import io
import json
import re
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

FILES = {
    "2018_first_half": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails201801a.zip",
    "2026_second_half": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails202609b.zip",
}
KNOWLEDGE_DATES = {"2018_first_half": "2018-01-31", "2026_second_half": "2026-10-15"}
EXPECTED_COLUMNS = ("SETTLEMENT DATE", "CUSIP", "SYMBOL", "QUANTITY (FAILS)", "DESCRIPTION", "PRICE")
TRAILER_COUNT_RE = re.compile(r"^Trailer record count\s+(\d+)\s*$", re.I)
TRAILER_QTY_RE = re.compile(r"^Trailer total quantity of shares\s+(\d+)\s*$", re.I)


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "NuevaEstrategia research audit contact research@example.com"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def parse_zip(payload: bytes):
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        raw = zf.read(names[0])
    lines = [line for line in raw.decode("utf-8-sig", errors="replace").splitlines() if line.strip()]
    rows = list(csv.reader(lines, delimiter="|"))
    header = tuple(x.strip().upper() for x in rows[0])
    if header != EXPECTED_COLUMNS:
        raise ValueError(f"unexpected schema: {header!r}")
    symbols = defaultdict(set)
    cusips = defaultdict(set)
    for row in rows[1:]:
        if len(row) != 6:
            continue
        _, cusip, symbol, *_ = [x.strip().upper() for x in row]
        if symbol:
            symbols[symbol].add(cusip)
            if cusip:
                cusips[cusip].add(symbol)
    return symbols, cusips


def load_universe(path: str) -> list[str]:
    with open(path, newline="", encoding="utf-8") as f:
        return [r["Ticker"].strip().upper() for r in csv.DictReader(f) if r.get("Ticker")]


def main() -> None:
    universe = load_universe("research/phase44_frozen_universe_335_tickers.csv")
    if len(universe) != 335 or len(set(universe)) != 335:
        raise SystemExit(f"Expected exactly 335 unique frozen symbols, got {len(universe)}")

    by_file = {}
    for label, url in FILES.items():
        symbols, cusips = parse_zip(download(url))
        present = [t for t in universe if t in symbols]
        missing = [t for t in universe if t not in symbols]
        multi_cusip = {t: sorted(c) for t, c in symbols.items() if t in set(universe) and len(c) > 1}
        by_file[label] = {
            "knowledge_date": KNOWLEDGE_DATES[label],
            "universe_size": len(universe),
            "covered_symbols": len(present),
            "coverage_pct": round(100 * len(present) / len(universe), 3),
            "missing_symbols": missing,
            "multi_cusip_symbols": multi_cusip,
            "distinct_ftd_cusips": len({c for t in present for c in symbols[t] if c}),
            "pit_rule": "symbol/CUSIP observations are usable only after the file knowledge date; settlement date is not the knowledge date",
        }

    covered_both = [t for t in universe if t in by_file["2018_first_half"]["missing_symbols"] is False]
    # Explicit set arithmetic keeps the report auditable without confusing historical absence with bad identity.
    s2018 = set(universe) - set(by_file["2018_first_half"]["missing_symbols"])
    s2026 = set(universe) - set(by_file["2026_second_half"]["missing_symbols"])
    both = sorted(s2018 & s2026)
    either = sorted(s2018 | s2026)

    report = {
        "phase": "44",
        "status": "PASS_IDENTITY_COVERAGE_GATE_CANDIDATE",
        "universe_source": "Phase 21C signal-panel ticker universe snapshot; 335 unique symbols",
        "universe_size": len(universe),
        "files": by_file,
        "coverage_intersection": {
            "covered_in_both_representative_files": len(both),
            "covered_in_both_pct": round(100 * len(both) / len(universe), 3),
            "covered_in_either": len(either),
            "covered_in_either_pct": round(100 * len(either) / len(universe), 3),
            "symbols_covered_in_both": both,
        },
        "interpretation": (
            "This is an identity/coverage gate only. Missing a symbol in a historical FTD file is not automatically a data failure because the frozen universe contains securities that may not have existed/listed at that date. Production alpha requires a date-appropriate active-universe panel and deterministic security identity, not a full 335/335 historical match. No FTD directional interpretation is authorized."
        ),
        "next_gate": "Construct a date-appropriate active-universe/CUSIP crosswalk and quantify coverage by historical signal date before any FTD return test.",
    }
    Path("ftd_universe_coverage_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
