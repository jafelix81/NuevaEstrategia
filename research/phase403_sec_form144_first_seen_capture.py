#!/usr/bin/env python3
"""Prospective SEC Form 144 / 144-A first-seen capture; no return tests or signals."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from research import phase401_form144a_full_parent_identity_census as p401

PHASE = 403
DATA_DIR = Path("research/data/sec_form144_first_seen")
STATE_PATH = DATA_DIR / "state.json"
EVENTS_PATH = DATA_DIR / "events.csv"
RECONCILIATION_PATH = DATA_DIR / "acceptance_reconciliation.csv"
FEED_OBSERVATIONS_PATH = DATA_DIR / "feed_observations.csv"
MANIFEST_PATH = Path("research/PHASE401_FORM144_CANDIDATE_CIK_MANIFEST_2026-11-14.json")
EXPECTED_MANIFEST_SHA256 = "d20a1e42c7dfe3ef91248aa2aeecd5af7d853b91"
EXPECTED_CANDIDATE_CIK_COUNT = 290
EXPECTED_SOURCE_ARTIFACT_SHA256 = "939d5564b14ce0f41df23a2c9ab681977cfde141cd0ea2b3c1213b1c5bfaf613"
MAX_FEED_ENTRIES = 50  # observed maximum in the first live SEC Atom bootstrap

FEEDS = {
    "144": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=144&owner=include&count=100&output=atom",
    "144A": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=144%2FA&owner=include&count=100&output=atom",
}

EVENT_FIELDS = [
    "accession", "form", "feed_name", "feed_names", "feed_title", "feed_summary",
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
    if isinstance(raw, bytes):
        raw = raw.decode("latin-1", "replace")
    match = re.search(r"ACCEPTANCE-DATETIME\s*:\s*(\d{14})", str(raw), re.I)
    if not match:
        return None, None
    accepted_et = datetime.strptime(match.group(1), "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
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
            return result
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
    accessions = {x["accession"] for x in entries}
    return bool(previous_latest_accession and len(entries) >= MAX_FEED_ENTRIES
                and previous_latest_accession not in accessions)

def interval_policy(previous_poll_utc, previous_poll_had_gap, current_poll_has_gap):
    if not previous_poll_utc:
        return None, "INITIAL_BASELINE_NO_LOWER_BOUND"
    if previous_poll_had_gap:
        return None, "PREVIOUS_POLL_GAP_INTERVAL_UNBOUNDED"
    if current_poll_has_gap:
        return None, "POSSIBLE_FEED_WINDOW_GAP"
    return previous_poll_utc, "BOUNDED_BY_SUCCESSIVE_SUCCESSFUL_POLLS"

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
                interval_status, run_id, mode, manifest):
    accepted = metadata.get("submission_acceptance_utc")
    feed_delta = seconds_between(item.get("feed_updated_utc"), accepted)
    seen_delta = seconds_between(response_received, accepted)
    interval_valid = interval_status == "BOUNDED_BY_SUCCESSIVE_SUCCESSFUL_POLLS"
    return {
        "accession": item["accession"],
        "form": metadata.get("submission_type") or item.get("form"),
        "feed_name": item["feed_name"],
        "feed_names": item.get("feed_names", [item["feed_name"]]),
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

def fetch_all_feeds():
    snapshots = {}
    for feed_name, url in FEEDS.items():
        raw = p401.fetch_bytes(url, sec=True, timeout=60, retries=4)
        received = now_utc()
        entries = parse_atom_feed(raw, feed_name, url)
        snapshots[feed_name] = {
            "url": url, "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "response_bytes": len(raw), "received_at_utc": received,
            "entries": entries, "entry_count": len(entries),
            "oldest_updated_utc": min((x["feed_updated_utc"] for x in entries if x["feed_updated_utc"]), default=None),
            "newest_updated_utc": max((x["feed_updated_utc"] for x in entries if x["feed_updated_utc"]), default=None),
        }
    return snapshots

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
    """Preserve one observation per accession/feed/poll, including overlaps."""
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
                "feed_url": snapshot.get("url"),
                "feed_raw_sha256": snapshot.get("raw_sha256"),
                "feed_response_received_utc": snapshot.get("received_at_utc"),
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
    snapshots = fetch_all_feeds()
    source_names_by_accession = feed_names_by_accession(snapshots)
    feed_observation_rows = build_feed_observation_rows(snapshots, run_id)
    existing = read_existing_accessions(events_path)
    existing_at_poll_start = set(existing)
    new_rows = []
    feed_summaries = {}
    latest_by_feed = dict(previous_state.get("latest_accession_by_feed", {}))
    last_poll_by_feed = dict(previous_state.get("last_successful_poll_utc_by_feed", {}))
    last_gap_by_feed = dict(previous_state.get("last_poll_possible_gap_by_feed", {}))
    hash_by_feed = dict(previous_state.get("last_feed_sha256_by_feed", {}))
    poll_count_by_feed = dict(previous_state.get("poll_count_by_feed", {}))
    candidate_matches = 0
    xml_resolved = 0

    for feed_name, snapshot in snapshots.items():
        entries = snapshot["entries"]
        prior_latest = latest_by_feed.get(feed_name)
        current_gap = detect_possible_gap(entries, prior_latest)
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
            "previous_latest_accession_present": (prior_latest in {x["accession"] for x in entries}) if prior_latest else None,
            "possible_feed_window_gap": current_gap,
            "interval_lower_bound_utc": interval_start,
            "interval_status": interval_status,
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
            event = build_event(
                item, metadata, poll_started, snapshot["received_at_utc"], interval_start,
                interval_status, run_id, mode, manifest
            )
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
        last_poll_by_feed[feed_name] = snapshot["received_at_utc"]
        last_gap_by_feed[feed_name] = current_gap
        hash_by_feed[feed_name] = snapshot["raw_sha256"]
        poll_count_by_feed[feed_name] = int(poll_count_by_feed.get(feed_name, 0)) + 1

    poll_completed = now_utc()
    state = {
        "schema_version": 1,
        "phase": PHASE,
        "source": "SEC EDGAR Latest Filings Atom feeds filtered to Form 144 and 144/A",
        "created_utc": previous_state.get("created_utc") or poll_started,
        "last_successful_poll_utc": poll_completed,
        "last_successful_poll_mode": mode,
        "last_successful_poll_run_id": str(run_id),
        "poll_count": int(previous_state.get("poll_count", 0)) + (0 if mode == "manual" else 1),
        "last_successful_poll_utc_by_feed": last_poll_by_feed,
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
    if mode != "manual":
        append_events(events_path, new_rows)
        feed_observation_rows_appended = append_feed_observations(
            data_dir / "feed_observations.csv", feed_observation_rows
        )
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

    summary = {
        "phase": PHASE, "mode": mode, "run_id": str(run_id),
        "poll_started_utc": poll_started, "poll_completed_utc": poll_completed,
        "feed_summaries": feed_summaries,
        "new_event_count": len(new_rows) if mode != "manual" else len({
            accession for summary in feed_summaries.values() for accession in summary["new_accessions"]
        }),
        "new_feed_entry_count": sum(len(x["new_accessions"]) for x in feed_summaries.values()),
        "new_cross_feed_overlap_count": max(
            0,
            sum(len(x["new_accessions"]) for x in feed_summaries.values()) - len({
                accession for summary in feed_summaries.values() for accession in summary["new_accessions"]
            }),
        ),
        "feed_observation_rows_observed": len(feed_observation_rows),
        "feed_observation_rows_appended": feed_observation_rows_appended,
        "new_xml_resolved_count": xml_resolved,
        "acceptance_reconciliation_attempts": acceptance_attempts,
        "acceptance_reconciliations_added": len(acceptance_reconciliations),
        "acceptance_reconciliations_unresolved": max(0, acceptance_attempts - len(acceptance_reconciliations)),
        "acceptance_reconciliation_source": "SEC filing-detail index page; separate append-only enrichment table",
        "new_candidate_issuer_matches": candidate_matches,
        "candidate_manifest_cik_count": len(candidate_ciks),
        "candidate_manifest_is_historical_f80_security_master": False,
        "possible_feed_window_gap": any(x["possible_feed_window_gap"] for x in feed_summaries.values()),
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
        "disposition": "APPEND_ONLY_FIRST_SEEN_EVENTS_CAPTURED" if new_rows and mode != "manual" else (
            "MANUAL_DIAGNOSTIC_NO_STATE_CHANGE" if mode == "manual" else "POLL_COMPLETE_NO_NEW_ACCESSIONS"
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
