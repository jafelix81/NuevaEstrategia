#!/usr/bin/env python3
"""Prospective SEC Form 144 / 144-A first-seen capture; no return tests or signals."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from research import phase401_form144a_full_parent_identity_census as p401
from research import phase509_form144_structured_detail_parser as p509

PHASE = 403
DATA_DIR = Path("research/data/sec_form144_first_seen")
STATE_PATH = DATA_DIR / "state.json"
EVENTS_PATH = DATA_DIR / "events.csv"
RECONCILIATION_PATH = DATA_DIR / "acceptance_reconciliation.csv"
FEED_OBSERVATIONS_PATH = DATA_DIR / "feed_observations.csv"
STRUCTURED_DETAILS_PATH = DATA_DIR / "sale_details.csv"
STRUCTURED_BACKFILL_LIMIT = 10
MANIFEST_PATH = Path("research/PHASE401_FORM144_CANDIDATE_CIK_MANIFEST_2026-11-14.json")
EXPECTED_MANIFEST_SHA256 = "d20a1e42c7dfe3ef91248aa2aeecd5af7d853b91"
EXPECTED_CANDIDATE_CIK_COUNT = 290
EXPECTED_SOURCE_ARTIFACT_SHA256 = "939d5564b14ce0f41df23a2c9ab681977cfde141cd0ea2b3c1213b1c5bfaf613"
MAX_FEED_ENTRIES = 100  # SEC Atom page-size ceiling; actual page length can be smaller
MAX_FEED_PAGES = 10       # fail closed after at most 1,000 raw Atom entries per feed/poll
FEED_PAGE_DELAY_SECONDS = 0.25

FEEDS = {
    "144": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=144&owner=include&count=100&output=atom",
    "144A": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=144%2FA&owner=include&count=100&output=atom",
}

EVENT_FIELDS = [
    "accession", "form", "feed_name", "feed_names", "cross_feed_provenance_complete",
    "capture_poll_status", "feed_title", "feed_summary",
    "feed_link", "feed_updated_raw", "feed_updated_utc", "feed_path_cik",
    "first_seen_at_utc", "first_seen_poll_started_utc",
    "first_seen_interval_lower_bound_utc", "first_seen_interval_upper_bound_utc",
    "first_seen_interval_status", "first_seen_poll_run_id", "capture_mode",
    "submission_acceptance_et", "submission_acceptance_utc",
    "feed_updated_minus_acceptance_seconds", "first_seen_upper_minus_acceptance_seconds",
    "timing_anomaly", "issuer_cik", "issuer_name", "filer_cik", "seller_name",
    "previous_accession", "remarks", "xml_status", "xml_source", "xml_sha256",
    "submission_txt_status", "candidate_issuer_match",
    "candidate_manifest_cik_count", "candidate_manifest_source_artifact_sha256",
    "historical_f80_membership_verified", "public_availability_certified",
    "research_observation_eligible", "signal_eligible", "same_day_intraday_use_authorized",
    "first_seen_is_upper_bound_not_exact_receipt",
]

RECON_FIELDS = [
    "accession", "form", "feed_updated_utc", "first_seen_at_utc",
    "acceptance_et", "acceptance_utc", "acceptance_source", "filing_date",
    "feed_updated_minus_acceptance_seconds", "first_seen_upper_minus_acceptance_seconds",
    "timing_anomaly", "filing_detail_url", "reconciliation_run_id",
    "reconciled_at_utc", "signal_eligible", "public_availability_certified",
]
FEED_OBSERVATION_FIELDS = [
    "poll_run_id", "feed_name", "accession", "form", "feed_updated_raw",
    "feed_updated_utc", "feed_link", "feed_path_cik", "feed_url",
    "feed_raw_sha256", "feed_response_received_utc",
]

def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def parse_utc(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def local_name(tag):
    return str(tag).rsplit("}", 1)[-1].lower()

def child_text(node, wanted):
    for child in list(node):
        if local_name(child.tag) == wanted.lower():
            return "".join(child.itertext()).strip()
    return None

def extract_accession(*values):
    for value in values:
        text = str(value or "")
        match = re.search(r"(?<!\d)(\d{10}-\d{2}-\d{6})(?!\d)", text)
        if match:
            return match.group(1)
    for value in values:
        text = str(value or "")
        match = re.search(r"(?<!\d)(\d{18})(?!\d)", text)
        if match:
            digits = match.group(1)
            return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"
    return None

def path_cik_from_url(url):
    match = re.search(r"/data/(\d+)/", str(url or ""), re.I)
    return p401.norm_cik(match.group(1)) if match else None

def parse_form_from_title(title, fallback):
    match = re.match(r"\s*(144/A|144)\b", str(title or ""), re.I)
    if match:
        return "144/A" if match.group(1).upper() == "144/A" else "144"
    return "144/A" if fallback == "144A" else "144"

def parse_atom_feed(raw, feed_name, feed_url):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    root = ET.fromstring(raw)
    entries = []
    for node in root.iter():
        if local_name(node.tag) != "entry":
            continue
        entry_id = child_text(node, "id")
        title = child_text(node, "title") or ""
        updated = child_text(node, "updated")
        summary_node = next((x for x in list(node) if local_name(x.tag) == "summary"), None)
        summary = "".join(summary_node.itertext()).strip() if summary_node is not None else ""
        links = [x for x in list(node) if local_name(x.tag) == "link"]
        link_node = next((x for x in links if x.attrib.get("rel") in (None, "", "alternate")), None)
        if link_node is None and links:
            link_node = links[0]
        link = link_node.attrib.get("href") if link_node is not None else entry_id
        accession = extract_accession(entry_id, link, title, summary)
        if not accession:
            continue
        updated_dt = parse_utc(updated)
        entries.append({
            "accession": accession,
            "form": parse_form_from_title(title, feed_name),
            "feed_name": feed_name,
            "feed_title": title,
            "feed_summary": summary[:3000],
            "feed_link": link or "",
            "feed_updated_raw": updated or "",
            "feed_updated_utc": updated_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z") if updated_dt else "",
            "feed_path_cik": path_cik_from_url(link),
            "feed_url": feed_url,
        })
    # One accession is one filing version. Keep a deterministic first source and retain all feed names.
    deduped = {}
    for item in entries:
        prior = deduped.get(item["accession"])
        if prior is None:
            item["feed_names"] = [feed_name]
            deduped[item["accession"]] = item
        elif feed_name not in prior["feed_names"]:
            prior["feed_names"].append(feed_name)
    return sorted(deduped.values(), key=lambda x: (x["feed_updated_utc"], x["accession"]))

def load_candidate_manifest(path=MANIFEST_PATH):
    raw = Path(path).read_bytes()
    # The repository blob SHA is pinned separately in GitHub; validate the immutable source artifact and exact CIK set here.
    manifest = json.loads(raw.decode("utf-8"))
    if manifest.get("source_artifact_sha256") != EXPECTED_SOURCE_ARTIFACT_SHA256:
        raise ValueError("Phase 401 candidate manifest source artifact digest mismatch")
    ciks = [p401.norm_cik(x) for x in manifest.get("candidate_ciks", [])]
    ciks = [x for x in ciks if x]
    if len(ciks) != EXPECTED_CANDIDATE_CIK_COUNT or len(set(ciks)) != EXPECTED_CANDIDATE_CIK_COUNT:
        raise ValueError("Phase 401 candidate manifest must contain exactly 290 unique CIKs")
    return set(ciks), manifest

def parse_acceptance_submission(raw):
    """Parse EDGAR's native SGML element and the legacy colon-delimited form.

    SEC complete-submission headers normally encode the clock as
    <ACCEPTANCE-DATETIME>YYYYMMDDhhmmss (without a closing tag). Older
    fixtures and some normalized payloads use ACCEPTANCE-DATETIME: value.
    Conflicting distinct clocks fail closed rather than selecting one.
    """
    if isinstance(raw, bytes):
        raw = raw.decode("latin-1", "replace")
    text = str(raw)
    matches = re.findall(
        r"(?:<\s*ACCEPTANCE-DATETIME\s*>\s*|ACCEPTANCE-DATETIME\s*:\s*)(\d{14})(?!\d)",
        text,
        flags=re.I,
    )
    unique = sorted(set(matches))
    if len(unique) != 1:
        return None, None
    accepted_et = datetime.strptime(unique[0], "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    dt = datetime.strptime(accepted_et, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo("America/New_York"))
    accepted_utc = dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return accepted_et, accepted_utc

def parse_acceptance_html(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    visible = html.unescape(re.sub(r"<[^>]+>", " ", str(raw)))
    visible = re.sub(r"\s+", " ", visible)
    match = re.search(r"\bAccepted\b\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", visible, re.I)
    filing = re.search(r"\bFiling Date\b\s*(\d{4}-\d{2}-\d{2})", visible, re.I)
    accepted_et = match.group(1) if match else None
    accepted_utc = None
    if accepted_et:
        dt = datetime.strptime(accepted_et, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo("America/New_York"))
        accepted_utc = dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return accepted_et, accepted_utc, filing.group(1) if filing else None

def extract_submission_xml(raw):
    if isinstance(raw, bytes):
        text = raw.decode("latin-1", "replace")
    else:
        text = str(raw)
    blocks = re.findall(r"<XML>\s*(.*?)\s*</XML>", text, flags=re.I | re.S)
    for block in blocks:
        if re.search(r"<\s*edgarSubmission\b", block, re.I):
            return block.encode("utf-8", "replace")
    if re.search(r"<\s*edgarSubmission\b", text, re.I):
        return text.encode("utf-8", "replace")
    return None

def fetch_document_metadata(item, candidate_ciks):
    result = {
        "submission_acceptance_et": None, "submission_acceptance_utc": None, "submission_type": None,
        "issuer_cik": None, "issuer_name": None, "filer_cik": None,
        "seller_name": None, "previous_accession": None, "remarks": "",
        "xml_status": "unresolved", "xml_source": None, "xml_sha256": None,
        "submission_txt_status": "not_attempted", "candidate_issuer_match": None,
        "structured_details": None, "structured_parse_status": "not_attempted",
        "structured_parse_error": None,
    }
    path_cik = item.get("feed_path_cik")
    accession = item["accession"]
    if not path_cik:
        result["submission_txt_status"] = "no_archive_path_cik"
        return result
    accession_digits = accession.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{int(path_cik)}/{accession_digits}"
    txt_url = f"{base}/{accession}.txt"
    xml_bytes = None
    try:
        submission = p401.fetch_bytes(txt_url, sec=True, timeout=45, retries=2)
        result["submission_txt_status"] = "retrieved"
        accepted_et, accepted_utc = parse_acceptance_submission(submission)
        result["submission_acceptance_et"] = accepted_et
        result["submission_acceptance_utc"] = accepted_utc
        xml_bytes = extract_submission_xml(submission)
        if xml_bytes is not None:
            result["xml_source"] = "complete_submission_xml_block"
    except Exception as exc:
        result["submission_txt_status"] = f"unresolved:{type(exc).__name__}:{str(exc)[:100]}"
    if xml_bytes is None:
        xml_url = f"{base}/primary_doc.xml"
        try:
            xml_bytes = p401.fetch_bytes(xml_url, sec=True, timeout=45, retries=2)
            result["xml_source"] = "primary_doc.xml"
        except Exception as exc:
            result["xml_status"] = f"unresolved:{type(exc).__name__}:{str(exc)[:100]}"
            result["structured_parse_status"] = "unresolved_fetch"
            return result
    result["xml_sha256"] = hashlib.sha256(xml_bytes).hexdigest()
    try:
        result["structured_details"] = p509.parse_form144_details(xml_bytes)
        result["structured_parse_status"] = "parsed"
    except Exception as exc:
        result["structured_parse_status"] = "parse_error"
        result["structured_parse_error"] = f"{type(exc).__name__}:{str(exc)[:160]}"
    try:
        parsed = p401.parse_form144_xml(xml_bytes)
        result.update({
            "submission_type": parsed.get("submission_type"),
            "issuer_cik": parsed.get("issuer_cik"),
            "issuer_name": parsed.get("issuer_name"),
            "filer_cik": parsed.get("filer_cik"),
            "seller_name": parsed.get("seller_name"),
            "previous_accession": p401.accession(parsed.get("previous_accession")) if parsed.get("previous_accession") else None,
            "remarks": " | ".join(parsed.get("remarks") or []),
            "xml_status": "retrieved",
            "xml_sha256": hashlib.sha256(xml_bytes).hexdigest(),
        })
        issuer_cik = p401.norm_cik(parsed.get("issuer_cik"))
        result["candidate_issuer_match"] = issuer_cik in candidate_ciks if issuer_cik else None
    except Exception as exc:
        result["xml_status"] = f"parse_error:{type(exc).__name__}:{str(exc)[:120]}"
        result["xml_sha256"] = hashlib.sha256(xml_bytes).hexdigest()
    return result

def seconds_between(later, earlier):
    a, b = parse_utc(later), parse_utc(earlier)
    return (a - b).total_seconds() if a and b else None

def detect_possible_gap(entries, previous_latest_accession):
    """A prior watermark absent after pagination means the interval is unbounded."""
    accessions = {x["accession"] for x in entries}
    return bool(previous_latest_accession and previous_latest_accession not in accessions)

def interval_policy(previous_poll_utc, previous_poll_had_gap, current_poll_has_gap):
    if not previous_poll_utc:
        return None, "INITIAL_BASELINE_NO_LOWER_BOUND"
    if previous_poll_had_gap:
        return None, "PREVIOUS_POLL_GAP_INTERVAL_UNBOUNDED"
    if current_poll_has_gap:
        return None, "POSSIBLE_FEED_WINDOW_GAP"
    return previous_poll_utc, "BOUNDED_BY_SUCCESSIVE_SUCCESSFUL_POLLS"

def previous_poll_start_by_feed(state):
    """Only explicit poll-start clocks may bound a future PIT interval.

    Legacy last_successful_poll_utc_by_feed values are page-receipt timestamps
    and are intentionally not reused as interval lower bounds.
    """
    return dict((state or {}).get("last_successful_poll_started_utc_by_feed", {}))


def read_json(path):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

def read_existing_accessions(path=EVENTS_PATH):
    path = Path(path)
    if not path.exists():
        return set()
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return {p401.accession(row.get("accession")) for row in csv.DictReader(handle) if row.get("accession")}

def append_events(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVENT_FIELDS, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                             for key, value in row.items()})

def build_event(item, metadata, poll_started, response_received, interval_start,
                interval_status, run_id, mode, manifest,
                cross_feed_provenance_complete=True, capture_poll_status="complete"):
    accepted = metadata.get("submission_acceptance_utc")
    feed_delta = seconds_between(item.get("feed_updated_utc"), accepted)
    seen_delta = seconds_between(response_received, accepted)
    interval_valid = interval_status == "BOUNDED_BY_SUCCESSIVE_SUCCESSFUL_POLLS"
    return {
        "accession": item["accession"],
        "form": metadata.get("submission_type") or item.get("form"),
        "feed_name": item["feed_name"],
        "feed_names": item.get("feed_names", [item["feed_name"]]),
        "cross_feed_provenance_complete": bool(cross_feed_provenance_complete),
        "capture_poll_status": capture_poll_status,
        "feed_title": item.get("feed_title"),
        "feed_summary": item.get("feed_summary"),
        "feed_link": item.get("feed_link"),
        "feed_updated_raw": item.get("feed_updated_raw"),
        "feed_updated_utc": item.get("feed_updated_utc"),
        "feed_path_cik": item.get("feed_path_cik"),
        "first_seen_at_utc": response_received,
        "first_seen_poll_started_utc": poll_started,
        "first_seen_interval_lower_bound_utc": interval_start,
        "first_seen_interval_upper_bound_utc": response_received,
        "first_seen_interval_status": interval_status,
        "first_seen_poll_run_id": str(run_id),
        "capture_mode": mode,
        "submission_acceptance_et": metadata.get("submission_acceptance_et"),
        "submission_acceptance_utc": accepted,
        "feed_updated_minus_acceptance_seconds": feed_delta,
        "first_seen_upper_minus_acceptance_seconds": seen_delta,
        "timing_anomaly": bool(seen_delta is not None and seen_delta < 0),
        "issuer_cik": metadata.get("issuer_cik"),
        "issuer_name": metadata.get("issuer_name"),
        "filer_cik": metadata.get("filer_cik"),
        "seller_name": metadata.get("seller_name"),
        "previous_accession": metadata.get("previous_accession"),
        "remarks": metadata.get("remarks"),
        "xml_status": metadata.get("xml_status"),
        "xml_source": metadata.get("xml_source"),
        "xml_sha256": metadata.get("xml_sha256"),
        "submission_txt_status": metadata.get("submission_txt_status"),
        "candidate_issuer_match": metadata.get("candidate_issuer_match"),
        "candidate_manifest_cik_count": len(manifest["candidate_ciks"]),
        "candidate_manifest_source_artifact_sha256": manifest["source_artifact_sha256"],
        "historical_f80_membership_verified": False,
        "public_availability_certified": False,
        "research_observation_eligible": bool(mode == "schedule" and interval_valid),
        "signal_eligible": False,
        "same_day_intraday_use_authorized": False,
        "first_seen_is_upper_bound_not_exact_receipt": True,
    }

def classify_atom_response(raw):
    """Classify a feed response without persisting or exposing its body.

    The classifier is diagnostic only. It never turns a malformed/empty
    response into a successful poll and does not infer why the provider
    returned the payload.
    """
    if raw is None:
        return "NO_RESPONSE"
    if isinstance(raw, str):
        sample = raw[:512].lstrip("\ufeff\x00\t\r\n ")
    else:
        if not raw:
            return "EMPTY"
        sample = raw[:512].decode("utf-8", "replace").lstrip("\ufeff\x00\t\r\n ")
    if not sample:
        return "EMPTY"
    if re.search(r"<\s*(?:!doctype\s+html|html\b)", sample, flags=re.I):
        return "HTML"
    if re.search(r"<\s*feed\b", sample, flags=re.I):
        return "ATOM_XML"
    if sample.startswith(("{", "[")):
        return "JSON"
    if sample.startswith("<") or re.search(r"<\?xml\b", sample, flags=re.I):
        return "XML_OR_MARKUP"
    return "OTHER_TEXT"


def count_atom_entries(raw):
    """Count raw Atom <entry> nodes before accession deduplication."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    root = ET.fromstring(raw)
    return sum(1 for node in root.iter() if local_name(node.tag) == "entry")


def fetch_all_feeds(previous_latest_by_feed=None, mode="schedule"):
    """Page each SEC Atom feed until its prior accession watermark is found.

    Offsets advance by raw Atom entry count, not unique accessions: EDGAR can
    emit multiple role rows for one accession. A short non-empty page is not
    assumed to be the end because the observed 144 feed returned 50 entries
    despite count=100. Repeated pages, fetch failures and the page ceiling
    remain gap/quarantine conditions.
    """
    previous_latest_by_feed = previous_latest_by_feed or {}
    snapshots = {}
    errors = {}
    for feed_name, base_url in FEEDS.items():
        prior_latest = previous_latest_by_feed.get(feed_name)
        max_pages = 1 if mode == "bootstrap" or not prior_latest else MAX_FEED_PAGES
        offset = 0
        pages = []
        combined = {}
        seen_page_hashes = set()
        previous_found = False
        page_error = None
        stop_reason = "max_pages_reached"
        total_raw_entries = 0

        for page_index in range(max_pages):
            page_url = f"{base_url}&start={offset}" if "?" in base_url else f"{base_url}?start={offset}"
            raw = None
            try:
                raw = p401.fetch_bytes(page_url, sec=True, timeout=60, retries=4)
                received = now_utc()
                page_sha = hashlib.sha256(raw).hexdigest()
                if page_sha in seen_page_hashes:
                    page_error = {
                        "url": page_url,
                        "error_type": "RepeatedPageHash",
                        "error": "SEC Atom pagination returned a previously observed page hash; offset may be ignored.",
                        "page_offset": offset,
                    }
                    stop_reason = "repeated_page_hash"
                    break
                seen_page_hashes.add(page_sha)
                raw_count = count_atom_entries(raw)
                page_entries = parse_atom_feed(raw, feed_name, page_url)
                pages.append({
                    "start": offset,
                    "raw_entry_count": raw_count,
                    "unique_accession_count": len(page_entries),
                    "response_bytes": len(raw),
                    "response_kind": classify_atom_response(raw),
                    "received_at_utc": received,
                    "raw_sha256": page_sha,
                    "url": page_url,
                })
                total_raw_entries += raw_count

                for item in page_entries:
                    item = dict(item)
                    item["_feed_page_offset"] = offset
                    item["_feed_page_url"] = page_url
                    item["_feed_page_raw_sha256"] = page_sha
                    item["_feed_page_received_utc"] = received
                    item["_feed_page_raw_entry_count"] = raw_count
                    accession = item["accession"]
                    if prior_latest and accession == prior_latest:
                        previous_found = True
                    combined.setdefault(accession, item)

                if previous_found:
                    stop_reason = "previous_latest_found"
                    break
                if raw_count == 0:
                    stop_reason = "empty_page"
                    break
                if page_index + 1 >= max_pages:
                    stop_reason = "bootstrap_single_page" if not prior_latest else "max_pages_reached"
                    if prior_latest:
                        page_error = {
                            "url": page_url,
                            "error_type": "PaginationLimitReached",
                            "error": f"Prior accession watermark not found within {max_pages} pages.",
                            "page_offset": offset,
                        }
                    break
                # Advance by raw Atom rows, including repeated issuer/reporting roles.
                offset += raw_count
                time.sleep(FEED_PAGE_DELAY_SECONDS)
            except Exception as exc:
                page_error = {
                    "url": page_url,
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:1000],
                    "page_offset": offset,
                    "response_bytes": len(raw) if raw is not None else None,
                    "response_kind": classify_atom_response(raw),
                    "raw_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
                }
                stop_reason = "page_fetch_error"
                break

        if page_error:
            errors[feed_name] = page_error
        if not pages:
            continue

        entries = sorted(combined.values(), key=lambda x: (x["feed_updated_utc"], x["accession"]))
        page_hashes = [page["raw_sha256"] for page in pages]
        aggregate_sha = hashlib.sha256("|".join(page_hashes).encode("ascii")).hexdigest()
        pagination_complete = bool(
            previous_found or stop_reason in ("empty_page", "bootstrap_single_page") or not prior_latest
        )
        if page_error:
            pagination_complete = False
        snapshots[feed_name] = {
            "url": base_url,
            "raw_sha256": aggregate_sha,
            "response_bytes": sum(page["response_bytes"] for page in pages),
            "received_at_utc": pages[-1]["received_at_utc"],
            "entries": entries,
            "entry_count": len(entries),
            "raw_entry_count": total_raw_entries,
            "oldest_updated_utc": min((x["feed_updated_utc"] for x in entries if x["feed_updated_utc"]), default=None),
            "newest_updated_utc": max((x["feed_updated_utc"] for x in entries if x["feed_updated_utc"]), default=None),
            "pages": pages,
            "page_count": len(pages),
            "pagination_complete": pagination_complete,
            "pagination_stop_reason": stop_reason,
            "previous_latest_accession": prior_latest,
            "previous_latest_accession_found": previous_found if prior_latest else None,
            "possible_feed_window_gap": bool(prior_latest and not previous_found),
        }
    return snapshots, errors

def read_event_rows(path=EVENTS_PATH):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

def read_reconciled_accessions(path=RECONCILIATION_PATH):
    path = Path(path)
    if not path.exists():
        return set()
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return {p401.accession(row.get("accession")) for row in csv.DictReader(handle) if row.get("accession")}

def append_reconciliations(path, rows):
    path = Path(path)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECON_FIELDS, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerows(rows)

def fetch_acceptance_from_index(event, run_id):
    accession = event.get("accession")
    path_cik = event.get("feed_path_cik")
    if not accession or not path_cik:
        return None
    base = f"https://www.sec.gov/Archives/edgar/data/{int(path_cik)}/{accession.replace('-', '')}"
    for page_name in (f"{accession}-index.htm", f"{accession}-index.html", f"{accession}-index-headers.html"):
        url = f"{base}/{page_name}"
        try:
            raw = p401.fetch_bytes(url, sec=True, timeout=40, retries=2)
            accepted_et, accepted_utc, filing_date = parse_acceptance_html(raw)
            if not accepted_utc:
                continue
            feed_delta = seconds_between(event.get("feed_updated_utc"), accepted_utc)
            seen_delta = seconds_between(event.get("first_seen_at_utc"), accepted_utc)
            return {
                "accession": accession,
                "form": event.get("form"),
                "feed_updated_utc": event.get("feed_updated_utc"),
                "first_seen_at_utc": event.get("first_seen_at_utc"),
                "acceptance_et": accepted_et,
                "acceptance_utc": accepted_utc,
                "acceptance_source": "SEC_filing_detail_index",
                "filing_date": filing_date,
                "feed_updated_minus_acceptance_seconds": feed_delta,
                "first_seen_upper_minus_acceptance_seconds": seen_delta,
                "timing_anomaly": bool(seen_delta is not None and seen_delta < 0),
                "filing_detail_url": url,
                "reconciliation_run_id": str(run_id),
                "reconciled_at_utc": now_utc(),
                "signal_eligible": False,
                "public_availability_certified": False,
            }
        except Exception:
            continue
    return None


def feed_names_by_accession(snapshots):
    """Return every official feed in which each accession appeared in this poll."""
    names = {}
    for feed_name, snapshot in snapshots.items():
        for item in snapshot.get("entries", []):
            accession = item.get("accession")
            if not accession:
                continue
            sources = names.setdefault(accession, [])
            if feed_name not in sources:
                sources.append(feed_name)
    return names


def build_feed_observation_rows(snapshots, run_id):
    """Preserve one observation per accession/feed/poll with page-level provenance."""
    rows = []
    for feed_name, snapshot in snapshots.items():
        for item in snapshot.get("entries", []):
            rows.append({
                "poll_run_id": str(run_id),
                "feed_name": feed_name,
                "accession": item.get("accession"),
                "form": item.get("form"),
                "feed_updated_raw": item.get("feed_updated_raw"),
                "feed_updated_utc": item.get("feed_updated_utc"),
                "feed_link": item.get("feed_link"),
                "feed_path_cik": item.get("feed_path_cik"),
                "feed_url": item.get("_feed_page_url") or snapshot.get("url"),
                "feed_raw_sha256": item.get("_feed_page_raw_sha256") or snapshot.get("raw_sha256"),
                "feed_response_received_utc": item.get("_feed_page_received_utc") or snapshot.get("received_at_utc"),
            })
    return rows


def append_feed_observations(path, rows):
    """Append idempotently by (run, feed, accession); never rewrite prior observations."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if path.exists() and path.stat().st_size > 0:
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                existing.add((row.get("poll_run_id"), row.get("feed_name"), row.get("accession")))
    pending = []
    for row in rows:
        key = (str(row.get("poll_run_id")), row.get("feed_name"), row.get("accession"))
        if key not in existing:
            pending.append(row)
            existing.add(key)
    if not pending:
        return 0
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FEED_OBSERVATION_FIELDS, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerows(pending)
    return len(pending)



def backfill_missing_structured_details(events_path, details_path, candidate_ciks, run_id,
                                        limit=STRUCTURED_BACKFILL_LIMIT):
    """Re-fetch a bounded batch of already captured filings missing structured detail rows.

    New events are parsed from the same XML retrieval used by the first-seen
    collector. Historical backfill is newest-first, append-only, hash-checked,
    and capped to limit SEC requests per scheduled run.
    """
    events = read_event_rows(events_path)
    completed = p509.read_completed_accessions(details_path)
    candidates = [
        row for row in events
        if row.get("accession")
        and row.get("feed_path_cik")
        and row.get("xml_sha256")
        and row.get("accession") not in completed
    ]
    candidates.sort(
        key=lambda row: (row.get("first_seen_at_utc") or "", row.get("accession") or ""),
        reverse=True,
    )
    attempts = 0
    parsed_count = 0
    parse_error_count = 0
    hash_mismatch_count = 0
    rows_appended = 0
    unresolved = []
    for event in candidates[:max(0, int(limit))]:
        item = {
            "accession": event.get("accession"),
            "feed_path_cik": event.get("feed_path_cik"),
        }
        attempts += 1
        metadata = fetch_document_metadata(item, candidate_ciks)
        if metadata.get("xml_sha256") and metadata.get("structured_parse_status") in ("parsed", "parse_error"):
            detail_rows = p509.build_detail_rows(event, metadata)
            rows_appended += p509.append_detail_rows(details_path, detail_rows)
            completed.add(event["accession"])
            if any(row.get("parse_status") == "source_hash_mismatch" for row in detail_rows):
                hash_mismatch_count += 1
            elif metadata.get("structured_parse_status") == "parsed":
                parsed_count += 1
            else:
                parse_error_count += 1
        else:
            unresolved.append({
                "accession": event.get("accession"),
                "structured_parse_status": metadata.get("structured_parse_status"),
                "submission_txt_status": metadata.get("submission_txt_status"),
                "xml_status": metadata.get("xml_status"),
            })
    remaining = [
        row for row in events
        if row.get("accession")
        and row.get("feed_path_cik")
        and row.get("xml_sha256")
        and row.get("accession") not in p509.read_completed_accessions(details_path)
    ]
    return {
        "limit": max(0, int(limit)),
        "attempts": attempts,
        "accessions_parsed": parsed_count,
        "accessions_with_parse_error": parse_error_count,
        "source_hash_mismatch_count": hash_mismatch_count,
        "detail_rows_appended": rows_appended,
        "unresolved_count": len(unresolved),
        "unresolved_sample": unresolved[:5],
        "remaining_accessions": len(remaining),
        "newest_first": True,
        "source_hash_mismatch_rows_are_not_feature_eligible": True,
        "signal_eligible_count": 0,
    }


def run(mode, output_dir, run_id, data_dir=DATA_DIR):
    if mode not in ("bootstrap", "schedule", "manual"):
        raise ValueError("mode must be bootstrap, schedule or manual")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir = Path(data_dir)
    state_path = data_dir / "state.json"
    events_path = data_dir / "events.csv"
    candidate_ciks, manifest = load_candidate_manifest()
    previous_state = read_json(state_path) or {}
    poll_started = now_utc()
    snapshots, feed_errors = fetch_all_feeds(
        previous_state.get("latest_accession_by_feed", {}), mode=mode
    )
    poll_status = "complete" if not feed_errors else ("partial" if snapshots else "failed")

    # If both feeds fail, retain an audit artifact and fail the job without advancing state.
    if not snapshots:
        poll_completed = now_utc()
        summary = {
            "phase": PHASE, "mode": mode, "run_id": str(run_id),
            "poll_started_utc": poll_started, "poll_completed_utc": poll_completed,
            "poll_status": "failed", "successful_feeds": [],
            "failed_feeds": sorted(feed_errors), "feed_errors": feed_errors,
            "feed_summaries": {}, "cross_feed_provenance_complete": False,
            "new_event_count": 0, "new_feed_entry_count": 0,
            "new_cross_feed_overlap_count": None,
            "feed_observation_rows_observed": 0, "feed_observation_rows_appended": 0,
            "new_xml_resolved_count": 0, "structured_detail_summary": {"parser_version": p509.PARSER_VERSION,
            "new_accessions_parsed": 0, "new_detail_rows_appended": 0, "backfill": {"attempts": 0,
            "accessions_parsed": 0, "accessions_with_parse_error": 0, "detail_rows_appended": 0,
            "unresolved_count": 0, "remaining_accessions": 0, "signal_eligible_count": 0},
            "signal_eligible_count": 0}, "acceptance_reconciliation_attempts": 0,
            "acceptance_reconciliations_added": 0, "acceptance_reconciliations_unresolved": 0,
            "new_candidate_issuer_matches": 0, "candidate_manifest_cik_count": len(candidate_ciks),
            "candidate_manifest_is_historical_f80_security_master": False,
            "possible_feed_window_gap": None, "possible_feed_window_gap_complete": False,
            "research_observation_eligible_count": 0, "signal_eligible_count": 0,
            "public_availability_certified": False, "acceptance_datetime_is_not_first_public_receipt": True,
            "first_seen_is_poll_receipt_upper_bound": True, "same_day_intraday_use_authorized": False,
            "forward_returns_used": False, "alpha_test_authorized": False,
            "bootstrap_loo_or_holdout_used": False, "f80_changed": False, "production_changed": False,
            "state_write": False, "events_written": 0, "disposition": "POLL_FAILED_ALL_FEEDS",
        }
        write_json(output_dir / "summary.json", summary)
        print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
        raise RuntimeError("All SEC Atom feeds failed; audit summary written and prior state preserved.")

    source_names_by_accession = feed_names_by_accession(snapshots)
    feed_observation_rows = build_feed_observation_rows(snapshots, run_id)
    existing = read_existing_accessions(events_path)
    existing_at_poll_start = set(existing)
    new_rows = []
    new_structured_rows = []
    feed_summaries = {}
    latest_by_feed = dict(previous_state.get("latest_accession_by_feed", {}))
    # Use the prior poll START as the interval lower bound. A multi-page live
    # feed can receive new filings while pages are being read; using the last
    # page receipt would be later than some arrivals and could introduce look-ahead.
    last_poll_by_feed = previous_poll_start_by_feed(previous_state)
    last_receipt_by_feed = dict(previous_state.get("last_successful_poll_utc_by_feed", {}))
    last_gap_by_feed = dict(previous_state.get("last_poll_possible_gap_by_feed", {}))
    hash_by_feed = dict(previous_state.get("last_feed_sha256_by_feed", {}))
    poll_count_by_feed = dict(previous_state.get("poll_count_by_feed", {}))
    candidate_matches = 0
    xml_resolved = 0

    for feed_name, snapshot in snapshots.items():
        entries = snapshot["entries"]
        prior_latest = latest_by_feed.get(feed_name)
        current_gap = snapshot.get("possible_feed_window_gap", detect_possible_gap(entries, prior_latest))
        prior_gap = bool(last_gap_by_feed.get(feed_name, False))
        interval_start, interval_status = interval_policy(
            last_poll_by_feed.get(feed_name), prior_gap, current_gap
        )
        feed_summaries[feed_name] = {
            "url": snapshot["url"], "raw_sha256": snapshot["raw_sha256"],
            "response_bytes": snapshot["response_bytes"], "received_at_utc": snapshot["received_at_utc"],
            "entry_count": snapshot["entry_count"], "oldest_updated_utc": snapshot["oldest_updated_utc"],
            "newest_updated_utc": snapshot["newest_updated_utc"],
            "previous_latest_accession": prior_latest,
            "previous_latest_accession_present": snapshot.get("previous_latest_accession_found"),
            "possible_feed_window_gap": current_gap,
            "interval_lower_bound_utc": interval_start,
            "interval_lower_bound_source": "previous_successful_poll_start_utc",
            "interval_status": interval_status,
            "page_count": snapshot.get("page_count", 1),
            "raw_entry_count": snapshot.get("raw_entry_count", snapshot["entry_count"]),
            "pagination_complete": snapshot.get("pagination_complete", True),
            "pagination_stop_reason": snapshot.get("pagination_stop_reason"),
            "pages": snapshot.get("pages", []),
            "new_accessions": [],
        }
        for item in entries:
            accession = item["accession"]
            if accession not in existing_at_poll_start:
                feed_summaries[feed_name]["new_accessions"].append(accession)
            if accession in existing:
                continue
            item = dict(item)
            item["feed_names"] = source_names_by_accession.get(accession, [feed_name])
            metadata = fetch_document_metadata(item, candidate_ciks)
            item_received = item.get("_feed_page_received_utc") or snapshot["received_at_utc"]
            event = build_event(
                item, metadata, poll_started, item_received, interval_start,
                interval_status, run_id, mode, manifest,
                cross_feed_provenance_complete=not bool(feed_errors),
                capture_poll_status=poll_status,
            )
            if metadata.get("xml_sha256") and metadata.get("structured_parse_status") in ("parsed", "parse_error"):
                new_structured_rows.extend(p509.build_detail_rows(event, metadata))
            if mode != "manual":
                new_rows.append(event)
            else:
                # Manual diagnostics never create persistent first-seen records.
                event["research_observation_eligible"] = False
            if metadata.get("xml_status") == "retrieved":
                xml_resolved += 1
            if metadata.get("candidate_issuer_match") is True:
                candidate_matches += 1
            existing.add(item["accession"])
        if entries:
            latest = max(entries, key=lambda x: (x.get("feed_updated_utc") or "", x["accession"]))
            latest_by_feed[feed_name] = latest["accession"]
        # Keep both clocks: poll start is the safe next-interval lower bound;
        # final page receipt is retained for audit and latency measurement.
        last_poll_by_feed[feed_name] = poll_started
        last_receipt_by_feed[feed_name] = snapshot["received_at_utc"]
        last_gap_by_feed[feed_name] = current_gap
        hash_by_feed[feed_name] = snapshot["raw_sha256"]
        poll_count_by_feed[feed_name] = int(poll_count_by_feed.get(feed_name, 0)) + 1

    poll_completed = now_utc()
    complete_poll = poll_status == "complete"
    prior_poll_count = int(previous_state.get("poll_count", 0))
    prior_partial_count = int(previous_state.get("partial_poll_count", 0))
    prior_complete_count = int(previous_state.get(
        "complete_poll_count", max(0, prior_poll_count - prior_partial_count)
    ))
    state = {
        "schema_version": 1,
        "phase": PHASE,
        "source": "SEC EDGAR Latest Filings Atom feeds filtered to Form 144 and 144/A",
        "created_utc": previous_state.get("created_utc") or poll_started,
        # The global successful-poll clock advances only when both feeds succeed.
        "last_successful_poll_utc": poll_completed if complete_poll else previous_state.get("last_successful_poll_utc"),
        "last_successful_poll_mode": mode if complete_poll else previous_state.get("last_successful_poll_mode"),
        "last_successful_poll_run_id": str(run_id) if complete_poll else previous_state.get("last_successful_poll_run_id"),
        "poll_count": prior_poll_count + (0 if mode == "manual" else 1),
        "complete_poll_count": prior_complete_count + (1 if complete_poll and mode != "manual" else 0),
        "partial_poll_count": prior_partial_count + (1 if poll_status == "partial" and mode != "manual" else 0),
        "last_poll_attempt_utc": poll_completed,
        "last_poll_attempt_run_id": str(run_id),
        "last_poll_status": poll_status,
        "last_poll_successful_feeds": sorted(snapshots),
        "last_poll_failed_feeds": sorted(feed_errors),
        "last_poll_errors": feed_errors,
        "last_successful_poll_started_utc_by_feed": last_poll_by_feed,
        "last_successful_poll_utc_by_feed": last_receipt_by_feed,
        "latest_accession_by_feed": latest_by_feed,
        "last_poll_possible_gap_by_feed": last_gap_by_feed,
        "last_feed_sha256_by_feed": hash_by_feed,
        "poll_count_by_feed": poll_count_by_feed,
        "candidate_manifest_source_artifact_sha256": manifest["source_artifact_sha256"],
        "candidate_manifest_cik_count": len(candidate_ciks),
        "historical_f80_membership_verified": False,
        "signal_eligible": False,
    }
    acceptance_reconciliations = []
    acceptance_attempts = 0
    feed_observation_rows_appended = 0
    structured_detail_summary = {
        "parser_version": p509.PARSER_VERSION, "new_accessions_parsed": 0,
        "new_detail_rows_appended": 0, "backfill": {"attempts": 0, "accessions_parsed": 0,
        "accessions_with_parse_error": 0, "source_hash_mismatch_count": 0, "detail_rows_appended": 0, "unresolved_count": 0,
        "remaining_accessions": 0, "signal_eligible_count": 0},
        "ledger_row_count": p509.count_detail_rows(data_dir / "sale_details.csv"),
        "ledger_accession_count": len(p509.read_completed_accessions(data_dir / "sale_details.csv")),
        "signal_eligible_count": 0,
    }
    if mode != "manual":
        append_events(events_path, new_rows)
        new_detail_rows_appended = p509.append_detail_rows(data_dir / "sale_details.csv", new_structured_rows)
        backfill_summary = backfill_missing_structured_details(
            events_path, data_dir / "sale_details.csv", candidate_ciks, run_id,
            limit=STRUCTURED_BACKFILL_LIMIT,
        )
        structured_detail_summary = {
            "parser_version": p509.PARSER_VERSION,
            "new_accessions_parsed": len({row["accession"] for row in new_structured_rows if row.get("detail_section") == "filing_header"}),
            "new_detail_rows_appended": new_detail_rows_appended,
            "backfill": backfill_summary,
            "ledger_row_count": p509.count_detail_rows(data_dir / "sale_details.csv"),
            "ledger_accession_count": len(p509.read_completed_accessions(data_dir / "sale_details.csv")),
            "signal_eligible_count": 0,
        }
        feed_observation_rows_appended = append_feed_observations(
            data_dir / "feed_observations.csv", feed_observation_rows
        )
        state["structured_detail_parser_version"] = p509.PARSER_VERSION
        state["structured_detail_last_run_id"] = str(run_id)
        state["structured_detail_ledger_row_count"] = structured_detail_summary["ledger_row_count"]
        state["structured_detail_ledger_accession_count"] = structured_detail_summary["ledger_accession_count"]
        state["structured_detail_backfill_remaining_accessions"] = structured_detail_summary["backfill"]["remaining_accessions"]
        state["last_feed_observation_row_count"] = len(feed_observation_rows)
        state["last_feed_observation_rows_appended"] = feed_observation_rows_appended
        reconciled = read_reconciled_accessions(data_dir / "acceptance_reconciliation.csv")
        for event in read_event_rows(events_path):
            accession = p401.accession(event.get("accession"))
            if not accession or accession in reconciled:
                continue
            acceptance_attempts += 1
            row = fetch_acceptance_from_index(event, run_id)
            if row:
                acceptance_reconciliations.append(row)
                reconciled.add(accession)
        append_reconciliations(data_dir / "acceptance_reconciliation.csv", acceptance_reconciliations)
        state["last_acceptance_reconciliation_utc"] = now_utc()
        state["acceptance_reconciled_accession_count"] = len(reconciled)
        write_json(state_path, state)

    observed_new_accessions = {
        accession for feed_summary in feed_summaries.values()
        for accession in feed_summary["new_accessions"]
    }
    overlap_count = max(
        0,
        sum(len(x["new_accessions"]) for x in feed_summaries.values()) - len(observed_new_accessions),
    )
    summary = {
        "phase": PHASE, "mode": mode, "run_id": str(run_id),
        "poll_started_utc": poll_started, "poll_completed_utc": poll_completed,
        "poll_status": poll_status,
        "successful_feeds": sorted(snapshots),
        "failed_feeds": sorted(feed_errors),
        "feed_errors": feed_errors,
        "cross_feed_provenance_complete": not bool(feed_errors),
        "research_observation_eligibility_scope": "successful_feeds_only" if feed_errors else "all_feeds",
        "feed_summaries": feed_summaries,
        "new_event_count": len(new_rows) if mode != "manual" else len(observed_new_accessions),
        "new_feed_entry_count": sum(len(x["new_accessions"]) for x in feed_summaries.values()),
        # A failed feed makes the observed overlap a lower bound, not a complete count.
        "new_cross_feed_overlap_count": overlap_count if not feed_errors else None,
        "feed_observation_rows_observed": len(feed_observation_rows),
        "feed_observation_rows_appended": feed_observation_rows_appended,
        "new_xml_resolved_count": xml_resolved,
        "acceptance_reconciliation_attempts": acceptance_attempts,
        "acceptance_reconciliations_added": len(acceptance_reconciliations),
        "acceptance_reconciliations_unresolved": max(0, acceptance_attempts - len(acceptance_reconciliations)),
        "acceptance_reconciliation_source": "SEC filing-detail index page; separate append-only enrichment table",
        "structured_detail_summary": structured_detail_summary,
        "new_candidate_issuer_matches": candidate_matches,
        "candidate_manifest_cik_count": len(candidate_ciks),
        "candidate_manifest_is_historical_f80_security_master": False,
        "possible_feed_window_gap": any(x["possible_feed_window_gap"] for x in feed_summaries.values()),
        "possible_feed_window_gap_complete": not bool(feed_errors),
        "research_observation_eligible_count": sum(bool(x.get("research_observation_eligible")) for x in new_rows),
        "signal_eligible_count": 0,
        "public_availability_certified": False,
        "acceptance_datetime_is_not_first_public_receipt": True,
        "first_seen_is_poll_receipt_upper_bound": True,
        "same_day_intraday_use_authorized": False,
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "bootstrap_loo_or_holdout_used": False,
        "f80_changed": False,
        "production_changed": False,
        "state_write": mode != "manual",
        "events_written": len(new_rows) if mode != "manual" else 0,
        "disposition": "PARTIAL_FEEDS_CAPTURED_WITH_FAILURES" if feed_errors else (
            "APPEND_ONLY_FIRST_SEEN_EVENTS_CAPTURED" if new_rows and mode != "manual" else (
                "MANUAL_DIAGNOSTIC_NO_STATE_CHANGE" if mode == "manual" else "POLL_COMPLETE_NO_NEW_ACCESSIONS"
            )
        ),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return summary

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("bootstrap", "schedule", "manual"), required=True)
    parser.add_argument("--output", default="phase403_output")
    parser.add_argument("--run-id", default="local")
    args = parser.parse_args()
    run(args.mode, args.output, args.run_id)

if __name__ == "__main__":
    main()
