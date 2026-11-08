#!/usr/bin/env python3
"""Phase 204: methodology-aware SEC MIDAS exchange/aggregate reconciliation."""
from __future__ import annotations
import argparse, hashlib, json, re, time
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

PHASE = 204
QUARTERS = ("2016 Q2", "2017 Q2", "2019 Q4")
CHANGE = date(2017, 5, 1)
SEC_METHOD = "https://www.sec.gov/featured-topics/market-structure-analytics/market-activity-report-methodology"


def venue(value: str) -> str:
    raw = (value or "").strip().upper()
    key = re.sub(r"[^A-Z0-9]+", "", raw)
    return {"EDGEA":"EDGA-A", "EDGAA":"EDGA-A", "EDGEX":"EDGE-X",
            "BATSY":"BATS-Y", "BATSZ":"BATS-Z"}.get(key, raw.replace(" ", ""))


def parse_date(value: str) -> date:
    parts = re.sub(r"\s+", " ", value.strip()).replace(",", "").split()
    months = {m.upper(): i for i, pair in enumerate(("JAN JANUARY", "FEB FEBRUARY", "MAR MARCH", "APR APRIL", "MAY", "JUN JUNE", "JUL JULY", "AUG AUGUST", "SEP SEPT SEPTEMBER", "OCT OCTOBER", "NOV NOVEMBER", "DEC DECEMBER"), 1) for m in pair.split()}
    if len(parts) == 2: return date(int(parts[1]), months[parts[0].upper()], 1)
    if len(parts) == 3: return date(int(parts[2]), months[parts[0].upper()], int(parts[1]))
    raise ValueError(f"bad_effective_date:{value}")


def parse_rule(text: str) -> dict:
    value = text.strip().rstrip(".;")
    if re.search(r"\s+for\s+", value, re.I): value = re.split(r"\s+for\s+", value, maxsplit=1, flags=re.I)[1]
    base_text = re.split(r"\s*\(&", value, maxsplit=1)[0]
    base = sorted({venue(x) for x in base_text.split(",") if x.strip()})
    additions = []
    rx = re.compile(r"&\s*(NYSE|NSX|CHX)\s+beginning\s+([A-Za-z]+(?:\s+\d{1,2})?,?\s+\d{4})", re.I)
    for m in rx.finditer(value): additions.append({"exchange":venue(m.group(1)), "date":parse_date(m.group(2)).isoformat()})
    return {"base":base, "additions":additions, "text":text.strip()}


def readme_rules(readme: str) -> dict:
    lines = [x.strip() for x in readme.splitlines()]
    def find(rx): return next((x for x in lines if re.search(rx, x, re.I)), None)
    generic = find(r"^Order-based exchanges\s*:")
    c2t = find(r"^Cancel-to-Trade\s*=")
    odd_rate = find(r"^Oddlot Rate\s*=")
    odd_vol = find(r"^Oddlot Volume\s*=")
    effective = next((x for x in lines if re.search(r"NYSE\s+beginning",x,re.I) and not re.match(r"(Cancel-to-Trade|Oddlot Rate|Oddlot Volume|Order-based exchanges)\s*[:=]",x,re.I)),None)
    def parse(line, colon=False):
        if not line: return None
        if colon: line = line.split(":",1)[1].strip()
        return parse_rule(line)
    relevant = [x for x in lines if re.search(r"Order-based exchanges|Cancel-to-Trade|Oddlot Rate|Oddlot Volume|NYSE beginning|NSX beginning|CHX beginning|TradesForOddLots|TradeVolForOddLots",x,re.I)]
    return {"generic_line":generic,"generic":parse(generic,True),"c2t_line":c2t,"c2t":parse(c2t),
            "odd_rate_line":odd_rate,"odd_rate":parse(odd_rate),"odd_vol_line":odd_vol,"odd_vol":parse(odd_vol),
            "effective_line":effective,"effective":parse(effective),"relevant_lines":relevant,
            "sha256":hashlib.sha256(readme.encode()).hexdigest()}


def active(rule, day, fallback=None):
    if rule is None: return set(fallback or ())
    result=set(rule["base"])
    for x in rule["additions"]:
        if day >= date.fromisoformat(x["date"]): result.add(x["exchange"])
    return result


def sec_venue_set(all_venues, day):
    result=set(all_venues); result.discard("AMEX")
    if day < CHANGE: result.discard("NYSE")
    return result


def self_test():
    assert venue("Edge-A")=="EDGA-A" and venue("Edga-A")=="EDGA-A"
    assert parse_date("May, 2017")==date(2017,5,1)
    assert parse_date("November 4, 2019")==date(2019,11,4)
    r=parse_rule("Arca, Bats-Y, Edga-A, Edge-X (& NYSE beginning May, 2017; & NSX beginning May 21, 2018 & CHX beginning November 4, 2019)")
    assert "NYSE" not in active(r,date(2017,4,28)) and "NYSE" in active(r,date(2017,5,1))
    assert "NSX" not in active(r,date(2018,5,20)) and "NSX" in active(r,date(2018,5,21))
    assert "CHX" not in active(r,date(2019,11,3)) and "CHX" in active(r,date(2019,11,4))
    assert sec_venue_set({"ARCA","NYSE","AMEX"},date(2017,4,28))=={"ARCA"}
    assert sec_venue_set({"ARCA","NYSE","AMEX"},date(2017,5,1))=={"ARCA","NYSE"}
    readme="\n".join(["Order-based exchanges: Arca, Bats-Y, CHX, NSX, Edga-A, Edge-X", "Cancel-to-Trade = Cancels/LitTrades for Arca, Bats-Y, CHX, NSX, Edga-A, Edge-X (& NYSE beginning May, 2017)", "Oddlot Rate=100*OddLots/TradesForOddLots for Arca, Bats-Y, CHX, NSX, Edga-A, Edge-X (& NYSE beginning May, 2017)", "Oddlot Volume=100*OddLotVol/TradeVolForOddLots for Arca, Bats-Y, CHX, NSX, Edga-A, Edge-X (& NYSE beginning May, 2017)"])
    p=readme_rules(readme)
    assert p["generic"]["base"]==["ARCA","BATS-Y","CHX","EDGA-A","EDGE-X","NSX"]
    assert p["c2t"]["additions"][0]["date"]=="2017-05-01" and p["odd_rate"] and p["odd_vol"]
    p=readme_rules("Order-based exchanges: Arca, Bats-Y\nArca, Bats-Y, Edga-A, Edge-X (& NYSE beginning May, 2017)")
    assert p["effective"]["additions"]==[{"exchange":"NYSE","date":"2017-05-01"}]
    return 7


def sum_field(records, conflicts, field, mode, rule, all_venues):
    from research.phase203_sec_midas_exchange_aggregate_reconciliation import EX_FIELDS
    source={"tradesforoddlots":"trades","tradevolforoddlots":"tradevol"}.get(field,field)
    idx=EX_FIELDS.index(source); keys={k[:3] for k in records if k[:3] not in conflicts}; sums=defaultdict(list)
    for k,v in records.items():
        base=k[:3]
        if base in conflicts: continue
        d=date.fromisoformat(k[0]); ex=venue(k[3])
        if mode=="all": ok=True
        elif mode=="sec": ok=ex in sec_venue_set(all_venues,d)
        else: ok=ex in active(rule,d,all_venues)
        if ok and v[idx] is not None: sums[base].append(v[idx])
    return {k:(sum(sums[k]) if sums.get(k) else None) for k in keys}


def compare(agg, agg_conflicts, candidate, ex_conflicts, field, tolerance):
    from research.phase203_sec_midas_exchange_aggregate_reconciliation import AGG_FIELDS
    idx=AGG_FIELDS.index(field); left=set(agg)-agg_conflicts; right=set(candidate)-ex_conflicts; common=sorted(left&right)
    mismatch=exact=within=missing=paired=0; maxdiff=0.0; signed=0.0; examples=[]
    for k in common:
        a=agg[k][idx]; b=candidate[k]
        if a is None and b is None: continue
        if a is None or b is None: missing+=1; mismatch+=1; continue
        paired+=1; delta=b-a; signed+=delta; diff=abs(delta); maxdiff=max(maxdiff,diff)
        if diff<=1e-9: exact+=1; within+=1
        elif diff<=tolerance: within+=1
        else:
            mismatch+=1
            if len(examples)<4: examples.append({"date":k[0],"ticker":k[1],"aggregate":a,"exchange_sum":b,"difference":delta})
    return {"keys_compared":len(common),"nonmissing_pairs":paired,"exact_matches":exact,"within_tolerance_matches":within,"mismatch_count":mismatch,"one_sided_missing_count":missing,"max_absolute_difference":maxdiff,"mean_signed_difference":signed/paired if paired else None,"tolerance":tolerance,"examples":examples}


def run_audit():
    from research.phase198_sec_midas_archive_inventory import fetch_sec_page, parse_inventory
    from research.phase199_sec_midas_disputed_quarter_content_audit import download_archive
    from research.phase202_sec_midas_per_exchange_archive_structure import fetch_exchange_inventory
    from research.phase203_sec_midas_exchange_aggregate_reconciliation import QUARTERS as Q, TOLERANCE, deterministic_sample, scan_aggregate_archive, scan_exchange_archive, AGG_FIELDS
    if tuple(Q)!=QUARTERS: raise RuntimeError("phase203_quarter_scope_changed")
    ai=parse_inventory(fetch_sec_page()); ei=fetch_exchange_inventory()
    if ai["quarter_count"]!=58 or ei["quarter_count"]!=58: raise RuntimeError("unexpected_SEC_quarter_inventory_count")
    results=[]
    for n,q in enumerate(QUARTERS):
        if n: time.sleep(1)
        ab,ah=download_archive(ai["quarter_urls"][q]); all_scan=scan_aggregate_archive(ab,q,None)
        tickers=deterministic_sample(all_scan["ticker_set"]); ag=scan_aggregate_archive(ab,q,set(tickers))
        eb,eh=download_archive(ei["quarter_urls"][q]); ex=scan_exchange_archive(eb,q,set(tickers))
        rules=readme_rules(ex["order_based_readme_text"]); all_venues={venue(k[3]) for k in ex["sample_records"] if venue(k[3])}
        ac=ag["sample_conflicts"]; ec={k[:3] for k in ex["sample_conflicts"]}; ar=ag["sample_records"]; er=ex["sample_records"]
        specs={
          "cancels":{"all_exchange_sum":("all",None),"sec_methodology_exclusion":("sec",None),"readme_cancel_to_trade":("rule",rules["c2t"] or rules["generic"])},
          "littrades":{"all_exchange_sum":("all",None),"sec_methodology_exclusion":("sec",None),"readme_cancel_to_trade":("rule",rules["c2t"] or rules["generic"])},
          "oddlots":{"all_exchange_sum":("all",None),"sec_methodology_exclusion":("sec",None),"readme_oddlot_rate":("rule",rules["odd_rate"] or rules["generic"]),"effective_order_based_alternative":("rule",rules["effective"] or rules["generic"])},
          "oddlotvol":{"all_exchange_sum":("all",None),"sec_methodology_exclusion":("sec",None),"readme_oddlot_volume":("rule",rules["odd_vol"] or rules["generic"]),"effective_order_based_alternative":("rule",rules["effective"] or rules["generic"])},
          "tradesforoddlots":{"all_exchange_sum":("all",None),"generic_order_based_line":("rule",rules["generic"]),"effective_order_based_line":("rule",rules["effective"] or rules["generic"]),"oddlot_rate_line_alternative":("rule",rules["odd_rate"] or rules["generic"])},
          "tradevolforoddlots":{"all_exchange_sum":("all",None),"generic_order_based_line":("rule",rules["generic"]),"effective_order_based_line":("rule",rules["effective"] or rules["generic"]),"oddlot_volume_line_alternative":("rule",rules["odd_vol"] or rules["generic"])},
        }
        for f in AGG_FIELDS: specs.setdefault(f,{"all_exchange_sum":("all",None)})
        variants={}
        for f,vs in specs.items():
            variants[f]={}
            for name,(mode,rule) in vs.items():
                candidate=sum_field(er,ec,f,mode,rule,all_venues)
                variants[f][name]=compare(ar,ac,candidate,ec,f,TOLERANCE[f])
        results.append({"quarter":q,"sample":{"tickers":len(tickers),"ticker_sha256":hashlib.sha256("\n".join(sorted(tickers)).encode()).hexdigest(),"aggregate_keys":len(ar)},
          "aggregate_archive":{"sha256":ag["archive_sha256"],"bytes":ag["archive_bytes"],"zip_crc_passed":ag["zip_crc_passed"],"rows":ag["row_count"],"tickers":ag["unique_tickers"],"date_range":[ag["min_date"],ag["max_date"]]},
          "exchange_archive":{"sha256":ex["archive_sha256"],"bytes":ex["archive_bytes"],"zip_crc_passed":ex["zip_crc_passed"],"monthly_members":ex["monthly_members"],"rows":ex["row_count"],"date_range":[ex["min_date"],ex["max_date"]],"rows_by_exchange":ex["rows_by_exchange"]},
          "http":{"aggregate":ah,"exchange":eh},"readme":{"sha256":rules["sha256"],"relevant_lines":rules["relevant_lines"],"parsed_rules":{k:v for k,v in rules.items() if k.endswith("_line") or k in ("generic","c2t","odd_rate","odd_vol","effective")}},
          "comparison":{"aggregate_conflicts":len(ac),"exchange_conflicts":len(ec),"venues":sorted(all_venues),"field_variants":variants}})
    return {"phase":PHASE,"status":"THREE_QUARTER_METHOD_SPECIFIC_RECONCILIATION_DIAGNOSTIC_COMPLETED","quarters_audited":list(QUARTERS),"aggregate_archive_quarter_count":ai["quarter_count"],"exchange_archive_quarter_count":ei["quarter_count"],"audit_as_of_utc":datetime.now(timezone.utc).isoformat(),
      "methodology":{"source_url":SEC_METHOD,"source_last_reviewed":"2026-07-17","change_date":CHANGE.isoformat(),"summary":"SEC excludes NYSE and Amex from Cancel-to-Trade, Odd Lot Rate and Odd Lot Volume aggregate measures before the NYSE Integrated Feed cutover; NYSE is included from 2017-05-01, while Amex remains excluded for those measures."},
      "interpretation":{"full_zip_crc_validated_for_all_six_archives":True,"monthly_exchange_csvs_fully_parsed":True,"readme_bytes_hashed_and_rule_lines_preserved":True,"methodology_aware_candidate_variants_compared":True,"complete_universe_reconciliation":False,"first_publication_time_verified":False,"strict_pit_admitted":False,"historical_permanent_security_identity_admitted":False,"off_exchange_flow_measure":False,"participant_identity_available":False,"alpha_test_authorized":False,"holdout_used":False,"production_changed":False,"data_purchase":False,"vendor_contact":False,"f80_frozen":True},
      "decision":"Compare documented field-specific rules; do not select a rule solely because it fits the sample. MIDAS remains slow market-structure context pending full-universe, PIT and identity gates.","quarter_results":results}


def main():
    p=argparse.ArgumentParser(); p.add_argument("--output-dir",default="phase204_output"); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test: print(f"Phase 204 self-tests passed: {self_test()}"); return 0
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True); result=run_audit()
    target=out/"phase204_sec_midas_methodology_aware_reconciliation.json"; target.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
