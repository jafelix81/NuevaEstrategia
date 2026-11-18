#!/usr/bin/env python3
"""Prospective SEC Form 4 / 4-A metadata first-seen capture.

This collector stores only public Atom-feed metadata and response hashes.
It does not download filing XML/text, infer transaction semantics, or emit signals.
"""
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

from research import phase401_form144a_full_parent_identity_census as p401

PHASE = 476
DATA_DIR = Path("research/data/sec_form4_first_seen")
STATE_PATH = DATA_DIR / "state.json"
EVENTS_PATH = DATA_DIR / "events.csv"
OBSERVATIONS_PATH = DATA_DIR / "feed_observations.csv"

PAGE_SIZE = 100
MAX_FEED_PAGES = 20
PAGE_DELAY_SECONDS = 0.35
FEEDS = {
    "4": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=include&count=100&output=atom",
    "4A": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4%2FA&owner=include&count=100&output=atom",
}

EVENT_FIELDS = [
    "accession", "form", "feed_name", "filing_date", "filing_url",
    "feed_path_cik_unverified", "feed_updated_raw", "feed_updated_utc",
    "first_seen_at_utc", "first_seen_poll_started_utc", "first_seen_poll_ended_utc",
    "first_seen_interval_lower_bound_utc", "first_seen_interval_upper_bound_utc",
    "first_seen_interval_status", "first_seen_poll_run_id", "capture_mode",
    "feed_page_offset", "feed_page_raw_sha256", "feed_page_received_at_utc",
    "acceptance_datetime_utc", "acceptance_clock_status",
    "security_identity_verified", "historical_f80_membership_verified",
    "owner_attribution_verified", "transaction_semantics_verified",
    "public_availability_certified", "event_metadata_interval_bounded",
    "research_observation_eligible", "signal_eligible",
    "same_day_intraday_use_authorized", "first_seen_is_upper_bound_not_exact_receipt",
]

OBSERVATION_FIELDS = [
    "poll_run_id", "feed_name", "page_offset", "raw_entry_count",
    "parsed_accession_count", "response_bytes", "response_received_at_utc",
    "raw_sha256", "feed_url", "page_status", "error_type", "error",
]

def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str | None):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    # Atom updated must carry an explicit UTC offset.  A naive timestamp
    # cannot be made PIT-safe by guessing that it means UTC.
    if dt.tzinfo is None or dt.utcoffset() is None:
        return None
    return dt.astimezone(timezone.utc)


def local_name(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1].lower()


def child_text(node: ET.Element, wanted: str) -> str | None:
    for child in list(node):
        if local_name(child.tag) == wanted.lower():
            return "".join(child.itertext()).strip()
    return None


def extract_accession(*values: object) -> str | None:
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


def parse_form(node: ET.Element, title: str) -> str | None:
    for child in list(node):
        if local_name(child.tag) == "category":
            term = str(child.attrib.get("term", "")).strip().upper()
            if term in {"4", "4/A"}:
                return term
    match = re.match(r"\s*(4/A|4)(?:\s|$|-)", str(title or ""), re.I)
    if match:
        return "4/A" if match.group(1).upper() == "4/A" else "4"
    return None


def filing_date_from_summary(summary: str) -> str:
    decoded = html.unescape(str(summary or ""))
    plain = re.sub(r"<[^>]*>", " ", decoded)
    match = re.search(r"Filed:\s*(\d{4}-\d{2}-\d{2})", plain, re.I)
    return match.group(1) if match else ""


def path_cik_from_url(url: str) -> str:
    match = re.search(r"/data/(\d+)/", str(url or ""), re.I)
    if not match:
        return ""
    return match.group(1).zfill(10)


def count_atom_entries(raw: bytes | str) -> int:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    root = ET.fromstring(raw)
    return sum(1 for node in root.iter() if local_name(node.tag) == "entry")


def parse_atom_feed(raw: bytes | str, feed_name: str, feed_url: str) -> list[dict]:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    root = ET.fromstring(raw)
    entries: list[dict] = []
    for node in root.iter():
        if local_name(node.tag) != "entry":
            continue
        entry_id = child_text(node, "id") or ""
        title = child_text(node, "title") or ""
        updated = child_text(node, "updated") or ""
        summary_node = next((x for x in list(node) if local_name(x.tag) == "summary"), None)
        summary = "".join(summary_node.itertext()).strip() if summary_node is not None else ""
        links = [x for x in list(node) if local_name(x.tag) == "link"]
        link_node = next((x for x in links if x.attrib.get("rel") in (None, "", "alternate")), None)
        if link_node is None and links:
            link_node = links[0]
        link = link_node.attrib.get("href", "") if link_node is not None else entry_id
        form = parse_form(node, title)
        if form not in {"4", "4/A"}:
            continue
        if feed_name == "4A" and form != "4/A":
            continue
        accession = extract_accession(entry_id, link, title, summary)
        if not accession:
            continue
        updated_dt = parse_utc(updated)
        entries.append({
            "accession": accession,
            "form": form,
            "feed_name": feed_name,
            "filing_date": filing_date_from_summary(summary),
            "filing_url": link,
            "feed_path_cik_unverified": path_cik_from_url(link),
            "feed_updated_raw": updated,
            "feed_updated_utc": (
                updated_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
                if updated_dt else ""
            ),
            "feed_url": feed_url,
        })
    return entries


def classify_poll_interval(
    mode: str,
    prior_watermark: str | None,
    watermark_found: bool,
    previous_successful_poll_end: str | None,
) -> str:
    if mode != "schedule":
        return "MANUAL_DIAGNOSTIC"
    if not prior_watermark:
        return "INITIAL_BASELINE_NO_LOWER_BOUND"
    if not watermark_found:
        return "GAP_OR_WATERMARK_NOT_FOUND"
    if not previous_successful_poll_end:
        return "NO_PRIOR_SUCCESSFUL_POLL"
    return "POLL_WATERMARK_BOUNDED"


def classify_interval(
    mode: str,
    prior_watermark: str | None,
    watermark_found: bool,
    previous_successful_poll_end: str | None,
    feed_updated_utc: str | None = None,
    first_seen_at_utc: str | None = None,
) -> str:
    """Bound an event only if the source feed timestamp falls inside our poll interval.

    Atom updated is not asserted to be the exact public-availability time. It is
    used only as a consistency guard: stale, missing or future source timestamps
    cannot be promoted to bounded metadata observations.
    """
    poll_status = classify_poll_interval(
        mode, prior_watermark, watermark_found, previous_successful_poll_end
    )
    if poll_status != "POLL_WATERMARK_BOUNDED":
        return poll_status
    feed_updated = parse_utc(feed_updated_utc)
    lower = parse_utc(previous_successful_poll_end)
    upper = parse_utc(first_seen_at_utc)
    if feed_updated is None or lower is None or upper is None:
        return "FEED_OR_RECEIPT_TIMESTAMP_UNKNOWN"
    if feed_updated <= lower:
        return "FEED_TIMESTAMP_NOT_AFTER_PREVIOUS_POLL"
    if feed_updated > upper:
        return "FEED_TIMESTAMP_AFTER_FIRST_SEEN"
    return "BOUNDED_METADATA_ONLY"


def _page_url(base_url: str, offset: int) -> str:
    return f"{base_url}&start={offset}"


def fetch_feed(
    feed_name: str,
    base_url: str,
    feed_state: dict,
    mode: str,
    run_id: str,
) -> dict:
    """Fetch newest entries through the prior accession watermark, fail closed on gaps."""
    prior = feed_state.get("latest_accession")
    previous_end = feed_state.get("last_successful_poll_end_utc")
    max_pages = MAX_FEED_PAGES if prior and mode == "schedule" else 1
    offset = 0
    pages: list[dict] = []
    combined: list[dict] = []
    seen_hashes: set[str] = set()
    first_page_entries: list[dict] = []
    watermark_found = False
    page_error: dict | None = None

    for page_index in range(max_pages):
        url = _page_url(base_url, offset)
        raw = None
        try:
            raw = p401.fetch_bytes(url, sec=True, timeout=60, retries=4)
            received = now_utc()
            digest = hashlib.sha256(raw).hexdigest()
            if digest in seen_hashes:
                page_error = {
                    "error_type": "RepeatedPageHash",
                    "error": "SEC Atom pagination repeated a page hash; offset may have been ignored.",
                    "page_offset": offset,
                }
                break
            seen_hashes.add(digest)
            raw_count = count_atom_entries(raw)
            parsed = parse_atom_feed(raw, feed_name, url)
            if page_index == 0:
                first_page_entries = list(parsed)
            pages.append({
                "poll_run_id": run_id,
                "feed_name": feed_name,
                "page_offset": offset,
                "raw_entry_count": raw_count,
                "parsed_accession_count": len(parsed),
                "response_bytes": len(raw),
                "response_received_at_utc": received,
                "raw_sha256": digest,
                "feed_url": url,
                "page_status": "HTTP_OK",
                "error_type": "",
                "error": "",
            })

            for item in parsed:
                if prior and item["accession"] == prior:
                    watermark_found = True
                    break
                item = dict(item)
                item["_page_offset"] = offset
                item["_page_received_at_utc"] = received
                item["_page_sha256"] = digest
                combined.append(item)

            if not prior:
                break
            if watermark_found:
                break
            if raw_count == 0:
                page_error = {
                    "error_type": "EmptyPageBeforeWatermark",
                    "error": "Feed ended before the prior accession watermark was found.",
                    "page_offset": offset,
                }
                break
            if page_index + 1 >= max_pages:
                page_error = {
                    "error_type": "PaginationLimitReached",
                    "error": f"Prior accession watermark not found within {max_pages} pages.",
                    "page_offset": offset,
                }
                break
            # Advance by raw Atom rows, not parsed or unique accessions.
            offset += raw_count
            time.sleep(PAGE_DELAY_SECONDS)
        except Exception as exc:
            page_error = {
                "error_type": type(exc).__name__,
                "error": str(exc)[:1000],
                "page_offset": offset,
                "response_bytes": len(raw) if raw is not None else None,
                "raw_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else "",
            }
            pages.append({
                "poll_run_id": run_id,
                "feed_name": feed_name,
                "page_offset": offset,
                "raw_entry_count": "",
                "parsed_accession_count": "",
                "response_bytes": len(raw) if raw is not None else "",
                "response_received_at_utc": now_utc(),
                "raw_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else "",
                "feed_url": url,
                "page_status": "ERROR",
                "error_type": type(exc).__name__,
                "error": str(exc)[:1000],
            })
            break

    poll_success = bool(
        pages and page_error is None and (not prior or watermark_found)
    )
    poll_interval_status = classify_poll_interval(mode, prior, watermark_found, previous_end)
    new_latest = first_page_entries[0]["accession"] if first_page_entries else prior
    latest_updated = first_page_entries[0]["feed_updated_utc"] if first_page_entries else ""

    candidate_event_count = len(combined)
    event_rows = []
    if poll_success:
        for item in combined:
            received = item["_page_received_at_utc"]
            event_interval_status = classify_interval(
                mode, prior, watermark_found, previous_end,
                item["feed_updated_utc"], received,
            )
            bounded = event_interval_status == "BOUNDED_METADATA_ONLY"
            event_rows.append({
                "accession": item["accession"],
                "form": item["form"],
                "feed_name": item["feed_name"],
                "filing_date": item["filing_date"],
                "filing_url": item["filing_url"],
                "feed_path_cik_unverified": item["feed_path_cik_unverified"],
                "feed_updated_raw": item["feed_updated_raw"],
                "feed_updated_utc": item["feed_updated_utc"],
                "first_seen_at_utc": received,
                "first_seen_poll_started_utc": "",
                "first_seen_poll_ended_utc": "",
                "first_seen_interval_lower_bound_utc": previous_end if bounded else "",
                "first_seen_interval_upper_bound_utc": received,
                "first_seen_interval_status": event_interval_status,
                "first_seen_poll_run_id": run_id,
                "capture_mode": mode,
                "feed_page_offset": item["_page_offset"],
                "feed_page_raw_sha256": item["_page_sha256"],
                "feed_page_received_at_utc": received,
                "acceptance_datetime_utc": "",
                "acceptance_clock_status": "NOT_FETCHED_METADATA_ONLY",
                "security_identity_verified": False,
                "historical_f80_membership_verified": False,
                "owner_attribution_verified": False,
                "transaction_semantics_verified": False,
                "public_availability_certified": False,
                "event_metadata_interval_bounded": bounded,
                "research_observation_eligible": False,
                "signal_eligible": False,
                "same_day_intraday_use_authorized": False,
                "first_seen_is_upper_bound_not_exact_receipt": True,
            })

    return {
        "feed_name": feed_name,
        "prior_watermark": prior or "",
        "watermark_found": watermark_found,
        "poll_success": poll_success,
        "interval_status": poll_interval_status,
        "new_latest_accession": new_latest or "",
        "latest_feed_updated_utc": latest_updated,
        "event_rows": event_rows,
        "page_observations": pages,
        "page_error": page_error or {},
        "raw_page_count": len(pages),
        "new_accession_count": len(event_rows),
        "candidate_accession_count": candidate_event_count,
        "suppressed_incomplete_poll_candidate_count": candidate_event_count if not poll_success else 0,
        "bounded_metadata_count": sum(1 for row in event_rows if row["event_metadata_interval_bounded"]),
    }


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"schema_version": 1, "phase": PHASE, "feeds": {}}
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("phase") != PHASE:
        raise ValueError("Unexpected Phase 476 state schema; refusing silent migration.")
    data.setdefault("feeds", {})
    return data


def existing_accessions() -> set[str]:
    if not EVENTS_PATH.exists():
        return set()
    with EVENTS_PATH.open("r", encoding="utf-8", newline="") as handle:
        return {row.get("accession", "") for row in csv.DictReader(handle) if row.get("accession")}


def append_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def atomic_write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temp.replace(path)


def run_capture(mode: str, run_id: str, output_dir: Path) -> dict:
    if mode not in {"schedule", "manual"}:
        raise ValueError("mode must be schedule or manual")
    poll_started = now_utc()
    state = load_state()
    known = existing_accessions()
    event_rows: list[dict] = []
    observation_rows: list[dict] = []
    feed_summaries: dict[str, dict] = {}
    feed_updates: dict[str, dict] = {}

    for feed_name, base_url in FEEDS.items():
        feed_state = state["feeds"].get(feed_name, {})
        result = fetch_feed(feed_name, base_url, feed_state, mode, run_id)
        feed_summaries[feed_name] = {
            key: result[key] for key in (
                "prior_watermark", "watermark_found", "poll_success", "interval_status",
                "new_latest_accession", "latest_feed_updated_utc", "raw_page_count",
                "new_accession_count", "candidate_accession_count",
                "suppressed_incomplete_poll_candidate_count", "bounded_metadata_count", "page_error",
            )
        }
        observation_rows.extend(result["page_observations"])
        for row in result["event_rows"]:
            accession = row["accession"]
            if accession in known:
                continue
            row["first_seen_poll_started_utc"] = poll_started
            event_rows.append(row)
            known.add(accession)
        feed_updates[feed_name] = result

    poll_ended = now_utc()
    for row in event_rows:
        row["first_seen_poll_ended_utc"] = poll_ended

    if mode == "schedule":
        append_csv(EVENTS_PATH, EVENT_FIELDS, event_rows)
        append_csv(OBSERVATIONS_PATH, OBSERVATION_FIELDS, observation_rows)
        for feed_name, result in feed_updates.items():
            if result["poll_success"]:
                state["feeds"][feed_name] = {
                    "latest_accession": result["new_latest_accession"],
                    "last_successful_poll_end_utc": poll_ended,
                    "last_poll_run_id": run_id,
                    "last_poll_status": "SUCCESS",
                    "latest_feed_updated_utc": result["latest_feed_updated_utc"],
                }
            else:
                old = dict(state["feeds"].get(feed_name, {}))
                old.update({
                    "last_poll_run_id": run_id,
                    "last_poll_status": "GAP_OR_FETCH_ERROR",
                })
                state["feeds"][feed_name] = old
        state["last_poll_run_id"] = run_id
        state["last_poll_started_utc"] = poll_started
        state["last_poll_ended_utc"] = poll_ended
        atomic_write_json(STATE_PATH, state)

    summary = {
        "phase": PHASE,
        "run_id": str(run_id),
        "mode": mode,
        "poll_started_utc": poll_started,
        "poll_ended_utc": poll_ended,
        "feed_count": len(FEEDS),
        "feeds": feed_summaries,
        "new_event_rows": len(event_rows),
        "incomplete_poll_candidate_rows_suppressed": sum(
            result["suppressed_incomplete_poll_candidate_count"] for result in feed_updates.values()
        ),
        "bounded_metadata_rows": sum(1 for row in event_rows if row["event_metadata_interval_bounded"]),
        "research_observation_eligible_rows": 0,
        "signal_eligible_rows": 0,
        "filing_xml_or_text_downloaded": False,
        "raw_transaction_rows_stored": False,
        "public_availability_certified": False,
        "alpha_test_authorized": False,
        "persistent_write": mode == "schedule",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "poll_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["schedule", "manual"], required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_capture(args.mode, args.run_id, args.output)


if __name__ == "__main__":
    main()
