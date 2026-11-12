#!/usr/bin/env python3
"""Contiguous, overlapping SEC Latest Filings Atom scan with fail-closed coverage accounting."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from research.phase303_sec_latest_filings_rss_probe import BASE, fetch, parse_atom
from research.phase304_sec_rss_count_cap_audit import analyze_feed_snapshot
from research.phase305_sec_rss_start_offset_audit import exact_form_type, row_key

COUNT = 100
STEP = 80
MAX_PAGES = 50
FORMS = {"form4": "4", "form4a": "4/A"}
OVERLAP = COUNT - STEP


def normalize_entity_identity(entry: dict) -> dict:
    title = entry.get("title", "")
    match = re.search(r"\((\d{10})\)\s*\(([^()]+)\)\s*$", title)
    if match:
        entry["entity_cik_from_title"] = match.group(1)
        entry["entity_role_from_title"] = match.group(2).strip().title()
    path_match = re.search(r"/data/(\d+)/", entry.get("link", ""))
    if path_match:
        entry["path_cik_from_link"] = path_match.group(1)
        cik = entry.get("entity_cik_from_title", "")
        entry["path_cik_matches_title_entity"] = bool(
            cik and str(int(path_match.group(1))) == str(int(cik))
        )
    return entry


def raw_row_key(entry: dict) -> tuple:
    normalized = normalize_entity_identity(dict(entry))
    key = row_key(normalized)
    if key[0] or key[3]:
        return key
    return ("ORPHAN", normalized.get("entry_id", ""), normalized.get("title", ""))


def raw_row_signature(entry: dict) -> tuple:
    normalized = normalize_entity_identity(dict(entry))
    return raw_row_key(normalized), row_fingerprint(normalized)


def row_fingerprint(entry: dict) -> tuple:
    return (
        entry.get("title", ""),
        entry.get("entry_id", ""),
        entry.get("feed_updated_raw", ""),
        entry.get("summary_raw", ""),
        entry.get("link", ""),
    )


def page_signature(page: dict) -> tuple:
    return tuple((raw_row_key(x), row_fingerprint(x)) for x in page.get("entries", []))


def analyze_contiguous_scan(
    pages: list[dict],
    head_recheck: dict | None,
    expected_form: str,
    count: int = COUNT,
    step: int = STEP,
    capped: bool = False,
) -> dict:
    ordered_pages = sorted(pages, key=lambda x: x["start"])
    raw_unique: dict[tuple, dict] = {}
    raw_fingerprints: dict[tuple, set] = defaultdict(set)
    raw_page_membership: dict[tuple, set] = defaultdict(set)
    raw_form_by_key: dict[tuple, str] = {}
    target_unique: dict[tuple, dict] = {}
    target_accession_page_rows: dict[str, dict[int, set]] = defaultdict(lambda: defaultdict(set))
    page_summaries = []
    raw_orphan_unique = set()
    raw_rows_total = 0

    for page in ordered_pages:
        entries = []
        target_entries = []
        page_form_counts = Counter()
        for original in page.get("entries", []):
            entry = normalize_entity_identity(dict(original))
            form = exact_form_type(entry.get("title", ""))
            entry["form_type_from_title"] = form
            entries.append(entry)
            page_form_counts[form or "UNPARSED"] += 1
            raw_rows_total += 1
            key = raw_row_key(entry)
            raw_page_membership[key].add(page["start"])
            raw_fingerprints[key].add(row_fingerprint(entry))
            raw_unique.setdefault(key, entry)
            raw_form_by_key.setdefault(key, form)
            if not entry.get("accession_from_link"):
                raw_orphan_unique.add(key)
            if form == expected_form:
                target_entries.append(entry)
                target_unique.setdefault(key, entry)
                accession = entry.get("accession_from_link", "")
                if accession:
                    target_accession_page_rows[accession][page["start"]].add(key)
        page_summaries.append({
            "start": page["start"],
            "http_status": page.get("http_status"),
            "status": page.get("status"),
            "raw_entity_rows": len(entries),
            "target_entity_rows": len(target_entries),
            "non_target_entity_rows": len(entries) - len(target_entries),
            "form_type_distribution": dict(sorted(page_form_counts.items())),
            "raw_sha256": page.get("raw_sha256", ""),
            "poll_started_at_utc": page.get("poll_started_at_utc"),
            "poll_completed_at_utc": page.get("poll_completed_at_utc"),
        })

    overlap_checks = []
    for left, right in zip(ordered_pages, ordered_pages[1:]):
        expected = min(max(0, count - step), len(right.get("entries", []))) if len(left.get("entries", [])) == count else 0
        left_tail = [raw_row_signature(x) for x in left.get("entries", [])[-expected:]] if expected else []
        right_head = [raw_row_signature(x) for x in right.get("entries", [])[:expected]] if expected else []
        matching_positions = sum(a == b for a, b in zip(left_tail, right_head))
        sequence_matches = left_tail == right_head
        overlap_checks.append({
            "left_start": left["start"],
            "right_start": right["start"],
            "shared_entity_rows": matching_positions,
            "expected_entity_row_overlap": expected,
            "matches_expected_overlap": sequence_matches,
            "ordered_overlap_sequence_matches": sequence_matches,
        })

    target_analysis = analyze_feed_snapshot(list(target_unique.values()), expected_form)
    structural_fields = (
        "orphan_entity_rows",
        "entry_id_link_accession_mismatches",
        "query_form_mismatches",
        "path_title_cik_mismatches",
        "duplicate_entity_rows",
        "accession_form_conflicts",
        "accession_updated_timestamp_conflicts",
    )
    structural_errors = sum(int(target_analysis.get(k, 0)) for k in structural_fields)
    row_conflicts = sum(1 for fingerprints in raw_fingerprints.values() if len(fingerprints) > 1)
    repeated_rows = sum(1 for starts in raw_page_membership.values() if len(starts) > 1)
    duplicate_appearances = raw_rows_total - len(raw_unique)
    within_page_duplicate_rows = sum(
        len(page.get("entries", [])) - len({raw_row_key(x) for x in page.get("entries", [])})
        for page in ordered_pages
    )

    accessions_spanning_pages = {
        accession: by_page for accession, by_page in target_accession_page_rows.items()
        if len(by_page) > 1
    }
    accessions_split = {
        accession: by_page for accession, by_page in accessions_spanning_pages.items()
        if len({tuple(sorted(keys)) for keys in by_page.values()}) > 1
    }

    first_page = next((x for x in ordered_pages if x["start"] == 0), None)
    recheck_ok = bool(
        head_recheck
        and head_recheck.get("http_status") == 200
        and head_recheck.get("status") == "ATOM_PARSED"
    )
    head_stable = bool(
        first_page and recheck_ok and page_signature(first_page) == page_signature(head_recheck)
    )
    all_requests_succeeded = (
        bool(ordered_pages)
        and all(x.get("http_status") == 200 and x.get("status") == "ATOM_PARSED" for x in ordered_pages)
        and recheck_ok
    )
    tail_seen = bool(ordered_pages and len(ordered_pages[-1].get("entries", [])) < count)
    overlap_stable = all(x["matches_expected_overlap"] for x in overlap_checks)
    if len(ordered_pages) <= 1:
        overlap_stable = True
    scan_capped = bool(capped and not tail_seen)
    complete_scan = bool(
        all_requests_succeeded
        and tail_seen
        and overlap_stable
        and head_stable
        and structural_errors == 0
        and row_conflicts == 0
    )

    non_target_counts = Counter(
        form for form in raw_form_by_key.values() if form != expected_form
    )
    return {
        "expected_form": expected_form,
        "page_count": len(ordered_pages),
        "pages": page_summaries,
        "all_requests_succeeded": all_requests_succeeded,
        "tail_seen": tail_seen,
        "scan_capped": scan_capped,
        "head_recheck_status": (head_recheck or {}).get("status"),
        "head_recheck_sha256": (head_recheck or {}).get("raw_sha256"),
        "head_page_stable_after_scan": head_stable,
        "overlap_checks": overlap_checks,
        "all_adjacent_overlaps_match": overlap_stable,
        "raw_entity_row_appearances": raw_rows_total,
        "unique_raw_entity_rows": len(raw_unique),
        "duplicate_raw_entity_row_appearances": duplicate_appearances,
        "within_page_duplicate_entity_rows": within_page_duplicate_rows,
        "unique_raw_orphan_entity_rows": len(raw_orphan_unique),
        "unique_target_entity_rows": len(target_unique),
        "unique_target_accessions": target_analysis["unique_accessions"],
        "target_rows_per_accession": target_analysis["entity_rows_per_accession"],
        "target_feed_updated_order_nonincreasing": target_analysis["feed_updated_order_nonincreasing"],
        "target_oldest_feed_updated": target_analysis["oldest_feed_updated"],
        "target_newest_feed_updated": target_analysis["newest_feed_updated"],
        "non_target_form_unique_row_counts": dict(sorted(non_target_counts.items())),
        "non_target_form_unique_rows": sum(non_target_counts.values()),
        "entity_rows_repeated_across_pages": repeated_rows,
        "accessions_spanning_multiple_pages": len(accessions_spanning_pages),
        "accessions_split_across_page_windows": len(accessions_split),
        "accession_split_details": {
            accession: {str(start): len(rows) for start, rows in by_page.items()}
            for accession, by_page in accessions_split.items()
        },
        "row_fingerprint_conflicts": row_conflicts,
        "target_structural_errors": {k: target_analysis.get(k, 0) for k in structural_fields},
        "target_structural_error_total": structural_errors,
        "complete_current_snapshot_scan": complete_scan,
        "coverage_interpretation": (
            "complete only for the SEC feed snapshot observed during this scan; not a historical archive"
            if complete_scan else
            "partial or unstable snapshot; do not claim complete current-feed coverage"
        ),
    }


def fetch_page(email: str, label: str, form: str, start: int, output_dir: Path) -> dict:
    params = {
        "action": "getcurrent",
        "type": form,
        "owner": "include",
        "count": str(COUNT),
        "start": str(start),
        "output": "atom",
    }
    url = BASE + "?" + urlencode(params)
    item = {
        "label": label,
        "form_type": form,
        "start": start,
        "count": COUNT,
        "requested_url": url,
        "poll_started_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PENDING",
        "entries": [],
    }
    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    try:
        payload, headers = fetch(url, user_agent)
        raw_path = output_dir / "raw" / f"{label}_start{start}_count{COUNT}.atom"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(payload)
        entries = parse_atom(payload)
        item.update({
            "status": "ATOM_PARSED",
            "poll_completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "http_status": headers["http_status"],
            "response_headers": headers,
            "raw_file": str(raw_path.relative_to(output_dir)),
            "raw_sha256": hashlib.sha256(payload).hexdigest(),
            "entries": entries,
        })
    except Exception as exc:
        item.update({
            "status": "QUERY_FAILED",
            "poll_completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "http_status": getattr(exc, "code", None),
            "error_type": type(exc).__name__,
            "error": str(exc)[:240],
            "raw_sha256": "",
        })
    return item


def run_scan(email: str, output_dir: Path) -> dict:
    if not email or "@" not in email or any(ch.isspace() for ch in email):
        raise ValueError("SEC_CONTACT_EMAIL_missing_or_invalid")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "raw").mkdir(exist_ok=True)
    results = {}
    total_requests = 0

    for label, form in FORMS.items():
        pages = []
        tail_seen = False
        for page_index in range(MAX_PAGES):
            start = page_index * STEP
            page = fetch_page(email, label, form, start, output_dir)
            pages.append(page)
            total_requests += 1
            if page.get("http_status") != 200 or page.get("status") != "ATOM_PARSED":
                break
            if len(page["entries"]) < COUNT:
                tail_seen = True
                break
            time.sleep(1.05)

        head_recheck = fetch_page(email, f"{label}_head_recheck", form, 0, output_dir)
        total_requests += 1
        analysis = analyze_contiguous_scan(
            pages, head_recheck, form, count=COUNT, step=STEP,
            capped=(len(pages) >= MAX_PAGES and not tail_seen),
        )
        results[label] = {
            "form_type": form,
            "requests": [
                {k: v for k, v in page.items() if k != "entries"}
                | {"raw_entity_rows": len(page.get("entries", []))}
                for page in pages
            ],
            "head_recheck": {k: v for k, v in head_recheck.items() if k != "entries"}
                | {"raw_entity_rows": len(head_recheck.get("entries", []))},
            "analysis": analysis,
        }
        time.sleep(1.05)

    all_requests_succeeded = all(x["analysis"]["all_requests_succeeded"] for x in results.values())
    structural_errors = sum(x["analysis"]["target_structural_error_total"] for x in results.values())
    row_conflicts = sum(x["analysis"]["row_fingerprint_conflicts"] for x in results.values())
    result = {
        "phase": 306,
        "status": "PASS_SCAN_AUDIT" if all_requests_succeeded and structural_errors == 0 and row_conflicts == 0 else "PARTIAL_OR_STRUCTURAL_FAILURE",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "scan_protocol": {
            "count": COUNT,
            "step": STEP,
            "overlap_rows": OVERLAP,
            "max_pages_per_form": MAX_PAGES,
            "max_raw_row_positions_covered": (MAX_PAGES - 1) * STEP + COUNT,
            "exact_form_token_required": True,
            "feed_head_rechecked_after_scan": True,
            "stop_when_page_has_fewer_than_count_rows": True,
        },
        "total_requests": total_requests,
        "form_results": results,
        "summary": {
            "all_requests_succeeded": all_requests_succeeded,
            "target_structural_errors": structural_errors,
            "row_fingerprint_conflicts": row_conflicts,
            "form4_unique_accessions": results["form4"]["analysis"]["unique_target_accessions"],
            "form4_unique_entity_rows": results["form4"]["analysis"]["unique_target_entity_rows"],
            "form4_non_target_rows": results["form4"]["analysis"]["non_target_form_unique_rows"],
            "form4_tail_seen": results["form4"]["analysis"]["tail_seen"],
            "form4_complete_current_snapshot_scan": results["form4"]["analysis"]["complete_current_snapshot_scan"],
            "form4_scan_capped": results["form4"]["analysis"]["scan_capped"],
            "form4a_unique_accessions": results["form4a"]["analysis"]["unique_target_accessions"],
            "form4a_unique_entity_rows": results["form4a"]["analysis"]["unique_target_entity_rows"],
            "form4a_tail_seen": results["form4a"]["analysis"]["tail_seen"],
            "form4a_complete_current_snapshot_scan": results["form4a"]["analysis"]["complete_current_snapshot_scan"],
            "all_forms_complete_current_snapshot_scan": all(x["analysis"]["complete_current_snapshot_scan"] for x in results.values()),
        },
        "controls": {
            "atom_updated_is_first_public_time": False,
            "exact_first_public_timestamp_verified": False,
            "strict_pit_admitted": False,
            "return_test": False,
            "alpha_test": False,
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
    (output_dir / "phase306_sec_rss_contiguous_scan_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase306_output")
    args = parser.parse_args()
    result = run_scan(os.environ.get("SEC_CONTACT_EMAIL", ""), Path(args.output))
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    print("PHASE306_STATUS=" + result["status"])
    if result["status"] != "PASS_SCAN_AUDIT":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
