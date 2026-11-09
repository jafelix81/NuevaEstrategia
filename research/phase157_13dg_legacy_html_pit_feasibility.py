#!/usr/bin/env python3
"""Phase 157: conservative legacy SEC Schedule 13D/G HTML feasibility audit."""
from __future__ import annotations
import argparse,csv,hashlib,html,json,re,statistics
from datetime import date,datetime
from html.parser import HTMLParser
from pathlib import Path
P124_RUN=42073725379; P124_ARTIFACT=13436764625
P124_CSV_SHA="be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5"
P124_ZIP_SHA="85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc"
P127_RUN=42079517644; P127_ARTIFACT=13438903901
P127_CSV_SHA="5fc30ba22d4e3ef99113761059a5761f1fd4ae61a6d0e3a69961fe194d739447"
P127_ZIP_SHA="b80d15d736ba6c45f4f3c5dd569604175e221414b31a28fd58a62010a805c166"

class BlockText(HTMLParser):
    BLOCKS={"address","article","br","center","div","dl","dt","dd","h1","h2","h3","hr","li","ol","p","pre","table","tbody","td","th","tr","ul"}
    def __init__(self): super().__init__(convert_charrefs=True); self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower() in self.BLOCKS:self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag.lower() in self.BLOCKS:self.parts.append("\n")
    def handle_data(self,data):self.parts.append(data)

def sha(b):return hashlib.sha256(b).hexdigest()
def read_csv(p):
    with Path(p).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def primary_document(raw,family):
    found=[]
    for doc in re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>",raw,re.I|re.S):
        m=re.search(r"<TYPE>\s*([^\r\n<]+)",doc,re.I)
        if not m:continue
        form=re.sub(r"\s+"," ",m.group(1)).strip().upper()
        if form not in {f"SC {family}",f"SC {family}/A"}:continue
        x=re.search(r"<TEXT>(.*?)</TEXT>",doc,re.I|re.S);body=x.group(1) if x else doc
        if not re.match(r"\s*<PDF>",body,re.I):found.append(body)
    if not found:raise ValueError(f"readable primary SC {family} document missing")
    found.sort(key=lambda x:("<HTML" in x[:2000].upper(),len(re.sub(r"<[^>]+>"," ",x))),reverse=True)
    return found[0]
def text_lines(raw,family):
    p=BlockText();p.feed(primary_document(raw,family))
    s=html.unescape("".join(p.parts)).replace("\xa0"," ").replace("\u200b"," ").replace("\ufeff"," ")
    return [re.sub(r"\s+"," ",x).strip() for x in s.splitlines() if re.sub(r"\s+"," ",x).strip()]

NOISE=re.compile(r"(?i)ACT\s+OF\s+1934|UNDER\s+THE\s+SECURITIES|FORMERLY\b|SCHEDULE\s+13[DG]|AMENDMENT\s+NO|SECURITIES\s+AND\s+EXCHANGE|WASHINGTON|UNITED\s+STATES|INFORMATION\s+TO\s+BE\s+INCLUDED|FILED\s+PURSUANT|PURSUANT\s+TO|TO\s+RULE|RULE\s+13D|CHECK\s+THE\s+APPROPRIATE|THE\s+REMAINDER|ANNUAL\s+FILING|INITIAL\s+FILING|FINAL\s+AMENDMENT|TITLE\s+OF\s+CLASS|CUSIP|DATE\s+OF\s+EVENT|NAME\s+OF\s+ISSUER|SEE\s+COVER\s+PAGE|SEC\s+USE\s+ONLY|§|\b13D-\d")
def clean_candidate(v):
    v=re.sub(r"\s+"," ",v or "").strip(" \t:;,.()[]*_-—")
    if len(v)<4 or len(v)>140 or not re.search(r"[A-Za-z]",v) or NOISE.search(v):return None
    return None if re.fullmatch(r"[\W\d_]+",v) else v
def cover_value(lines,pattern,kind,limit=40):
    if kind=="issuer":
        for line in lines[:22]:
            m=re.search(r"^\s*name\s+of\s+issuer\s*:\s*(.+)$",line,re.I)
            if m:
                c=clean_candidate(m.group(1))
                if c:return c,"INLINE_COLON"
    for i in range(min(len(lines),limit)):
        for width in range(1,4):
            phrase=" ".join(lines[i:i+width]);m=re.search(pattern,phrase,re.I)
            if not m:continue
            head=phrase[:m.start()]
            if kind=="class" and re.search(r"name\s+of\s+issuer",head,re.I):continue
            candidates=[];c=clean_candidate(head)
            if c:candidates.append((len(c),0,c))
            for n in range(1,5):
                c=clean_candidate(" ".join(lines[max(0,i-n):i]))
                if c:candidates.append((len(c),n,c))
            if candidates:
                _,n,value=max(candidates,key=lambda x:(x[0],-x[1]))
                return value,("INLINE_BEFORE" if n==0 else f"PRE_LABEL_{n}")
    return None,"LABEL_NOT_FOUND"

DATE_RE=re.compile(r"(?i)(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}")
def parse_date(s):
    s=(s or "").strip().replace(",","")
    for fmt in ("%B %d %Y","%b %d %Y","%m/%d/%Y","%m/%d/%y","%Y-%m-%d"):
        try:return datetime.strptime(s,fmt).date()
        except ValueError:pass
    return None
def event_date(lines):
    for i in range(min(len(lines),100)):
        for w in range(1,4):
            phrase=" ".join(lines[i:i+w])
            if re.search(r"date\s+of\s+event",phrase,re.I) and re.search(r"requires\s+filing",phrase,re.I):
                found=[]
                for j in range(max(0,i-2),min(len(lines),i+w+4)):
                    for m in DATE_RE.finditer(lines[j]):
                        d=parse_date(m.group(0))
                        if d:found.append((abs(j-i),0 if j>=i else 1,d,m.group(0)))
                if found:
                    _,_,d,raw=min(found);return d,raw,"LABEL_WINDOW"
                return None,None,"LABEL_NO_DATE"
    return None,None,"LABEL_NOT_FOUND"

OWNER_NOISE=re.compile(r"(?i)IDENTIFICATION|S\.\s*S\.?|I\.\s*R\.\s*S\.?|ABOVE PERSON|ENTITIES ONLY|CHECK THE|SEC USE|CITIZENSHIP|SOURCE OF FUNDS|VOTING POWER|DISPOSITIVE POWER|AGGREGATE AMOUNT|PERCENT OF CLASS|REPORTING PERSON|PAGE\s+\d")
def first_owner(lines):
    for i in range(min(len(lines),350)):
        for w in range(1,3):
            phrase=" ".join(lines[i:i+w]);m=re.search(r"names?\s+of\s+reporting\s+persons?",phrase,re.I)
            if not m:continue
            tail=phrase[m.end():].strip(" :.-")
            if len(tail)>=3 and not OWNER_NOISE.search(tail):return tail,"INLINE"
            for j in range(i+w,min(len(lines),i+w+10)):
                v=re.sub(r"\s+"," ",lines[j]).strip(" :;,.()[]*_")
                if 3<=len(v)<=140 and not OWNER_NOISE.search(v) and not re.fullmatch(r"[\W\d_]+",v):return v,"FOLLOWING_LINE"
            return None,"LABEL_NO_CANDIDATE"
    return None,"LABEL_NOT_FOUND"

NUM_RE=re.compile(r"(?<![A-Za-z])(?:[-+]?\d[\d,]*(?:\.\d+)?\s*%?|NONE|N/?A)(?![A-Za-z])",re.I)
def numeric_after_label(lines,pattern):
    for i in range(min(len(lines),350)):
        for w in range(1,3):
            phrase=" ".join(lines[i:i+w]);m=re.search(pattern,phrase,re.I)
            if not m:continue
            tail=phrase[m.end():].strip(" :.-")
            if tail:
                vals=[x.group(0).strip() for x in NUM_RE.finditer(tail)]
                vals=[x for x in vals if not re.fullmatch(r"\(?\s*\d{1,2}\s*\)?",x)]
                if vals:return vals[-1],"INLINE_VALUE"
            for j in range(i+w,min(len(lines),i+w+5)):
                v=lines[j].strip()
                if re.fullmatch(r"\d{1,2}[.)]?",v) and v.strip(".) ")!="0":continue
                if re.search(r"(?i)^(?:page\s+\d|cusip\s+no|schedule\s+13[dg]|sole\s+voting|shared\s+voting|sole\s+dispositive|shared\s+dispositive|aggregate|percent|citizenship|source\s+of\s+funds)",v):continue
                vals=[x.group(0).strip() for x in NUM_RE.finditer(v)]
                if vals:return vals[-1],"FOLLOWING_LINE_VALUE"
            return None,"LABEL_NO_NUMERIC_VALUE"
    return None,"LABEL_NOT_FOUND"
def item4_purpose(lines,family):
    if family!="13D":return False,0
    start=None
    for i,line in enumerate(lines[:1000]):
        if re.search(r"\bITEM\s*4\b",line,re.I) and re.search(r"PURPOSE\s+OF\s+TRANSACTION"," ".join(lines[i:i+4]),re.I):
            start=i;break
    if start is None:return False,0
    end=next((i for i in range(start+1,min(len(lines),1200)) if re.search(r"\bITEM\s*5\b",lines[i],re.I)),None)
    return (True,sum(len(x) for x in lines[start+1:end])) if end is not None else (True,0)
def quarter_end(d):return d.month in (3,6,9,12) and d.day=={3:31,6:30,9:30,12:31}[d.month]
def wrate(rows,pred):
    den=sum(float(r["sample_weight"]) for r in rows)
    return sum(float(r["sample_weight"]) for r in rows if pred(r))/den if den else None

def audit(p124_dir,p127_dir,outdir):
    p124=Path(p124_dir);p127=Path(p127_dir)
    b124=(p124/"phase124_global_13dg_submission_audit.csv").read_bytes()
    b127=(p127/"phase127_sec_13dg_xml_cusip_audit.csv").read_bytes()
    if sha(b124)!=P124_CSV_SHA or sha(b127)!=P127_CSV_SHA:raise ValueError("immutable source CSV hash mismatch")
    s124=json.loads((p124/"phase124_global_13dg_summary.json").read_text())
    s127=json.loads((p127/"phase127_sec_13dg_xml_cusip_summary.json").read_text())
    if s124.get("sampled_index_rows_resolved")!=600 or s124.get("download_or_mirror_failures")!=0:raise ValueError("Phase 124 source summary mismatch")
    if s127.get("status")!="PASS_ARTIFACT_ONLY_XML_CUSIP_SCHEMA_CORRECTION" or s127.get("source_phase124_run_id")!=P124_RUN:raise ValueError("Phase 127 source summary mismatch")
    r124=read_csv(p124/"phase124_global_13dg_submission_audit.csv");r127=read_csv(p127/"phase127_sec_13dg_xml_cusip_audit.csv")
    if len(r124)!=600 or len({r["accession"] for r in r124})!=600 or len(r127)!=599:raise ValueError("source dimensions changed")
    cby={r["accession"]:r for r in r127};out=[];errors=[];raw_verified=0
    for r in r124:
        rp=p124/(r.get("raw_file") or "")
        if not rp.is_file():errors.append({"accession":r["accession"],"error":"raw missing"});continue
        rawb=rp.read_bytes();digest=sha(rawb)
        if digest!=r.get("raw_sha256"):errors.append({"accession":r["accession"],"error":"raw hash mismatch"});continue
        raw_verified+=1
        if r.get("is_index_alias","").lower()=="true" or r.get("download_status")=="INDEX_ALIAS_NON_13DG" or r.get("xml_present","").lower()=="true":continue
        c=cby.get(r["accession"])
        if not c or c.get("raw_sha256")!=digest or c.get("cusip_source")!="LEGACY_HTML_EXACT_TOKEN":errors.append({"accession":r["accession"],"error":"Phase 127 CUSIP join mismatch"});continue
        family=r["family"].upper();lines=text_lines(rawb.decode("utf-8","replace"),family)
        issuer,im=cover_value(lines,r"(?:\(\s*name\s+of\s+issuer\s*\)|name\s+of\s+issuer\s*\))","issuer")
        cls,cm=cover_value(lines,r"(?:\(\s*title\s+of\s+class(?:\s+of\s+securities)?\s*\)|title\s+of\s+class(?:\s+of\s+securities)?\s*\))","class")
        ev,evraw,evstatus=event_date(lines);owner,om=first_owner(lines)
        pats={"sole_voting":r"sole\s+voting\s+power","shared_voting":r"shared\s+voting\s+power","sole_dispositive":r"sole\s+dispositive\s+power","shared_dispositive":r"shared\s+dispositive\s+power","aggregate":r"aggregate\s+(?:amount\s+)?(?:beneficially\s+owned|number\s+of\s+shares)","percent":r"percent(?:age)?\s+of\s+class"}
        fv={k:numeric_after_label(lines,p) for k,p in pats.items()};i4,i4chars=item4_purpose(lines,family)
        filed=date.fromisoformat(r["filing_date_header"]) if r.get("filing_date_header") else None
        lag=(filed-ev).days if filed and ev else None
        acc=r.get("acceptance_datetime") or "";av=bool(re.fullmatch(r"\d{14}",acc));after=acc[8:]>="160000" if av else None
        out.append({"accession":r["accession"],"quarter":r["quarter"],"family":family,"is_amendment":r.get("is_amendment","").lower()=="true","filing_date":r.get("filing_date_header"),"acceptance_datetime_et":acc or None,"acceptance_timestamp_valid":av,"acceptance_after_1600_et":after,"subject_header_cik_provenance_only":r.get("subject_cik"),"filer_header_cik":r.get("filer_cik"),"body_issuer_name_candidate":issuer,"issuer_extraction_method":im,"class_title_candidate":cls,"class_extraction_method":cm,"cusip":c.get("cusip"),"cusip_status":c.get("cusip_status"),"event_date":ev.isoformat() if ev else None,"event_date_raw":evraw,"event_date_extraction_status":evstatus,"event_to_filing_calendar_days":lag,"first_reporting_person_candidate":owner,"owner_extraction_method":om,"first_cover_owner_fields":{k:{"raw_value_candidate":v[0],"status":v[1]} for k,v in fv.items()},"item4_purpose_section_present":i4,"item4_purpose_chars":i4chars,"sample_weight":float(r["sample_weight"]),"raw_sha256":digest})
    if len(out)!=497 or raw_verified!=600 or errors:raise ValueError(f"reconciliation failed legacy={len(out)} raw={raw_verified} errors={errors[:2]}")
    controls={"0001549575-20-000008":"Seritage Growth Properties","0001903596-22-000671":"Nano Mobile Healthcare, Inc.","0001193125-21-208169":"Seritage Growth Properties","0001172661-24-001310":"StoneCastle Financial Corp."}
    by={r["accession"]:r for r in out};control={};norm=lambda x:re.sub(r"[^A-Z0-9]","",str(x or "").upper())
    for a,expected in controls.items():
        actual=by.get(a,{}).get("body_issuer_name_candidate");ok=norm(actual)==norm(expected)
        control[a]={"expected":expected,"actual":actual,"pass":ok}
        if not ok:errors.append({"accession":a,"error":"manual issuer control failed","actual":actual})
    if errors:raise ValueError(f"manual controls failed: {errors}")
    fams={}
    for fam in ("13D","13G"):
        fs=[r for r in out if r["family"]==fam];dated=[r for r in fs if r["event_date"]];lags=[r["event_to_filing_calendar_days"] for r in dated if r["event_to_filing_calendar_days"] is not None]
        qn=sum(quarter_end(date.fromisoformat(r["event_date"])) for r in dated)
        fams[fam]={"filings":len(fs),"amendments":sum(r["is_amendment"] for r in fs),"body_issuer_candidate_n":sum(bool(r["body_issuer_name_candidate"]) for r in fs),"class_title_candidate_n":sum(bool(r["class_title_candidate"]) for r in fs),"cusip_checksum_valid_n":sum(r["cusip_status"]=="UNIQUE_CHECKSUM_VALID" for r in fs),"event_date_n":len(dated),"event_date_weighted_coverage":round(wrate(fs,lambda r:bool(r["event_date"])),6),"quarter_end_event_date_n":qn,"quarter_end_pct_unweighted_among_parsed":round(100*qn/len(dated),4) if dated else None,"quarter_end_pct_weighted_among_parsed":round(100*wrate(dated,lambda r:quarter_end(date.fromisoformat(r["event_date"]))),4) if dated else None,"event_to_filing_lag_median_calendar_days":statistics.median(lags) if lags else None,"event_to_filing_lag_max_calendar_days":max(lags) if lags else None,"future_event_dates":sum(x<0 for x in lags),"same_day_event_dates":sum(x==0 for x in lags),"event_lags_over_365_days":sum(x>365 for x in lags),"acceptance_timestamp_valid_n":sum(r["acceptance_timestamp_valid"] for r in fs),"acceptance_after_1600_et_n":sum(r["acceptance_after_1600_et"] is True for r in fs),"first_reporting_person_candidate_n":sum(bool(r["first_reporting_person_candidate"]) for r in fs),"item4_purpose_section_n":sum(r["item4_purpose_section_present"] for r in fs)}
    fields={}
    for k in pats:fields[k]={"numeric_value_candidate_n":sum(bool(r["first_cover_owner_fields"][k]["raw_value_candidate"]) for r in out),"label_missing_n":sum(r["first_cover_owner_fields"][k]["status"]=="LABEL_NOT_FOUND" for r in out),"label_without_numeric_value_n":sum(r["first_cover_owner_fields"][k]["status"]=="LABEL_NO_NUMERIC_VALUE" for r in out)}
    summary={"phase":157,"status":"COMPLETED_LEGACY_HTML_PIT_FEASIBILITY_AUDIT","sources":{"phase124_run_id":P124_RUN,"phase124_artifact_id":P124_ARTIFACT,"phase124_artifact_zip_sha256":P124_ZIP_SHA,"phase124_csv_sha256":sha(b124),"phase127_run_id":P127_RUN,"phase127_artifact_id":P127_ARTIFACT,"phase127_artifact_zip_sha256":P127_ZIP_SHA,"phase127_csv_sha256":sha(b127),"sample_index_rows":600,"raw_submission_hashes_verified":raw_verified,"actual_13dg_filings":599,"legacy_html_filings":len(out),"structured_xml_filings_excluded":102},"by_family":fams,"ownership_field_value_candidates_first_cover_owner_only":fields,"combined":{"body_issuer_candidate_n":sum(bool(r["body_issuer_name_candidate"]) for r in out),"class_title_candidate_n":sum(bool(r["class_title_candidate"]) for r in out),"cusip_checksum_valid_n":sum(r["cusip_status"]=="UNIQUE_CHECKSUM_VALID" for r in out),"cusip_missing_n":sum(r["cusip_status"]=="MISSING" for r in out),"cusip_invalid_n":sum(r["cusip_status"]=="UNIQUE_CHECKSUM_INVALID" for r in out),"event_date_n":sum(bool(r["event_date"]) for r in out),"future_event_dates":sum((r["event_to_filing_calendar_days"] or 0)<0 for r in out),"acceptance_timestamp_valid_n":sum(r["acceptance_timestamp_valid"] for r in out),"acceptance_after_1600_et_n":sum(r["acceptance_after_1600_et"] is True for r in out),"first_reporting_person_candidate_n":sum(bool(r["first_reporting_person_candidate"]) for r in out),"item4_purpose_section_n_13d_only":sum(r["item4_purpose_section_present"] for r in out)},"manual_body_issuer_controls":control,"decision":{"legacy_html":"useful feasibility coverage, but candidates remain unvalidated beyond four manual identity controls; no panel promotion","issuer_identity":"body issuer name plus cover CUSIP are provenance candidates; header subject CIK and current OpenFIGI are not historical PIT security master","ownership":"only first cover-owner candidate/value fields are extracted; never sum reporting-person rows or infer independent owners","event_date":"reported event date is not public knowledge time or necessarily a trade date; use EDGAR acceptance timestamp as conservative knowledge boundary","amendments":"filing-time state updates; cross-quarter parent accession and line-level ownership diff remain unresolved","history":"600-row filing-index sample across 2016Q1-2026Q3, not a complete filing population or eligible-security universe","alpha":"NO_RETURN_TEST_NO_FEATURE_PANEL_NO_ALPHA_CLAIM","f80_modified":False,"final_holdout_used":False}}
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    with (outdir/"phase157_legacy_13dg_html_field_audit.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader()
        for r in out:w.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()})
    (outdir/"phase157_legacy_13dg_html_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return summary
def main():
    p=argparse.ArgumentParser();p.add_argument("--phase124-dir",required=True);p.add_argument("--phase127-dir",required=True);p.add_argument("--output-dir",required=True);a=p.parse_args()
    x=audit(a.phase124_dir,a.phase127_dir,a.output_dir)
    print(json.dumps({"phase":157,"status":x["status"],"sources":x["sources"],"by_family":x["by_family"],"combined":x["combined"],"decision":x["decision"]},indent=2))
if __name__=="__main__":main()
