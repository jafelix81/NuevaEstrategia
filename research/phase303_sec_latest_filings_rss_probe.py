#!/usr/bin/env python3
"""One-time SEC Latest Filings Atom/RSS feasibility probe for Forms 4 and 4/A.

This is a prospective endpoint probe only. Feed updated timestamps are not
treated as exact first-public timestamps; raw entity rows, complete-submission
header cross-checks and poll intervals are preserved for future validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from xml.etree import ElementTree as ET

BASE = "https://www.sec.gov/cgi-bin/browse-edgar"
HOST = "www.sec.gov"
MAX_BYTES = 20 * 1024 * 1024
QUERIES = {
    "form4": {"action": "getcurrent", "type": "4", "owner": "include", "count": "100", "output": "atom"},
    "form4a": {"action": "getcurrent", "type": "4/A", "owner": "include", "count": "100", "output": "atom"},
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(element: ET.Element, name: str) -> str:
    for child in list(element):
        if local_name(child.tag) == name:
            return (child.text or "").strip()
    return ""


def form_from_title(title: str) -> str:
    match = re.match(r"^\s*(\d+(?:/A)?)\s*[-–:]", title, re.I)
    return match.group(1).upper() if match else ""


def accession_from_url(url: str) -> str:
    dashed = re.search(r"(\d{10}-\d{2}-\d{6})", url)
    if dashed:
        return dashed.group(1)
    digits = re.findall(r"(?<!\d)(\d{18})(?!\d)", url)
    if not digits:
        return ""
    value = digits[-1]
    return f"{value[:10]}-{value[10:12]}-{value[12:]}"


def parse_entity_title(title: str) -> dict:
    role_match = re.search(r"\((Issuer|Reporting)\)\s*$", title, re.I)
    role = role_match.group(1).title() if role_match else ""
    cik_match = re.search(r"\((\d{10})\)\s*(?:\((?:Issuer|Reporting)\))?\s*$", title, re.I)
    entity_cik = cik_match.group(1) if cik_match else ""
    name = re.sub(r"^\s*\d+(?:/A)?\s*[-–:]\s*", "", title, flags=re.I)
    name = re.sub(r"\s+\(\d{10}\)\s*(?:\((?:Issuer|Reporting)\))?\s*$", "", name, flags=re.I)
    return {"entity_name_from_title": name.strip(), "entity_cik_from_title": entity_cik, "entity_role_from_title": role}


def parse_atom(payload: bytes) -> list[dict]:
    root = ET.fromstring(payload)
    if local_name(root.tag) != "feed":
        raise ValueError("atom_root_is_not_feed")
    entries = []
    for node in root.iter():
        if local_name(node.tag) != "entry":
            continue
        title = child_text(node, "title")
        entry_id = child_text(node, "id")
        updated = child_text(node, "updated")
        summary = child_text(node, "summary")
        links = [
            child.attrib.get("href", "")
            for child in list(node)
            if local_name(child.tag) == "link" and child.attrib.get("href")
        ]
        link = links[0] if links else ""
        path_cik_match = re.search(r"/data/(\d+)/", link)
        entity = parse_entity_title(title)
        path_cik = path_cik_match.group(1) if path_cik_match else ""
        path_matches_title = bool(
            path_cik and entity["entity_cik_from_title"]
            and str(int(path_cik)) == str(int(entity["entity_cik_from_title"]))
        )
        entries.append({
            "title": title,
            "form_type_from_title": form_from_title(title),
            **entity,
            "path_cik_from_link": path_cik,
            "path_cik_matches_title_entity": path_matches_title,
            "accession_from_link": accession_from_url(link),
            "entry_id": entry_id,
            "feed_updated_raw": updated,
            "link": link,
            "summary_raw": summary,
        })
    return entries


def group_filing_entries(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    grouped = defaultdict(list)
    orphans = []
    for entry in entries:
        key = entry["accession_from_link"]
        if key:
            grouped[key].append(entry)
        else:
            orphans.append(entry)
    filings = []
    for accession, rows in sorted(grouped.items()):
        forms = sorted({x["form_type_from_title"] for x in rows if x["form_type_from_title"]})
        issuer_ciks = sorted({x["entity_cik_from_title"] for x in rows if x["entity_role_from_title"] == "Issuer" and x["entity_cik_from_title"]})
        reporting_ciks = sorted({x["entity_cik_from_title"] for x in rows if x["entity_role_from_title"] == "Reporting" and x["entity_cik_from_title"]})
        roles = sorted({x["entity_role_from_title"] for x in rows if x["entity_role_from_title"]})
        filings.append({
            "accession": accession,
            "form_type": forms[0] if len(forms) == 1 else "CONFLICT",
            "form_types": forms,
            "raw_entity_row_count": len(rows),
            "entity_roles": roles,
            "issuer_ciks": issuer_ciks,
            "reporting_ciks": reporting_ciks,
            "path_title_cik_match_count": sum(bool(x["path_cik_matches_title_entity"]) for x in rows),
            "path_title_cik_mismatch_count": sum(not x["path_cik_matches_title_entity"] for x in rows),
            "feed_updated_values": sorted({x["feed_updated_raw"] for x in rows if x["feed_updated_raw"]}),
        })
    return filings, orphans


def parse_acceptance_datetime(payload: bytes) -> str:
    match = re.search(rb"<ACCEPTANCE-DATETIME>\s*(\d{14})", payload, re.I)
    if not match:
        return ""
    raw = match.group(1).decode("ascii")
    value = datetime.strptime(raw, "%Y%m%d%H%M%S").replace(tzinfo=ZoneInfo("America/New_York"))
    return value.isoformat()


def feed_updated_matches_acceptance(feed_updated_raw: str, acceptance_iso: str) -> bool:
    if not feed_updated_raw or not acceptance_iso:
        return False
    try:
        return datetime.fromisoformat(feed_updated_raw) == datetime.fromisoformat(acceptance_iso)
    except ValueError:
        return False


def fetch(url: str, user_agent: str) -> tuple[bytes, dict]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != HOST:
        raise ValueError("non_sec_https_url_rejected")
    request = Request(url, headers={
        "User-Agent": user_agent,
        "Accept": "application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.1",
        "Accept-Encoding": "identity",
    })
    with urlopen(request, timeout=45) as response:
        payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError("rss_response_size_limit_exceeded")
        final_host = urlparse(response.geturl()).netloc.lower()
        if final_host != HOST:
            raise ValueError("non_sec_redirect_rejected")
        headers = {
            "http_status": int(response.status),
            "content_type": response.headers.get("Content-Type", ""),
            "date": response.headers.get("Date", ""),
            "last_modified": response.headers.get("Last-Modified", ""),
            "etag": response.headers.get("ETag", ""),
            "final_url": response.geturl(),
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        return payload, headers


def crosscheck_complete_submissions(
    filings: list[dict], entity_rows: list[dict], user_agent: str, raw_dir: Path
) -> list[dict]:
    checks = []
    for form in ("4", "4/A"):
        filing = next((x for x in filings if x["form_type"] == form), None)
        if filing is None:
            checks.append({"form_type": form, "status": "NO_SAMPLE_ACCESSION"})
            continue
        accession = filing["accession"]
        rows = [x for x in entity_rows if x["accession_from_link"] == accession]
        selected = next((x for x in rows if x["entity_role_from_title"] == "Issuer"), rows[0] if rows else None)
        if not selected or not selected["path_cik_from_link"]:
            checks.append({"form_type": form, "accession": accession, "status": "NO_USABLE_ENTITY_PATH"})
            continue
        accession_compact = accession.replace("-", "")
        path_cik = str(int(selected["path_cik_from_link"]))
        url = f"https://www.sec.gov/Archives/edgar/data/{path_cik}/{accession_compact}/{accession}.txt"
        item = {
            "form_type": form,
            "accession": accession,
            "selected_entity_role": selected["entity_role_from_title"],
            "selected_entity_cik": selected["entity_cik_from_title"],
            "requested_url": url,
            "feed_updated_values": filing["feed_updated_values"],
            "status": "PENDING",
        }
        try:
            payload, headers = fetch(url, user_agent)
            raw_path = raw_dir / f"submission_{form.replace('/', '_')}_{accession_compact}.txt"
            raw_path.write_bytes(payload)
            acceptance_iso = parse_acceptance_datetime(payload)
            updated_matches = [
                feed_updated_matches_acceptance(x, acceptance_iso)
                for x in filing["feed_updated_values"]
            ]
            item.update({
                "status": "HEADER_PARSED" if acceptance_iso else "ACCEPTANCE_HEADER_MISSING",
                "response_headers": headers,
                "raw_file": str(raw_path.relative_to(raw_dir.parent)),
                "acceptance_datetime_et": acceptance_iso,
                "feed_updated_equals_acceptance": any(updated_matches),
                "complete_submission_bytes": len(payload),
                "complete_submission_sha256": hashlib.sha256(payload).hexdigest(),
            })
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            item.update({
                "status": "DOWNLOAD_FAILED",
                "error_type": type(exc).__name__,
                "error": str(exc)[:240],
            })
        checks.append(item)
        time.sleep(1.0)
    return checks


def run_probe(email: str, output_dir: Path) -> dict:
    if not email or "@" not in email or any(ch.isspace() for ch in email):
        raise ValueError("SEC_CONTACT_EMAIL_missing_or_invalid")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    query_results = []
    all_entries = []
    for label, params in QUERIES.items():
        url = BASE + "?" + urlencode(params)
        started = datetime.now(timezone.utc)
        item = {
            "query_label": label,
            "requested_url": url,
            "poll_started_at_utc": started.isoformat(),
            "status": "PENDING",
        }
        try:
            payload, headers = fetch(url, user_agent)
            completed = datetime.now(timezone.utc)
            raw_path = raw_dir / f"{label}.atom"
            raw_path.write_bytes(payload)
            entries = parse_atom(payload)
            item.update({
                "status": "ATOM_PARSED",
                "poll_completed_at_utc": completed.isoformat(),
                "response_headers": headers,
                "raw_file": str(raw_path.relative_to(output_dir)),
                "entry_row_count": len(entries),
                "form_counts_by_entity_row": {},
            })
            counts = {}
            for entry in entries:
                form = entry["form_type_from_title"] or "UNPARSED"
                counts[form] = counts.get(form, 0) + 1
                entry["query_label"] = label
            item["form_counts_by_entity_row"] = counts
            item["unique_accession_count"] = len({x["accession_from_link"] for x in entries if x["accession_from_link"]})
            all_entries.extend(entries)
        except (HTTPError, URLError, TimeoutError, ValueError, ET.ParseError) as exc:
            item.update({
                "status": "QUERY_FAILED",
                "poll_completed_at_utc": datetime.now(timezone.utc).isoformat(),
                "error_type": type(exc).__name__,
                "error": str(exc)[:240],
            })
        query_results.append(item)
        time.sleep(1.0)

    filings, orphan_entries = group_filing_entries(all_entries)
    form_counts = {}
    raw_form_counts = {}
    for filing in filings:
        form = filing["form_type"]
        form_counts[form] = form_counts.get(form, 0) + 1
    for entry in all_entries:
        form = entry["form_type_from_title"] or "UNPARSED"
        raw_form_counts[form] = raw_form_counts.get(form, 0) + 1
    valid_queries = sum(x["status"] == "ATOM_PARSED" for x in query_results)
    issuer_reporting_pairs = sum(bool(x["issuer_ciks"]) and bool(x["reporting_ciks"]) for x in filings)
    complete_checks = crosscheck_complete_submissions(filings, all_entries, user_agent, raw_dir)
    status = "PASS_ATOM_ENDPOINT" if valid_queries >= 1 else "BLOCKED_NO_VALID_ATOM_RESPONSE"
    result = {
        "phase": 303,
        "status": status,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "query_results": query_results,
        "summary": {
            "queries_attempted": len(QUERIES),
            "valid_atom_responses": valid_queries,
            "raw_entity_entry_rows": len(all_entries),
            "unique_accessions": len(filings),
            "orphan_entry_rows_without_accession": len(orphan_entries),
            "raw_form_counts_by_entity_row": raw_form_counts,
            "form_counts_by_accession": form_counts,
            "form4_accessions": form_counts.get("4", 0),
            "form4a_accessions": form_counts.get("4/A", 0),
            "accessions_with_issuer_entity_row": sum(bool(x["issuer_ciks"]) for x in filings),
            "accessions_with_reporting_entity_row": sum(bool(x["reporting_ciks"]) for x in filings),
            "accessions_with_both_issuer_and_reporting_rows": issuer_reporting_pairs,
            "accessions_with_exactly_two_entity_rows": sum(x["raw_entity_row_count"] == 2 for x in filings),
            "path_title_cik_mismatches": sum(x["path_title_cik_mismatch_count"] for x in filings),
            "complete_submission_header_crosschecks": sum(x.get("status") == "HEADER_PARSED" for x in complete_checks),
            "feed_updated_equals_acceptance": sum(x.get("feed_updated_equals_acceptance") is True for x in complete_checks),
        },
        "complete_submission_crosschecks": complete_checks,
        "entity_rows": all_entries,
        "filings": filings,
        "orphan_entity_rows": orphan_entries,
        "controls": {
            "exact_first_public_timestamp_verified": False,
            "historical_backfill_available": False,
            "strict_pit_admitted": False,
            "alpha_test": False,
            "return_test": False,
            "bootstrap_loo": False,
            "chronological_oos": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "parameters_changed": False,
            "email_sent": False,
            "data_purchase": False,
        },
    }
    (output_dir / "phase303_rss_probe_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase303_output")
    parser.add_argument("--contact-email", required=True)
    args = parser.parse_args()
    result = run_probe(args.contact_email.strip(), Path(args.output_dir))
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    print("PHASE303_STATUS=" + result["status"])
    if result["status"] != "PASS_ATOM_ENDPOINT":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
