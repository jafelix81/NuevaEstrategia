#!/usr/bin/env python3
"""Prospective SEC Form 13F first-seen metadata capture.

This collector polls the public EDGAR Latest Filings Atom feed for 13F-HR/A
and 13F-NT families. It stores accession-level feed metadata, hashes and
bounded poll intervals only. It does not download filing XML, reconstruct
holdings, map securities, calculate returns or emit trading signals.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import time
import xml.etree.ElementTree as ETREE
from datetime import date, datetime, time as dt_time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from research import phase401_form144a_full_parent_identity_census as p401

PHASE = 614
DATA_DIR = Path("research/data/sec_13f_first_seen")
STATE_PATH = DATA_DIR / "state.json"
EVENTS_PATH = DATA_DIR / "events.csv"
PAGE_OBSERVATIONS_PATH = DATA_DIR / "page_observations.csv"
ACCESSION_OBSERVATIONS_PATH = DATA_DIR / "accession_observations.csv"

PAGE_SIZE = 100
MAX_FEED_PAGES = 50
PAGE_DELAY_SECONDS = 0.35
ET_TZ = ZoneInfo("America/New_York")

FEEDS = {
    "13F-HR": (
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent"
        "&type=13F-HR&owner=include&count=100&output=atom"
    ),
    "13F-HR-A": (
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent"
        "&type=13F-HR%2FA&owner=include&count=100&output=atom"
    ),
    "13F-NT": (
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent"
        "&type=13F-NT&owner=include&count=100&output=atom"
    ),
    "13F-NT-A": (
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent"
        "&type=13F-NT%2FA&owner=include&count=100&output=atom"
    ),
}
ALLOWED_FORMS = {
    "13F-HR": {"13F-HR"},
    "13F-HR-A": {"13F-HR/A"},
    "13F-NT": {"13F-NT"},
    "13F-NT-A": {"13F-NT/A"},
}

EVENT_FIELDS = [
    "accession", "form", "feed_name", "filing_date", "filing_url",
    "feed_path_cik_unverified", "feed_updated_raw", "feed_updated_utc",
    "first_seen_at_utc", "first_seen_poll_started_utc", "first_seen_poll_ended_utc",
    "first_seen_interval_lower_bound_utc", "first_seen_interval_upper_bound_utc",
    "first_seen_interval_status", "first_seen_poll_run_id", "capture_mode",
    "feed_page_offset", "feed_page_raw_sha256", "feed_page_received_at_utc",
    "legal_filing_date_floor_utc", "conservative_knowledge_upper_bound_utc",
    "acceptance_datetime_utc", "acceptance_clock_status",
    "manager_identity_verified", "security_identity_verified",
    "historical_f80_membership_verified", "public_availability_certified",
    "event_metadata_interval_bounded", "metadata_observation_eligible",
    "research_observation_eligible", "signal_eligible",
    "first_seen_is_upper_bound_not_exact_receipt",
]

PAGE_FIELDS = [
    "poll_run_id", "feed_name", "page_offset", "raw_entry_count",
    "parsed_accession_occurrence_count", "response_bytes",
    "response_received_at_utc", "raw_sha256", "feed_url",
    "page_status", "error_type", "error",
]

ACCESSION_OBSERVATION_FIELDS = [
    "poll_run_id", "observation_sequence", "feed_name", "accession", "form",
    "filing_date", "filing_url", "feed_path_cik_unverified",
    "feed_updated_raw", "feed_updated_utc", "feed_url", "page_offset",
    "page_raw_sha256", "page_received_at_utc", "is_prior_accession_watermark",
    "is_timestamp_boundary", "poll_success", "poll_interval_status",
    "event_interval_status", "is_duplicate_within_feed",
    "is_duplicate_across_feeds", "is_preexisting_ledger_accession",
    "canonical_event_emitted", "candidate_suppressed_in_incomplete_poll",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def legal_filing_date_floor_utc(filing_date: str | date) -> str:
    """06:00 ET on the official Filing Date; not an acceptance timestamp."""
    filed = filing_date if isinstance(filing_date, date) else date.fromisoformat(str(filing_date))
    floor = datetime.combine(filed, dt_time(6, 0), tzinfo=ET_TZ)
    return iso_utc(floor)


def local_name(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1].lower()


def child_text(node: ETREE.Element, wanted: str) -> str | None:
    for child in list(node):
        if local_name(child.tag) == wanted.lower():
            return "".join(child.itertext()).strip()
    return None


def extract_accession(*values: object) -> str | None:
    for value in values:
        match = re.search(r"(?<!\d)(\d{10}-\d{2}-\d{6})(?!\d)", str(value or ""))
        if match:
            return match.group(1)
    for value in values:
        match = re.search(r"(?<!\d)(\d{18})(?!\d)", str(value or ""))
        if match:
            digits = match.group(1)
            return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"
    return None


def parse_form(node: ETREE.Element, title: str) -> str | None:
    for child in list(node):
        if local_name(child.tag) == "category":
            term = str(child.attrib.get("term", "")).strip().upper()
            if term:
                return term
    match = re.match(r"\s*(13F-(?:HR|NT)(?:/A)?)(?:\s|$|-)", str(title or ""), re.I)
    return match.group(1).upper() if match else None


def filing_date_from_summary(summary: str) -> str:
    decoded = html.unescape(str(summary or ""))
    plain = re.sub(r"<[^>]*>", " ", decoded)
    match = re.search(r"Filed:\s*(\d{4}-\d{2}-\d{2})", plain, re.I)
    return match.group(1) if match else ""


def path_cik_from_url(url: str) -> str:
    match = re.search(r"/data/(\d+)/", str(url or ""), re.I)
    return match.group(1).zfill(10) if match else ""


def count_atom_entries(raw: bytes | str) -> int:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    root = ETREE.fromstring(raw)
    return sum(1 for node in root.iter() if local_name(node.tag) == "entry")


def parse_atom_feed(raw: bytes | str, feed_name: str, feed_url: str) -> list[dict]:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    root = ETREE.fromstring(raw)
    allowed = ALLOWED_FORMS[feed_name]
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
        if form not in allowed:
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
            "feed_updated_utc": iso_utc(updated_dt) if updated_dt else "",
            "feed_updated_timestamp_status": "OFFSET_AWARE" if updated_dt else "UNKNOWN_OR_NAIVE",
            "feed_url": feed_url,
        })
    return entries


def classify_event_interval(
    mode: str,
    poll_success: bool,
    previous_successful_poll_end: str | None,
    feed_updated_utc: str | None,
    first_seen_upper_bound_utc: str | None,
) -> str:
    if mode != "schedule":
        return "MANUAL_DIAGNOSTIC"
    if not poll_success:
        return "POLL_INCOMPLETE_CANDIDATE_SUPPRESSED"
    lower = parse_utc(previous_successful_poll_end)
    upper = parse_utc(first_seen_upper_bound_utc)
    updated = parse_utc(feed_updated_utc)
    if lower is None:
        return "NO_PRIOR_SUCCESSFUL_POLL"
    if upper is None or updated is None:
        return "FEED_OR_RECEIPT_TIMESTAMP_UNKNOWN"
    if updated <= lower:
        return "FEED_TIMESTAMP_NOT_AFTER_PREVIOUS_POLL"
    if updated > upper:
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
    poll_started_utc: str,
) -> dict:
    """Fetch newest entries through accession or time boundary; fail closed on gaps."""
    prior = str(feed_state.get("latest_accession") or "").strip()
    previous_end = feed_state.get("last_successful_poll_end_utc")
    baseline = not prior and not previous_end
    max_pages = 1 if mode != "schedule" or baseline else MAX_FEED_PAGES
    offset = 0
    pages: list[dict] = []
    observations: list[dict] = []
    candidates: list[dict] = []
    seen_hashes: set[str] = set()
    first_page_entries: list[dict] = []
    boundary_found = baseline
    boundary_type = "INITIAL_BASELINE" if baseline else ""
    page_error: dict = {}

    for page_index in range(max_pages):
        url = _page_url(base_url, offset)
        raw = None
        try:
            raw = p401.fetch_bytes(url, sec=True, timeout=60, retries=4)
            received = now_utc()
            digest = hashlib.sha256(raw).hexdigest()
            if digest in seen_hashes:
                raise ValueError("repeated_page_hash_pagination_may_be_ignored")
            seen_hashes.add(digest)
            raw_count = count_atom_entries(raw)
            parsed = parse_atom_feed(raw, feed_name, url)
            if page_index == 0:
                first_page_entries = list(parsed)

            updated_values = [parse_utc(item["feed_updated_utc"]) for item in parsed]
            valid_updated = [x for x in updated_values if x is not None]
            if any(a < b for a, b in zip(valid_updated, valid_updated[1:])):
                raise ValueError("feed_updated_order_not_newest_first")

            pages.append({
                "poll_run_id": str(run_id),
                "feed_name": feed_name,
                "page_offset": offset,
                "raw_entry_count": raw_count,
                "parsed_accession_occurrence_count": len(parsed),
                "response_bytes": len(raw),
                "response_received_at_utc": received,
                "raw_sha256": digest,
                "feed_url": url,
                "page_status": "HTTP_OK",
                "error_type": "",
                "error": "",
            })

            for item in parsed:
                is_prior = bool(prior and item["accession"] == prior)
                updated = parse_utc(item["feed_updated_utc"])
                lower = parse_utc(previous_end)
                is_time_boundary = bool(lower and updated and updated <= lower)
                occurrence = {
                    **item,
                    "_page_offset": offset,
                    "_page_received_at_utc": received,
                    "_page_sha256": digest,
                    "_is_prior_accession_watermark": is_prior,
                    "_is_timestamp_boundary": is_time_boundary,
                }
                observations.append(occurrence)
                if is_prior:
                    boundary_found = True
                    boundary_type = "ACCESSION"
                    break
                if is_time_boundary:
                    boundary_found = True
                    boundary_type = "TIMESTAMP"
                    break
                candidates.append(occurrence)

            if baseline or boundary_found:
                break
            if raw_count == 0:
                if not prior and previous_end:
                    boundary_found = True
                    boundary_type = "EMPTY_NO_NEW_ENTRIES"
                    break
                page_error = {
                    "error_type": "EmptyPageBeforeBoundary",
                    "error": "Feed ended before the prior accession or timestamp boundary.",
                    "page_offset": offset,
                }
                break
            if not prior and previous_end and raw_count < PAGE_SIZE:
                boundary_found = True
                boundary_type = "END_OF_FEED"
                break
            if page_index + 1 >= max_pages:
                page_error = {
                    "error_type": "PaginationLimitReached",
                    "error": f"No prior accession or timestamp boundary within {max_pages} pages.",
                    "page_offset": offset,
                }
                break
            offset += raw_count
            time.sleep(PAGE_DELAY_SECONDS)
        except Exception as exc:
            page_error = {
                "error_type": type(exc).__name__,
                "error": str(exc)[:1000],
                "page_offset": offset,
            }
            pages.append({
                "poll_run_id": str(run_id),
                "feed_name": feed_name,
                "page_offset": offset,
                "raw_entry_count": "",
                "parsed_accession_occurrence_count": "",
                "response_bytes": len(raw) if raw is not None else "",
                "response_received_at_utc": now_utc(),
                "raw_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else "",
                "feed_url": url,
                "page_status": "ERROR",
                "error_type": type(exc).__name__,
                "error": str(exc)[:1000],
            })
            break

    poll_success = bool(pages and not page_error and boundary_found)
    poll_interval_status = (
        "INITIAL_BASELINE_NO_LOWER_BOUND" if baseline else
        "POLL_BOUNDARY_FOUND" if poll_success else
        "GAP_OR_FETCH_ERROR"
    )
    for item in observations:
        item["_poll_success"] = poll_success
        item["_poll_interval_status"] = poll_interval_status
        item["_event_interval_status"] = (
            "PRIOR_ACCESSION_BOUNDARY" if item["_is_prior_accession_watermark"] else
            "TIMESTAMP_BOUNDARY" if item["_is_timestamp_boundary"] else
            classify_event_interval(
                mode, poll_success, previous_end, item["feed_updated_utc"],
                item["_page_received_at_utc"],
            )
        )
    new_latest = first_page_entries[0]["accession"] if first_page_entries else prior
    latest_updated = first_page_entries[0]["feed_updated_utc"] if first_page_entries else ""
    return {
        "feed_name": feed_name,
        "prior_watermark": prior,
        "previous_successful_poll_end_utc": previous_end or "",
        "boundary_found": boundary_found,
        "boundary_type": boundary_type,
        "poll_success": poll_success,
        "poll_interval_status": poll_interval_status,
        "new_latest_accession": new_latest or prior,
        "latest_feed_updated_utc": latest_updated,
        "event_candidates": candidates,
        "page_observations": pages,
        "accession_observations": observations,
        "page_error": page_error,
        "raw_page_count": len(pages),
        "candidate_accession_occurrence_count": len(candidates),
        "candidate_accession_count": len({x["accession"] for x in candidates}),
    }


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"schema_version": 1, "phase": PHASE, "feeds": {}}
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("phase") != PHASE:
        raise ValueError("unexpected Phase 614 state schema; refusing silent migration")
    data.setdefault("feeds", {})
    return data


def existing_accessions() -> set[str]:
    if not EVENTS_PATH.exists():
        return set()
    with EVENTS_PATH.open("r", encoding="utf-8", newline="") as handle:
        return {
            row.get("accession", "")
            for row in csv.DictReader(handle)
            if row.get("accession")
        }


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
    preexisting = set(known)
    page_rows: list[dict] = []
    accession_rows: list[dict] = []
    event_rows: list[dict] = []
    feed_summaries: dict[str, dict] = {}
    feed_results: dict[str, dict] = {}
    seen_this_poll: set[str] = set()

    for feed_name, base_url in FEEDS.items():
        feed_state = state["feeds"].get(feed_name, {})
        result = fetch_feed(
            feed_name, base_url, feed_state, mode, str(run_id), poll_started
        )
        feed_results[feed_name] = result
        page_rows.extend(result["page_observations"])
        feed_summaries[feed_name] = {
            key: result[key] for key in (
                "prior_watermark", "previous_successful_poll_end_utc",
                "boundary_found", "boundary_type", "poll_success",
                "poll_interval_status", "new_latest_accession",
                "latest_feed_updated_utc", "raw_page_count",
                "candidate_accession_occurrence_count",
                "candidate_accession_count", "page_error",
            )
        }
        within_feed: set[str] = set()
        feed_obs: list[dict] = []
        for item in result["accession_observations"]:
            accession = item["accession"]
            duplicate_within = accession in within_feed
            duplicate_across = not duplicate_within and accession in seen_this_poll
            observation = {
                "poll_run_id": str(run_id),
                "observation_sequence": len(accession_rows) + 1,
                "feed_name": feed_name,
                "accession": accession,
                "form": item["form"],
                "filing_date": item["filing_date"],
                "filing_url": item["filing_url"],
                "feed_path_cik_unverified": item["feed_path_cik_unverified"],
                "feed_updated_raw": item["feed_updated_raw"],
                "feed_updated_utc": item["feed_updated_utc"],
                "feed_url": item["feed_url"],
                "page_offset": item["_page_offset"],
                "page_raw_sha256": item["_page_sha256"],
                "page_received_at_utc": item["_page_received_at_utc"],
                "is_prior_accession_watermark": item["_is_prior_accession_watermark"],
                "is_timestamp_boundary": item["_is_timestamp_boundary"],
                "poll_success": item["_poll_success"],
                "poll_interval_status": item["_poll_interval_status"],
                "event_interval_status": item["_event_interval_status"],
                "is_duplicate_within_feed": duplicate_within,
                "is_duplicate_across_feeds": duplicate_across,
                "is_preexisting_ledger_accession": accession in preexisting,
                "canonical_event_emitted": False,
                "candidate_suppressed_in_incomplete_poll": (
                    not result["poll_success"] and not item["_is_prior_accession_watermark"]
                ),
            }
            accession_rows.append(observation)
            feed_obs.append(observation)
            within_feed.add(accession)
            seen_this_poll.add(accession)

        emitted = 0
        for item in result["event_candidates"]:
            accession = item["accession"]
            if not result["poll_success"] or accession in known:
                continue
            received = item["_page_received_at_utc"]
            interval_status = classify_event_interval(
                mode, result["poll_success"],
                feed_state.get("last_successful_poll_end_utc"),
                item["feed_updated_utc"], received,
            )
            bounded = interval_status == "BOUNDED_METADATA_ONLY"
            try:
                legal_floor = legal_filing_date_floor_utc(item["filing_date"])
            except Exception:
                legal_floor = ""
            knowledge_upper = ""
            if bounded and legal_floor:
                knowledge_upper = iso_utc(max(parse_utc(received), parse_utc(legal_floor)))
            event_rows.append({
                "accession": accession,
                "form": item["form"],
                "feed_name": feed_name,
                "filing_date": item["filing_date"],
                "filing_url": item["filing_url"],
                "feed_path_cik_unverified": item["feed_path_cik_unverified"],
                "feed_updated_raw": item["feed_updated_raw"],
                "feed_updated_utc": item["feed_updated_utc"],
                "first_seen_at_utc": received,
                "first_seen_poll_started_utc": poll_started,
                "first_seen_poll_ended_utc": "",
                "first_seen_interval_lower_bound_utc": (
                    feed_state.get("last_successful_poll_end_utc", "") if bounded else ""
                ),
                "first_seen_interval_upper_bound_utc": received if bounded else "",
                "first_seen_interval_status": interval_status,
                "first_seen_poll_run_id": str(run_id),
                "capture_mode": mode,
                "feed_page_offset": item["_page_offset"],
                "feed_page_raw_sha256": item["_page_sha256"],
                "feed_page_received_at_utc": received,
                "legal_filing_date_floor_utc": legal_floor,
                "conservative_knowledge_upper_bound_utc": knowledge_upper,
                "acceptance_datetime_utc": "",
                "acceptance_clock_status": "NOT_RETRIEVED_FEED_UPDATED_IS_UNVERIFIED",
                "manager_identity_verified": False,
                "security_identity_verified": False,
                "historical_f80_membership_verified": False,
                "public_availability_certified": False,
                "event_metadata_interval_bounded": bounded,
                "metadata_observation_eligible": bounded and bool(knowledge_upper),
                "research_observation_eligible": False,
                "signal_eligible": False,
                "first_seen_is_upper_bound_not_exact_receipt": True,
            })
            known.add(accession)
            emitted += 1
            for observation in feed_obs:
                if (
                    observation["accession"] == accession
                    and not observation["is_prior_accession_watermark"]
                    and not observation["canonical_event_emitted"]
                    and observation["poll_success"]
                ):
                    observation["canonical_event_emitted"] = True
                    break
        feed_summaries[feed_name]["new_accession_count"] = emitted
        feed_summaries[feed_name]["bounded_metadata_count"] = sum(
            1 for row in event_rows
            if row["feed_name"] == feed_name and row["metadata_observation_eligible"]
        )

    poll_ended = now_utc()
    for row in event_rows:
        row["first_seen_poll_ended_utc"] = poll_ended

    all_successful = all(x["poll_success"] for x in feed_results.values())
    if mode == "schedule":
        append_csv(EVENTS_PATH, EVENT_FIELDS, event_rows)
        append_csv(PAGE_OBSERVATIONS_PATH, PAGE_FIELDS, page_rows)
        append_csv(ACCESSION_OBSERVATIONS_PATH, ACCESSION_OBSERVATION_FIELDS, accession_rows)
        for feed_name, result in feed_results.items():
            if result["poll_success"]:
                state["feeds"][feed_name] = {
                    "latest_accession": result["new_latest_accession"],
                    "last_successful_poll_end_utc": poll_ended,
                    "last_poll_run_id": str(run_id),
                    "last_poll_status": "SUCCESS",
                    "latest_feed_updated_utc": result["latest_feed_updated_utc"],
                }
            else:
                prior_state = dict(state["feeds"].get(feed_name, {}))
                prior_state.update({
                    "last_poll_run_id": str(run_id),
                    "last_poll_status": "GAP_OR_FETCH_ERROR",
                })
                state["feeds"][feed_name] = prior_state
        state["last_poll_run_id"] = str(run_id)
        state["last_poll_started_utc"] = poll_started
        state["last_poll_ended_utc"] = poll_ended
        state["all_feeds_successful"] = all_successful
        atomic_write_json(STATE_PATH, state)

    summary = {
        "phase": PHASE,
        "run_id": str(run_id),
        "mode": mode,
        "poll_started_utc": poll_started,
        "poll_ended_utc": poll_ended,
        "feed_count": len(FEEDS),
        "feeds": feed_summaries,
        "all_feeds_successful": all_successful,
        "new_accession_count": len(event_rows),
        "metadata_observation_eligible_count": sum(
            1 for row in event_rows if row["metadata_observation_eligible"]
        ),
        "research_observation_eligible_count": 0,
        "signal_eligible_count": 0,
        "page_observation_count": len(page_rows),
        "accession_observation_count": len(accession_rows),
        "same_feed_duplicate_occurrences": sum(
            1 for row in accession_rows if row["is_duplicate_within_feed"]
        ),
        "cross_feed_duplicate_occurrences": sum(
            1 for row in accession_rows if row["is_duplicate_across_feeds"]
        ),
        "filing_xml_or_text_downloaded": False,
        "holdings_rows_downloaded": False,
        "raw_transaction_rows_persisted": False,
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
