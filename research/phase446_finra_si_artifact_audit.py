#!/usr/bin/env python3
"""Audit completeness risks in a Phase 31 FINRA short-interest artifact ZIP.

The script never treats absent symbols as zero. It detects whether successful
settlement pulls hit the documented synchronous API row ceiling and whether the
artifact preserves metadata needed to prove a complete snapshot.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


def _csv_rows(zf: zipfile.ZipFile, member: str) -> list[dict[str, str]]:
    with zf.open(member, "r") as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        return list(csv.DictReader(text))


def audit_artifact(path: str | Path, sync_cap: int = 5000) -> dict[str, Any]:
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        required = {"si_download_audit.csv", "short_interest_features.csv"}
        missing = sorted(required - names)
        if missing:
            raise ValueError(f"Missing required artifact members: {missing}")
        audit = _csv_rows(zf, "si_download_audit.csv")
        features = _csv_rows(zf, "short_interest_features.csv")

    success = [r for r in audit if (r.get("status") or "").lower() == "ok"]
    errors = [r for r in audit if (r.get("status") or "").lower() != "ok"]
    row_counts = Counter(int(r.get("rows") or 0) for r in success)
    cap_hits = [r for r in success if int(r.get("rows") or 0) >= sync_cap]

    tickers = sorted({(r.get("Ticker") or r.get("symbolCode") or "").strip() for r in features} - {""})
    initials = Counter(t[0].upper() for t in tickers if t)
    settlement_dates = sorted({(r.get("settlementDate") or r.get("Date") or "").strip() for r in features} - {""})
    qty_values = []
    for row in features:
        raw = row.get("currentShortPositionQuantity")
        if raw not in (None, ""):
            try:
                qty_values.append(float(raw))
            except ValueError:
                pass

    audit_fields = set(audit[0]) if audit else set()
    metadata_candidates = {
        "record_total": {"recordTotal", "record_total", "record_total_count"},
        "record_offset": {"recordOffset", "record_offset"},
        "record_limit": {"recordLimit", "record_limit"},
        "async_request_id": {"requestId", "request_id", "asyncRequestId"},
        "pagination_complete": {"paginationComplete", "pagination_complete"},
    }
    metadata_saved = {
        key: bool(fields & audit_fields) for key, fields in metadata_candidates.items()
    }

    all_success_at_cap = bool(success) and len(cap_hits) == len(success)
    complete_snapshot_proven = (
        bool(success)
        and not errors
        and not cap_hits
        and metadata_saved["record_total"]
        and (metadata_saved["pagination_complete"] or metadata_saved["record_offset"])
    )

    observed_initials = sorted(initials)
    alphabetical_prefix_likely = bool(observed_initials) and observed_initials[-1] <= "D"
    return {
        "audit_rows": len(audit),
        "successful_settlement_requests": len(success),
        "failed_settlement_requests": len(errors),
        "successful_response_row_counts": dict(sorted(row_counts.items())),
        "successful_requests_at_or_above_sync_cap": len(cap_hits),
        "sync_cap": sync_cap,
        "all_successful_requests_hit_sync_cap": all_success_at_cap,
        "failed_settlements": [r.get("settlementDate") for r in errors],
        "feature_rows": len(features),
        "feature_settlement_dates": len(settlement_dates),
        "feature_date_min": settlement_dates[0] if settlement_dates else None,
        "feature_date_max": settlement_dates[-1] if settlement_dates else None,
        "observed_unique_tickers": len(tickers),
        "observed_ticker_initials": dict(sorted(initials.items())),
        "alphabetical_prefix_through_D_likely": alphabetical_prefix_likely,
        "nonpositive_current_short_quantity_rows": sum(q <= 0 for q in qty_values),
        "audit_metadata_saved": metadata_saved,
        "complete_snapshot_proven": complete_snapshot_proven,
        "zero_inference_allowed": complete_snapshot_proven,
        "classification": (
            "POTENTIALLY_TRUNCATED_AT_SYNC_CAP"
            if all_success_at_cap
            else "INCOMPLETE_OR_UNVERIFIED"
            if not complete_snapshot_proven
            else "COMPLETE_SNAPSHOT_EVIDENCE_PRESENT"
        ),
        "interpretation": (
            "Observed symbols are a subset from capped responses; do not interpret symbol absence as zero or as full-universe coverage."
            if not complete_snapshot_proven
            else "Snapshot completeness evidence is present; still require effective-dated security eligibility before zero inference."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip")
    parser.add_argument("--sync-cap", type=int, default=5000)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = audit_artifact(args.artifact_zip, args.sync_cap)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
