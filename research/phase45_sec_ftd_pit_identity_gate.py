#!/usr/bin/env python3
"""Phase 45: SEC FTD PIT identity feasibility gate.

This phase deliberately does NOT run alpha tests. It asks whether public SEC
FTD files can establish a date-appropriate active universe and deterministic
CUSIP identity without treating missing symbols as zero.
"""
from __future__ import annotations

import csv
import io
import json
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

UNIVERSE_PATH = "research/phase44_frozen_universe_335_tickers.csv"
# Representative first-half January files. The file itself is knowable only
# after SEC publication; the exact cutoff is recorded explicitly below.
SAMPLES = {
    "2018_01a": {
        "url": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails201801a.zip",
        "knowledge_date": "2018-01-31",
    },
    "2020_01a": {
        "url": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails202001a.zip",
        "knowledge_date": "2020-01-31",
    },
    "2022_01a": {
        "url": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails202201a.zip",
        "knowledge_date": "2022-01-31",
    },
    "2024_01a": {
        "url": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails202401a.zip",
        "knowledge_date": "2024-01-31",
    },
    "2026_01a": {
        "url": "https://www.sec.gov/files/data/fails-deliver-data/cnsfails202601a.zip",
        "knowledge_date": "2026-01-31",
    },
}
EXPECTED = ("SETTLEMENT DATE", "CUSIP", "SYMBOL", "QUANTITY (FAILS)", "DESCRIPTION", "PRICE")


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "NuevaEstrategia research audit contact research@example.com"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def parse(payload: bytes):
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        raw = zf.read(names[0])
    rows = list(csv.reader([x for x in raw.decode("utf-8-sig", errors="replace").splitlines() if x.strip()], delimiter="|"))
    header = tuple(x.strip().upper() for x in rows[0])
    if header != EXPECTED:
        raise ValueError(f"unexpected schema {header!r}")
    out = defaultdict(set)
    for row in rows[1:]:
        if len(row) != 6:
            continue
        _, cusip, symbol, *_ = [x.strip().upper() for x in row]
        if symbol:
            out[symbol].add(cusip)
    return out


def main() -> None:
    with open(UNIVERSE_PATH, newline="", encoding="utf-8") as f:
        universe = [r["Ticker"].strip().upper() for r in csv.DictReader(f) if r.get("Ticker")]
    if len(universe) != 335 or len(set(universe)) != 335:
        raise SystemExit(f"expected 335 unique tickers, got {len(universe)}")
    U = set(universe)

    reports = {}
    observed = {}
    for label, meta in SAMPLES.items():
        symbols = parse(download(meta["url"]))
        present = sorted(U & set(symbols))
        observed[label] = set(present)
        reports[label] = {
            "knowledge_date": meta["knowledge_date"],
            "covered_symbols": len(present),
            "coverage_pct": round(100 * len(present) / len(U), 3),
            "missing_symbols": sorted(U - set(present)),
            "cusip_count_for_covered_symbols": sum(len(symbols[t]) for t in present),
        }

    # A conservative observable-only panel: names observed in every sample.
    always_observed = set.intersection(*observed.values())
    ever_observed = set.union(*observed.values())

    # CUSIP continuity is reported, but it is not treated as proof that a
    # security was continuously listed when FTD is absent.
    parsed_all = {label: parse(download(meta["url"])) for label, meta in SAMPLES.items()}
    same_cusip_2018_2026 = []
    changed_or_unresolved = []
    for t in sorted(always_observed):
        c18 = parsed_all["2018_01a"].get(t, set())
        c26 = parsed_all["2026_01a"].get(t, set())
        if c18 & c26:
            same_cusip_2018_2026.append(t)
        else:
            changed_or_unresolved.append(t)

    report = {
        "phase": "45",
        "status": "COMPLETE",
        "gate": "FAIL_ACTIVE_UNIVERSE_IDENTITY_NOT_PROVABLE_FROM_PUBLIC_FTD_ALONE",
        "alpha_authorized": False,
        "universe_size": 335,
        "samples": reports,
        "always_observed_count": len(always_observed),
        "always_observed_pct": round(100 * len(always_observed) / 335, 3),
        "ever_observed_count": len(ever_observed),
        "ever_observed_pct": round(100 * len(ever_observed) / 335, 3),
        "cusip_same_2018_2026_among_always_observed": len(same_cusip_2018_2026),
        "cusip_changed_or_unresolved_among_always_observed": len(changed_or_unresolved),
        "interpretation": (
            "FTD files have broad observable coverage, but a missing ticker/CUSIP observation cannot distinguish inactive/unlisted security from an active security with zero fails. CUSIP continuity among observed names does not solve this missing-zero problem. Restricting alpha to always-observed names would introduce survivorship/selection bias and is therefore prohibited."
        ),
        "decision": "PARK_FOR_PUBLIC_DATA_ALPHA",
        "required_to_reopen": "A deterministic historical security-master/listing-status source with PIT-effective dates, or an independently validated historical active-universe panel. Do not infer activity from current ticker lists or from FTD presence alone.",
        "baseline_protection": "F80_TOP20_PARTIAL50_BASELINE_C20 unchanged; no returns, ranking, holding-period, or exposure rules tested or changed.",
    }
    Path("ftd_pit_identity_gate.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0)


if __name__ == "__main__":
    main()
