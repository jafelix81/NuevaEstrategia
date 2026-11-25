#!/usr/bin/env python3
"""Phase 607 — reconcile selected SEC 13F TSV exceptions to original EDGAR XML."""
from __future__ import annotations

import hashlib
import gzip
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import PurePosixPath
from pathlib import Path

try:
    from research.sec_user_agent import resolve_sec_user_agent
except ModuleNotFoundError:
    from sec_user_agent import resolve_sec_user_agent

SAMPLES = [
    {"label":"2018_unmatched_large_token","cik":"1325091","accession":"0001325091-18-000003"},
    {"label":"2018_sequence_match_control","cik":"1692234","accession":"0000950123-18-000878"},
    {"label":"2018_duplicate_sequence","cik":"728889","accession":"0000728889-18-000299"},
    {"label":"2026_unmatched_numeric","cik":"1631353","accession":"0001951757-26-001605"},
    {"label":"2026_nonnumeric_reference","cik":"1828822","accession":"0001828822-26-000007"},
    {"label":"2026_duplicate_sequence","cik":"1890906","accession":"0001890906-26-000061"},
]


def local_name(tag: str) -> str:
    return str(tag).split("}")[-1].split(":")[-1]


def tokenize_reference(value: str) -> dict:
    tokens = [x for x in re.split(r"[,\s]+", str(value or "").strip()) if x]
    return {
        "zero_tokens": sum(x == "0" for x in tokens),
        "numeric_tokens": [x for x in tokens if x.isdigit() and x != "0"],
        "nonnumeric_tokens": [x for x in tokens if not x.isdigit()],
    }


def child_text(node: ET.Element, wanted: str) -> str:
    for child in list(node):
        if local_name(child.tag).lower() == wanted.lower():
            return (child.text or "").strip()
    return ""


def parse_13f_xml(payload: bytes) -> dict:
    root = ET.fromstring(payload)
    manager_entries = []
    info_tokens = []
    info_rows = 0
    for node in root.iter():
        tag = local_name(node.tag).lower()
        if tag == "othermanager2":
            manager_entries.append({
                "sequence_number": child_text(node, "sequenceNumber"),
                "cik": child_text(node, "cik"),
                "file_number": child_text(node, "form13FFileNumber"),
                "name": child_text(node, "name"),
            })
        elif tag == "infotable":
            info_rows += 1
            for child in node.iter():
                if local_name(child.tag).lower() == "othermanager":
                    info_tokens.extend(tokenize_reference(child.text or "")["numeric_tokens"])
                    info_tokens.extend("NONNUM:" + x for x in tokenize_reference(child.text or "")["nonnumeric_tokens"])
                    info_tokens.extend("ZERO" for _ in range(tokenize_reference(child.text or "")["zero_tokens"]))
    return {
        "manager_entries": manager_entries,
        "info_table_rows": info_rows,
        "info_tokens": info_tokens,
    }


def summarize_source_xml(parsed_documents: list[dict]) -> dict:
    managers = []
    info_tokens = []
    info_rows = 0
    for doc in parsed_documents:
        managers.extend(doc["manager_entries"])
        info_tokens.extend(doc["info_tokens"])
        info_rows += doc["info_table_rows"]
    sequence_values = [x["sequence_number"] for x in managers if x["sequence_number"].isdigit()]
    sequence_counts = Counter(sequence_values)
    sequence_set = set(sequence_values)
    numeric_tokens = [x for x in info_tokens if x not in {"ZERO"} and not x.startswith("NONNUM:")]
    zero_tokens = sum(x == "ZERO" for x in info_tokens)
    nonnumeric_tokens = [x[7:] for x in info_tokens if x.startswith("NONNUM:")]
    matched = sum(x in sequence_set for x in numeric_tokens)
    ambiguous = sum(sequence_counts.get(x, 0) > 1 for x in numeric_tokens)
    return {
        "manager_entry_rows": len(managers),
        "manager_sequence_values": len(sequence_values),
        "unique_manager_sequences": len(sequence_set),
        "duplicate_sequence_values": {k:v for k,v in sorted(sequence_counts.items()) if v > 1},
        "info_table_rows": info_rows,
        "numeric_reference_tokens": len(numeric_tokens),
        "zero_reference_tokens": zero_tokens,
        "nonnumeric_reference_tokens": len(nonnumeric_tokens),
        "sequence_matched_tokens": matched,
        "unmatched_numeric_tokens": len(numeric_tokens) - matched,
        "ambiguous_sequence_tokens": ambiguous,
        "sample_unmatched_numeric": [x for x in numeric_tokens if x not in sequence_set][:12],
        "sample_nonnumeric": nonnumeric_tokens[:12],
    }


def request_bytes(url: str, user_agent: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": user_agent,
        "Accept-Encoding": "identity",
        "Accept": "application/json,application/xml,text/xml,*/*",
    })
    with urllib.request.urlopen(req, timeout=timeout) as response:
        payload = response.read()
        if payload[:2] == b"\\x1f\\x8b":
            payload = gzip.decompress(payload)
        return payload


def walk_xml_files(base_url: str, user_agent: str, depth: int = 0,
                   seen: set[str] | None = None) -> list[str]:
    if seen is None:
        seen = set()
    if depth > 2 or base_url in seen:
        return []
    seen.add(base_url)
    payload = request_bytes(base_url.rstrip("/") + "/index.json", user_agent)
    data = json.loads(payload.decode("utf-8"))
    items = data.get("directory", {}).get("item", [])
    found = []
    for item in items:
        name = str(item.get("name") or "")
        kind = str(item.get("type") or "").lower()
        if kind == "file" and name.lower().endswith(".xml"):
            found.append(base_url.rstrip("/") + "/" + name)
        elif kind == "dir" and depth < 2:
            low = name.lower()
            if low.startswith("xsl") or "13f" in low or "info" in low:
                found.extend(walk_xml_files(base_url.rstrip("/") + "/" + name, user_agent, depth + 1, seen))
        time.sleep(0.08)
    return found


def audit_sample(sample: dict, user_agent: str) -> dict:
    accession_compact = sample["accession"].replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{int(sample['cik'])}/{accession_compact}"
    try:
        xml_urls = walk_xml_files(base, user_agent)
    except Exception as exc:
        return {"label":sample["label"],"accession":sample["accession"],"status":"INDEX_FETCH_ERROR",
                "error_type":type(exc).__name__,"error":str(exc)[:400],"index_url":base+"/index.json"}
    # Prefer primary / information-table files. Keep a small, bounded set.
    xml_urls = sorted(set(xml_urls), key=lambda u: (
        0 if "primary_doc" in u.lower() else 1 if "infotable" in u.lower() or "information" in u.lower() else 2,
        len(u), u
    ))[:8]
    documents = []
    errors = []
    for url in xml_urls:
        try:
            payload = request_bytes(url, user_agent)
            parsed = parse_13f_xml(payload)
            if parsed["manager_entries"] or parsed["info_table_rows"]:
                documents.append({
                    "url":url,"bytes":len(payload),"sha256":hashlib.sha256(payload).hexdigest(),
                    "manager_entries":parsed["manager_entries"],"info_table_rows":parsed["info_table_rows"],
                    "info_tokens":parsed["info_tokens"],
                })
        except Exception as exc:
            errors.append({"url":url,"error_type":type(exc).__name__,"error":str(exc)[:250]})
        time.sleep(0.12)
    aggregate = summarize_source_xml(documents)
    status = "PASS_SOURCE_XML_PARSED" if documents and (aggregate["manager_entry_rows"] or aggregate["info_table_rows"]) else "NO_RELEVANT_XML_PARSED"
    return {
        "label":sample["label"],"accession":sample["accession"],"cik":sample["cik"],
        "status":status,"index_url":base+"/index.json","xml_urls_discovered":len(xml_urls),
        "documents":documents,"fetch_or_parse_errors":errors,"source_xml_summary":aggregate,
        "signal_eligible":False,
    }


def main() -> None:
    user_agent, source = resolve_sec_user_agent()
    output = {"phase":607,"generated_utc":datetime.now(timezone.utc).isoformat(),
              "user_agent_source":source,"status":"UNKNOWN","samples":[]}
    for sample in SAMPLES:
        try:
            output["samples"].append(audit_sample(sample,user_agent))
        except Exception as exc:
            output["samples"].append({"label":sample["label"],"accession":sample["accession"],
                                      "status":"AUDIT_ERROR","error_type":type(exc).__name__,
                                      "error":str(exc)[:400]})
    good = sum(x.get("status")=="PASS_SOURCE_XML_PARSED" for x in output["samples"])
    output["status"] = "PASS_BOUNDED_SOURCE_XML_RECONCILIATION" if good == len(SAMPLES) else "PARTIAL_SOURCE_XML_RECONCILIATION"
    output["interpretation"] = (
        "Original EDGAR XML parsing and within-filing sequence/reference comparison only. "
        "No beneficial ownership, control, trade direction, alpha, OOS, bootstrap, LOO or production eligibility is inferred."
    )
    output["next_gate"] = (
        "Compare these source XML findings to exact TSV rows from the same accessions; expand the sample only where the source-vs-dataset discrepancy remains material."
    )
    Path("phase607_sec_13f_source_xml_reconciliation.json").write_text(json.dumps(output,indent=2),encoding="utf-8")
    print(json.dumps(output,indent=2))


if __name__ == "__main__":
    main()
