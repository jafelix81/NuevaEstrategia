#!/usr/bin/env python3
"""Descriptive SEC Form 345 issuer-symbol/security-title audit; no alpha inference."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, re, zipfile
from collections import defaultdict
from pathlib import Path

ARTIFACT_ID=12781850078
RUN_ID=40606706518
OUTER_SHA="203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66"
PERIODS={
 "2012Q1":("2012q1_form345.zip","0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357"),
 "2026Q3":("2026q3_form345.zip","a4e6a681cfcfa43a3d9d3b1de6f5da14c200b99".replace("a3d9d3b1de6f5da14c200b99","a3d9d3b1de6f5da14c200b99"))}
# Exact nested archive hashes are frozen below.
PERIODS["2026Q3"]=("2026q3_form345.zip","a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3")
FORMS={"4","4/A"}
SENTINELS={"","NONE","N/A","NA","NULL","-","[NONE]"}
CLASS_RE=re.compile(r"\b(CLASS|SERIES)\s+([A-Z0-9]+)\b",re.I)

def sha(b): return hashlib.sha256(b).hexdigest()
def sentinel(v): return str(v or "").strip().upper() in SENTINELS

def class_tokens(titles):
    out=set()
    for title in titles:
        t=re.sub(r"\s+"," ",str(title or "")).strip().upper()
        if "COMMON" in t and ("STOCK" in t or "SHARE" in t):
            m=CLASS_RE.search(t)
            if m: out.add((m.group(1).upper(),m.group(2).upper()))
    return out

def summarize_period(period, submissions, nonderiv):
    forms=[r for r in submissions if str(r.get("DOCUMENT_TYPE","")).strip() in FORMS]
    by_acc={str(r.get("ACCESSION_NUMBER","")).strip():r for r in forms}
    linked=[r for r in nonderiv if str(r.get("ACCESSION_NUMBER","")).strip() in by_acc]
    groups=defaultdict(list)
    for r in linked:
        s=by_acc[str(r.get("ACCESSION_NUMBER","")).strip()]
        groups[(str(s.get("ISSUERCIK","")).strip().lstrip("0"),str(r.get("ACCESSION_NUMBER","")).strip())].append(r)
    multi_titles=multi_common=multi_classes=multi_class_single=multi_class_comma=0
    for (_,acc),rows in groups.items():
        titles={re.sub(r"\s+"," ",str(x.get("SECURITY_TITLE","") or "")).strip().upper() for x in rows}
        multi_titles += len(titles)>1
        common={t for t in titles if "COMMON" in t and ("STOCK" in t or "SHARE" in t)}
        multi_common += len(common)>1
        tokens=class_tokens(titles)
        if len(tokens)>1:
            multi_classes+=1
            raw=by_acc[acc].get("ISSUERTRADINGSYMBOL","")
            if "," in str(raw): multi_class_comma+=1
            else: multi_class_single+=1
    valid=[r for r in forms if not sentinel(r.get("ISSUERTRADINGSYMBOL",""))]
    ciks_by_symbol=defaultdict(set); symbols_by_cik=defaultdict(set)
    for r in valid:
        cik=str(r.get("ISSUERCIK","")).strip().lstrip("0")
        sym=str(r.get("ISSUERTRADINGSYMBOL","") or "").strip().upper()
        if cik and sym:
            ciks_by_symbol[sym].add(cik); symbols_by_cik[cik].add(sym)
    sent_forms=sum(sentinel(r.get("ISSUERTRADINGSYMBOL","")) for r in forms)
    sent_rows=sum(sentinel(by_acc[str(r.get("ACCESSION_NUMBER","")).strip()].get("ISSUERTRADINGSYMBOL","")) for r in linked)
    return {
      "period":period,
      "form4_and_4a_submissions":len(forms),
      "distinct_issuer_ciks":len({str(r.get("ISSUERCIK","")).strip().lstrip("0") for r in forms if str(r.get("ISSUERCIK","")).strip()}),
      "nonderivative_form4_rows":len(linked),
      "distinct_nonderivative_form4_accessions":len(groups),
      "issuer_symbol_raw_field":{
        "nonblank_filings":sum(bool(str(r.get("ISSUERTRADINGSYMBOL","")).strip()) for r in forms),
        "sentinel_filings":sent_forms,
        "sentinel_filing_pct":round(100*sent_forms/len(forms),6) if forms else None,
        "comma_delimited_filings":sum("," in str(r.get("ISSUERTRADINGSYMBOL","")) for r in forms),
        "exchange_prefixed_filings":sum(":" in str(r.get("ISSUERTRADINGSYMBOL","")) for r in forms),
        "numeric_only_filings":sum(bool(re.fullmatch(r"\d+",str(r.get("ISSUERTRADINGSYMBOL","")).strip())) for r in forms),
        "exact_raw_symbol_values_linked_to_multiple_issuer_ciks":sum(len(v)>1 for v in ciks_by_symbol.values()),
        "issuers_with_multiple_distinct_non_sentinel_symbol_values_in_quarter":sum(len(v)>1 for v in symbols_by_cik.values())
      },
      "nonderivative_rows_with_sentinel_issuer_symbol":sent_rows,
      "nonderivative_sentinel_row_pct":round(100*sent_rows/len(linked),6) if linked else None,
      "security_title_diagnostics":{
        "accessions_with_multiple_distinct_titles":multi_titles,
        "accessions_with_multiple_common_stock_or_share_titles":multi_common,
        "accessions_with_multiple_common_class_or_series_tokens":multi_classes,
        "multi_class_accessions_with_single_issuer_symbol_string":multi_class_single,
        "multi_class_accessions_with_comma_delimited_issuer_symbol_string":multi_class_comma
      },
      "interpretation":{
        "issuer_trading_symbol_is_submission_level_not_transaction_row_level":True,
        "symbol_field_alone_resolves_class_specific_security_identity":False,
        "multi_class_accessions_require_security_title_to_listing_crosswalk":True,
        "ticker_reuse_and_multiple_issuer_symbol_values_require_effective_dates":True
      }
    }

def analyze_archive(path, enforce_hash=True):
    raw=Path(path).read_bytes(); outer_hash=sha(raw)
    if enforce_hash and outer_hash!=OUTER_SHA: raise ValueError("outer ZIP SHA-256 mismatch")
    periods={}
    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        for period,(member,expected) in PERIODS.items():
            nested=outer.read(member); nested_hash=sha(nested)
            if enforce_hash and nested_hash!=expected: raise ValueError(f"{period} nested ZIP SHA-256 mismatch")
            with zipfile.ZipFile(io.BytesIO(nested)) as z:
                sub=list(csv.DictReader(io.StringIO(z.read("SUBMISSION.tsv").decode("utf-8-sig")),delimiter="\t"))
                nd=list(csv.DictReader(io.StringIO(z.read("NONDERIV_TRANS.tsv").decode("utf-8-sig")),delimiter="\t"))
            periods[period]=summarize_period(period,sub,nd)
            periods[period]["source"]={"member":member,"nested_zip_sha256":nested_hash,"submission_rows":len(sub),"nonderivative_rows_all_forms":len(nd)}
    return {"phase":453,"source":{"artifact_id":ARTIFACT_ID,"workflow_run_id":RUN_ID,"outer_zip_sha256":outer_hash,"outer_zip_bytes":len(raw)},"periods":periods,
      "decision":{"disposition":"DIRECT_ISSUER_SYMBOL_FIELD_CONFIRMED_BUT_NOT_A_SECURITY_MASTER","legacy_html_53_of_96_is_not_a_ceiling_on_bulk_dataset_symbol_availability":True,"security_identity_gate_passed":False,"alpha_authorized":False,"frozen_baseline_changed":False}}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True,type=Path); p.add_argument("--output",type=Path); p.add_argument("--allow-noncanonical-hash",action="store_true"); a=p.parse_args()
    result=analyze_archive(a.input,not a.allow_noncanonical_hash); data=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.output:a.output.write_text(data,encoding="utf-8")
    else:print(data)
if __name__=="__main__":main()
