"""Phase 173: Cboe Option EOD Summary OI temporal semantics and PIT gates.

This module records previously audited public-sample facts and enforces conservative
knowledge-time rules. It does not download licensed data or build alpha features.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PRODUCT_PAGE_HISTORY_START = "2012-01"
FAQ_HISTORY_START = "2010-01"
OI_SEMANTICS = "PREVIOUS_NIGHT_OCC_EOD_AT_START_OF_QUOTE_DATE"
SOURCE = "Cboe Option EOD Summary"

SAMPLE = {
    "audit_origin": "Phase 55 successful hosted audit",
    "run_id": 41763011186,
    "artifact_id": 13290668468,
    "sample_date": "2023-08-25",
    "variants": 2,
    "rows_per_variant": 32672,
    "underlyings": ["^SPX", "SPY", "TSLA", "^VIX"],
    "legacy_335_overlap": 1,
    "base_fields_nonnull_rate": 1.0,
    "calcs_fields_nonnull_rate": 1.0,
    "positive_iv_rate": [0.9275, 0.9126],
    "positive_oi_rate": 0.772,
    "positive_volume_rate": 0.4035,
    "representative_universe_sample": False,
}

def conservative_history_floor(product_page_start: str = PRODUCT_PAGE_HISTORY_START,
                               faq_start: str = FAQ_HISTORY_START) -> str:
    """Use the later published start until the source resolves its discrepancy."""
    for value in (product_page_start, faq_start):
        if len(value) != 7 or value[4] != "-" or not value[:4].isdigit() or not value[5:].isdigit():
            raise ValueError("history_start_must_be_YYYY_MM")
        month = int(value[5:])
        if not 1 <= month <= 12:
            raise ValueError("invalid_history_start_month")
    return max(product_page_start, faq_start)

def _aware_utc(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("knowledge_timestamps_must_be_timezone_aware")
    return parsed.astimezone(timezone.utc)

def feature_knowledge_time(occ_available_at: Optional[str],
                           file_first_received_at: Optional[str],
                           identity_map_available_at: Optional[str]) -> dict:
    """A feature is eligible only when all required availability timestamps exist."""
    raw = (occ_available_at, file_first_received_at, identity_map_available_at)
    if any(value is None for value in raw):
        return {"eligible": False, "knowledge_time_utc": None,
                "reason": "MISSING_REQUIRED_AVAILABILITY_TIMESTAMP"}
    parsed = [_aware_utc(value) for value in raw]
    latest = max(parsed)
    return {"eligible": True, "knowledge_time_utc": latest.isoformat(),
            "reason": "MAX_OF_OCC_FILE_RECEIPT_AND_IDENTITY_MAP"}

def build_audit() -> dict:
    return {
        "phase": 173,
        "source": SOURCE,
        "product_page_history_start": PRODUCT_PAGE_HISTORY_START,
        "faq_history_start": FAQ_HISTORY_START,
        "conservative_history_floor": conservative_history_floor(),
        "oi_semantics": OI_SEMANTICS,
        "oi_static_during_session": True,
        "oi_is_same_day_close_measure": False,
        "sample": SAMPLE,
        "sample_schema_status": "PASS_PHASE55_PUBLIC_SAMPLE_ONLY",
        "broad_pit_universe_coverage": "NOT_TESTED",
        "historical_first_receipt_vintages": "BLOCKED_UNVERIFIED",
        "licensing_and_price": "NOT_CONFIRMED",
        "pit_admission": False,
        "alpha_admission": False,
        "forward_returns_tested": False,
        "bootstrap_loo_tested": False,
        "chronological_oos_tested": False,
        "final_holdout_used": False,
        "production_changed": False,
        "f80_changed": False,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase173_output/phase173_option_eod_oi_pit_semantics.json")
    args = parser.parse_args()
    result = build_audit()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
