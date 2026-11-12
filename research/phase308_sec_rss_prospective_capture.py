#!/usr/bin/env python3
"""Prospective SEC Form 4/4-A RSS capture with immutable raw pages and first-observation intervals."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from research.phase303_sec_latest_filings_rss_probe import BASE, fetch, parse_atom
from research.phase305_sec_rss_start_offset_audit import exact_form_type
from research.phase306_sec_rss_contiguous_scan import (
    analyze_contiguous_scan,
    normalize_entity_identity,
    raw_row_key,
)

COUNT = 100
STEP = 80
MAX_PAGES = 50
FORMS = {"form4": "4", "form4a": "4/A"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value: str | None):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch_page(email: str, label: str, form: str, start: int, output_dir: Path) -> dict:
    params = {
        "action": "getcurrent",
        "type": form,
        "owner": "only",
        "count": str(COUNT),
        "start": str(start),
        "output": "atom",
    }
    url = BASE + "?" + urlencode(params)
    item = {
        "label": label,
        "form_type": form,
        "owner_mode": "only",
        "start": start,
        "count": COUNT,
        "requested_url": url,
        "poll_started_at_utc": utc_now(),
        "status": "PENDING",
        "entries": [],
    }
    try:
        payload, headers = fetch(url, f"NuevaEstrategia Smart Money Research (contact: {email})")
        raw_path = output_dir / "raw" / f"{label}_start{start}_count{COUNT}.atom"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(payload)
        entries = parse_atom(payload)
        item.update({
            "status": "ATOM_PARSED",
            "http_status": headers["http_status"],
            "response_headers": headers,
            "poll_completed_at_utc": utc_now(),
            "raw_file": str(raw_path.relative_to(output_dir)),
            "raw_sha256": hashlib.sha256(payload).hexdigest(),
            "entries": entries,
        })
    except Exception as exc:
        item.update({
            "status": "QUERY_FAILED",
            "http_status": getattr(exc, "code", None),
            "poll_completed_at_utc": utc_now(),
            "error_type": type(exc).__name__,
            "error": str(exc)[:240],
            "raw_sha256": "",
        })
    return item


def build_accession_events(pages_by_form: dict) -> tuple[list[dict], dict]:
    events = []
    form_counts = {}
    for label, form in FORMS.items():
        unique_rows = {}
        for page in pages_by_form[label]:
            for original in page.get("entries", []):
                entry = normalize_entity_identity(dict(original))
                exact = exact_form_type(entry.get("title", ""))
                entry["form_type_from_title"] = exact
                if exact != form:
                    continue
                unique_rows.setdefault(raw_row_key(entry), entry)
        grouped = defaultdict(list)
        for entry in unique_rows.values():
            accession = entry.get("accession_from_link", "")
            if not accession:
                continue
            grouped[accession].append({
                "entity_role": entry.get("entity_role_from_title", ""),
                "entity_cik": entry.get("entity_cik_from_title", ""),
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "feed_updated_raw": entry.get("feed_updated_raw", ""),
            })
        form_counts[label] = {
            "form_type": form,
            "unique_entity_rows": len(unique_rows),
            "unique_accessions": len(grouped),
        }
        for accession, rows in grouped.items():
            rows = sorted(rows, key=lambda x: (x["entity_role"], x["entity_cik"], x["title"]))
            issuer_ciks = sorted({x["entity_cik"] for x in rows if x["entity_role"] == "Issuer" and x["entity_cik"]})
            owner_ciks = sorted({x["entity_cik"] for x in rows if x["entity_role"] == "Reporting" and x["entity_cik"]})
            updated_values = sorted({x["feed_updated_raw"] for x in rows if x["feed_updated_raw"]})
            events.append({
                "form_type": form,
                "accession": accession,
                "issuer_ciks": issuer_ciks,
                "reporting_owner_ciks": owner_ciks,
                "entity_rows": rows,
                "feed_updated_values": updated_values,
            })
    return events, form_counts


def compact_ledger(ledger: dict) -> dict:
    ledger.setdefault("accessions", {})
    for record in ledger["accessions"].values():
        seen = record.pop("entity_rows_seen", {})
        last_rows = record.pop("last_entity_rows", [])
        rows = list(seen.values()) if isinstance(seen, dict) else []
        if not rows:
            rows = last_rows if isinstance(last_rows, list) else []
        if rows:
            identities = sorted({
                f'{row.get("entity_role","")}|{row.get("entity_cik","")}|{row.get("title","")}|{row.get("link","")}'
                for row in rows
            })
            record["entity_row_count"] = len(identities)
            record["entity_row_set_sha256"] = hashlib.sha256("\n".join(identities).encode()).hexdigest()
        updated_values = record.pop("feed_updated_values_seen", [])
        if updated_values:
            record.setdefault("first_feed_updated_raw", updated_values[0])
            record["last_feed_updated_raw"] = updated_values[-1]
        record.pop("entity_row_set_sha256_history", None)
    return ledger


def merge_capture_into_ledger(
    ledger: dict,
    capture: dict,
    accession_events: list[dict],
) -> tuple[dict, dict]:
    ledger.setdefault("schema_version", 1)
    ledger.setdefault("source", "SEC EDGAR Latest Filings Atom")
    ledger.setdefault("created_at_utc", capture["capture_started_at_utc"])
    ledger.setdefault("accessions", {})
    ledger.setdefault("captures", [])
    ledger.setdefault("last_complete_capture_end_utc", None)
    ledger.setdefault("last_complete_snapshot_accessions", [])
    ledger = compact_ledger(ledger)

    previous_complete_end = ledger.get("last_complete_capture_end_utc")
    previous_dt = parse_utc(previous_complete_end)
    current_start_dt = parse_utc(capture["capture_started_at_utc"])
    gap_minutes = (
        (current_start_dt - previous_dt).total_seconds() / 60
        if previous_dt and current_start_dt else None
    )
    gap_detected = bool(gap_minutes is not None and gap_minutes > 90)
    previous_snapshot = set(ledger.get("last_complete_snapshot_accessions", []))
    current_snapshot = {
        f'{event["form_type"]}:{event["accession"]}' for event in accession_events
    }
    snapshot_complete = bool(capture.get("snapshot_complete"))
    missing_since_previous = sorted(previous_snapshot - current_snapshot) if snapshot_complete else []
    new_since_previous = sorted(current_snapshot - previous_snapshot) if snapshot_complete and previous_snapshot else []

    new_accessions = 0
    changed_entity_rows = 0
    for event in accession_events:
        key = f'{event["form_type"]}:{event["accession"]}'
        existing = ledger["accessions"].get(key)
        current_rows = event.get("entity_rows", [])
        current_row_keys = {
            f'{row.get("entity_role","")}|{row.get("entity_cik","")}|{row.get("title","")}|{row.get("link","")}'
            for row in current_rows
        }
        if existing is None:
            new_accessions += 1
            existing = {
                "form_type": event["form_type"],
                "accession": event["accession"],
                "first_observed_at_utc": capture["capture_started_at_utc"],
                "first_observation_interval_start_utc": previous_complete_end,
                "first_observation_interval_end_utc": capture["capture_started_at_utc"],
                "first_observation_interval_width_minutes": gap_minutes,
                "first_observation_lower_bound_quality": (
                    "bounded_by_previous_complete_capture"
                    if previous_complete_end else "left_censored_no_prior_complete_capture"
                ),
                "gap_before_first_observation_detected": gap_detected,
                "first_seen_run_id": capture.get("run_id"),
                "seen_count": 0,
                "entity_row_count": 0,
                "entity_row_set_sha256": "",
                "first_feed_updated_raw": (
                    event.get("feed_updated_values", [None])[0]
                    if event.get("feed_updated_values") else None
                ),
            }
        row_set_hash = hashlib.sha256("\n".join(sorted(current_row_keys)).encode()).hexdigest()
        prior_hash = existing.get("entity_row_set_sha256", "")
        if prior_hash and prior_hash != row_set_hash:
            changed_entity_rows += 1
        elif not prior_hash:
            changed_entity_rows += len(current_row_keys)
        existing["entity_row_count"] = len(current_row_keys)
        existing["entity_row_set_sha256"] = row_set_hash
        if event.get("feed_updated_values"):
            existing["last_feed_updated_raw"] = event["feed_updated_values"][-1]
        existing["issuer_ciks"] = event.get("issuer_ciks", [])
        existing["reporting_owner_ciks"] = event.get("reporting_owner_ciks", [])
        existing["last_entity_rows"] = current_rows
        existing["last_observed_at_utc"] = capture["capture_completed_at_utc"]
        existing["last_seen_run_id"] = capture.get("run_id")
        existing["last_seen_snapshot_complete"] = snapshot_complete
        existing["seen_count"] = int(existing.get("seen_count", 0)) + 1
        ledger["accessions"][key] = existing

    raw_manifest = json.dumps(
        capture.get("raw_page_hashes", {}), sort_keys=True, separators=(",", ":")
    ).encode()
    raw_page_count = sum(len(rows) for rows in capture.get("raw_page_hashes", {}).values())
    capture_record = {
        "run_id": capture.get("run_id"),
        "workflow_sha": capture.get("workflow_sha"),
        "capture_started_at_utc": capture["capture_started_at_utc"],
        "capture_completed_at_utc": capture["capture_completed_at_utc"],
        "status": capture.get("status"),
        "snapshot_complete": snapshot_complete,
        "gap_before_capture_minutes": gap_minutes,
        "gap_before_capture_detected": gap_detected,
        "form_counts": capture.get("form_counts", {}),
        "form_scans": capture.get("form_scans", {}),
        "raw_page_count": raw_page_count,
        "raw_page_manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
        "new_accessions_this_capture": new_accessions,
        "changed_entity_rows_this_capture": changed_entity_rows,
        "missing_since_previous_complete_snapshot": missing_since_previous,
        "new_since_previous_complete_snapshot": new_since_previous,
    }
    ledger["captures"].append(capture_record)
    ledger["last_capture_started_at_utc"] = capture["capture_started_at_utc"]
    ledger["last_capture_completed_at_utc"] = capture["capture_completed_at_utc"]
    ledger["last_capture_status"] = capture.get("status")
    if snapshot_complete:
        ledger["last_complete_capture_end_utc"] = capture["capture_completed_at_utc"]
        ledger["last_complete_snapshot_accessions"] = sorted(current_snapshot)
    ledger["updated_at_utc"] = capture["capture_completed_at_utc"]
    today_utc = capture["capture_completed_at_utc"][:10]
    repo_snapshot_due = ledger.get("last_repo_snapshot_date") != today_utc
    if repo_snapshot_due:
        ledger["last_repo_snapshot_date"] = today_utc
    ledger["repo_snapshot_due"] = repo_snapshot_due
    ledger["total_capture_count" = len(ledger["captures"])
    ledger["total_unique_accessions"] = len(ledger["accessions"])

    merge_summary = {
        "new_accessions_this_capture": new_accessions,
        "changed_entity_rows_this_capture": changed_entity_rows,
        "missing_since_previous_complete_snapshot": len(missing_since_previous),
        "new_since_previous_complete_snapshot": len(new_since_previous),
        "gap_before_capture_minutes": gap_minutes,
        "gap_before_capture_detected": gap_detected,
        "ledger_total_capture_count": ledger["total_capture_count"],
        "ledger_total_unique_accessions": ledger["total_unique_accessions"],
        "last_complete_capture_end_utc": ledger.get("last_complete_capture_end_utc"),
        "repo_snapshot_due": repo_snapshot_due,
    }
    return ledger, merge_summary


def run_capture(email: str, output_dir: Path, ledger_path: Path, run_id: str, workflow_sha: str) -> dict:
    if not email or "@" not in email or any(ch.isspace() for ch in email):
        raise ValueError("SEC_CONTACT_EMAIL_missing_or_invalid")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "raw").mkdir(exist_ok=True)
    capture_started = utc_now()
    pages_by_form = {}
    analyses = {}
    request_records = []
    raw_hashes = {}

    for label, form in FORMS.items():
        pages = []
        for page_index in range(MAX_PAGES):
            start = page_index * STEP
            page = fetch_page(email, label, form, start, output_dir)
            pages.append(page)
            request_records.append({k: v for k, v in page.items() if k != "entries"} | {
                "raw_entity_rows": len(page.get("entries", []))
            })
            if page.get("status") != "ATOM_PARSED" or page.get("http_status") != 200:
                break
            if len(page.get("entries", [])) < COUNT:
                break
            time.sleep(1.05)
        head = fetch_page(email, f"{label}_head_recheck", form, 0, output_dir)
        request_records.append({k: v for k, v in head.items() if k != "entries"} | {
            "raw_entity_rows": len(head.get("entries", []))
        })
        analyses[label] = analyze_contiguous_scan(
            pages,
            head,
            form,
            count=COUNT,
            step=STEP,
            capped=(len(pages) >= MAX_PAGES and len(pages[-1].get("entries", [])) == COUNT),
        )
        pages_by_form[label] = pages
        raw_hashes[label] = [
            {"start": p["start"], "sha256": p.get("raw_sha256", ""), "raw_file": p.get("raw_file", "")}
            for p in pages
        ] + [{"start": 0, "sha256": head.get("raw_sha256", ""), "raw_file": head.get("raw_file", ""), "role": "head_recheck"}]
        time.sleep(1.05)

    capture_completed = utc_now()
    accession_events, form_counts = build_accession_events(pages_by_form)
    snapshot_complete = all(x.get("complete_current_snapshot_scan") for x in analyses.values())
    all_requests_succeeded = all(
        p.get("status") == "ATOM_PARSED" and p.get("http_status") == 200
        for label_pages in pages_by_form.values() for p in label_pages
    )
    all_requests_succeeded = all_requests_succeeded and all(
        analyses[label].get("head_recheck_status") == "ATOM_PARSED"
        for label in FORMS
    )
    structural_errors = sum(analyses[label]["target_structural_error_total"] for label in FORMS)
    row_conflicts = sum(analyses[label]["row_fingerprint_conflicts"] for label in FORMS)
    status = "PASS_COMPLETE_CAPTURE" if snapshot_complete and all_requests_succeeded and structural_errors == 0 and row_conflicts == 0 else "PARTIAL_CAPTURE"

    capture = {
        "run_id": str(run_id),
        "workflow_sha": workflow_sha,
        "capture_started_at_utc": capture_started,
        "capture_completed_at_utc": capture_completed,
        "status": status,
        "snapshot_complete": snapshot_complete,
        "all_requests_succeeded": all_requests_succeeded,
        "target_structural_errors": structural_errors,
        "row_fingerprint_conflicts": row_conflicts,
        "form_counts": form_counts,
        "form_scans": {
            label: {
                "page_count": analyses[label]["page_count"],
                "unique_target_accessions": analyses[label]["unique_target_accessions"],
                "unique_target_entity_rows": analyses[label]["unique_target_entity_rows"],
                "tail_seen": analyses[label]["tail_seen"],
                "scan_capped": analyses[label]["scan_capped"],
                "head_page_stable_after_scan": analyses[label]["head_page_stable_after_scan"],
                "all_adjacent_overlaps_match": analyses[label]["all_adjacent_overlaps_match"],
                "target_structural_error_total": analyses[label]["target_structural_error_total"],
                "row_fingerprint_conflicts": analyses[label]["row_fingerprint_conflicts"],
                "complete_current_snapshot_scan": analyses[label]["complete_current_snapshot_scan"],
            }
            for label in FORMS
        },
        "raw_page_hashes": raw_hashes,
    }

    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    else:
        ledger = {}
    ledger, merge_summary = merge_capture_into_ledger(ledger, capture, accession_events)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

    result = {
        "phase": 308,
        "status": status,
        "capture": capture,
        "summary": {
            "form4_accessions": analyses["form4"]["unique_target_accessions"],
            "form4_entity_rows": analyses["form4"]["unique_target_entity_rows"],
            "form4a_accessions": analyses["form4a"]["unique_target_accessions"],
            "form4a_entity_rows": analyses["form4a"]["unique_target_entity_rows"],
            "snapshot_complete": snapshot_complete,
            "all_requests_succeeded": all_requests_succeeded,
            "target_structural_errors": structural_errors,
            "row_fingerprint_conflicts": row_conflicts,
            "request_count": len(request_records),
            **merge_summary,
        },
        "requests": request_records,
        "controls": {
            "owner_filter": "only",
            "exact_form_token_required": True,
            "atom_updated_is_first_public_time": False,
            "first_observation_is_poll_interval_not_first_public_timestamp": True,
            "strict_pit_admitted": False,
            "return_or_alpha_test": False,
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
    (output_dir / "phase308_sec_rss_capture_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "ledger_snapshot.json").write_text(
        ledger_path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase308_output")
    parser.add_argument("--ledger", default="research/data/sec_rss_prospective_ledger.json")
    args = parser.parse_args()
    result = run_capture(
        os.environ.get("SEC_CONTACT_EMAIL", ""),
        Path(args.output),
        Path(args.ledger),
        os.environ.get("GITHUB_RUN_ID", "local"),
        os.environ.get("GITHUB_SHA", ""),
    )
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    print("PHASE308_STATUS=" + result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
