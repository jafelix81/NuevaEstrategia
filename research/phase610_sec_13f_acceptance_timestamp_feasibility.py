#!/usr/bin/env python3
"""Phase 610 — SEC 13F acceptance timestamp feasibility audit."""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.sec_user_agent import resolve_sec_user_agent

SAMPLES = [
    {"label":"2018_marshall_wace","cik":"1325091","accession":"0001325091-18-000003"},
    {"label":"2018_clean_control","cik":"1692234","accession":"0000950123-18-000878"},
    {"label":"2018_oppenheimer_group","cik":"728889","accession":"0000728889-18-000299"},
    {"label":"2026_dakota_unmatched","cik":"1631353","accession":"0001951757-26-001605"},
    {"label":"2026_xxec_nonnumeric","cik":"1828822","accession":"0001828822-26-000007"},
    {"label":"2026_allspring_group","cik":"1890906","accession":"0001890906-26-000061"},
]


class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        value = re.sub(r"\s+", " ", data or "").strip()
        if value:
            self.parts.append(value)


def extract_labeled_value(parts: list[str], label: str, pattern: str) -> str | None:
    label_lower = label.lower()
    compiled = re.compile(pattern)
    for i, part in enumerate(parts):
        if part.strip().lower().rstrip(":") == label_lower:
            for candidate in parts[i+1:i+5]:
                match = compiled.search(candidate)
                if match:
                    return match.group(1)
    joined = " ".join(parts)
    match = re.search(rf"{re.escape(label)}\s*:?\s*{pattern}", joined, re.IGNORECASE)
    return match.group(1) if match else None


def parse_filing_detail_html(payload: bytes) -> dict:
    parser = TextCollector()
    parser.feed(payload.decode("utf-8", errors="replace"))
    accepted = extract_labeled_value(parser.parts, "Accepted", r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})")
    filing_date = extract_labeled_value(parser.parts, "Filing Date", r"(\d{4}-\d{2}-\d{2})")
    period = extract_labeled_value(parser.parts, "Period of Report", r"(\d{4}-\d{2}-\d{2})")
    accepted_date_matches = None
    conservative_date = None
    if accepted and filing_date:
        accepted_date_matches = accepted[:10] == filing_date
        conservative_date = (datetime.strptime(filing_date,"%Y-%m-%d").date()+timedelta(days=1)).isoformat()
    return {
        "accepted_at_et": accepted,
        "filing_date": filing_date,
        "period_of_report": period,
        "accepted_date_matches_filing_date": accepted_date_matches,
        "conservative_knowledge_date_after_filing_date": conservative_date,
        "timestamp_present": bool(accepted),
    }


def request_page(url: str, user_agent: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent":user_agent,
        "Accept-Encoding":"identity",
        "Accept":"text/html,application/xhtml+xml,*/*",
    })
    with urllib.request.urlopen(req,timeout=60) as response:
        payload=response.read()
        if payload[:2] == b"\x1f\x8b":
            payload=gzip.decompress(payload)
        return payload


def audit_sample(sample: dict, user_agent: str) -> dict:
    accession_compact=sample["accession"].replace("-","")
    index_url=(f"https://www.sec.gov/Archives/edgar/data/{int(sample['cik'])}/"
               f"{accession_compact}/{sample['accession']}-index.htm")
    try:
        payload=request_page(index_url,user_agent)
        fields=parse_filing_detail_html(payload)
        status="PASS" if fields["timestamp_present"] and fields["filing_date"] else "PARTIAL_MISSING_ACCEPTANCE_OR_FILING_DATE"
        return {
            "label":sample["label"],"cik":sample["cik"],"accession":sample["accession"],
            "status":status,"source_url":index_url,"html_bytes":len(payload),
            "html_sha256":hashlib.sha256(payload).hexdigest(),**fields,
            "timestamp_timezone_label":"SEC filing detail page displayed time (Eastern Time)",
        }
    except Exception as exc:
        return {"label":sample["label"],"cik":sample["cik"],"accession":sample["accession"],
                "status":"FETCH_ERROR","source_url":index_url,
                "error_type":type(exc).__name__,"error":str(exc)[:400]}


def main():
    user_agent,source=resolve_sec_user_agent()
    results=[audit_sample(s,user_agent) for s in SAMPLES]
    good=sum(x.get("status")=="PASS" for x in results)
    matches=sum(x.get("accepted_date_matches_filing_date") is True for x in results)
    out={
        "phase":610,"generated_utc":datetime.now(timezone.utc).isoformat(),
        "user_agent_source":source,"status":"PASS_ACCEPTANCE_TIMESTAMP_FEASIBILITY" if good==len(SAMPLES) else "PARTIAL_ACCEPTANCE_TIMESTAMP_FEASIBILITY",
        "samples_total":len(SAMPLES),"samples_with_accepted_timestamp":good,
        "accepted_date_matches_filing_date":matches,"samples":results,
        "methodology":"Use the exact SEC filing-detail Accepted timestamp (displayed ET) where available. Until full coverage is established, a conservative fallback is to make the filing unavailable until after its filing date; convert to the first subsequent XNYS session only with a validated exchange calendar.",
        "signal_eligible":False,
    }
    Path("phase610_sec_13f_acceptance_timestamp_feasibility.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out,indent=2))


if __name__=="__main__":
    main()
