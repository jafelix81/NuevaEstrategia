#!/usr/bin/env python3
"""Hash-pinned SEC Schedule 13D/G structured-XML ownership semantics audit."""
from __future__ import annotations
import argparse, csv, hashlib, json, re, xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

PHASE124_RUN_ID = 42073725379
PHASE124_ARTIFACT_ID = 13436764625
PHASE124_ZIP_SHA256 = "85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc"
PHASE124_CSV_SHA256 = "be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5"
VALUES = {str(i): i for i in range(10)} | {chr(65+i): 10+i for i in range(26)} | {"*":36,"@":37,"#":38}

def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def tag(e: ET.Element) -> str: return e.tag.rsplit("}",1)[-1]
def elems(n: ET.Element, names: set[str]): return [x for x in n.iter() if tag(x) in names]
def vals(n: ET.Element, names: set[str]): return [(x.text or "").strip() for x in elems(n,names) if (x.text or "").strip()]
def first(n: ET.Element, names: set[str]):
    v=vals(n,names); return v[0] if v else ""
def valid_cusip(v: str) -> bool:
    v=str(v or "").strip().upper()
    if len(v)!=9 or v[0] not in VALUES or v=="000000000": return False
    total=0
    for i,c in enumerate(v[:8]):
        d=VALUES.get(c)
        if d is None: return False
        if i%2: d*=2
        total+=d//10+d%10
    return v[8].isdigit() and (10-total%10)%10==int(v[8])
def cusip_status(xs):
    if not xs:return "MISSING"
    if len(xs)>1:return "MULTIPLE_DISTINCT_VALUES_RETAIN_ALL"
    x=xs[0]
    if x=="000000000":return "ZERO_PLACEHOLDER"
    if len(x)!=9:return "MALFORMED_LENGTH"
    return "VALID_CHECKSUM" if valid_cusip(x) else "INVALID_CHECK_DIGIT"
def norm_num(v):
    v=(v or "").strip().replace(",","")
    if not v:return ""
    try:return format(Decimal(v).normalize(),"f")
    except InvalidOperation:return v

def extract_xml(raw: str) -> ET.Element:
    for doc in re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>",raw,re.I|re.S):
        fn=re.search(r"<FILENAME>\s*([^\r\n<]+)",doc,re.I)
        ft=re.search(r"<TYPE>\s*([^\r\n<]+)",doc,re.I)
        if not fn or Path(fn.group(1).strip()).name.lower()!="primary_doc.xml":continue
        if not ft or not re.match(r"SCHEDULE\s+13[DG](?:/A)?$",ft.group(1).strip(),re.I):continue
        m=re.search(r"<XML>(.*?)</XML>",doc,re.I|re.S)
        if not m:raise ValueError("primary_doc.xml XML payload missing")
        x=m.group(1).lstrip("\ufeff\r\n\t ")
        x=re.sub(r"^<\?xml\s+[^?]*\?>\s*","",x,count=1,flags=re.I)
        try:return ET.fromstring(x)
        except ET.ParseError as e:raise ValueError(f"invalid primary XML: {e}") from e
    raise ValueError("primary Schedule 13D/G XML not found")

def parse_owner(n: ET.Element, family: str) -> dict[str,str]:
    if family=="13D":
        f={"name":{"reportingPersonName"},"cik":{"reportingPersonCIK"},"no_cik":{"reportingPersonNoCIK"},"aggregate":{"aggregateAmountOwned"},"percent":{"percentOfClass"}}
    else:
        f={"name":{"reportingPersonName"},"cik":{"reportingPersonCIK","reportingPersonCik"},"no_cik":set(),"aggregate":{"reportingPersonBeneficiallyOwnedAggregateNumberOfShares"},"percent":{"classPercent"}}
    f.update({"sole_voting":{"soleVotingPower"},"shared_voting":{"sharedVotingPower"},"sole_dispositive":{"soleDispositivePower"},"shared_dispositive":{"sharedDispositivePower"}})
    return {k:first(n,v) if v else "" for k,v in f.items()}

def parse_filing(row: dict[str,str], raw: bytes) -> dict[str,Any]:
    if not row.get("raw_sha256") or sha(raw)!=row["raw_sha256"]:raise ValueError(f"raw hash mismatch: {row.get('accession')}")
    root=extract_xml(raw.decode("utf-8",errors="replace")); fam=row["family"].strip().upper()
    ns=root.tag.split("}",1)[0].lstrip("{") if "}" in root.tag else ""
    if fam not in {"13D","13G"} or ns.lower()!=f"http://www.sec.gov/edgar/schedule{fam}".lower():raise ValueError("family/namespace mismatch")
    if not first(root,{"submissionType"}).upper().replace("SCHEDULE ","").startswith(fam):raise ValueError("submission type mismatch")
    issuer=next(iter(elems(root,{"issuerInfo"})),None); filer=next(iter(elems(root,{"filer"})),None); cover=next(iter(elems(root,{"coverPageHeader"})),None)
    if issuer is None or filer is None or cover is None:raise ValueError("issuer/filer/cover block missing")
    issuer_cik=first(issuer,{"issuerCIK","issuerCik"}).zfill(10); filer_cik=first(filer,{"cik"}).zfill(10)
    if issuer_cik!=(row.get("subject_cik") or "").zfill(10):raise ValueError("subject issuer CIK/header mismatch")
    if filer_cik!=(row.get("filer_cik") or "").zfill(10):raise ValueError("filer CIK/header mismatch")
    if fam=="13D": cusip_tags={"issuerCUSIP","issuerCusipNumber"}; event_tags={"dateOfEvent"}; owner_tag="reportingPersonInfo"
    else: cusip_tags={"issuerCusip","issuerCusipNumber"}; event_tags={"eventDateRequiresFilingThisStatement"}; owner_tag="coverPageHeaderReportingPersonDetails"
    cusips=list(dict.fromkeys(x.upper() for x in vals(issuer,cusip_tags)))
    owners=[parse_owner(x,fam) for x in elems(root,{owner_tag})]
    if not owners:raise ValueError("reporting-person blocks missing")
    sigs=Counter()
    for o in owners:
        s=tuple(norm_num(o[k]) for k in ("aggregate","percent","sole_voting","shared_voting","sole_dispositive","shared_dispositive"))
        if any(s):sigs[s]+=1
    purpose=vals(root,{"transactionPurpose"}) if fam=="13D" else []
    funds=vals(root,{"fundsSource"}) if fam=="13D" else []
    return {"accession":row["accession"],"quarter":row["quarter"],"family":fam,"is_amendment":row["is_amendment"].lower()=="true","issuer_cik":issuer_cik,"filer_cik":filer_cik,
      "cusips":cusips,"cusip_status":cusip_status(cusips),"class_title":first(cover,{"securitiesClassTitle"}),
      "event_date":first(cover,event_tags),"previous_accession":first(root,{"previousAccessionNumber"}),"amendment_no":first(cover,{"amendmentNo"}),
      "owners":owners,"owner_cik_count":sum(bool(o["cik"]) for o in owners),"owner_no_cik_count":sum(bool(o["no_cik"]) for o in owners),
      "owner_core_complete":sum(bool(o["name"] and o["aggregate"] and o["percent"]) for o in owners),
      "owner_powers_complete":sum(all(o[k] for k in ("sole_voting","shared_voting","sole_dispositive","shared_dispositive")) for o in owners),
      "repeated_signature_excess":sum(n-1 for n in sigs.values() if n>1),"has_repeated_signature":any(n>1 for n in sigs.values()),
      "all_same_signature":len(owners)>1 and len(sigs)==1 and next(iter(sigs.values()),0)==len(owners),
      "purpose_chars":sum(map(len,purpose)),"funds_present":bool(funds)}

def audit(input_dir: Path) -> dict[str,Any]:
    cp=input_dir/"phase124_global_13dg_submission_audit.csv"; payload=cp.read_bytes()
    if sha(payload)!=PHASE124_CSV_SHA256:raise ValueError("Phase 124 CSV hash mismatch")
    with cp.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    if len(rows)!=600 or len({r["accession"] for r in rows})!=600:raise ValueError("Phase 124 sample dimensions changed")
    actual=[r for r in rows if r.get("is_index_alias","").lower()!="true"]
    xml=[r for r in actual if r.get("xml_present","").lower()=="true"]
    if len(actual)!=599 or len(xml)!=102:raise ValueError("actual/XML sample counts changed")
    mandatory=[r for r in actual if r.get("mandatory_xml_expected","").lower()=="true"]
    if len(mandatory)!=99 or sum(r in xml for r in mandatory)!=99:raise ValueError("mandatory XML coverage changed")
    parsed=[parse_filing(r,(input_dir/r["raw_file"]).read_bytes()) for r in xml]
    if len(parsed)!=102 or any(not x["event_date"] for x in parsed):raise ValueError("structured XML parse/event-date coverage changed")
    by={}
    for fam in ("13D","13G"):
        fs=[x for x in parsed if x["family"]==fam]; owners=[o for x in fs for o in x["owners"]]; am=[x for x in fs if x["is_amendment"]]
        by[fam]={"filings":len(fs),"quarters":sorted({x["quarter"] for x in fs}),"amendments":len(am),"amendments_with_previous_accession":sum(bool(x["previous_accession"]) for x in am),
          "amendment_number_present":sum(bool(x["amendment_no"]) for x in am),"cusip_present":sum(bool(x["cusips"]) for x in fs),
          "cusip_valid_checksum":sum(x["cusip_status"]=="VALID_CHECKSUM" for x in fs),"cusip_zero_placeholder":sum(x["cusip_status"]=="ZERO_PLACEHOLDER" for x in fs),
          "cusip_bad_check_digit":sum(x["cusip_status"]=="INVALID_CHECK_DIGIT" for x in fs),"cusip_malformed":sum(x["cusip_status"]=="MALFORMED_LENGTH" for x in fs),
          "reporting_person_blocks":len(owners),"owner_names":sum(bool(o["name"]) for o in owners),"owner_cik":sum(bool(o["cik"]) for o in owners),"owner_no_cik_flag":sum(bool(o["no_cik"]) for o in owners),
          "owner_core_complete":sum(bool(o["name"] and o["aggregate"] and o["percent"]) for o in owners),"owner_all_four_powers":sum(all(o[k] for k in ("sole_voting","shared_voting","sole_dispositive","shared_dispositive")) for o in owners),
          "filings_with_repeated_signature":sum(x["has_repeated_signature"] for x in fs),"filings_all_owners_same_signature":sum(x["all_same_signature"] for x in fs),
          "repeated_signature_excess_owner_rows":sum(x["repeated_signature_excess"] for x in fs),"purpose_text_present":sum(x["purpose_chars"]>0 for x in fs),"purpose_text_chars":sum(x["purpose_chars"] for x in fs),"funds_source_present":sum(x["funds_present"] for x in fs)}
    q=Counter(x["quarter"] for x in parsed); am=sum(x["amendments"] for x in by.values()); prev=sum(x["amendments_with_previous_accession"] for x in by.values())
    owners=sum(x["reporting_person_blocks"] for x in by.values()); core=sum(x["owner_core_complete"] for x in by.values()); powers=sum(x["owner_all_four_powers"] for x in by.values())
    repeated=sum(x["filings_with_repeated_signature"] for x in by.values()); excess=sum(x["repeated_signature_excess_owner_rows"] for x in by.values())
    cusip_valid=sum(x["cusip_valid_checksum"] for x in by.values()); zero=sum(x["cusip_zero_placeholder"] for x in by.values()); bad=sum(x["cusip_bad_check_digit"] for x in by.values()); malformed=sum(x["cusip_malformed"] for x in by.values())
    return {"phase":156,"status":"COMPLETED_STRUCTURED_XML_FIELD_AND_NONADDITIVE_OWNERSHIP_AUDIT",
      "source":{"phase124_run_id":PHASE124_RUN_ID,"phase124_artifact_id":PHASE124_ARTIFACT_ID,"phase124_artifact_zip_sha256":PHASE124_ZIP_SHA256,"phase124_csv_sha256":sha(payload),
        "sample_rows":600,"actual_13dg_filings":599,"structured_xml_filings":102,"xml_share_pct":round(100*102/599,4),"mandatory_xml_expected":99,"mandatory_xml_present":99,
        "voluntary_pre_mandatory_xml":3,"structured_xml_quarters":sorted(q),"structured_xml_quarter_count":len(q),"quarter_counts":dict(sorted(q.items())),
        "subject_issuer_and_filer_header_concordance":"PASS_ALL_102","raw_submission_hashes":"PASS_ALL_102"},
      "by_family":by,
      "combined":{"filings":102,"cusip_present":102,"cusip_valid_checksum":cusip_valid,"cusip_zero_placeholder":zero,"cusip_bad_check_digit":bad,"cusip_malformed":malformed,
        "reporting_person_blocks":owners,"owner_core_complete":core,"owner_all_four_powers":powers,"amendments":am,"amendments_with_previous_accession":prev,"previous_accession_pct":round(100*prev/am,4),
        "filings_with_repeated_signature":repeated,"repeated_signature_excess_owner_rows":excess},
      "decision":{"structured_history":"Mandatory XML starts 2024-12-18; only 8 sampled quarters through 2026Q3, too short alone for multi-regime OOS.",
        "identity":"102/102 issuer/filer header matches; 98 valid CUSIPs, 2 zero placeholders, 1 bad check digit, 1 malformed. Current OpenFIGI is not effective-dated.",
        "owners":"13G reporting-person CIK absent in 158/158 blocks; 13D CIK present in 90/152. Never substitute filer CIK.",
        "aggregation":"Identical ownership tuples repeat in 48/102 filings; do not sum reporting-person rows without group/control adjudication.",
        "amendments":"Only 32/59 amendments have previousAccessionNumber; missing parent is unresolved, not an original filing.",
        "alpha":"NO_RETURN_TEST_NO_ALPHA_CLAIM","f80_modified":False,"final_holdout_used":False}}

def main():
    p=argparse.ArgumentParser();p.add_argument("--input-dir",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    out=audit(a.input_dir);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"phase":156,"status":out["status"],"source":out["source"],"combined":out["combined"],"decision":out["decision"]},indent=2))
if __name__=="__main__":main()