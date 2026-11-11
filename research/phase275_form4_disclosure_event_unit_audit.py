#!/usr/bin/env python3
"""Phase 275: Form 4 disclosure-event unit, owner-proxy and class consistency audit."""
from __future__ import annotations
import argparse, io, json, re, zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
import exchange_calendars as xc
from research.phase271_form4_open_market_purchase_screen import (
    EXPECTED_OUTER_SHA256, EXPECTED_INNER_SHA256, sha256_bytes, read_tsv,
    classify_purchase_row,
)

def parse_filing_date(value: str) -> date:
    value=(value or "").strip()
    for fmt in ("%d-%b-%Y","%Y-%m-%d","%m/%d/%Y"):
        try: return datetime.strptime(value,fmt).date()
        except ValueError: pass
    raise ValueError(f"invalid filing date: {value!r}")

def parse_transaction_date(value: str) -> date | None:
    value=(value or "").strip()
    for fmt in ("%d-%b-%Y","%Y-%m-%d","%m/%d/%Y"):
        try: return datetime.strptime(value,fmt).date()
        except ValueError: pass
    return None

def normalize_security_title(value: str) -> str:
    return " ".join((value or "").upper().split())

def normalize_address(row: dict[str,Any]) -> str:
    raw=" ".join(str(row.get(k) or "") for k in
        ("owner_street1","owner_street2","owner_city","owner_state","owner_zip"))
    return " ".join(re.sub(r"[^A-Z0-9]+"," ",raw.upper()).split())

def next_session_close(filing_date: date, calendar=None) -> dict[str,str]:
    calendar=calendar or xc.get_calendar("XNYS")
    sessions=calendar.sessions_in_range(filing_date+timedelta(days=1),
                                        filing_date+timedelta(days=14))
    if not len(sessions): raise ValueError("no XNYS session after filing date")
    session=sessions[0]
    return {"session":session.date().isoformat(),
            "close_utc":calendar.session_close(session).isoformat()}

def enriched_candidate_rows(inner_bytes: bytes, period: str) -> list[dict[str,Any]]:
    with zipfile.ZipFile(io.BytesIO(inner_bytes)) as zf:
        submissions=read_tsv(zf,"SUBMISSION.tsv")
        transactions=read_tsv(zf,"NONDERIV_TRANS.tsv")
        footnotes=read_tsv(zf,"FOOTNOTES.tsv")
        owners=read_tsv(zf,"REPORTINGOWNER.tsv")
    sub_by={r["ACCESSION_NUMBER"]:r for r in submissions}
    owner_by=defaultdict(list)
    for r in owners: owner_by[r["ACCESSION_NUMBER"]].append(r)
    foot_by=defaultdict(dict)
    for r in footnotes: foot_by[r["ACCESSION_NUMBER"]][r["FOOTNOTE_ID"]]=r["FOOTNOTE_TXT"]
    require_false=period>="2023Q2"
    out=[]
    for tx in transactions:
        acc=tx.get("ACCESSION_NUMBER",""); sub=sub_by.get(acc)
        if not sub: continue
        own=owner_by.get(acc,[]); refs=set()
        for key,value in tx.items():
            if key.endswith("_FN"): refs.update(re.findall(r"F\\d+",value or ""))
        foot=" ".join(foot_by[acc].get(ref,"") for ref in sorted(refs))
        flags=classify_purchase_row(
            {**tx,"DOCUMENT_TYPE":sub.get("DOCUMENT_TYPE","")},
            foot,len(own),sub.get("AFF10B5ONE",""),require_false)
        eligible=(flags["base"] and flags["explicit_open_market"]
            and flags["no_private_disclosure"] and flags["no_plan_disclosure"]
            and flags["no_mechanical_disclosure"] and flags["direct_ownership"]
            and flags["single_reporting_owner"] and flags["common_stock_title"]
            and flags["aff_gate"])
        if not eligible: continue
        if len(own)!=1: raise AssertionError("eligible candidate must have one reporting owner")
        o=own[0]; txdate=parse_transaction_date(tx.get("TRANS_DATE",""))
        out.append({
            "accession":acc,"issuer_cik":sub.get("ISSUERCIK",""),
            "issuer_name":sub.get("ISSUERNAME",""),"ticker":sub.get("ISSUERTRADINGSYMBOL",""),
            "filing_date":sub.get("FILING_DATE",""),
            "transaction_date":txdate.isoformat() if txdate else None,
            "security_title":tx.get("SECURITY_TITLE",""),
            "transaction_row_key":tx.get("NONDERIV_TRANS_SK",""),
            "owner_cik":o.get("RPTOWNERCIK",""),"owner_name":o.get("RPTOWNERNAME",""),
            "owner_relationship_raw":o.get("RPTOWNER_RELATIONSHIP",""),
            "owner_title":o.get("RPTOWNER_TITLE",""),
            "owner_street1":o.get("RPTOWNER_STREET1",""),
            "owner_street2":o.get("RPTOWNER_STREET2",""),
            "owner_city":o.get("RPTOWNER_CITY",""),"owner_state":o.get("RPTOWNER_STATE",""),
            "owner_zip":o.get("RPTOWNER_ZIPCODE",""),
            "owner_file_number":o.get("FILE_NUMBER",""),"aff_status":flags["aff_status"],
        })
    return out

def build_disclosure_events(rows: list[dict[str,Any]], period: str, calendar=None) -> dict[str,Any]:
    calendar=calendar or xc.get_calendar("XNYS")
    groups=defaultdict(list)
    for r in rows:
        if not r.get("issuer_cik") or not r.get("owner_cik") or not r.get("accession"):
            raise ValueError("candidate missing issuer, owner or accession key")
        filing=parse_filing_date(r.get("filing_date",""))
        txdate=date.fromisoformat(r["transaction_date"]) if r.get("transaction_date") else None
        if txdate and txdate>filing: continue
        groups[(r["issuer_cik"],filing)].append(r)
    events=[]
    for (issuer,filing),g in sorted(groups.items(),key=lambda x:(x[0][1],x[0][0])):
        accessions={r["accession"] for r in g}; owners={r["owner_cik"] for r in g}
        if len(accessions)<2 or len(owners)<2: continue
        owner_rows={}
        for r in g:
            old=owner_rows.get(r["owner_cik"])
            if old and old["owner_name"]!=r["owner_name"]:
                raise ValueError("owner name inconsistent within disclosure event")
            owner_rows[r["owner_cik"]]=r
        by_date=defaultdict(list)
        for r in g:
            if r.get("transaction_date"): by_date[r["transaction_date"]].append(r)
        strict=[]
        for txdate,date_rows in sorted(by_date.items()):
            by_title=defaultdict(list)
            for r in date_rows: by_title[normalize_security_title(r.get("security_title",""))].append(r)
            for title,title_rows in sorted(by_title.items()):
                a={r["accession"] for r in title_rows}; o={r["owner_cik"] for r in title_rows}
                if title and len(a)>=2 and len(o)>=2:
                    strict.append({"transaction_date":txdate,"security_title_normalized":title,
                                   "accessions":len(a),"owners":len(o),"rows":len(title_rows)})
        raw_titles=sorted({r["security_title"].strip() for r in g if r.get("security_title")})
        normalized_titles=sorted({normalize_security_title(r.get("security_title",""))
                                   for r in g if r.get("security_title")})
        addresses={normalize_address(r) for r in owner_rows.values() if normalize_address(r)}
        roles=Counter(r.get("owner_relationship_raw","unknown") or "unknown"
                      for r in owner_rows.values())
        owner_titles=Counter(r.get("owner_title","(blank)") or "(blank)"
                             for r in owner_rows.values())
        owner_dates=defaultdict(set)
        for r in g:
            if r.get("transaction_date"): owner_dates[r["owner_cik"]].add(r["transaction_date"])
        availability=next_session_close(filing,calendar)
        same_security=len(normalized_titles)==1
        events.append({
            "issuer_cik":issuer,"ticker":g[0].get("ticker",""),"filing_date":filing.isoformat(),
            "first_conservative_tradable_session":availability["session"],
            "first_conservative_tradable_close_utc":availability["close_utc"],
            "transaction_rows":len(g),"unique_accessions":len(accessions),
            "unique_reporting_owner_ciks":len(owners),"transaction_dates":sorted(by_date),
            "transaction_date_count":len(by_date),
            "same_trade_date_multi_owner_cluster_count":len(strict),
            "strict_trade_date_clusters":strict,
            "owners_with_multiple_transaction_dates":sum(len(v)>1 for v in owner_dates.values()),
            "security_title_values":raw_titles,"security_title_normalized_values":normalized_titles,
            "security_title_consistent":same_security,
            "primary_same_security_event_eligible":same_security,
            "owner_relationship_counts":dict(sorted(roles.items())),
            "owner_title_counts":dict(sorted(owner_titles.items())),
            "unique_normalized_mailing_addresses":len(addresses),
            "all_owner_mailing_addresses_match":len(addresses)==1,
            "mailing_address_interpretation":
                "administrative/mailing proxy only; never beneficial-owner affiliation evidence",
            "owner_independence_proven":False,
            "owner_independence_status":"NOT_ESTABLISHED_BY_DISTINCT_CIKS_OR_MAILING_ADDRESSES",
            "owner_ciks":sorted(owners),"accessions":sorted(accessions),
            "plan_status":"AFF10B5ONE_FALSE_REQUIRED_BY_SCREEN"
                if period>="2023Q2" else "UNKNOWN_PRE_CHECKBOX_ERA",
        })
    issuer_counts=Counter(e["issuer_cik"] for e in events)
    return {
        "period":period,"candidate_rows":len(rows),"multi_owner_disclosure_events":len(events),
        "unique_issuers_in_events":len(issuer_counts),
        "unique_accessions_in_events":len({a for e in events for a in e["accessions"]}),
        "unique_reporting_owners_in_events":len({o for e in events for o in e["owner_ciks"]}),
        "rows_in_events":sum(e["transaction_rows"] for e in events),
        "events_with_multiple_transaction_dates":sum(e["transaction_date_count"]>1 for e in events),
        "events_with_security_title_mismatch":sum(not e["security_title_consistent"] for e in events),
        "primary_same_security_event_count":sum(e["primary_same_security_event_eligible"] for e in events),
        "events_with_one_normalized_mailing_address":sum(e["all_owner_mailing_addresses_match"] for e in events),
        "events_with_any_owner_multiple_transaction_dates":
            sum(e["owners_with_multiple_transaction_dates"]>0 for e in events),
        "issuers_with_multiple_disclosure_events":sum(n>1 for n in issuer_counts.values()),
        "same_trade_date_cluster_count":sum(e["same_trade_date_multi_owner_cluster_count"] for e in events),
        "events":events,
    }

def analyze_artifact(path: str|Path) -> dict[str,Any]:
    outer=Path(path).read_bytes()
    if sha256_bytes(outer)!=EXPECTED_OUTER_SHA256: raise ValueError("Phase 39 outer SHA-256 mismatch")
    periods={}
    with zipfile.ZipFile(io.BytesIO(outer)) as zf:
        for filename,expected in EXPECTED_INNER_SHA256.items():
            inner=zf.read(filename)
            if sha256_bytes(inner)!=expected: raise ValueError(f"Phase 39 inner SHA-256 mismatch: {filename}")
            period="2012Q1" if filename.startswith("2012") else "2026Q3"
            periods[period]=build_disclosure_events(enriched_candidate_rows(inner,period),period)
    return {
        "phase":275,"date":"2026-11-10",
        "source_artifact":{"workflow_run_id":40606706518,"artifact_id":12781850078,
            "outer_sha256":EXPECTED_OUTER_SHA256,"inner_sha256":EXPECTED_INNER_SHA256},
        "method":"Exact Phase 271 eligibility reused. Primary information event is issuer CIK x date-only FILING_DATE; transaction dates are nested attributes.",
        "periods":periods,
        "decision":"Use issuer-filing-date disclosure event as primary unit. Same-trade-date clusters are nested descriptors. Owner independence is not proven; addresses are administrative proxies only. No return or alpha test.",
        "strict_pit_admitted":False,"alpha_test_authorized":False,"forward_returns_tested":False,
        "bootstrap_loo_tested":False,"chronological_oos_tested":False,"holdout_used":False,
        "f80_frozen":True,"production_changed":False,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact",required=True); ap.add_argument("--output",required=True)
    args=ap.parse_args()
    result=analyze_artifact(args.artifact)
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    for period,item in result["periods"].items():
        print(f"{period}: rows={item['candidate_rows']} events={item['multi_owner_disclosure_events']} "
              f"issuers={item['unique_issuers_in_events']} accessions={item['unique_accessions_in_events']} "
              f"owners={item['unique_reporting_owners_in_events']} trade_date_clusters={item['same_trade_date_cluster_count']}")
    print("PHASE275: DISCLOSURE_EVENT_UNIT_DEDUPLICATED; STRICT_PIT_AND_ALPHA_NOT_ADMITTED")

if __name__=="__main__": main()
