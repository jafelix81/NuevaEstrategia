#!/usr/bin/env python3
"""Phase 455: exact as-filed Form 4 candidate overlap with the frozen 335 ticker snapshot."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, zipfile
from collections import defaultdict
from pathlib import Path

ARTIFACT_SHA256 = "16614b404f007b78f47951ef84604660ea6612f0c86f1b2ba5a6fa7b7d52d80c"
UNIVERSE_SHA256 = "f850655a22a8843dad90e9562b3152b9ca064560586109022b5bfd205a003dda"
UNIVERSE_BLOB_SHA1 = "7edbd62b4fb34a6123276e4ce45cb3c1c62479c7"
UNIVERSE_COMMIT = "1aa1b91f383ce9cef375a43e775c736a27356a5f"
PERIOD_HASHES = {
 "2006Q1":"62becdadbe5eaff68f03edefe2ba2357c8bb498a1f825b697003e087cf98e6ce",
 "2012Q1":"0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357",
 "2023Q1":"0b476188f52a0862e71886eb31a81f6345fc6616403b52188484aef0438cfcfb",
 "2023Q2":"7e636787231ae0f00accf5c3627298402dedd1aefffd7c50fb48292e5d3a8fbb",
 "2025Q3":"9c57f272b7230500771f661bc1fe181527ed6b76a6f45d23a910c7fc7e9fcfa4",
 "2026Q3":"a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3",
}
EXPECTED_ROWS = {"2006Q1":10,"2012Q1":102,"2023Q1":59,"2023Q2":92,"2025Q3":65,"2026Q3":85}
SENTINELS = {"","NONE","N/A","NA","NULL","-","[NONE]"}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\\0".encode()+data).hexdigest()

def load_universe(path: Path, enforce_hash: bool=True) -> set[str]:
    raw=path.read_bytes()
    if enforce_hash and (sha(raw)!=UNIVERSE_SHA256 or blob_sha(raw)!=UNIVERSE_BLOB_SHA1):
        raise ValueError("frozen 335 ticker snapshot hash mismatch")
    rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if not rows or list(rows[0])!=["Ticker"]:
        raise ValueError("universe CSV must contain exactly the Ticker column")
    tickers=[str(r["Ticker"] or "").strip().upper() for r in rows]
    if len(tickers)!=335 or any(not x for x in tickers) or len(set(tickers))!=335:
        raise ValueError("expected exactly 335 unique nonblank tickers")
    return set(tickers)

def classify_symbol(raw, universe):
    s=str(raw or "").strip().upper()
    if s in SENTINELS: return s,"unknown"
    if any(c in s for c in ",:;") or any(c.isspace() for c in s): return s,"ambiguous_format"
    return s,"exact_335_match" if s in universe else "outside_snapshot"

def summarize(rows, universe, require_all_periods=False):
    if not rows: raise ValueError("candidate panel is empty")
    enriched=[]
    for r in rows:
        if any(not str(r.get(k) or "").strip() for k in ("accession","issuer_cik","filing_date","issuer_symbol_as_filed")):
            raise ValueError("candidate row missing required identity field")
        s,status=classify_symbol(r.get("issuer_symbol_as_filed"),universe)
        enriched.append({**r,"_symbol":s,"_status":status})
    def group_match(group):
        return len({x["_symbol"] for x in group})==1 and {x["_status"] for x in group}=={"exact_335_match"}
    def counts(group):
        acc=defaultdict(list); cik=defaultdict(list); event=defaultdict(list)
        for r in group:
            acc[r["accession"]].append(r); cik[r["issuer_cik"]].append(r)
            event[(r["issuer_cik"],r["filing_date"])].append(r)
        return {
          "candidate_rows":len(group),"accessions":len(acc),"issuer_ciks":len(cik),
          "issuer_filing_events":len(event),
          "exact_match_rows":sum(x["_status"]=="exact_335_match" for x in group),
          "exact_match_accessions":sum(group_match(v) for v in acc.values()),
          "exact_match_issuer_ciks":sum(group_match(v) for v in cik.values()),
          "exact_match_issuer_filing_events":sum(group_match(v) for v in event.values()),
          "unique_exact_match_symbols":len({x["_symbol"] for x in group if x["_status"]=="exact_335_match"}),
          "ambiguous_format_rows":sum(x["_status"]=="ambiguous_format" for x in group),
          "unknown_symbol_rows":sum(x["_status"]=="unknown" for x in group),
          "outside_snapshot_rows":sum(x["_status"]=="outside_snapshot" for x in group),
        }
    periods=sorted(PERIOD_HASHES) if require_all_periods else sorted({r.get("period") for r in enriched})
    per_period={}
    for period in periods:
        part=[r for r in enriched if r.get("period")==period]
        if not part: raise ValueError(f"missing candidate events for {period}")
        per_period[period]=counts(part)
    cik_symbols=defaultdict(set); symbol_ciks=defaultdict(set)
    for r in enriched:
        cik_symbols[r["issuer_cik"]].add(r["_symbol"]); symbol_ciks[r["_symbol"]].add(r["issuer_cik"])
    events=defaultdict(list)
    for r in enriched:
        if r["_status"]=="exact_335_match": events[(r["issuer_cik"],r["filing_date"])].append(r)
    examples=[]
    for (cik,filing_date),group in sorted(events.items(),key=lambda x:(x[0][1],x[0][0])):
        if len({x["_symbol"] for x in group})==1:
            examples.append({"periods":sorted({x["period"] for x in group}),"issuer_cik":cik,
              "ticker":group[0]["_symbol"],"filing_date":filing_date,
              "accessions":sorted({x["accession"] for x in group}),"candidate_transaction_rows":len(group)})
    return {"periods":per_period,"overall":counts(enriched),
      "identity_diagnostics":{"unique_candidate_issuer_ciks":len(cik_symbols),
        "issuer_ciks_with_multiple_as_filed_symbols_across_sample":sum(len(v)>1 for v in cik_symbols.values()),
        "raw_symbols_linked_to_multiple_issuer_ciks":sum(len(v)>1 for v in symbol_ciks.values()),
        "unique_raw_symbols":len(symbol_ciks),
        "unique_exact_snapshot_symbols":len({x["_symbol"] for x in enriched if x["_status"]=="exact_335_match"})},
      "exact_match_event_examples":examples,
      "controls":{"matching_rule":"outer trim + uppercase + exact single-symbol equality",
        "exchange_prefixes_stripped":False,"comma_delimited_symbols_split":False,
        "ticker_changes_inferred":False,"historical_universe_membership_verified":False,
        "security_class_or_listing_identity_verified":False,"filing_date_is_exact_first_public_receipt":False,
        "strict_pit_admitted":False,"alpha_authorized":False,"f80_changed":False}}

def analyze(artifact_path: Path, universe_path: Path, enforce_hash: bool=True):
    raw=artifact_path.read_bytes()
    if enforce_hash and sha(raw)!=ARTIFACT_SHA256: raise ValueError("Phase 342 artifact SHA-256 mismatch")
    universe=load_universe(universe_path,enforce_hash)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        payload=json.loads(z.read("phase342_output/phase342_sec_insider_bulk_sample_audit.json"))
        rows=[]
        for period,expected_hash in PERIOD_HASHES.items():
            member=f"phase342_input/{period.lower()}_form345.zip"
            if sha(z.read(member))!=expected_hash: raise ValueError(f"{period} nested SEC archive hash mismatch")
            candidates=payload["archives"][period].get("candidate_events",[])
            if len(candidates)!=EXPECTED_ROWS[period]: raise ValueError(f"{period} candidate row count mismatch")
            rows.extend({**r,"period":period} for r in candidates)
    if len(rows)!=413: raise ValueError(f"expected 413 candidate rows, found {len(rows)}")
    result=summarize(rows,universe,require_all_periods=True)
    result.update({"phase":455,"source":{
      "phase342_run_id":43265704634,"phase342_artifact_id":13965917386,
      "phase342_artifact_sha256":sha(raw),"candidate_rows":len(rows),
      "universe_source_commit":UNIVERSE_COMMIT,
      "universe_source_path":"research/phase44_frozen_universe_335_tickers.csv",
      "universe_git_blob_sha1":blob_sha(universe_path.read_bytes()),
      "universe_sha256":sha(universe_path.read_bytes()),"universe_size":len(universe)},
      "decision":{"disposition":"DESCRIPTIVE_OVERLAP_ONLY; HISTORICAL_MEMBERSHIP_AND_SECURITY_IDENTITY_NOT_ESTABLISHED",
        "continue_candidate_specific_identity_audit":True,
        "expand_to_full_quarterly_census_before_any_event_study":True,
        "alpha_authorized":False,"frozen_baseline_changed":False}})
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifact",type=Path,required=True); p.add_argument("--universe",type=Path,required=True)
    p.add_argument("--output",type=Path); p.add_argument("--allow-noncanonical-hash",action="store_true")
    a=p.parse_args(); result=analyze(a.artifact,a.universe,not a.allow_noncanonical_hash)
    out=json.dumps(result,indent=2,sort_keys=True)+"\\n"
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(out,encoding="utf-8")
    else: print(out,end="")
if __name__=="__main__": main()
