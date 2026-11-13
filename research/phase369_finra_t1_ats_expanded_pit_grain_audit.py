#!/usr/bin/env python3
"""Phase 369: expand FINRA T1 ATS date-field and symbol/firm bridge audit.

Nineteen stratified historic T1 weeks are retrieved in full. The audit tests
whether ATS summary rows retain initial publication-date values and whether
ATS symbol aggregates reconcile to firm-grain rows using the only safe
symbol-level bridge: one unambiguous aggregate row with one nonmissing
productTypeCode per symbol. Firm rows do not carry productTypeCode, so the
field is never used as a fabricated firm-row key.

Only aggregate counts and distributions are written. No raw rows, symbols,
MPIDs, CRDs or firm names are retained. No returns or alpha tests are run.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests

BASE_URL="https://api.finra.org/data/group/otcmarket/name/weeklySummaryHistoric"
PAGE_LIMIT=5000
MAX_OFFSET=500000
WEEKS=(
    "2021-11-15",
    "2022-01-03","2022-04-04","2022-07-11","2022-10-03",
    "2023-01-09","2023-04-03","2023-07-10","2023-10-02",
    "2024-01-08","2024-04-01","2024-07-08","2024-10-07",
    "2025-01-06","2025-04-07","2025-07-07","2025-10-06",
    "2025-10-20","2025-11-10",
)
TIER="T1"
ATS_AGG="ATS_W_SMBL"
ATS_FIRM="ATS_W_SMBL_FIRM"
ATS_TYPES={"ATS_W_FIRM","ATS_W_SMBL","ATS_W_SMBL_FIRM","ATS_W_VOL_STATS"}
DATE_FIELDS=("weekStartDate","initialPublishedDate","lastUpdateDate","lastReportedDate")


def norm(value):
    return str(value or "").strip().upper()


def parse_date(value):
    if value is None or str(value).strip()=="":
        return None
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def parse_integer(value):
    if value is None or str(value).strip()=="":
        return None
    try:
        x=Decimal(str(value).replace(",","").strip())
    except (InvalidOperation,ValueError):
        return None
    if not x.is_finite() or x<0 or x!=x.to_integral_value():
        return None
    return int(x)


def build_query(week,limit,offset):
    return {
        "compareFilters":[
            {"fieldName":"historicalWeek","fieldValue":week,"compareType":"EQUAL"},
            {"fieldName":"tierIdentifier","fieldValue":TIER,"compareType":"EQUAL"},
        ],
        "limit":limit,
        "offset":offset,
    }


def parse_rows(payload):
    if isinstance(payload,list):
        return [x for x in payload if isinstance(x,dict)]
    if isinstance(payload,dict):
        if payload.get("message") or payload.get("statusCode"):
            raise RuntimeError("FINRA returned an error envelope")
        data=payload.get("data",[])
        if isinstance(data,dict):
            data=data.get("data",[])
        if isinstance(data,list):
            return [x for x in data if isinstance(x,dict)]
        if data in (None,""):
            return []
    raise RuntimeError("Unexpected FINRA response envelope")


def request_page(session,week,offset):
    body=build_query(week,PAGE_LIMIT,offset)
    for attempt in range(4):
        try:
            response=session.post(BASE_URL,json=body,timeout=(20,120))
            if response.status_code in {408,429,500,502,503,504}:
                if attempt==3:
                    response.raise_for_status()
                retry=response.headers.get("Retry-After")
                try: delay=float(retry) if retry else 2**(attempt+1)
                except (TypeError,ValueError): delay=2**(attempt+1)
                time.sleep(max(0,min(delay,30)))
                continue
            response.raise_for_status()
            rows=parse_rows(response.json())
            headers={str(k).lower():v for k,v in response.headers.items()}
            if "record-total" not in headers:
                raise RuntimeError("Missing Record-Total")
            if "record-offset" in headers and int(headers["record-offset"])!=offset:
                raise RuntimeError("Record-Offset mismatch")
            if int(headers.get("total-records-on-page",len(rows)))!=len(rows):
                raise RuntimeError("Total-Records-On-Page mismatch")
            if len(rows)>PAGE_LIMIT:
                raise RuntimeError("Page exceeded requested limit")
            return rows,int(headers["record-total"])
        except (requests.RequestException,ValueError) as exc:
            if attempt==3:
                raise RuntimeError(f"FINRA request failed ({type(exc).__name__})") from exc
            time.sleep(min(2**(attempt+1),20))
    raise RuntimeError("FINRA request retries exhausted")


def fetch_partition(session,week):
    rows=[]
    offset=0
    total=None
    pages=0
    while True:
        batch,record_total=request_page(session,week,offset)
        if total is None:
            total=record_total
        elif total!=record_total:
            raise RuntimeError("Record-Total changed during pagination")
        pages+=1
        rows.extend(batch)
        print(f"[Phase369] {week} offset={offset} rows={len(batch)} total={record_total}",flush=True)
        if len(rows)==total:
            break
        if len(rows)>total:
            raise RuntimeError("Retrieved rows exceeded Record-Total")
        if not batch:
            raise RuntimeError("Pagination made no progress")
        offset+=len(batch)
        if offset>MAX_OFFSET:
            raise RuntimeError("Offset exceeded FINRA maximum")
        time.sleep(0.15)
    return rows,total,pages


class GapStats:
    def __init__(self):
        self.rows=0
        self.missing_base=0
        self.missing_target=0
        self.invalid=0
        self.gaps=[]

    def add(self,base_raw,target_raw):
        self.rows+=1
        if base_raw is None or str(base_raw).strip()=="":
            self.missing_base+=1
        if target_raw is None or str(target_raw).strip()=="":
            self.missing_target+=1
        if base_raw is None or target_raw is None or str(base_raw).strip()=="" or str(target_raw).strip()=="":
            return
        base=parse_date(base_raw); target=parse_date(target_raw)
        if base is None or target is None:
            self.invalid+=1
            return
        self.gaps.append((target-base).days)

    def summary(self):
        values=sorted(self.gaps)
        def q(p):
            if not values:return None
            idx=max(0,min(len(values)-1,int((len(values)*p+0.999999999))-1))
            return values[idx]
        positive=sum(x>0 for x in values)
        return {
            "rows":self.rows,
            "comparable":len(values),
            "missing_base":self.missing_base,
            "missing_target":self.missing_target,
            "invalid":self.invalid,
            "positive_gap_rows":positive,
            "positive_gap_pct":round(100*positive/len(values),4) if values else None,
            "zero_gap_rows":sum(x==0 for x in values),
            "negative_gap_rows":sum(x<0 for x in values),
            "p50_days":q(.50),
            "p90_days":q(.90),
            "p95_days":q(.95),
            "p99_days":q(.99),
            "maximum_days":max(values) if values else None,
            "minimum_days":min(values) if values else None,
        }


def audit_ats_bridge(rows):
    aggregates=defaultdict(list)
    firms=defaultdict(list)
    missing_aggregate_symbol=0
    missing_firm_symbol=0
    for row in rows:
        typ=norm(row.get("summaryTypeCode"))
        symbol=norm(row.get("issueSymbolIdentifier"))
        if typ==ATS_AGG:
            if symbol: aggregates[symbol].append(row)
            else: missing_aggregate_symbol+=1
        elif typ==ATS_FIRM:
            if symbol: firms[symbol].append(row)
            else: missing_firm_symbol+=1

    aggregate_symbols=set(aggregates)
    firm_symbols=set(firms)
    shared=aggregate_symbols & firm_symbols
    aggregate_only=aggregate_symbols-firm_symbols
    firm_only=firm_symbols-aggregate_symbols
    ambiguous=0
    mapped=[]
    for symbol in shared:
        ar=aggregates[symbol]
        product_types={norm(x.get("productTypeCode")) for x in ar}
        if len(ar)!=1 or len(product_types)!=1 or "" in product_types:
            ambiguous+=1
        else:
            mapped.append((symbol,ar[0]))

    exact_shares=0
    exact_trades=0
    exact_both=0
    mismatch=0
    invalid_numeric=0
    participant_rows=0
    missing_participant_identity=0
    duplicate_participant_symbol_keys=0
    de_minimis_rows=0
    de_minimis_shares=0
    aggregate_shares_total=0
    firm_shares_total=0
    aggregate_trades_total=0
    firm_trades_total=0

    for symbol,aggregate in mapped:
        firm_rows=firms[symbol]
        agg_shares=parse_integer(aggregate.get("totalWeeklyShareQuantity"))
        agg_trades=parse_integer(aggregate.get("totalWeeklyTradeCount"))
        share_values=[]
        trade_values=[]
        participant_keys=Counter()
        for row in firm_rows:
            participant_rows+=1
            mpid=norm(row.get("MPID"))
            crd=norm(row.get("firmCRDNumber"))
            name=norm(row.get("marketParticipantName"))
            is_de_minimis="DE MINIMIS" in name
            if is_de_minimis:
                de_minimis_rows+=1
            elif not (mpid or (crd and crd!="0")):
                missing_participant_identity+=1
            key=mpid or (crd if crd!="0" else "") or name
            if key:
                participant_keys[key]+=1
            shares=parse_integer(row.get("totalWeeklyShareQuantity"))
            trades=parse_integer(row.get("totalWeeklyTradeCount"))
            share_values.append(shares)
            trade_values.append(trades)
            if is_de_minimis and shares is not None:
                de_minimis_shares+=shares
        duplicate_participant_symbol_keys+=sum(1 for count in participant_keys.values() if count>1)
        if agg_shares is None or agg_trades is None or any(x is None for x in share_values+trade_values):
            invalid_numeric+=1
            continue
        firm_shares=sum(share_values)
        firm_trades=sum(trade_values)
        aggregate_shares_total+=agg_shares
        firm_shares_total+=firm_shares
        aggregate_trades_total+=agg_trades
        firm_trades_total+=firm_trades
        share_match=firm_shares==agg_shares
        trade_match=firm_trades==agg_trades
        exact_shares+=int(share_match)
        exact_trades+=int(trade_match)
        exact_both+=int(share_match and trade_match)
        mismatch+=int(not (share_match and trade_match))

    coverage=round(100*len(mapped)/len(shared),6) if shared else None
    exact_pct=round(100*exact_both/len(mapped),6) if mapped else None
    bridge_pass=(
        bool(mapped)
        and not aggregate_only and not firm_only
        and not ambiguous
        and not missing_aggregate_symbol and not missing_firm_symbol
        and not invalid_numeric and mismatch==0
        and not missing_participant_identity
        and not duplicate_participant_symbol_keys
        and not de_minimis_rows
    )
    return {
        "aggregate_unique_symbols":len(aggregate_symbols),
        "firm_unique_symbols":len(firm_symbols),
        "shared_symbols":len(shared),
        "aggregate_only_symbols":len(aggregate_only),
        "firm_only_symbols":len(firm_only),
        "unambiguous_bridges":len(mapped),
        "ambiguous_symbols":ambiguous,
        "unambiguous_bridge_coverage_pct":coverage,
        "missing_aggregate_symbol_rows":missing_aggregate_symbol,
        "missing_firm_symbol_rows":missing_firm_symbol,
        "participant_rows_on_mapped_symbols":participant_rows,
        "participant_rows_missing_mpid_crd_excluding_de_minimis":missing_participant_identity,
        "duplicate_participant_symbol_keys":duplicate_participant_symbol_keys,
        "de_minimis_rows":de_minimis_rows,
        "de_minimis_share_quantity":de_minimis_shares,
        "invalid_numeric_symbols":invalid_numeric,
        "share_quantity_exact_matches":exact_shares,
        "trade_count_exact_matches":exact_trades,
        "both_exact_matches":exact_both,
        "exact_bridge_pct":exact_pct,
        "aggregate_shares_total":aggregate_shares_total,
        "firm_shares_total":firm_shares_total,
        "aggregate_trades_total":aggregate_trades_total,
        "firm_trades_total":firm_trades_total,
        "share_total_delta":firm_shares_total-aggregate_shares_total,
        "trade_total_delta":firm_trades_total-aggregate_trades_total,
        "bridge_gate":"PASS" if bridge_pass else "FAIL_OR_REVIEW",
        "raw_identifiers_retained":False,
    }


def analyze_partition(rows,week,record_total,pages):
    summary_counts=Counter()
    symbol_sets=defaultdict(set)
    date_stats=defaultdict(GapStats)
    date_missing=Counter()
    date_invalid=Counter()
    for row in rows:
        typ=norm(row.get("summaryTypeCode")) or "__MISSING__"
        summary_counts[typ]+=1
        symbol=norm(row.get("issueSymbolIdentifier"))
        if symbol:
            symbol_sets[typ].add(symbol)
        for field in DATE_FIELDS:
            raw=row.get(field)
            if raw is None or str(raw).strip()=="":
                date_missing[field]+=1
            elif parse_date(raw) is None:
                date_invalid[field]+=1
        date_stats[typ].add(row.get("initialPublishedDate"),row.get("lastUpdateDate"))

    ats_types_present={t for t in ATS_TYPES if summary_counts.get(t,0)>0}
    ats_gap_rows=sum(date_stats[t].summary()["positive_gap_rows"] for t in ats_types_present)
    ats_rows=sum(summary_counts[t] for t in ats_types_present)
    otc_gap_rows=sum(
        date_stats[t].summary()["positive_gap_rows"]
        for t in summary_counts if t.startswith("OTC_")
    )
    otc_rows=sum(
        summary_counts[t] for t in summary_counts if t.startswith("OTC_")
    )
    bridge=audit_ats_bridge(rows)
    date_complete=not any(date_missing.values()) and not any(date_invalid.values())
    pit_candidate=date_complete and ats_rows>0 and ats_gap_rows==0
    return {
        "week":week,
        "tier":TIER,
        "rows":len(rows),
        "record_total":record_total,
        "pages":pages,
        "retrieval_count_match":len(rows)==record_total,
        "summary_type_counts":dict(sorted(summary_counts.items())),
        "unique_symbol_counts_by_summary_type":{
            typ:len(symbols) for typ,symbols in sorted(symbol_sets.items())
        },
        "date_field_missing_counts":dict(date_missing),
        "date_field_invalid_counts":dict(date_invalid),
        "last_update_gap_by_summary_type":{
            typ:stats.summary() for typ,stats in sorted(date_stats.items())
        },
        "ats_rows_with_post_initial_update":ats_gap_rows,
        "ats_rows_total":ats_rows,
        "otc_rows_with_post_initial_update":otc_gap_rows,
        "otc_rows_total":otc_rows,
        "ats_date_pit_candidate":pit_candidate,
        "ats_symbol_firm_bridge":bridge,
        "raw_rows_retained":False,
        "raw_identifiers_retained":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="phase369_finra_t1_ats_expanded_pit_grain_audit")
    args=parser.parse_args()
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    session=requests.Session()
    session.headers.update({
        "Accept":"application/json",
        "Content-Type":"application/json",
        "Data-API-Version":"1",
        "User-Agent":"SmartMoneyResearch-Phase369/1.0",
    })
    token=os.getenv("FINRA_API_TOKEN","").strip()
    if token:
        session.headers["Authorization"]=f"Bearer {token}"

    partitions=[]
    errors=[]
    for week in WEEKS:
        try:
            rows,total,pages=fetch_partition(session,week)
            partitions.append(analyze_partition(rows,week,total,pages))
            del rows
        except Exception as exc:
            errors.append({"week":week,"error_type":type(exc).__name__,"error":str(exc)[:240]})

    all_complete=len(partitions)==len(WEEKS) and not errors and all(x["retrieval_count_match"] for x in partitions)
    all_pit=all_complete and all(x["ats_date_pit_candidate"] for x in partitions)
    all_bridge=all_complete and all(x["ats_symbol_firm_bridge"]["bridge_gate"]=="PASS" for x in partitions)
    summary={
        "phase":369,
        "source":"FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "sample_weeks":list(WEEKS),
        "tier":TIER,
        "expected_partitions":len(WEEKS),
        "completed_partitions":len(partitions),
        "total_rows":sum(x["rows"] for x in partitions),
        "total_pages":sum(x["pages"] for x in partitions),
        "errors":errors,
        "all_partitions_complete":all_complete,
        "all_t1_ats_date_gates_pass":all_pit,
        "all_t1_ats_bridge_gates_pass":all_bridge,
        "pit_availability_established":False,
        "historical_signal_test_authorized":False,
        "forward_returns_used":False,
        "holdout_used":False,
        "f80_changed":False,
        "raw_rows_retained":False,
        "raw_identifiers_retained":False,
        "partitions":partitions,
        "research_disposition":(
            "T1_ATS_WIDER_DATE_AND_GRAIN_CANDIDATE"
            if all_pit and all_bridge
            else "T1_ATS_REQUIRES_EXCLUSIONS_OR_FURTHER_REVIEW"
        ),
    }
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps({
        "phase":369,
        "all_partitions_complete":all_complete,
        "all_t1_ats_date_gates_pass":all_pit,
        "all_t1_ats_bridge_gates_pass":all_bridge,
        "total_rows":summary["total_rows"],
        "total_pages":summary["total_pages"],
        "errors":errors,
        "pit_availability_established":False,
        "historical_signal_test_authorized":False,
    },indent=2),flush=True)
    if not all_complete:
        raise SystemExit(1)


if __name__=="__main__":
    main()
