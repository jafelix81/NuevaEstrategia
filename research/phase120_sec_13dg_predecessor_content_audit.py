#!/usr/bin/env python3
"""Fetch and reconcile 45 SEC 13D/13G predecessor submissions from Phase 119.

No return data, feature engineering, or alpha tests are performed.
"""
from __future__ import annotations
import argparse, csv, hashlib, html, json, re, time, urllib.error, urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

SEC_BASE = "https://www.sec.gov/Archives/"
DEFAULT_UA = "jafelix81 research contact jafelix@gmail.com"

def norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().upper()

def norm_cik(value: str | None) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(10) if digits else None

def norm_cusip(value: str | None) -> str | None:
    value = re.sub(r"[^A-Z0-9]", "", norm(value))
    if len(value) != 9 or value == "000000000":
        return None
    return value

def norm_form(value: str | None) -> str:
    value = norm(value)
    if value.startswith("SCHEDULE "):
        value = "SC " + value[len("SCHEDULE "):]
    return value

def form_family(value: str | None) -> str | None:
    value = norm_form(value)
    if value in {"SC 13D", "SC 13D/A"}: return "13D"
    if value in {"SC 13G", "SC 13G/A"}: return "13G"
    return None

def tag_values(root: ET.Element, tag: str) -> list[str]:
    return [e.text.strip() for e in root.iter()
            if e.tag.split("}")[-1].lower() == tag.lower() and e.text and e.text.strip()]

def first_tag(root: ET.Element, *tags: str) -> str | None:
    for tag in tags:
        values = tag_values(root, tag)
        if values: return values[0]
    return None

def xml_root(raw: str) -> ET.Element | None:
    for block in re.findall(r"<XML>(.*?)</XML>", raw, flags=re.I | re.S):
        if "edgarSubmission" not in block: continue
        try: return ET.fromstring(block.strip())
        except ET.ParseError: continue
    return None

def parse_header(raw: str) -> dict:
    match = re.search(r"<SEC-HEADER>(.*?)</SEC-HEADER>", raw, flags=re.I | re.S)
    header = match.group(1) if match else raw[:100000]
    def one(pattern):
        m = re.search(pattern, header, flags=re.I | re.S)
        return m.group(1).strip() if m else None
    def section_cik(section):
        return norm_cik(one(rf"{section}\s*:.*?CENTRAL INDEX KEY\s*:\s*(\d+)"))
    filed = one(r"FILED AS OF DATE\s*:\s*(\d{8})")
    return {
        "accession": one(r"ACCESSION NUMBER\s*:\s*([0-9-]{20})"),
        "form": norm_form(one(r"CONFORMED SUBMISSION TYPE\s*:\s*([A-Z0-9 /-]+)")),
        "filed_date": f"{filed[:4]}-{filed[4:6]}-{filed[6:8]}" if filed else None,
        "acceptance_datetime": one(r"ACCEPTANCE-DATETIME>\s*(\d{14})"),
        "header_subject_cik": section_cik("SUBJECT COMPANY"),
        "header_filer_cik": section_cik("FILED BY"),
        "subject_name": one(r"SUBJECT COMPANY\s*:.*?COMPANY CONFORMED NAME\s*:\s*([^\r\n]+)"),
        "filer_name": one(r"FILED BY\s*:.*?COMPANY CONFORMED NAME\s*:\s*([^\r\n]+)"),
    }

def parse_xml_snapshot(raw: str, family: str | None) -> dict:
    root = xml_root(raw)
    if root is None: return {"xml_present": False, "cusip": None, "class_title": None, "persons": []}
    issuer = first_tag(root, "issuerCIK", "issuerCik")
    filer = first_tag(root, "cik")
    cusip = first_tag(root, "issuerCUSIP", "issuerCusip")
    class_title = first_tag(root, "securitiesClassTitle")
    person_tag = "reportingPersonInfo" if family == "13D" else "coverPageHeaderReportingPersonDetails"
    persons = []
    for node in root.iter():
        if node.tag.split("}")[-1] != person_tag: continue
        def local_first(*tags):
            for tag in tags:
                values = [e.text.strip() for e in node.iter()
                          if e.tag.split("}")[-1].lower() == tag.lower() and e.text and e.text.strip()]
                if values: return values[0]
            return None
        persons.append({
            "cik": norm_cik(local_first("reportingPersonCIK")) if family == "13D" else None,
            "name": local_first("reportingPersonName"),
            "percent": local_first("percentOfClass" if family == "13D" else "classPercent"),
            "amount": local_first("aggregateAmountOwned" if family == "13D" else "reportingPersonBeneficiallyOwnedAggregateNumberOfShares"),
            "type": local_first("typeOfReportingPerson"),
        })
    return {"xml_present": True, "xml_issuer_cik": norm_cik(issuer), "xml_filer_cik": norm_cik(filer),
            "cusip": norm_cusip(cusip), "class_title": class_title, "persons": persons,
            "event_date": first_tag(root, "dateOfEvent") if family == "13D" else first_tag(root, "eventDateRequiresFilingThisStatement"),
            "amendment_no": first_tag(root, "amendmentNo"),
            "previous_accession": first_tag(root, "previousAccessionNumber")}

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.parts=[]
    def handle_data(self, data):
        value=re.sub(r"\s+"," ",data).strip()
        if value: self.parts.append(value)

def legacy_fields(raw: str) -> dict:
    # Conservative field probe only; not a full legacy ownership-table parser.
    docs = re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>", raw, flags=re.I | re.S)
    primary = next((d for d in docs if re.search(r"<TYPE>\s*(?:SC\s+)?13[DG]", d, flags=re.I)), raw)
    parser=TextExtractor(); parser.feed(primary)
    text=html.unescape(" ".join(parser.parts))
    cusips=[]
    for m in re.finditer(r"CUSIP(?:\s+(?:NO\.?|NUMBER))?\s*[:#]?\s*([A-Z0-9]{6,9})", text, flags=re.I):
        c=norm_cusip(m.group(1))
        if c and c not in cusips: cusips.append(c)
    class_title=None
    m=re.search(r"TITLE OF CLASS OF SECURITIES\s*[:\-]?\s*([A-Z0-9][A-Z0-9 ,.&()/'-]{2,100})", text, flags=re.I)
    if m: class_title=re.sub(r"\s+"," ",m.group(1)).strip(" :-")
    return {"xml_present":False, "cusip":cusips[0] if len(cusips)==1 else None,
            "cusip_candidates":cusips, "class_title":class_title, "persons":[]}

def parse_submission(raw: str, family: str | None) -> dict:
    header=parse_header(raw)
    family = form_family(header.get("form")) or family
    details=parse_xml_snapshot(raw,family)
    if not details["xml_present"]: details=legacy_fields(raw)
    return {**header, **details}

def fetch_url(url: str, user_agent: str, retries: int = 5) -> tuple[int, bytes, str]:
    last_error=""
    for attempt in range(retries):
        req=urllib.request.Request(url, headers={"User-Agent":user_agent, "Accept-Encoding":"identity"})
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                return response.status, response.read(), ""
        except urllib.error.HTTPError as exc:
            status=exc.code
            try: body=exc.read()
            except Exception: body=b""
            if status not in {429,500,502,503,504}:
                return status, body, f"HTTP {status}"
            retry_after=exc.headers.get("Retry-After") if exc.headers else None
            delay=float(retry_after) if retry_after and retry_after.isdigit() else min(2**attempt,16)
            last_error=f"HTTP {status}"
        except Exception as exc:
            last_error=type(exc).__name__ + ": " + str(exc)
            delay=min(2**attempt,16)
        time.sleep(delay)
    return 0,b"",last_error or "retry limit"

def valid_accession(raw: str, expected: str) -> bool:
    h=parse_header(raw)
    return h.get("accession")==expected

def choose_mirror(results: list[dict]) -> tuple[dict | None, str]:
    ok=[x for x in results if x.get("valid")]
    if not ok: return None,"NO_VALID_PATH"
    hashes={x["sha256"] for x in ok}
    if len(hashes)>1: return None,"MIRROR_CONTENT_CONFLICT"
    return ok[0],("IDENTICAL_MIRRORS" if len(ok)>1 else "SINGLE_VALID_PATH")

def compare_pair(current: dict, previous: dict, manifest: dict, mirror_status: str) -> dict:
    expected_family=form_family(manifest["current_form"])
    checks={
        "previous_accession_match": previous.get("accession")==manifest["previous_accession"],
        "previous_form_family_match": form_family(previous.get("form"))==expected_family,
        "previous_subject_cik_match": previous.get("header_subject_cik")==norm_cik(manifest["current_issuer_cik"]),
        "previous_filer_cik_match": previous.get("header_filer_cik")==norm_cik(manifest["current_filer_cik"]),
        "previous_date_before_current": bool(previous.get("filed_date") and previous["filed_date"] < manifest["current_filing_date"]),
        "current_header_matches_manifest": (
            current.get("accession")==manifest["current_accession"] and
            current.get("header_subject_cik")==norm_cik(manifest["current_issuer_cik"]) and
            current.get("header_filer_cik")==norm_cik(manifest["current_filer_cik"]) and
            form_family(current.get("form"))==expected_family and
            current.get("filed_date")==manifest["current_filing_date"]
        )
    }
    if any(v is False for v in checks.values()):
        header_status="CONFLICT"
    elif any(v is None for v in checks.values()):
        header_status="INCOMPLETE"
    else: header_status="PASS"
    xml_checks={}
    for prefix, filing in (("current",current),("previous",previous)):
        if filing.get("xml_present"):
            xml_checks[f"{prefix}_xml_subject_matches_header"] = filing.get("xml_issuer_cik")==filing.get("header_subject_cik")
            xml_checks[f"{prefix}_xml_filer_matches_header"] = filing.get("xml_filer_cik")==filing.get("header_filer_cik")
    cc=norm_cusip(current.get("cusip") or manifest.get("current_cusip"))
    pc=norm_cusip(previous.get("cusip"))
    if cc and pc: security_status="CUSIP_MATCH" if cc==pc else "CUSIP_MISMATCH"
    else:
        ctitle=norm(current.get("class_title")); ptitle=norm(previous.get("class_title"))
        security_status="CLASS_TITLE_MATCH_ONLY" if ctitle and ptitle and ctitle==ptitle else "UNRESOLVED"
    cpersons={norm(p.get("name")):p for p in current.get("persons",[]) if p.get("name")}
    ppersons={norm(p.get("name")):p for p in previous.get("persons",[]) if p.get("name")}
    shared=sorted(set(cpersons)&set(ppersons))
    person_metrics={
        "current_person_count":len(cpersons),"previous_person_count":len(ppersons),
        "shared_person_count":len(shared),
        "person_name_jaccard": (len(shared)/len(set(cpersons)|set(ppersons))) if cpersons or ppersons else None,
        "shared_person_ownership_changes":[
            {"name":name,"current_percent":cpersons[name].get("percent"),"previous_percent":ppersons[name].get("percent"),
             "current_amount":cpersons[name].get("amount"),"previous_amount":ppersons[name].get("amount")}
            for name in shared
        ]
    }
    if header_status=="CONFLICT" or any(v is False for v in xml_checks.values()): lineage_status="HEADER_CONFLICT"
    elif header_status=="INCOMPLETE": lineage_status="HEADER_INCOMPLETE"
    elif security_status in {"CUSIP_MATCH","CLASS_TITLE_MATCH_ONLY"}: lineage_status="HEADER_AND_SECURITY_PASS"
    elif security_status=="CUSIP_MISMATCH": lineage_status="SECURITY_CONFLICT"
    else: lineage_status="HEADER_ONLY_SECURITY_UNRESOLVED"
    return {"current_accession":manifest["current_accession"],"previous_accession":manifest["previous_accession"],
            "family":expected_family,"current_filing_date":manifest["current_filing_date"],
            "previous_filing_date":previous.get("filed_date"),"previous_acceptance_datetime":previous.get("acceptance_datetime"),
            "mirror_status":mirror_status,"header_status":header_status,"security_status":security_status,
            "lineage_status":lineage_status,"current_cusip":cc,"previous_cusip":pc,
            "current_class_title":current.get("class_title"),"previous_class_title":previous.get("class_title"),
            "current_xml":current.get("xml_present"),"previous_xml":previous.get("xml_present"),
            "current_subject_name":current.get("subject_name"),"previous_subject_name":previous.get("subject_name"),
            "current_filer_name":current.get("filer_name"),"previous_filer_name":previous.get("filer_name"),
            "checks":{**checks,**xml_checks},**person_metrics}

def load_manifest(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=45: raise ValueError(f"expected 45 validated manifest rows, found {len(rows)}")
    accessions=[r["previous_accession"] for r in rows]
    if len(set(accessions))!=45: raise ValueError("previous accession manifest is not unique")
    for r in rows:
        paths=[p for p in r["previous_paths_pipe"].split("|") if p]
        if len(paths)<1 or any(not p.startswith("edgar/data/") or ".." in p for p in paths):
            raise ValueError(f"invalid archive paths for {r['previous_accession']}")
    return rows

def run_audit(phase84_dir: Path, manifest_path: Path, output_dir: Path, user_agent: str) -> dict:
    rows=load_manifest(manifest_path)
    output_dir.mkdir(parents=True,exist_ok=True)
    raw_dir=output_dir/"predecessor_submissions"; raw_dir.mkdir(exist_ok=True)
    results=[]; failures=[]
    for i,row in enumerate(rows,1):
        current_path=phase84_dir/row["current_raw_file"]
        if not current_path.exists():
            failures.append({"previous_accession":row["previous_accession"],"error":"current artifact raw file missing"})
            continue
        current_raw=current_path.read_text(encoding="utf-8",errors="replace")
        current=parse_submission(current_raw,form_family(row["current_form"]))
        candidate_results=[]
        for path in [p for p in row["previous_paths_pipe"].split("|") if p]:
            url=SEC_BASE+path
            status,body,error=fetch_url(url,user_agent)
            raw=body.decode("utf-8",errors="replace") if body else ""
            valid=status==200 and valid_accession(raw,row["previous_accession"])
            candidate_results.append({"path":path,"url":url,"http_status":status,"error":error,
                                      "valid":valid,"sha256":hashlib.sha256(body).hexdigest() if body else None,
                                      "raw":raw if valid else None})
            time.sleep(0.16)
        selected,mirror_status=choose_mirror(candidate_results)
        if selected is None:
            failures.append({"previous_accession":row["previous_accession"],"mirror_status":mirror_status,
                             "paths":[{k:v for k,v in x.items() if k!="raw"} for x in candidate_results]})
            continue
        previous_raw=selected["raw"]
        previous=parse_submission(previous_raw,form_family(row["current_form"]))
        raw_name=row["previous_accession"].replace("-","")+".txt"
        (raw_dir/raw_name).write_text(previous_raw,encoding="utf-8")
        result=compare_pair(current,previous,row,mirror_status)
        result["selected_archive_path"]=selected["path"]
        result["candidate_paths"]=[{k:v for k,v in x.items() if k!="raw"} for x in candidate_results]
        results.append(result)
        print(f"[{i:02d}/{len(rows)}] {row['previous_accession']} {result['lineage_status']} ({mirror_status})",flush=True)
    counts=Counter(x["lineage_status"] for x in results)
    clean=(len(results)==45 and not failures and counts.get("HEADER_CONFLICT",0)==0 and counts.get("SECURITY_CONFLICT",0)==0)
    fully_resolved=clean and counts.get("HEADER_ONLY_SECURITY_UNRESOLVED",0)==0
    summary={
        "phase":"120-sec-13dg-predecessor-content-audit",
        "status":"PASS" if fully_resolved else ("PASS_WITH_CAVEATS" if clean else "INCOMPLETE_OR_CONFLICT"),
        "manifest_rows":len(rows),"predecessor_downloads_validated":len(results),"download_or_accession_failures":len(failures),
        "lineage_status_counts":dict(counts),"mirror_status_counts":dict(Counter(x["mirror_status"] for x in results)),
        "previous_xml_count":sum(bool(x["previous_xml"]) for x in results),
        "previous_legacy_html_count":sum(x["previous_xml"] is False for x in results),
        "cusip_match_count":sum(x["security_status"]=="CUSIP_MATCH" for x in results),
        "cusip_mismatch_count":sum(x["security_status"]=="CUSIP_MISMATCH" for x in results),
        "class_title_only_count":sum(x["security_status"]=="CLASS_TITLE_MATCH_ONLY" for x in results),
        "security_unresolved_count":sum(x["security_status"]=="UNRESOLVED" for x in results),
        "results":results,"failures":failures,
        "limitations":["The 45 links are a stratified pilot subset, not a global 13D/13G census.",
                       "A legacy HTML parse does not establish full reporting-person/ownership continuity.",
                       "SEC acceptance time is not proof of public dissemination time; use next-session conservative availability.",
                       "No returns, feature, or alpha tests are performed."]
    }
    (output_dir/"phase120_predecessor_audit.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    with (output_dir/"phase120_predecessor_audit.csv").open("w",encoding="utf-8",newline="") as f:
        fields=["current_accession","previous_accession","family","current_filing_date","previous_filing_date",
                "lineage_status","header_status","security_status","mirror_status","current_xml","previous_xml",
                "current_cusip","previous_cusip","current_person_count","previous_person_count",
                "shared_person_count","person_name_jaccard","selected_archive_path"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for x in results: w.writerow({k:x.get(k) for k in fields})
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--phase84-dir",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--user-agent",default=DEFAULT_UA)
    args=p.parse_args()
    summary=run_audit(args.phase84_dir,args.manifest,args.output_dir,args.user_agent)
    print(json.dumps({k:v for k,v in summary.items() if k not in {"results","failures"}},indent=2))
    if summary["status"] not in {"PASS","PASS_WITH_CAVEATS"}: raise SystemExit(2)

if __name__=="__main__": main()
