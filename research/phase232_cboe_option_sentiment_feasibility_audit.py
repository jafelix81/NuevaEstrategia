#!/usr/bin/env python3
"""Reproducible, documentation-only feasibility audit for Cboe Option Sentiment."""
from __future__ import annotations
import json
from pathlib import Path

SPEC_FIELDS = (
"trade_date","underlying_symbol","call_volume","put_volume","total_volume",
"avg_call_volume","avg_put_volume","avg_total_volume","call_trades","put_trades",
"total_trades","avg_call_size","avg_put_size","underlying_volume","call_premium","put_premium",
"spot_close","split_adj_close","net_option_delta","oi_calls","oi_puts","call_premium_bought",
"call_premium_sold","put_premium_bought","put_premium_sold","calls_bought","puts_bought",
"iv30","hv20","vega_total","cust_volume","firm_volume","mkt_mkr_volume","exch_vol_cboe",
"exch_vol_c2","exch_vol_edgx","exch_vol_bzx","exch_vol_phlx","exch_vol_nom","exch_vol_bxo",
"exch_vol_gem","exch_vol_ise","exch_vol_merc","exch_vol_amex","exch_vol_arca","exch_vol_miax",
"exch_vol_pearl","exch_vol_emld","exch_vol_box","implied_borrow","norm_25d_skew_30","iv90",
"underlying_security_type","otm_call_oi","otm_put_oi","spot_chg","directional_pct","size1",
"size2_10","size11_100","size101_500","size501_1000","size1001up","dtx1","dtx2_5",
"dtx6_30","dtx31_90","dtx91_180","dtx181_360","dtx360up","calls_sold","puts_sold",
"itmcalls","atmcalls","otmcalls","itmputs","atmputs","otmputs","exch_vol_memx","exch_vol_sphr"
)
DIRECTIONAL_FIELDS = (
"net_option_delta","call_premium_bought","call_premium_sold","put_premium_bought",
"put_premium_sold","calls_bought","puts_bought","calls_sold","puts_sold","directional_pct"
)
PARTICIPANT_FIELDS = ("cust_volume","firm_volume","mkt_mkr_volume")
OI_FIELDS = ("oi_calls","oi_puts","otm_call_oi","otm_put_oi")
VOL_SKEW_FIELDS = ("iv30","iv90","hv20","norm_25d_skew_30","vega_total","implied_borrow")
SIZE_FIELDS = ("size1","size2_10","size11_100","size101_500","size501_1000","size1001up")
DTX_FIELDS = ("dtx1","dtx2_5","dtx6_30","dtx31_90","dtx91_180","dtx181_360","dtx360up")
NOT_ADMITTED_FIELDS = ("avg_call_volume","avg_put_volume","avg_total_volume","avg_call_size","avg_put_size",
                       "split_adj_close","hv20","iv30","iv90","implied_borrow","norm_25d_skew_30")

SOURCES = {
    "specification": "https://cdn.cboe.com/resources/data_shop/Option_Sentiment_Data_Spec.pdf",
    "faq": "https://datashop.cboe.com/faqs",
    "early_exercise_research": "https://www.cboe.com/insights/posts/how-early-exercise-order-flow-impacts-equity-option-put-call-ratios",
}

def audit_specification() -> dict:
    unique = len(set(SPEC_FIELDS)) == len(SPEC_FIELDS)
    exact_count = len(SPEC_FIELDS) == 80
    required = {"trade_date","underlying_symbol","underlying_volume","net_option_delta",
                "oi_calls","oi_puts","cust_volume","firm_volume","mkt_mkr_volume",
                "iv30","iv90","norm_25d_skew_30","implied_borrow"}
    return {
        "phase": 232,
        "source": "Cboe DataShop Option Sentiment",
        "spec_version": "v1.4 (05/25)",
        "documented_historical_start": "2012-01 (month precision)",
        "frequency": "daily",
        "documented_fields": len(SPEC_FIELDS),
        "field_count_exactly_80": exact_count,
        "field_names_unique": unique,
        "required_research_fields_present": required.issubset(SPEC_FIELDS),
        "directional_field_count": len(DIRECTIONAL_FIELDS),
        "participant_category_fields": list(PARTICIPANT_FIELDS),
        "open_interest_fields": list(OI_FIELDS),
        "volatility_skew_borrow_fields": list(VOL_SKEW_FIELDS),
        "size_bucket_fields": list(SIZE_FIELDS),
        "days_to_expiration_bucket_fields": list(DTX_FIELDS),
        "documented_universe": {
            "included": ["U.S.-listed stock options","ETF options","index options","OPRA-disseminated options"],
            "excluded": ["options on futures","non-U.S. markets"],
            "all_symbols_includes_proprietary_indices": True,
            "delisted_symbol_continuity_verified": False,
            "daily_symbol_coverage_verified": False
        },
        "availability": {
            "subscription_preliminary": "after trade-date close; target 8-9 p.m. ET",
            "subscription_complete": "next morning; target 5-6 a.m. ET",
            "first_subscription_day": "first day of subscription: preliminary may arrive around same time as complete; both files same content",
            "historical_order_delivery": "complete files delivered at end of order processing day",
            "general_faq_daily_sftp": "typically 00:05-03:00 ET following trade date; may be delayed until after next market open",
            "historical_first_receipt_timestamps_available": False,
            "immutable_correction_vintages_documented": False,
            "receipt_log_required_for_strict_pit": True
        },
        "pit_gates": {
            "history_depth_documented": True,
            "daily_cadence_documented": True,
            "directional_schema_documented": True,
            "broad_us_opra_universe_documented": True,
            "historical_first_receipt": False,
            "correction_vintage_semantics": False,
            "historical_active_delisted_coverage": False,
            "raw_sample_schema_audit": False,
            "pricing_and_license_verified": False
        },
        "fields_not_admitted_until_semantics_verified": list(NOT_ADMITTED_FIELDS),
        "primary_hypothesis": "net_option_delta scaled by underlying_volume adds incremental residual-return information beyond prior returns and frozen LTM/F80",
        "secondary_hypotheses": [
            "large-size versus small-size directional premium/volume imbalance",
            "non-ITM and customer-volume measures are more robust than raw put/call ratios",
            "skew, IV term structure and implied borrow forecast risk/squeeze states rather than assumed equity direction"
        ],
        "data_purchased": False,
        "raw_sample_downloaded": False,
        "pit_admission": False,
        "alpha_admission": False,
        "production_changed": False,
        "f80_changed": False,
        "final_holdout_used": False,
        "overall_status": "CONDITIONAL_HIGH_PRIORITY_CANDIDATE_PIT_BLOCKED",
        "sources": SOURCES
    }

def main() -> int:
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default="phase232_output/phase232_cboe_option_sentiment_feasibility.json")
    args=ap.parse_args()
    result=audit_specification()
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result["field_count_exactly_80"] and result["field_names_unique"] else 1

if __name__=="__main__": raise SystemExit(main())
