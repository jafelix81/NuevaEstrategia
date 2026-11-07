#!/usr/bin/env python3
"""Phase 169: Cboe Option Sentiment specification and PIT feasibility audit."""
from __future__ import annotations
import argparse, json
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo

SOURCE = "Cboe Option Sentiment"
SPEC_VERSION = "v1.4 0525"
ADVERTISED_HISTORY_START = "2012-01"
ET = ZoneInfo("America/New_York")

FIELDS = (
"trade_date","underlying_symbol","call_volume","put_volume","total_volume",
"avg_call_volume","avg_put_volume","avg_total_volume","call_trades","put_trades",
"total_trades","avg_call_size","avg_put_size","underlying_volume","call_premium",
"put_premium","spot_close","split_adj_close","net_option_delta","oi_calls","oi_puts",
"call_premium_bought","call_premium_sold","put_premium_bought","put_premium_sold",
"calls_bought","puts_bought","iv30","hv20","vega_total","cust_volume","firm_volume",
"mkt_mkr_volume","exch_vol_cboe","exch_vol_c2","exch_vol_edgx","exch_vol_bzx",
"exch_vol_phlx","exch_vol_nom","exch_vol_bxo","exch_vol_gem","exch_vol_ise",
"exch_vol_merc","exch_vol_amex","exch_vol_arca","exch_vol_miax","exch_vol_pearl",
"exch_vol_emld","exch_vol_box","implied_borrow","norm_25d_skew_30","iv90",
"underlying_security_type","otm_call_oi","otm_put_oi","spot_chg","directional_pct",
"size1","size2_10","size11_100","size101_500","size501_1000","size1001up",
"dtx1","dtx2_5","dtx6_30","dtx31_90","dtx91_180","dtx181_360","dtx360up",
"calls_sold","puts_sold","itmcalls","atmcalls","otmcalls","itmputs","atmputs",
"otmputs","exch_vol_memx","exch_vol_sphr",
)
DATE_FIELDS=frozenset({"trade_date"})
STRING_FIELDS=frozenset({"underlying_symbol","underlying_security_type"})
FLOAT_FIELDS=frozenset({
"avg_call_size","avg_put_size","call_premium","put_premium","spot_close",
"split_adj_close","net_option_delta","call_premium_bought","call_premium_sold",
"put_premium_bought","put_premium_sold","iv30","hv20","implied_borrow",
"norm_25d_skew_30","iv90","spot_chg","directional_pct",
})
INTEGER_FIELDS=frozenset(FIELDS)-DATE_FIELDS-STRING_FIELDS-FLOAT_FIELDS
OPTIONAL_BLANK_FIELDS=frozenset({
"avg_call_size","avg_put_size","cust_volume","firm_volume","mkt_mkr_volume",
"size1","size2_10","size11_100","size101_500","size501_1000","size1001up",
})
EXCHANGE_VOLUME_FIELDS=tuple(x for x in FIELDS if x.startswith("exch_vol_"))
CANDIDATE_FEATURES={
"signed_directional_premium":"(call_premium_bought-call_premium_sold)-(put_premium_bought-put_premium_sold)",
"net_option_delta":"vendor midpoint-relative directional-trade estimate",
"directional_activity_share":"directional_pct / 100; source uses percentage points",
"volatility_context":"iv30, iv90, norm_25d_skew_30, hv20, implied_borrow",
"opening_oi_state":"oi_calls, oi_puts, otm_call_oi, otm_put_oi; prior-night OCC state",
"clearing_capacity_mix":"cust_volume, firm_volume, mkt_mkr_volume; not owner identity",
}
KNOWN_PIT_BLOCKERS=(
"current orderability unconfirmed; legacy product route redirects to DataShop home",
"no public sample located",
"no immutable historical first-receipt or preliminary/final vintage log",
"product-specific delivery schedule conflicts with general DataShop SFTP timing guidance",
"no effective-dated permanent underlying identifier or delisted-name coverage established",
"vendor 20-session averages have undocumented window endpoint semantics",
"split-adjusted close has no demonstrated historical as-of adjustment vintage",
)

def schema_audit(headers):
    raw=[str(x).strip() for x in headers]
    counts=Counter(raw)
    duplicates=sorted(k for k,v in counts.items() if v>1)
    observed=set(raw); expected=set(FIELDS)
    missing=sorted(expected-observed); extra=sorted(observed-expected)
    ok=not duplicates and not missing and not extra and len(raw)==len(FIELDS)
    return {"status":"PASS_SPEC_SCHEMA" if ok else "FAIL_SPEC_SCHEMA",
            "expected_fields":len(FIELDS),"observed_fields":len(raw),
            "missing_fields":missing,"extra_fields":extra,"duplicate_fields":duplicates}

def directional_pct_fraction(value):
    try: x=Decimal(str(value))
    except (InvalidOperation,ValueError) as exc: raise ValueError("directional_pct_not_numeric") from exc
    if not x.is_finite() or x<0 or x>100: raise ValueError("directional_pct_out_of_percentage_point_range")
    return x/Decimal("100")

def signed_directional_premium(row):
    names=("call_premium_bought","call_premium_sold","put_premium_bought","put_premium_sold")
    vals=[]
    for name in names:
        raw=row.get(name)
        if raw is None or str(raw).strip()=="": return None
        try: val=Decimal(str(raw))
        except (InvalidOperation,ValueError) as exc: raise ValueError(f"invalid_premium:{name}") from exc
        if not val.is_finite(): raise ValueError(f"invalid_premium:{name}")
        vals.append(val)
    cb,cs,pb,ps=vals
    return (cb-cs)-(pb-ps)

def _aware_iso(value,label):
    try: parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc: raise ValueError(f"{label}_invalid_iso_timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None: raise ValueError(f"{label}_timezone_required")
    return parsed.astimezone(ET)

def knowledge_time_gate(trade_date,first_received_at,decision_at):
    try: day=date.fromisoformat(trade_date)
    except ValueError as exc: raise ValueError("trade_date_invalid") from exc
    received=_aware_iso(first_received_at,"first_received_at")
    decision=_aware_iso(decision_at,"decision_at")
    if received.date()<day: raise ValueError("receipt_precedes_trade_date")
    if decision<received: raise ValueError("decision_precedes_first_receipt")
    if decision.date()<=day: raise ValueError("same_trade_date_decision_not_allowed")
    return {"eligible":True,"trade_date":day.isoformat(),
            "first_received_at_et":received.isoformat(),"decision_at_et":decision.isoformat(),
            "knowledge_time_basis":"ACTUAL_FIRST_RECEIPT","same_day_use":False,
            "next_session_calendar_validation":"NOT_IMPLEMENTED"}

def build_summary():
    return {"phase":169,"source":SOURCE,"audit_status":"PASS_SPECIFICATION_FEASIBILITY_ONLY",
            "specification":SPEC_VERSION,"advertised_history_start":ADVERTISED_HISTORY_START,
            "spec_field_count":len(FIELDS),"field_count_unique":len(set(FIELDS)),
            "exchange_volume_field_count":len(EXCHANGE_VOLUME_FIELDS),
            "optional_blank_field_count":len(OPTIONAL_BLANK_FIELDS),
            "public_sample_found":False,"current_orderability":"UNCONFIRMED",
            "historical_coverage_complete":False,"first_receipt_proven":False,
            "strict_pit":False,"alpha_admission":False,
            "candidate_feature_names":list(CANDIDATE_FEATURES),
            "known_pit_blockers":list(KNOWN_PIT_BLOCKERS),
            "data_purchase_or_vendor_contact":False,"production_change":False,"f80_change":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",default="phase169_output")
    args=parser.parse_args()
    summary=build_summary(); out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"phase169_cboe_option_sentiment_feasibility.json").write_text(
        json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
