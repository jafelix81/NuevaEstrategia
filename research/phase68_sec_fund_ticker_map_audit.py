#!/usr/bin/env python3
"""Audit current SEC CIK mapping for the frozen 335-name candidate universe."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from research.phase50_form144_global_index_pilot import (
    current_cik_candidates, load_universe,
)

OUT = Path("phase68_sec_fund_ticker_map_audit")
PHASE66_UNRESOLVED = {
    "ARKF", "ARKG", "ARKK", "ARKQ", "ARKW", "BITO", "IEFA", "IWM", "JETS",
    "KRE", "OIH", "SMH", "SOXX", "VEA", "VNQ", "VWO", "XBI", "XLB", "XLE",
    "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY",
}


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "ticker", "mapped", "ciks", "sources", "fund_classes",
        "multiple_cik_candidates", "was_unresolved_in_phase66",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tickers = load_universe()
    ticker_details, cik_to_tickers, unresolved, source_errors = current_cik_candidates(tickers)
    rows = []
    for ticker in tickers:
        item = ticker_details[ticker]
        rows.append({
            "ticker": ticker,
            "mapped": bool(item.get("ciks")),
            "ciks": ";".join(item.get("ciks") or []),
            "sources": ";".join(item.get("sources") or []),
            "fund_classes": json.dumps(item.get("fund_classes") or [], sort_keys=True),
            "multiple_cik_candidates": len(item.get("ciks") or []) > 1,
            "was_unresolved_in_phase66": ticker in PHASE66_UNRESOLVED,
        })
    source_counts = Counter()
    for row in rows:
        for source in filter(None, row["sources"].split(";")):
            source_counts[source] += 1
    newly_mapped = sorted(PHASE66_UNRESOLVED - set(unresolved))
    still_unresolved = sorted(PHASE66_UNRESOLVED & set(unresolved))
    duplicate_cik_tickers = {
        cik: values for cik, values in cik_to_tickers.items() if len(values) > 1
    }
    summary = {
        "phase": "68-sec-fund-ticker-map-repair",
        "status": "COMPLETE",
        "universe_size": len(tickers),
        "mapped_tickers": len(tickers) - len(unresolved),
        "unresolved_tickers": sorted(unresolved),
        "phase66_unresolved_count": len(PHASE66_UNRESOLVED),
        "newly_mapped_vs_phase66": newly_mapped,
        "still_unresolved_from_phase66": still_unresolved,
        "source_ticker_counts": dict(source_counts),
        "candidate_cik_count": len(cik_to_tickers),
        "ciks_shared_by_multiple_tickers": len(duplicate_cik_tickers),
        "shared_cik_tickers": duplicate_cik_tickers,
        "multiple_cik_ticker_count": sum(bool(row["multiple_cik_candidates"]) for row in rows),
        "mapping_source_errors": source_errors,
        "official_mutual_fund_symbol_field_supported": True,
        "historical_pit_mapping": "NOT_ESTABLISHED",
        "fund_series_class_to_security_class_mapping": "NOT_ESTABLISHED",
        "economic_test_authorized": False,
    }
    write_csv(OUT / "ticker_mapping.csv", rows)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if source_errors or len(tickers) != 335 or len(tickers) - len(unresolved) < 308:
        raise RuntimeError("Phase 68 ticker mapping audit failed; inspect artifacts")


if __name__ == "__main__":
    main()
