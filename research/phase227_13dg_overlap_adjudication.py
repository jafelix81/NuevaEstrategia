#!/usr/bin/env python3
"""Phase 227: separate all-zero repeated 13D/G tuples from positive overlap.

Uses the Phase 226 hash-pinned source parser; no returns or alpha are computed.
"""
import argparse, csv, json, hashlib, re, xml.etree.ElementTree as ET
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
SOURCE_ZIP_SHA256="85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc"
SOURCE_CSV_SHA256="be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5"
OWNER_TAGS={"13D":"reportingPersonInfo","13G":"coverPageHeaderReportingPersonDetails"}
AGG={"13D":"aggregateAmountOwned","13G":"reportingPersonBeneficiallyOwnedAggregateNumberOfShares"}
PCT={"13D":"percentOfClass","13G":"classPercent"}
GROUP={"13D":"memberOfGroup","13G":"memberGroup"}
FIELDS=("aggregate","percent","sole_voting","shared_voting","sole_dispositive","shared_dispositive")
def local_name(e): return e.tag.rsplit("}",1)[-1]
def first(e,names):
    if isinstance(names,str): names={names}
    for x in e.iter():
        if local_name(x) in names and (x.text or "").strip(): return " ".join((x.text or "").split())
    return ""
def extract_xml(raw):
    for doc in re.findall(rb"<DOCUMENT>(.*?)</DOCUMENT>",raw,re.I|re.S):
        fn=re.search(rb"<FILENAME>\s*([^\r\n<]+)",doc,re.I); typ=re.search(rb"<TYPE>\s*([^\r\n<]+)",doc,re.I)
        if not fn or Path(fn.group(1).decode("utf-8","replace").strip()).name.lower()!="primary_doc.xml": continue
        if not typ or not re.match(rb"SCHEDULE\s+13[DG](?:/A)?$",typ.group(1).strip(),re.I): continue
        m=re.search(rb"<XML>(.*?)</XML>",doc,re.I|re.S)
        if not m: raise ValueError("primary_xml_payload_missing")
        x=m.group(1).decode("utf-8-sig","replace").strip(); x=re.sub(r"^<\?xml\s+[^?]*\?>\s*","",x,count=1,flags=re.I)
        return ET.fromstring(x)
    raise ValueError("primary_schedule_13dg_xml_missing")
def parse_owner(e,fam):
    return {"aggregate":first(e,AGG[fam]),"percent":first(e,PCT[fam]),"sole_voting":first(e,"soleVotingPower"),"shared_voting":first(e,"sharedVotingPower"),"sole_dispositive":first(e,"soleDispositivePower"),"shared_dispositive":first(e,"sharedDispositivePower")}
def signature(o): return tuple(str(number(o[k]).normalize()) if number(o[k]) is not None else str(o[k] or "") for k in FIELDS)

EXPECTED = {
    "13D": {"groups": 26, "positive": 25, "zero": 1, "positive_rows": 90, "zero_rows": 4, "positive_filings": 20, "zero_only_filings": 1},
    "13G": {"groups": 32, "positive": 25, "zero": 7, "positive_rows": 72, "zero_rows": 23, "positive_filings": 21, "zero_only_filings": 6, "mixed_filings": 1},
}

def number(v):
    try: return Decimal(str(v).replace(",", "")) if str(v).strip() else None
    except InvalidOperation: return None

def classify(sig):
    if not any(sig): return "EMPTY"
    vals=[number(v) for v in sig]
    if any(v is None for v in vals): return "UNKNOWN_OR_PARTIAL"
    if all(v == 0 for v in vals): return "ZERO_POSITION"
    if vals[0] > 0: return "POSITIVE_POSITION"
    return "NONPOSITIVE_OR_INCONSISTENT"

def run(input_dir: Path, source_zip: Path):
    if hashlib.sha256(source_zip.read_bytes()).hexdigest()!=SOURCE_ZIP_SHA256: raise ValueError("artifact_zip_hash_mismatch")
    csv_path=input_dir / "phase124_global_13dg_submission_audit.csv"
    csv_bytes=csv_path.read_bytes()
    if hashlib.sha256(csv_bytes).hexdigest()!=SOURCE_CSV_SHA256: raise ValueError("source_csv_hash_mismatch")
    with csv_path.open(encoding="utf-8-sig", newline="") as f: all_rows=list(csv.DictReader(f))
    if len(all_rows)!=600: raise ValueError("source_index_row_count_mismatch")
    actual=[r for r in all_rows if r.get("is_index_alias", "").lower()!="true"]
    if len(actual)!=599: raise ValueError("actual_filing_count_mismatch")
    rows=[r for r in actual if r.get("xml_present", "").lower()=="true"]
    if len(rows)!=102: raise ValueError("xml_filing_count_mismatch")
    parsed=[]
    for r in rows:
        raw=(input_dir / r["raw_file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=r["raw_sha256"]: raise ValueError("raw_submission_hash_mismatch:"+r["accession"])
        root=extract_xml(raw)
        fam=r["family"].upper(); owners=[]
        for e in root.iter():
            if local_name(e)==OWNER_TAGS[fam]: owners.append(parse_owner(e,fam))
        groups=defaultdict(list)
        for owner in owners:
            sig=signature(owner)
            if any(sig): groups[sig].append(owner)
        repeated=[(sig,members,classify(sig)) for sig,members in groups.items() if len(members)>1]
        parsed.append((fam,repeated))
    result={}
    for fam in ("13D", "13G"):
        filings=[g for family,g in parsed if family==fam]
        groups=[x for filing in filings for x in filing]
        positive=[x for x in groups if x[2]=="POSITIVE_POSITION"]
        zero=[x for x in groups if x[2]=="ZERO_POSITION"]
        row={"filings":len(filings),"any_repeat_filings":sum(bool(f) for f in filings),"groups":len(groups),"positive":len(positive),"zero":len(zero),"positive_rows":sum(len(x[1]) for x in positive),"zero_rows":sum(len(x[1]) for x in zero),"positive_filings":sum(any(x[2]=="POSITIVE_POSITION" for x in f) for f in filings),"zero_only_filings":sum(bool(f) and all(x[2]=="ZERO_POSITION" for x in f) for f in filings),"mixed_filings":sum(any(x[2]=="ZERO_POSITION" for x in f) and any(x[2]=="POSITIVE_POSITION" for x in f) for f in filings)}
        for key,value in EXPECTED[fam].items():
            if row[key] != value: raise ValueError(f"{fam}:{key}:{row[key]}!={value}")
        result[fam]=row
    allgroups=[x for _,filing in parsed for x in filing]
    combined={"filings":len(parsed),"any_repeat_filings":sum(bool(f) for _,f in parsed),"groups":len(allgroups),"positive":sum(x[2]=="POSITIVE_POSITION" for x in allgroups),"zero":sum(x[2]=="ZERO_POSITION" for x in allgroups),"positive_rows":sum(len(x[1]) for x in allgroups if x[2]=="POSITIVE_POSITION"),"zero_rows":sum(len(x[1]) for x in allgroups if x[2]=="ZERO_POSITION"),"positive_filings":sum(any(x[2]=="POSITIVE_POSITION" for x in f) for _,f in parsed),"zero_only_filings":sum(bool(f) and all(x[2]=="ZERO_POSITION" for x in f) for _,f in parsed),"mixed_filings":sum(any(x[2]=="ZERO_POSITION" for x in f) and any(x[2]=="POSITIVE_POSITION" for x in f) for _,f in parsed)}
    if combined != {"filings":102,"any_repeat_filings":48,"groups":58,"positive":50,"zero":8,"positive_rows":162,"zero_rows":27,"positive_filings":41,"zero_only_filings":7,"mixed_filings":1}:
        raise ValueError(f"combined_counts_mismatch:{combined}")
    return {"phase":227,"status":"PASS_ZERO_SIGNATURE_EXCLUSION","source_artifact_id":13436764625,"summary":{"13D":result["13D"],"13G":result["13G"],"combined":combined},"controls":{"alpha_test":False,"returns_used":False,"holdout_used":False,"production_changed":False,"f80_changed":False,"ownership_rows_summed":False}}

def main():
    p=argparse.ArgumentParser();p.add_argument("--input-dir",type=Path,required=True);p.add_argument("--source-zip",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    r=run(a.input_dir,a.source_zip);a.output.write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8");print(json.dumps(r,indent=2))
if __name__=="__main__":raise SystemExit(main())
