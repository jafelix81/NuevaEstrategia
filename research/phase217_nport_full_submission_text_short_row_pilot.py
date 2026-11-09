#!/usr/bin/env python3
"""Phase 217: line-referenced SEC N-PORT complete-submission-text pilot.

This validates a manually transcribed evidence fixture. It does NOT download,
hash, or parse the raw SEC submission/XML and does not estimate prevalence or
test returns.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

EVIDENCE_PATH = Path(__file__).with_name(
    "phase217_nport_full_submission_text_short_row_pilot.json"
)


def load_evidence(path: Path = EVIDENCE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_audit(evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    ev = evidence if evidence is not None else load_evidence()
    if ev.get("phase") != 217:
        raise ValueError("Unexpected Phase 217 evidence identity")
    filing = ev["filing"]
    rows = ev["selected_rows"]
    gates = ev["gates"]
    controls = ev["controls"]

    if filing["accession"] != "0001145549-25-033457":
        raise ValueError("Unexpected N-PORT accession")
    if filing["form"] != "NPORT-P" or filing["registrant_cik"] != "0001467631":
        raise ValueError("Unexpected filing identity")
    report_date = date.fromisoformat(filing["period_of_report"])
    filed_date = date.fromisoformat(filing["filing_date"])
    lag = (filed_date - report_date).days
    if lag != filing["report_to_acceptance_lag_calendar_days"] or lag != 58:
        raise ValueError("Report-to-filing lag does not reproduce")
    accepted = datetime.fromisoformat(filing["acceptance_datetime_et"])
    if accepted.date() != filed_date or accepted.strftime("%H:%M:%S") != "16:04:35":
        raise ValueError("SEC-HEADER acceptance timestamp does not reproduce")
    if filing["next_full_session_candidate"] != "2025-05-29":
        raise ValueError("Unexpected conservative next-session candidate")

    if len(rows) != 23:
        raise ValueError("Expected exactly 23 selected, line-referenced examples")
    cusips = [row["cusip"] for row in rows]
    if len(set(cusips)) != len(cusips):
        raise ValueError("Duplicate CUSIP in selected fixture")

    for row in rows:
        for key, expected in ev["row_invariants"].items():
            if key == "balance_negative":
                valid = row["balance"] < 0
            elif key == "val_usd_negative":
                valid = row["val_usd"] < 0
            elif key == "pct_nav_negative":
                valid = row["pct_nav"] < 0
            else:
                valid = row.get(key) == expected
            if not valid:
                raise ValueError(f"Row invariant failed for {row['name']}: {key}")
        if len(row["cusip"]) != 9:
            raise ValueError(f"Selected row has non-nine-character CUSIP: {row['name']}")
        if row["source_line_start"] > row["source_line_end"]:
            raise ValueError(f"Invalid source line range: {row['name']}")

    if controls["raw_submission_sha256_verified"] or controls["raw_primary_xml_sha256_verified"]:
        raise ValueError("Raw hashes must remain unverified in this web-text pilot")
    if controls["alpha_test"] or controls["forward_return_test"] or controls["holdout_used"]:
        raise ValueError("Phase 217 is a source audit only")
    if not controls["f80_frozen"]:
        raise ValueError("Frozen F80 control changed")
    if gates["first_public_receipt_capture"] != "NOT_VERIFIED":
        raise ValueError("First public receipt must remain unverified")
    if gates["effective_dated_cusip_isin_to_listing_crosswalk"] != "NOT_ESTABLISHED":
        raise ValueError("Historical listing crosswalk must remain unadmitted")

    return {
        "phase": 217,
        "audit_as_of": ev["audit_as_of"],
        "status": ev["status"],
        "accession": filing["accession"],
        "fund_name": filing["fund_name"],
        "period_of_report": filing["period_of_report"],
        "accepted_et": filing["acceptance_datetime_et"],
        "report_to_filing_lag_calendar_days": lag,
        "complete_submission_text_lines": filing["complete_submission_text_lines"],
        "complete_submission_text_size_bytes": filing["complete_submission_text_size_bytes"],
        "selected_direct_short_common_equity_examples": len(rows),
        "unique_cusips": len(set(cusips)),
        "all_selected_rows_match_short_ec_corp_us_ns_common_stock": True,
        "raw_submission_sha256_verified": False,
        "raw_primary_xml_sha256_verified": False,
        "first_public_receipt_verified": False,
        "prevalence_estimated": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_frozen": True,
        "decision": ev["decision"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("phase217_output/phase217_nport_full_submission_text_audit_result.json"),
    )
    args = parser.parse_args()
    result = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
