"""Phase 356: encode documented Cboe Open-Close EOD historical convention regimes.

This is a documentation-derived policy matrix, not a raw-data normalizer.
Transforms remain gated until historical samples validate their direction and
field-level semantics. No returns, alpha, PIT-vintage, or production test.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

SUPPORTED_EXCHANGES = ("C1", "C2", "BZX", "EDGX")
C1_START = date(2005, 1, 3)
OTHER_START = date(2018, 1, 2)
C1_OI_SHIFT_END = date(2019, 10, 4)
C2_OI_SHIFT_END = date(2018, 5, 11)
C1_EXCHANGE_VOLUME_OLD_END = date(2019, 10, 4)
C2_INDUSTRY_VOLUME_DOUBLED_END = date(2018, 5, 11)
C1_PREVIOUS_CLOSE_EXCHANGE_ONLY_END = date(2019, 10, 4)
C2_PREVIOUS_CLOSE_EXCHANGE_ONLY_END = date(2018, 5, 11)
C1_GTH_START = date(2023, 12, 11)


def as_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid ISO quote date: {value!r}") from exc


def convention_for(exchange: str, quote_date: str | date) -> dict:
    """Return conservative, field-specific historical convention metadata.

    A caller must not apply any numeric transform solely because this policy
    reports it. The source documentation establishes a convention break, but
    the transform direction and field-level implementation still require
    representative historical-file validation.
    """
    venue = str(exchange or "").strip().upper()
    if venue not in SUPPORTED_EXCHANGES:
        raise ValueError(f"unsupported Cboe exchange: {exchange!r}")
    day = as_date(quote_date)
    start = C1_START if venue == "C1" else OTHER_START
    if day < start:
        raise ValueError(
            f"{venue} Open-Close EOD history is documented from {start.isoformat()}"
        )

    oi_shifted = (
        (venue == "C1" and day <= C1_OI_SHIFT_END)
        or (venue == "C2" and day <= C2_OI_SHIFT_END)
    )
    if oi_shifted:
        oi_regime = "SHIFTED_ONE_DAY_AHEAD_VENDOR_DOCUMENTED"
        oi_feature_gate = "QUARANTINE_DIRECTION_REQUIRES_HISTORICAL_VALIDATION"
    else:
        oi_regime = "START_OF_DAY_CONVENTION_VENDOR_DOCUMENTED"
        oi_feature_gate = "ELIGIBLE_ONLY_AFTER_FILE_AND_RECEIPT_VALIDATION"

    if venue == "C1" and day <= C1_EXCHANGE_VOLUME_OLD_END:
        exchange_volume_factor = 2.0
        exchange_volume_action = "MULTIPLY_BY_2_TO_MATCH_POST_BREAK_FORMULA_PENDING_SAMPLE_VALIDATION"
    else:
        exchange_volume_factor = 1.0
        exchange_volume_action = "NO_DOCUMENTED_SCALE_BREAK"

    if venue == "C2" and day <= C2_INDUSTRY_VOLUME_DOUBLED_END:
        industry_volume_factor = 0.5
        industry_volume_action = "DIVIDE_BY_2_TO_MATCH_POST_BREAK_SCALE_PENDING_SAMPLE_VALIDATION"
    else:
        industry_volume_factor = 1.0
        industry_volume_action = "NO_DOCUMENTED_SCALE_BREAK"

    if (
        (venue == "C1" and day <= C1_PREVIOUS_CLOSE_EXCHANGE_ONLY_END)
        or (venue == "C2" and day <= C2_PREVIOUS_CLOSE_EXCHANGE_ONLY_END)
    ):
        previous_close_scope = "VENUE_ONLY_NOT_INDUSTRY_WIDE"
        previous_close_gate = "DROP_FROM_CROSS_VENUE_FEATURES_OR_REBUILD_INDEPENDENTLY"
    else:
        previous_close_scope = "INDUSTRY_WIDE_VENDOR_DOCUMENTED"
        previous_close_gate = "ELIGIBLE_ONLY_AFTER_FILE_VALIDATION"

    if venue == "C1" and day >= C1_GTH_START:
        session_scope = "RTH_PLUS_GLOBAL_TRADING_HOURS"
    else:
        session_scope = "RTH_ONLY"

    format_regime = (
        "LEGACY_PRE_2011_FORMAT_REQUIRES_LEGACY_PARSER"
        if venue == "C1" and day.year < 2011
        else "POST_2011_FORMAT"
    )

    return {
        "exchange": venue,
        "quote_date": day.isoformat(),
        "documented_history_start": start.isoformat(),
        "format_regime": format_regime,
        "session_scope": session_scope,
        "open_interest_regime": oi_regime,
        "open_interest_feature_gate": oi_feature_gate,
        "total_exchange_volume_normalization_factor_candidate": exchange_volume_factor,
        "total_exchange_volume_action": exchange_volume_action,
        "total_industry_volume_normalization_factor_candidate": industry_volume_factor,
        "total_industry_volume_action": industry_volume_action,
        "previous_close_scope": previous_close_scope,
        "previous_close_feature_gate": previous_close_gate,
        "participant_side_volume_scaling": "UNVERIFIED_DO_NOT_INFER_FROM_TOTAL_EXCHANGE_VOLUME_RULE",
        "total_industry_volume_and_open_interest_quality": "THIRD_PARTY_BEST_EFFORT",
        "delivery_schedule": "OVERNIGHT_AFTER_MIDNIGHT_US_EASTERN",
        "exact_first_receipt_utc_proven": False,
        "historical_correction_vintages_proven": False,
        "numeric_transforms_applied": False,
    }


def audit_matrix() -> dict:
    dates = (
        "2005-01-03", "2010-12-31", "2011-01-03",
        "2018-01-02", "2018-05-11", "2018-05-14",
        "2019-10-04", "2019-10-07",
        "2023-12-08", "2023-12-11",
    )
    rows = []
    rejected_pre_start = []
    for venue in SUPPORTED_EXCHANGES:
        for day in dates:
            try:
                rows.append(convention_for(venue, day))
            except ValueError:
                rejected_pre_start.append({"exchange": venue, "quote_date": day})
    return {
        "phase": 356,
        "status": "DOCUMENTED_POLICY_MATRIX_ONLY_NOT_HISTORICAL_DATA_VALIDATION",
        "source": "Cboe DataShop Open-Close Volume Summary product page and linked EOD/legacy specifications",
        "matrix_rows": rows,
        "pre_history_combinations_rejected": rejected_pre_start,
        "gates": {
            "historical_sample_validation": False,
            "historical_coverage_established": False,
            "pit_vintages_admitted": False,
            "numeric_transforms_applied": False,
            "return_test_authorized": False,
            "alpha_admission": False,
            "holdout_used": False,
            "f80_frozen": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase356_output/regime_matrix.json")
    args = parser.parse_args()
    result = audit_matrix()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PHASE356_STATUS=" + result["status"])
    print("REGIME_ROWS=" + str(len(result["matrix_rows"])))
    print("PRE_HISTORY_REJECTIONS=" + str(len(result["pre_history_combinations_rejected"])))
    print("NUMERIC_TRANSFORMS_APPLIED=0")
    print("PIT_ALPHA_GATES=CLOSED")


if __name__ == "__main__":
    main()
