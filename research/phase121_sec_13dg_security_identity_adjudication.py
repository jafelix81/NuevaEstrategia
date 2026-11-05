#!/usr/bin/env python3
"""Offline adjudication of SEC 13D/13G predecessor security identity.

Consumes immutable Phase 84 current filings and the live Phase 120 predecessor
archive. No network requests, return data, feature engineering, or alpha tests.
"""
from __future__ import annotations
import argparse, csv, hashlib, html, json, re
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

ADJUDICATIONS = {
    "0001104659-24-129092": {
        "category": "DOCUMENTED_SPAC_BUSINESS_COMBINATION",
        "effective_date": "2023-03-30",
        "detail": "DiamondHead Holdings Corp. completed its business combination with Great Southern Homes and became United Homes Group; the old SPAC security and post-combination common stock are successor securities, not an unchanged CUSIP.",
        "evidence": ["https://www.nasdaq.com/press-release/diamondhead-holdings-corp.-and-great-southern-homes-announce-closing-of-business"]
    },
    "0000038777-24-000179": {
        "category": "DOCUMENTED_REVERSE_SPLIT",
        "effective_date": "2023-07-26",
        "detail": "Benitec effected a 1-for-17 reverse stock split and assigned new CUSIP 08205P209; the prior CUSIP 08205P100 is the pre-split security.",
        "evidence": ["https://www.benitec.com/for-investors/news-events/press-releases/detail/103/benitec-biopharma-announces-1-for-17-reverse-stock-split-effective-july-26-2023"]
    },
    "0001104659-25-014195": {
        "category": "DOCUMENTED_ADS_RATIO_CHANGE",
        "effective_date": "2024-04-16",
        "detail": "NuCana changed its ADS ratio from one ADS per ordinary share to one ADS per 25 ordinary shares; the ADS CUSIP changed from 67022C106 to 67022C205.",
        "evidence": ["https://www.sec.gov/Archives/edgar/data/1709626/000119380524000454/e663457_ex99-ai.htm"]
    },
    "0001398344-25-002939": {
        "category": "PREDECESSOR_CUSIP_MISKEY_SUSPECTED",
        "effective_date": None,
        "detail": "The predecessor filing names Toro Corp. (CIK 1941131) but reports 891092108, which SEC filing evidence associates with The Toro Company (CIK 737758). Toro Corp. filings identify Y8900D108. Treat the predecessor CUSIP as a likely filing-level mis-key, not as a corporate-action transition.",
        "evidence": [
            "https://www.sec.gov/Archives/edgar/data/1941131/000095015724000837/sc13d-a.htm",
            "https://www.sec.gov/Archives/edgar/data/737758/000093247115003976/toroco.htm"
        ]
    },
    "0001445546-26-005159": {
        "category": "CROSS_SERIES_LINK_WITHIN_TRUST",
        "effective_date": None,
        "detail": "The predecessor CUSIP 33740F854 is FT Vest U.S. Equity Deep Buffer ETF - August (DAUG); the current CUSIP 33740F458 is FT Vest U.S. Equity Moderate Buffer ETF - April (GAPR). GAPR began on 2023-04-21, after the predecessor filing dated 2021-05-10. This is a different ETF series under the same trust CIK, not the same security.",
        "evidence": [
            "https://www.ftportfolios.com/etf/DAUG",
            "https://www.ftportfolios.com/etf/GAPR"
        ]
    }
}

MONTHS = {"JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE","JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER"}

def norm(value):
    return re.sub(r"\s+"," ",str(value or "")).strip().upper()

def norm_cik(value):
    digits=re.sub(r"\D","",str(value or ""))
    return digits.zfill(10) if digits else None

def norm_cusip(value):
    value=re.sub(r"[^A-Z0-9]","",norm(value))
    return value if len(value)==9 and value!="000000000" else None

def valid_cusip(value):
    c=re.sub(r"[^A-Z0-9*@#]","",str(value or "").upper())
    if len(c)!=9 or not c[-1].isdigit(): return False
    values={str(i):i for i in range(10)}
    values.update({chr(65+i):10+i for i in range(26)})
    values.update({"*":36,"@":37,"#":38})
    total=0
    for i,ch in enumerate(c[:8]):
        if ch not in values:return False
        v=values[ch]*(1 if i%2==0 else 2)
        total+=v//10+v%10
    return (10-total%10)%10==int(c[8])

def family_of(form):
    f=norm(form)
    if f.startswith("SCHEDULE "):f="SC "+f[len("SCHEDULE "):]
    if f in {"SC 13D","SC 13D/A"}:return "13D"
    if f in {"SC 13G","SC 13G/A"}:return "13G"
    return None

def header(raw):
    m=re.search(r"<SEC-HEADER>(.*?)</SEC-HEADER>",raw,re.I|re.S)
    h=m.group(1) if m else raw[:100000]
    def one(p):
        x=re.search(p,h,re.I|re.S)
        return x.group(1).strip() if x else None
    def cik(section):
        x=one(rf"{section}\s*:.*?CENTRAL INDEX KEY\s*:\s*(\d+)")
        return norm_cik(x)
    filed=one(r"FILED AS OF DATE\s*:\s*(\d{8})")
    return {
        "accession":one(r"ACCESSION NUMBER\s*:\s*([0-9-]{20})"),
        "form":norm(one(r"CONFORMED SUBMISSION TYPE\s*:\s*([A-Z0-9 /-]+)")),
        "filed_date":f"{filed[:4]}-{filed[4:6]}-{filed[6:8]}" if filed else None,
        "subject_cik":cik("SUBJECT COMPANY"),
        "filer_cik":cik("FILED BY"),
        "subject_name":one(r"SUBJECT COMPANY\s*:.*?COMPANY CONFORMED NAME\s*:\s*([^\r\n]+)"),
        "filer_name":one(r"FILED BY\s*:.*?COMPANY CONFORMED NAME\s*:\s*([^\r\n]+)")
    }

def xml_root(raw):
    for block in re.findall(r"<XML>(.*?)</XML>",raw,re.I|re.S):
        if "edgarSubmission" in block:
            try:return ET.fromstring(block.strip())
            except ET.ParseError:pass
    return None

def tag_values(root,tag):
    return [e.text.strip() for e in root.iter() if e.tag.split("}")[-1].lower()==tag.lower() and e.text and e.text.strip()]

def first_tag(root,*tags):
    for tag in tags:
        vals=tag_values(root,tag)
        if vals:return vals[0]
    return None

def parse_xml(raw,family):
    root=xml_root(raw)
    if root is None:return None
    cusips=[]
    for tag in ("issuerCUSIP","issuerCusip","issuerCusipNumber"):
        cusips.extend(tag_values(root,tag))
    cusips=sorted(set(norm_cusip(x) for x in cusips if norm_cusip(x)))
    person_tag="reportingPersonInfo" if family=="13D" else "coverPageHeaderReportingPersonDetails"
    persons=[]
    for node in root.iter():
        if node.tag.split("}")[-1]!=person_tag:continue
        def local(*tags):
            for tag in tags:
                vals=[e.text.strip() for e in node.iter() if e.tag.split("}")[-1].lower()==tag.lower() and e.text and e.text.strip()]
                if vals:return vals[0]
        persons.append({
            "name":local("reportingPersonName"),
            "cik":norm_cik(local("reportingPersonCIK")) if family=="13D" else None,
            "amount":local("aggregateAmountOwned" if family=="13D" else "reportingPersonBeneficiallyOwnedAggregateNumberOfShares"),
            "percent":local("percentOfClass" if family=="13D" else "classPercent"),
        })
    return {"xml_present":True,"cusip":cusips[0] if len(cusips)==1 else None,"cusip_candidates":cusips,
            "class_title":first_tag(root,"securitiesClassTitle"),"persons":persons}

def strip_html(raw):
    txt=re.sub(r"(?is)<(?:br|/p|/div|/tr|/td|/th|/li|/h[1-6])[^>]*>","\n",raw)
    txt=re.sub(r"(?is)<[^>]+>"," ",txt)
    txt=html.unescape(txt).replace("\xa0"," ").replace("\u200b","")
    return "\n".join(re.sub(r"\s+"," ",x).strip() for x in txt.splitlines() if x.strip())

def cusips_from_text(text):
    found=set()
    patterns=[
        r"CUSIP(?:\s+(?:NO\.?|NUMBER))?\s*(?:#|:)?\s*([A-Z0-9]{6,9})(?:\s+([A-Z0-9]{1,3}))?",
        r"\b([A-Z0-9]{9}|[A-Z0-9]{6,8}\s+[A-Z0-9]{1,3})\s*\(?CUSIP(?:\s+(?:NO\.?|NUMBER))?\)?"
    ]
    for pattern in patterns:
        for m in re.finditer(pattern,text,re.I):
            a=(m.group(1) or "").upper().strip()
            b=(m.group(2) or "").upper().strip() if m.lastindex and m.lastindex>=2 else ""
            if a in MONTHS or a in {"NUMBER","CUSIP","NONE","N/A"}:continue
            candidate=a if len(a)==9 else (a+b if 6<=len(a)<=8 and len(a)+len(b)==9 else "")
            if candidate and valid_cusip(candidate):found.add(candidate)
    return sorted(found)

def legacy_persons(text):
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    names=[]
    for m in re.finditer(r"ITEM\s*1\s*:\s*REPORTING PERSON\s*[-:]\s*([^\n]+)",text,re.I):
        candidate=m.group(1).strip()
        if candidate and candidate not in names:names.append(candidate)
    for i,line in enumerate(lines[:2000]):
        if "NAME OF REPORTING PERSON" not in line.upper() and "NAMES OF REPORTING PERSON" not in line.upper():continue
        suffix=re.sub(r"^\s*\d*\.?\s*","",line)
        suffix=re.sub(r"NAMES? OF REPORTING PERSONS?","",suffix,flags=re.I).strip(" :.-")
        candidate=suffix if len(suffix)>=3 else None
        if not candidate:
            for cand in lines[i+1:i+6]:
                up=cand.upper()
                if any(k in up for k in ["I.R.S. IDENTIFICATION","CHECK THE APPROPRIATE","SEC USE ONLY","CITIZENSHIP","NUMBER OF SHARES","SOLE VOTING","SHARED VOTING","AGGREGATE AMOUNT","PERCENT OF CLASS","TYPE OF REPORTING PERSON"]):continue
                if re.fullmatch(r"[\d().\s]+",cand):continue
                if sum(ch.isalpha() for ch in cand)>=3 and len(cand)<160:
                    candidate=cand;break
        if candidate and candidate not in names:names.append(candidate)
    return [{"name":n,"amount":None,"percent":None} for n in names]

def parse_legacy(raw):
    text=strip_html(raw)
    cands=cusips_from_text(text)
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    title=None
    for i,line in enumerate(lines[:700]):
        if not any(label in line.upper() for label in ["TITLE OF CLASS OF SECURITIES","TITLE AND CLASS OF SECURITIES"]):continue
        suffix=re.sub(r"(?i).*?TITLE (?:OF|AND) CLASS OF SECURITIES\s*[:\-]?\s*","",line).strip(" ():.-")
        if suffix and len(suffix)>2 and "CUSIP" not in suffix.upper():
            title=suffix;break
        for back in range(i-1,max(-1,i-4),-1):
            cand=lines[back].strip(" -_")
            if not cand or len(cand)<3:continue
            if any(k in cand.upper() for k in ["NAME OF ISSUER","CUSIP","DATE OF EVENT","SCHEDULE 13","AMENDMENT NO"]):continue
            if re.fullmatch(r"[\d.,/\- ]+",cand):continue
            title=cand;break
        if title:break
        for cand in lines[i+1:i+4]:
            if any(k in cand.upper() for k in ["CUSIP","DATE OF EVENT","CHECK THE APPROPRIATE","SCHEDULE 13"]):continue
            if len(cand)>2:title=cand;break
        if title:break
    if not title:
        for i,line in enumerate(lines[:1000]):
            if re.search(r"ITEM\s*2\s*\(?D\)?",line,re.I) and ("TITLE OF CLASS" in line.upper() or "TITLE AND CLASS" in line.upper()):
                title=next((x for x in lines[i+1:i+5] if "CUSIP" not in x.upper() and "DATE OF EVENT" not in x.upper() and len(x)>2),None)
                if title:break
    return {"xml_present":False,"cusip":cands[0] if len(cands)==1 else None,"cusip_candidates":cands,
            "class_title":title,"persons":legacy_persons(text)}

def parse_filing(raw,family):
    h=header(raw)
    actual_family=family_of(h.get("form")) or family
    root=xml_root(raw)
    d=parse_xml(raw,actual_family) if root is not None else parse_legacy(raw)
    return {**h,**d}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--phase84-dir",type=Path,required=True)
    p.add_argument("--phase120-dir",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    phase120=json.loads((a.phase120_dir/"phase120_predecessor_audit.json").read_text(encoding="utf-8"))
    if phase120.get("predecessor_downloads_validated")!=45 or phase120.get("download_or_accession_failures")!=0:
        raise ValueError("Phase 120 input artifact is not the expected complete 45/45 download")
    with a.manifest.open(encoding="utf-8-sig",newline="") as f: manifest=list(csv.DictReader(f))
    with (a.phase84_dir/"pilot_header_validation.csv").open(encoding="utf-8-sig",newline="") as f: phase84_rows={x["accession"]:x for x in csv.DictReader(f)}
    if len(manifest)!=45 or len({x["previous_accession"] for x in manifest})!=45:
        raise ValueError("manifest must contain 45 unique predecessor accessions")
    results=[]
    for row in manifest:
        prev=row["previous_accession"]
        prev_path=a.phase120_dir/"predecessor_submissions"/(prev.replace("-","")+".txt")
        curr_path=a.phase84_dir/row["current_raw_file"]
        if not prev_path.exists() or not curr_path.exists():
            raise FileNotFoundError(f"missing raw input for {row['current_accession']} -> {prev}")
        family=family_of(row["current_form"])
        current_bytes=curr_path.read_bytes()
        current_meta=phase84_rows.get(row["current_accession"])
        if not current_meta or current_meta.get("raw_file")!=row["current_raw_file"] or hashlib.sha256(current_bytes).hexdigest()!=current_meta.get("source_sha256"):
            raise ValueError(f"Phase 84 raw hash/path mismatch for {row['current_accession']}")
        current=parse_filing(current_bytes.decode("utf-8",errors="replace"),family)
        previous_bytes=prev_path.read_bytes()
        prior_phase120=next(x for x in phase120["results"] if x["current_accession"]==row["current_accession"])
        selected_meta=next((x for x in prior_phase120["candidate_paths"] if x["path"]==prior_phase120["selected_archive_path"] and x["valid"]),None)
        if not selected_meta or hashlib.sha256(previous_bytes).hexdigest()!=selected_meta.get("sha256"):
            raise ValueError(f"Phase 120 predecessor raw hash mismatch for {prev}")
        previous=parse_filing(previous_bytes.decode("utf-8",errors="replace"),family)
        c_cusip=norm_cusip(current.get("cusip") or row.get("current_cusip"))
        p_cusip=norm_cusip(previous.get("cusip"))
        if c_cusip and p_cusip:
            security_status="CUSIP_MATCH" if c_cusip==p_cusip else "CUSIP_MISMATCH"
        elif norm(current.get("class_title")) and norm(current.get("class_title"))==norm(previous.get("class_title")):
            security_status="NO_CUSIP_CLASS_TITLE_MATCH" if not c_cusip and not p_cusip else "CLASS_TITLE_ONLY"
        else:
            security_status="UNRESOLVED"
        c_names={norm(x.get("name")) for x in current.get("persons",[]) if x.get("name")}
        p_names={norm(x.get("name")) for x in previous.get("persons",[]) if x.get("name")}
        shared=sorted(c_names&p_names); union=c_names|p_names
        adjudication=ADJUDICATIONS.get(row["current_accession"])
        if security_status=="CUSIP_MISMATCH" and not adjudication:
            raise ValueError(f"unadjudicated CUSIP mismatch {row['current_accession']}")
        if security_status=="UNRESOLVED" and row["current_accession"]!="0000950170-25-007683":
            raise ValueError(f"unexpected unresolved security identity {row['current_accession']}")
        if security_status=="NO_CUSIP_CLASS_TITLE_MATCH" and row["current_accession"]!="0000950170-25-007683":
            raise ValueError(f"unexpected no-CUSIP class match {row['current_accession']}")
        results.append({
            "current_accession":row["current_accession"],"previous_accession":prev,"family":family,
            "current_filing_date":row["current_filing_date"],"previous_filing_date":previous.get("filed_date"),
            "current_issuer_name":current.get("subject_name"),"previous_issuer_name":previous.get("subject_name"),
            "current_filer_name":current.get("filer_name"),"previous_filer_name":previous.get("filer_name"),
            "current_issuer_cik":current.get("subject_cik"),"previous_issuer_cik":previous.get("subject_cik"),
            "current_filer_cik":current.get("filer_cik"),"previous_filer_cik":previous.get("filer_cik"),
            "current_cusip":c_cusip,"previous_cusip":p_cusip,"security_status":security_status,
            "current_class_title":current.get("class_title"),"previous_class_title":previous.get("class_title"),
            "current_xml":bool(current.get("xml_present")),"previous_xml":bool(previous.get("xml_present")),
            "current_person_count":len(c_names),"previous_person_count":len(p_names),"shared_person_count":len(shared),
            "person_name_jaccard":len(shared)/len(union) if union else None,
            "shared_person_names":shared,
            "phase120_header_status":prior_phase120.get("header_status"),
            "phase120_mirror_status":prior_phase120.get("mirror_status"),
            "raw_hashes_valid":True,
            "adjudication":adjudication
        })
    counts=Counter(x["security_status"] for x in results)
    adjs=Counter((x["adjudication"] or {}).get("category","NONE") for x in results)
    if len(results)!=45 or counts["CUSIP_MISMATCH"]!=5 or counts["NO_CUSIP_CLASS_TITLE_MATCH"]!=1 or counts["UNRESOLVED"]!=0:
        raise ValueError(f"unexpected security status distribution: {dict(counts)}")
    if any(x["phase120_header_status"]!="PASS" for x in results):
        raise ValueError("one or more SEC header identity checks did not pass")
    summary={
        "phase":"121-sec-13dg-security-identity-adjudication",
        "status":"PASS_WITH_CAVEATS",
        "manifest_rows":len(manifest),
        "predecessor_downloads_validated":phase120["predecessor_downloads_validated"],
        "phase120_mirror_status_counts":phase120["mirror_status_counts"],
        "phase120_header_identity_pass_count":sum(x["phase120_header_status"]=="PASS" for x in results),
        "raw_hash_validation_count":sum(x["raw_hashes_valid"] for x in results),
        "security_status_counts":dict(counts),
        "adjudication_counts":dict(adjs),
        "current_xml_count":sum(x["current_xml"] for x in results),
        "previous_xml_count":sum(x["previous_xml"] for x in results),
        "legacy_previous_count":sum(not x["previous_xml"] for x in results),
        "limitations":[
            "This is a 45-link stratified pilot, not a global 13D/13G recall or universe-coverage audit.",
            "Legacy HTML reporting-person extraction is heuristic; name overlap is diagnostic only and is not an acceptance gate.",
            "The SEC previousAccessionNumber pointer is not sufficient security identity: a series trust can link different ETF series under one issuer CIK.",
            "Corporate-action CUSIP transitions need effective-dated security mapping; they are not interchangeable identifiers.",
            "The Toro predecessor CUSIP is strongly inconsistent with its own issuer CIK/name and is treated as a likely filing-level mis-key, not a verified corporate action.",
            "SEC acceptance time is not proof of public dissemination time; conservative next-session availability remains required.",
            "No returns, feature, or alpha tests are performed."
        ],
        "results":results
    }
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/"phase121_security_identity_adjudication.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    fields=["current_accession","previous_accession","family","current_filing_date","previous_filing_date",
            "security_status","current_cusip","previous_cusip","current_class_title","previous_class_title",
            "current_issuer_cik","previous_issuer_cik","current_filer_cik","previous_filer_cik",
            "current_person_count","previous_person_count","shared_person_count","person_name_jaccard",
            "phase120_header_status","phase120_mirror_status","adjudication_category"]
    with (a.output_dir/"phase121_security_identity_adjudication.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for x in results:
            row={k:x.get(k) for k in fields}
            row["adjudication_category"]=(x["adjudication"] or {}).get("category")
            w.writerow(row)
    print(json.dumps({k:v for k,v in summary.items() if k!="results"},indent=2))

if __name__=="__main__":main()
