#!/usr/bin/env python3
"""Fail-closed field-dimensionality and semantics audit for Cboe Option Sentiment."""
from __future__ import annotations
import json
from pathlib import Path

try:
    from .phase232_cboe_option_sentiment_feasibility_audit import SPEC_FIELDS
except ImportError:
    from phase232_cboe_option_sentiment_feasibility_audit import SPEC_FIELDS

SPEC_URL = "https://datashop.cboe.com/Documents/Cboe_OptionSentiment_Specs.pdf"
FAQ_URL = "https://datashop.cboe.com/faqs"
EARLY_EXERCISE_URL = "https://www.cboe.com/insights/posts/how-early-exercise-order-flow-impacts-equity-option-put-call-ratios"

NOTE2_BLANK_FIELDS = (
    "avg_call_size", "avg_put_size", "cust_volume", "firm_volume", "mkt_mkr_volume",
    "size1", "size2_10", "size11_100", "size101_500", "size501_1000", "size1001up",
)
FOOTNOTE_MARKERS = {
    "net_option_delta": 2,
    "call_premium_bought": 3,
    "call_premium_sold": 3,
    "put_premium_bought": 3,
    "put_premium_sold": 3,
    "calls_bought": 3,
    "puts_bought": 3,
    "calls_sold": 2,
    "puts_sold": 2,
    "avg_call_size": 2,
    "avg_put_size": 2,
    "cust_volume": 2,
    "firm_volume": 2,
    "mkt_mkr_volume": 2,
}
DIRECTIONAL_DESCRIPTION_FIELDS = (
    "net_option_delta", "call_premium_bought", "call_premium_sold",
    "put_premium_bought", "put_premium_sold", "calls_bought", "puts_bought",
    "calls_sold", "puts_sold",
)
NOTE3_RULE_FIELDS = ("net_option_delta",)
PARTICIPANT_FIELDS = ("cust_volume", "firm_volume", "mkt_mkr_volume")
SIZE_FIELDS = ("size1", "size2_10", "size11_100", "size101_500", "size501_1000", "size1001up")
DTX_FIELDS = ("dtx1", "dtx2_5", "dtx6_30", "dtx31_90", "dtx91_180", "dtx181_360", "dtx360up")
MONEYNESS_FIELDS = ("itmcalls", "atmcalls", "otmcalls", "itmputs", "atmputs", "otmputs")
OI_FIELDS = ("oi_calls", "oi_puts", "otm_call_oi", "otm_put_oi")
NON_DIRECTIONAL_MONEYNESS_FIELDS = MONEYNESS_FIELDS
DELTA_UNITS_SPECIFIED = False
DELTA_SIGN_CONVENTION_SPECIFIED = False
DELTA_MULTIPLIER_AND_DELIVERABLE_RULE_SPECIFIED = False
DIRECTIONAL_PCT_DENOMINATOR_SPECIFIED = False
CANCELLED_TRADE_FIELD_SCOPE_SPECIFIED = False

def audit_specification() -> dict:
    fields = set(SPEC_FIELDS)
    mismatch = [
        field for field in ("net_option_delta", "calls_sold", "puts_sold")
        if FOOTNOTE_MARKERS.get(field) == 2 and field not in NOTE2_BLANK_FIELDS
    ]
    checks = {
        "exactly_80_fields": len(SPEC_FIELDS) == 80,
        "unique_field_names": len(fields) == 80,
        "note2_blank_fields_exist": set(NOTE2_BLANK_FIELDS).issubset(fields),
        "all_directional_description_fields_exist": set(DIRECTIONAL_DESCRIPTION_FIELDS).issubset(fields),
        "participant_fields_exist": set(PARTICIPANT_FIELDS).issubset(fields),
        "size_fields_exist": set(SIZE_FIELDS).issubset(fields),
        "dtx_fields_exist": set(DTX_FIELDS).issubset(fields),
        "moneyness_fields_exist": set(MONEYNESS_FIELDS).issubset(fields),
        "oi_fields_exist": set(OI_FIELDS).issubset(fields),
    }
    return {
        "phase": 233,
        "source": "Cboe DataShop Option Sentiment",
        "spec_version": "v1.4 (05/25)",
        "specification_url": SPEC_URL,
        "faq_url": FAQ_URL,
        "early_exercise_research_url": EARLY_EXERCISE_URL,
        "documented_field_count": len(SPEC_FIELDS),
        "checks": checks,
        "all_schema_checks_pass": all(checks.values()),
        "footnote_cross_reference": {
            "note2_blank_fields": list(NOTE2_BLANK_FIELDS),
            "note3_direction_rule": "Above midpoint = buy; below midpoint = sell; spread, late, and tied trades excluded.",
            "note4_cancel_rule": "Cancelled trades are backed out from the totals; field-specific scope is not enumerated.",
            "field_markers": FOOTNOTE_MARKERS,
            "mismatched_fields": mismatch,
            "mismatch_count": len(mismatch),
            "interpretation": "Documentation cross-reference inconsistency; not evidence that the raw values are wrong."
        },
        "field_dimensionality": {
            "directional_aggregate_fields": list(DIRECTIONAL_DESCRIPTION_FIELDS),
            "participant_category_fields": list(PARTICIPANT_FIELDS),
            "size_bucket_fields": list(SIZE_FIELDS),
            "dtx_bucket_fields": list(DTX_FIELDS),
            "moneyness_fields": list(MONEYNESS_FIELDS),
            "open_interest_fields": list(OI_FIELDS),
            "direction_by_participant_available": False,
            "direction_by_size_available": False,
            "direction_by_dtx_available": False,
            "direction_by_moneyness_available": False,
            "customer_call_put_buy_sell_cross_tab_available": False,
            "non_itm_put_call_volume_computable": True,
            "non_itm_put_call_is_directional": False,
            "participant_categories_identify_beneficial_owners": False
        },
        "primary_feature": {
            "field": "net_option_delta",
            "status": "SUSPENDED_PENDING_PROVIDER_CLARIFICATION",
            "units_specified": DELTA_UNITS_SPECIFIED,
            "sign_convention_specified": DELTA_SIGN_CONVENTION_SPECIFIED,
            "multiplier_and_deliverable_rule_specified": DELTA_MULTIPLIER_AND_DELIVERABLE_RULE_SPECIFIED,
            "normalization_by_underlying_volume_authorized": False
        },
        "hypothesis_decisions": [
            {"hypothesis": "net option delta adds residual-return information", "decision": "SUSPEND", "reason": "Units, sign, multiplier/deliverable and field-specific methodology are unspecified."},
            {"hypothesis": "large-size directional flow", "decision": "KILL_UNIMPLEMENTABLE", "reason": "Size buckets are total volume, not side-specific."},
            {"hypothesis": "customer net directional flow", "decision": "KILL_UNIMPLEMENTABLE", "reason": "OCC participant volume is not cross-tabbed by call/put or buy/sell."},
            {"hypothesis": "non-ITM put/call volume", "decision": "NON_DIRECTIONAL_CONTROL_ONLY", "reason": "Moneyness fields provide total call/put volume without buy/sell side."},
            {"hypothesis": "participant mix", "decision": "CONTEXT_ONLY", "reason": "Clearing categories do not identify beneficial owners or informed investors."},
            {"hypothesis": "IV, skew and implied borrow", "decision": "SEPARATE_RISK_STATE_HYPOTHESES", "reason": "Do not presume equity-direction alpha."},
            {"hypothesis": "open interest", "decision": "PRIOR_NIGHT_STATE_ONLY", "reason": "Cboe FAQ specifies previous-night OCC EOD OI, static intraday."}
        ],
        "availability": {
            "subscription_preliminary_target": "8-9 p.m. ET after trade-date close",
            "subscription_complete_target": "5-6 a.m. ET next morning",
            "first_subscription_day": "Preliminary and complete may be generated around the same time with identical content.",
            "historical_order_delivery": "Complete files delivered at end of order-processing day.",
            "general_faq_daily_sftp": "Typically 00:05-03:00 ET next day; delays may extend past next market open.",
            "historical_first_receipt_logs_verified": False,
            "immutable_correction_vintages_verified": False,
            "strict_pit_admission": False
        },
        "sample": {
            "public_raw_sample_found_in_reviewed_documentation": False,
            "raw_sample_downloaded": False,
            "representative_date_symbol_coverage_verified": False
        },
        "data_purchased": False,
        "vendor_contacted": False,
        "alpha_test_run": False,
        "bootstrap_or_loo_run": False,
        "chronological_oos_run": False,
        "final_holdout_used": False,
        "production_changed": False,
        "f80_changed": False,
        "overall_status": "SCHEMA_DIMENSIONS_REDUCED_PRIMARY_FEATURE_SUSPENDED_PIT_BLOCKED",
    }

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase233_output/phase233_cboe_option_sentiment_semantics.json")
    args = parser.parse_args()
    result = audit_specification()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_schema_checks_pass"] and result["footnote_cross_reference"]["mismatch_count"] == 3 else 1

if __name__ == "__main__":
    raise SystemExit(main())
