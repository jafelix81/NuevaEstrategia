#!/usr/bin/env python3
"""Phase 225: SEC Schedule 13D/G event-date lag and amendment-semantics audit."""
from __future__ import annotations
import argparse, csv, hashlib, json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from research.phase213_13dg_legacy_event_date_recovery import (
    ARTIFACT_SHA256, CSV_NAME, CSV_SHA256, extract_amendment_marker,
    extract_event, family, is_true, parse_date, primary_document, validate_header,
)

SOURCE_RUN_ID = 42073725379
SOURCE_ARTIFACT_ID = 13436764625
SOURCE_SAMPLE_N = 600
SOURCE_ACTUAL_N = 599
REFORM_13D = date(2024, 2, 5)
REFORM_13G = date(2024, 9, 30)

def weighted_quantile(values: Iterable[float], weights: Iterable[float], q: float) -> float | None:
    pairs = sorted((float(v), float(w)) for v, w in zip(values, weights)
                   if v is not None and w is not None and float(w) > 0)
    if not pairs:
        return None
    threshold = min(max(float(q), 0.0), 1.0) * sum(w for _, w in pairs)
    cumulative = 0.0
    for value, weight in pairs:
        cumulative += weight
        if cumulative >= threshold:
            return value
    return pairs[-1][0]

def _pct(n: float, d: float) -> float | None:
    return round(100.0 * n / d, 4) if d else None

def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    parsed = [r for r in rows if r["event_date"] is not None]
    total_w = sum(r["sample_weight"] for r in rows)
    parsed_w = sum(r["sample_weight"] for r in parsed)
    qend = [r for r in parsed if r["event_quarter_end"]]
    lags = [r["lag_calendar_days"] for r in parsed]
    weights = [r["sample_weight"] for r in parsed]
    ordered = sorted(lags)
    def uq(q: float) -> float | None:
        if not ordered: return None
        pos = (len(ordered)-1)*q
        lo, hi = int(pos), min(int(pos)+1, len(ordered)-1)
        return round(ordered[lo]*(hi-pos)+ordered[hi]*(pos-lo), 4)
    return {
        "n":len(rows), "parsed_n":len(parsed),
        "unweighted_coverage_pct":_pct(len(parsed),len(rows)),
        "sample_weighted_coverage_pct":_pct(parsed_w,total_w),
        "quarter_end_unweighted_pct_within_parsed":_pct(len(qend),len(parsed)),
        "quarter_end_sample_weighted_pct_within_parsed":_pct(sum(r["sample_weight"] for r in qend),parsed_w),
        "lag_median_calendar_days_unweighted":uq(.5),
        "lag_median_calendar_days_weighted":weighted_quantile(lags,weights,.5),
        "lag_p90_calendar_days_unweighted":uq(.9),
        "lag_p90_calendar_days_weighted":weighted_quantile(lags,weights,.9),
        "lag_over_30_days_n":sum(x>30 for x in lags),
        "lag_over_90_days_n":sum(x>90 for x in lags),
        "lag_over_365_days_n":sum(x>365 for x in lags),
        "lag_max_calendar_days":max(lags) if lags else None,
        "same_day_event_and_filing_n":sum(x==0 for x in lags),
        "future_event_date_n":sum(x<0 for x in lags),
    }

def _rules(value: str | None) -> list[str]:
    if not value: return []
    try: parsed=json.loads(value)
    except (TypeError,json.JSONDecodeError): return []
    return [str(x) for x in parsed] if isinstance(parsed,list) else []

def audit(input_dir: Path, zip_path: Path | None = None) -> dict[str, Any]:
    zip_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest() if zip_path else None
    if zip_sha is not None and zip_sha != ARTIFACT_SHA256:
        raise ValueError(f"Phase 124 ZIP SHA-256 mismatch: {zip_sha}")
    csv_path=input_dir/CSV_NAME
    csv_sha=hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if csv_sha != CSV_SHA256: raise ValueError(f"Phase 124 CSV SHA-256 mismatch: {csv_sha}")
    with csv_path.open(encoding="utf-8-sig",newline="") as f: source=list(csv.DictReader(f))
    if len(source)!=SOURCE_SAMPLE_N: raise ValueError(f"Expected {SOURCE_SAMPLE_N} rows, got {len(source)}")
    rows=[]; raw_hashes=header_checks=primary_checks=xml_checks=aliases=0
    amendment_methods=Counter()
    for sr in source:
        raw_bytes=(input_dir/sr["raw_file"]).read_bytes()
        if hashlib.sha256(raw_bytes).hexdigest()!=sr["raw_sha256"]:
            raise ValueError(f"Raw SHA-256 mismatch: {sr['accession']}")
        raw_hashes+=1; raw=raw_bytes.decode("latin1")
        validate_header(raw,sr); header_checks+=1
        if is_true(sr.get("is_index_alias")):
            aliases+=1; continue
        if family(sr.get("form")) not in {"13D","13G"}: raise ValueError(f"Unexpected form: {sr['accession']}")
        primary=primary_document(raw)
        if primary is None or family(primary[0])!=family(sr["form"]):
            raise ValueError(f"Primary document/form mismatch: {sr['accession']}")
        primary_checks+=1; body=primary[1]
        event,method=extract_event(body)
        xml=is_true(sr.get("xml_present"))
        if xml:
            expected=parse_date(sr.get("event_date") or "")
            if event is None or event!=expected: raise ValueError(f"XML event-date mismatch: {sr['accession']}")
            xml_checks+=1
        cover_no,amend_method=extract_amendment_marker(body,xml)
        amendment_methods[amend_method]+=1
        filing=date.fromisoformat(sr["filing_date_header"])
        weight=float(sr["sample_weight"])
        rules=_rules(sr.get("rule_designations"))
        rows.append({
            "accession":sr["accession"],"family":family(sr["form"]),
            "filing_date":filing,"acceptance_datetime":sr["acceptance_datetime"],
            "event_date":event,"event_method":method,"xml_present":xml,
            "index_amendment":is_true(sr.get("is_amendment")),
            "cover_amendment_no":cover_no,"amendment_method":amend_method,
            "rule_designations":rules,"sample_weight":weight,
            "lag_calendar_days":(filing-event).days if event else None,
            "event_quarter_end":bool(event and (event.month,event.day) in {(3,31),(6,30),(9,30),(12,31)}),
        })
    if (raw_hashes,header_checks,primary_checks,xml_checks,aliases,len(rows))!=(600,600,599,102,1,599):
        raise ValueError("Unexpected immutable-sample integrity counts")
    parsed=[r for r in rows if r["event_date"] is not None]
    by_cohort={}
    for fam in ("13D","13G"):
        for amend in (False,True):
            g=[r for r in rows if r["family"]==fam and r["index_amendment"]==amend]
            by_cohort[f"{fam}_{'amendment' if amend else 'initial'}"]=summarize_group(g)
    reform={}
    for fam,cut in (("13D",REFORM_13D),("13G",REFORM_13G)):
        for era,pred in (("pre",lambda r,c=cut:r["filing_date"]<c),
                         ("post",lambda r,c=cut:r["filing_date"]>=c)):
            reform[f"{fam}_{era}_{cut.isoformat()}"]=summarize_group([r for r in rows if r["family"]==fam and pred(r)])
    rules={}
    for rule in ("Rule 13d-1(b)","Rule 13d-1(c)","Rule 13d-1(d)"):
        g=[r for r in rows if r["family"]=="13G" and r["xml_present"] and rule in r["rule_designations"]]
        rules[rule]=summarize_group(g)
    index_a=sum(r["index_amendment"] for r in rows)
    cover_pos=sum(r["cover_amendment_no"] is not None and r["cover_amendment_no"]>0 for r in rows)
    cover_zero=sum(r["cover_amendment_no"]==0 for r in rows)
    not_a_positive=sum((not r["index_amendment"]) and r["cover_amendment_no"] is not None and r["cover_amendment_no"]>0 for r in rows)
    a_not_positive=sum(r["index_amendment"] and not (r["cover_amendment_no"] is not None and r["cover_amendment_no"]>0) for r in rows)
    outliers=sorted((r for r in parsed if r["lag_calendar_days"]>90),
                    key=lambda r:(-r["lag_calendar_days"],r["accession"]))[:12]
    return {
        "phase":225,"status":"COMPLETED_STRATIFIED_13DG_EVENT_SEMANTICS_LAG_AUDIT",
        "source":{"phase124_run_id":SOURCE_RUN_ID,"phase124_artifact_id":SOURCE_ARTIFACT_ID,
                  "phase124_artifact_zip_sha256_expected":ARTIFACT_SHA256,
                  "phase124_artifact_zip_sha256_verified":zip_sha==ARTIFACT_SHA256 if zip_sha else None,
                  "phase124_csv_sha256_verified":csv_sha,
                  "sampling_frame":"43 quarters, 2016Q1-2026Q3; quarter x form-family x index-amendment strata",
                  "sample_is_stratified_descriptive_not_unstratified_random":True},
        "integrity":{"source_rows":len(source),"actual_13dg_rows":len(rows),"index_aliases_quarantined":aliases,
                     "raw_submission_sha256_verified":raw_hashes,
                     "sec_header_accession_acceptance_filing_date_verified":header_checks,
                     "primary_13dg_documents_verified":primary_checks,
                     "structured_xml_event_dates_verified":xml_checks},
        "event_date_methods":dict(Counter(r["event_method"] for r in rows)),
        "by_family_and_index_amendment":by_cohort,
        "regulatory_era_descriptive":reform,
        "xml_13g_rule_designation_subset":{
            "n_total":sum(r["family"]=="13G" and r["xml_present"] and bool(r["rule_designations"]) for r in rows),
            "by_rule":rules,
            "scope_warning":"Only 68 XML 13G rows carry parsed rule designations; do not extrapolate to legacy HTML."},
        "amendment_marker_audit":{
            "index_form_suffix_A_n":index_a,"cover_amendment_number_positive_n":cover_pos,
            "cover_amendment_number_zero_n":cover_zero,
            "cover_amendment_number_missing_n":len(rows)-cover_pos-cover_zero,
            "cover_marker_method_counts":dict(amendment_methods),
            "index_not_A_but_positive_cover_number_n":not_a_positive,
            "index_A_but_no_positive_cover_number_n":a_not_positive},
        "event_date_outliers_over_90_days":[
            {"accession":r["accession"],"family":r["family"],"index_amendment":r["index_amendment"],
             "filing_date":r["filing_date"].isoformat(),"event_date":r["event_date"].isoformat(),
             "lag_calendar_days":r["lag_calendar_days"]} for r in outliers],
        "interpretation":{"event_date_is_public_knowledge_time":False,
            "knowledge_clock":"SEC-header ACCEPTANCE-DATETIME; first regular session whose open is strictly after acceptance.",
            "13D_vs_13G":"Keep separate. 13G is much more quarter-end weighted and has longer filing-event lags in this weighted sample; this is consistent with different reporting mechanics, not proof of trade dates.",
            "13G_amendments":"Do not treat quarter-end 13G amendments as transaction-level flow; they may be reporting/threshold snapshots.",
            "amendment_marker":"Index /A suffix and cover amendment number are not perfectly concordant; preserve both and reconstruct lineage.",
            "sample_limits":"Stratified 600-filing sample; weighted descriptive estimates only; no inferential confidence intervals."},
        "alpha_test_performed":False,"forward_returns_used":False,
        "bootstrap_or_loo_performed":False,"final_holdout_used":False,
        "production_changed":False,"f80_changed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir",type=Path,required=True)
    p.add_argument("--zip-path",type=Path,default=None)
    p.add_argument("--output-json",type=Path,required=True)
    a=p.parse_args()
    result=audit(a.input_dir,a.zip_path)
    a.output_json.parent.mkdir(parents=True,exist_ok=True)
    a.output_json.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
