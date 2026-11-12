#!/usr/bin/env python3
"""Audit SEC EDGAR owner=include/only/exclude semantics for Form 4 RSS queries."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from research.phase303_sec_latest_filings_rss_probe import BASE, fetch, parse_atom
from research.phase304_sec_rss_count_cap_audit import analyze_feed_snapshot
from research.phase305_sec_rss_start_offset_audit import exact_form_type
from research.phase306_sec_rss_contiguous_scan import (
    normalize_entity_identity,
    raw_row_key,
    raw_row_signature,
    page_signature,
)

COUNT = 100
STEP = 80
ONLY_OFFSETS = tuple(range(0, 2001, 80))
INCLUDE_FORM4_OFFSETS = (0, 80, 320, 400)
MODES = ("include", "only", "exclude")
FORMS = {"form4": "4", "form4a": "4/A"}


def analyze_mode_form(pages: list[dict], recheck: dict | None, expected_form: str) -> dict:
    ordered = sorted(pages, key=lambda x: x["start"])
    unique_rows = {}
    raw_appearances = 0
    within_page_duplicates = 0
    page_summaries = []
    overlap_checks = []

    for page in ordered:
        page_entries = []
        page_keys = []
        page_target = []
        for original in page.get("entries", []):
            entry = normalize_entity_identity(dict(original))
            form = exact_form_type(entry.get("title", ""))
            entry["form_type_from_title"] = form
            page_entries.append(entry)
            key = raw_row_key(entry)
            page_keys.append(key)
            unique_rows.setdefault(key, entry)
            raw_appearances += 1
            if form == expected_form:
                page_target.append(entry)
        within_page_duplicates += len(page_keys) - len(set(page_keys))
        page_summaries.append({
            "start": page["start"],
            "http_status": page.get("http_status"),
            "status": page.get("status"),
            "raw_entity_rows": len(page_entries),
            "target_entity_rows": len(page_target),
        })

    for left, right in zip(ordered, ordered[1:]):
        if right["start"] - left["start"] != STEP:
            continue
        expected = COUNT - STEP if len(left.get("entries", [])) == COUNT else 0
        left_tail = [raw_row_signature(x) for x in left.get("entries", [])[-expected:]] if expected else []
        right_head = [raw_row_signature(x) for x in right.get("entries", [])[:expected]] if expected else []
        matches = left_tail == right_head
        overlap_checks.append({
            "left_start": left["start"],
            "right_start": right["start"],
            "expected_overlap_rows": expected,
            "matching_positions": sum(a == b for a, b in zip(left_tail, right_head)),
            "ordered_overlap_matches": matches,
        })

    target_rows = {
        key: entry for key, entry in unique_rows.items()
        if exact_form_type(entry.get("title", "")) == expected_form
    }
    target_analysis = analyze_feed_snapshot(list(target_rows.values()), expected_form)
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
    form_counts = Counter(
        exact_form_type(entry.get("title", "")) or "UNPARSED"
        for entry in unique_rows.values()
    )
    all_requests_succeeded = bool(ordered) and all(
        page.get("http_status") == 200 and page.get("status") == "ATOM_PARSED"
        for page in ordered
    )
    recheck_ok = bool(
        recheck and recheck.get("http_status") == 200 and recheck.get("status") == "ATOM_PARSED"
    )
    head_stable = bool(
        ordered and recheck_ok and ordered[0]["start"] == 0
        and page_signature(ordered[0]) == page_signature(recheck)
    )
    if recheck is not None:
        all_requests_succeeded = all_requests_succeeded and recheck_ok
    overlaps_stable = all(x["ordered_overlap_matches"] for x in overlap_checks)
    if len(ordered) <= 1:
        overlaps_stable = True
    tail_seen = any(len(page.get("entries", [])) < COUNT for page in ordered)
    starts_contiguous = bool(ordered) and [x["start"] for x in ordered] == [
        i * STEP for i in range(len(ordered))
    ]
    complete_snapshot = bool(
        recheck is not None and all_requests_succeeded and tail_seen
        and starts_contiguous and overlaps_stable and head_stable
        and structural_errors == 0
    )
    target_accessions = sorted({
        entry.get("accession_from_link", "")
        for entry in target_rows.values()
        if entry.get("accession_from_link")
    })
    page0_accessions = sorted({
        entry.get("accession_from_link", "")
        for entry in (ordered[0].get("entries", []) if ordered else [])
        if exact_form_type(entry.get("title", "")) == expected_form
        and entry.get("accession_from_link")
    })
    return {
        "expected_form": expected_form,
        "page_count": len(ordered),
        "pages": page_summaries,
        "all_requests_succeeded": all_requests_succeeded,
        "starts_contiguous": starts_contiguous,
        "tail_seen": tail_seen,
        "head_page_stable_after_recheck": head_stable if recheck is not None else None,
        "overlap_checks": overlap_checks,
        "all_adjacent_overlaps_match": overlaps_stable,
        "raw_entity_row_appearances": raw_appearances,
        "unique_raw_entity_rows": len(unique_rows),
        "duplicate_raw_entity_row_appearances": raw_appearances - len(unique_rows),
        "within_page_duplicate_entity_rows": within_page_duplicates,
        "unique_target_entity_rows": len(target_rows),
        "unique_target_accessions": len(target_accessions),
        "target_accessions": target_accessions,
        "page0_target_accessions": page0_accessions,
        "non_target_form_unique_row_counts": dict(sorted(
            (k, v) for k, v in form_counts.items() if k != expected_form
        )),
        "non_target_form_unique_rows": sum(v for k, v in form_counts.items() if k != expected_form),
        "target_rows_per_accession": target_analysis["entity_rows_per_accession"],
        "target_role_counts": dict(sorted(Counter(
            entry.get("entity_role_from_title", "UNPARSED")
            for entry in target_rows.values()
        ).items())),
        "target_structural_errors": {k: target_analysis.get(k, 0) for k in structural_fields},
        "target_structural_error_total": structural_errors,
        "complete_current_snapshot_scan": complete_snapshot,
    }


def evaluate_owner_filter_semantics(results: dict) -> dict:
    only4 = results["only"]["form4"]["analysis"]
    only4a = results["only"]["form4a"]["analysis"]
    exclude4 = results["exclude"]["form4"]["analysis"]
    exclude4a = results["exclude"]["form4a"]["analysis"]
    include4 = results["include"]["form4"]["analysis"]

    only4_non_ownership = sum(
        count for form, count in only4["non_target_form_unique_row_counts"].items()
        if form not in {"4", "4/A"}
    )
    only4a_non_target = sum(
        count for form, count in only4a["non_target_form_unique_row_counts"].items()
        if form != "4/A"
    )
    exclude_target_accessions = (
        exclude4["unique_target_accessions"] + exclude4a["unique_target_accessions"]
    )
    include_non_target = include4["non_target_form_unique_rows"]
    include_accessions = set(include4["page0_target_accessions"])
    only_accessions = set(only4["page0_target_accessions"])
    accessions_preserved = include_accessions == only_accessions
    isolation_supported = (
        only4_non_ownership == 0
        and only4a_non_target == 0
        and exclude_target_accessions == 0
        and include_non_target > 0
        and only4["unique_target_accessions"] > 0
    )
    return {
        "owner_only_non_ownership_rows_in_type4_query": only4_non_ownership,
        "owner_only_non_4a_rows_in_type4a_query": only4a_non_target,
        "owner_exclude_target_accessions": exclude_target_accessions,
        "owner_include_non_target_rows_in_type4_control": include_non_target,
        "owner_only_page0_form4_accessions": len(only_accessions),
        "owner_include_page0_form4_accessions": len(include_accessions),
        "owner_only_preserves_include_page0_accession_set": accessions_preserved,
        "owner_only_isolates_ownership_forms": isolation_supported,
        "owner_only_filter_useful_for_capture": isolation_supported and accessions_preserved,
        "owner_only_current_snapshot_complete": (
            only4["complete_current_snapshot_scan"]
            and only4a["complete_current_snapshot_scan"]
        ),
    }


def fetch_page(email: str, mode: str, label: str, form: str, start: int, output_dir: Path) -> dict:
    params = {
        "action": "getcurrent",
        "type": form,
        "owner": mode,
        "count": str(COUNT),
        "start": str(start),
        "output": "atom",
    }
    url = BASE + "?" + urlencode(params)
    item = {
        "mode": mode,
        "form_type": form,
        "start": start,
        "requested_url": url,
        "poll_started_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PENDING",
        "entries": [],
    }
    try:
        payload, headers = fetch(url, f"NuevaEstrategia Smart Money Research (contact: {email})")
        raw_path = output_dir / "raw" / f"{mode}_{label}_start{start}.atom"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(payload)
        entries = parse_atom(payload)
        item.update({
            "status": "ATOM_PARSED",
            "http_status": headers["http_status"],
            "response_headers": headers,
            "poll_completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "raw_file": str(raw_path.relative_to(output_dir)),
            "raw_sha256": hashlib.sha256(payload).hexdigest(),
            "entries": entries,
        })
    except Exception as exc:
        item.update({
            "status": "QUERY_FAILED",
            "http_status": getattr(exc, "code", None),
            "poll_completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "error_type": type(exc).__name__,
            "error": str(exc)[:240],
            "raw_sha256": "",
        })
    return item


def run_audit(email: str, output_dir: Path) -> dict:
    if not email or "@" not in email or any(ch.isspace() for ch in email):
        raise ValueError("SEC_CONTACT_EMAIL_missing_or_invalid")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "raw").mkdir(exist_ok=True)
    results = {}
    requests = []
    for mode in MODES:
        results[mode] = {}
        for label, form in FORMS.items():
            if mode == "only":
                offsets = ONLY_OFFSETS
            elif mode == "include" and label == "form4":
                offsets = INCLUDE_FORM4_OFFSETS
            else:
                offsets = (0,)
            pages = []
            for start in offsets:
                page = fetch_page(email, mode, label, form, start, output_dir)
                pages.append(page)
                requests.append({k: v for k, v in page.items() if k != "entries"} | {
                    "raw_entity_rows": len(page.get("entries", []))
                })
                time.sleep(1.05)
                if mode == "only" and len(page.get("entries", [])) < COUNT:
                    break
            recheck = None
            if mode == "only":
                recheck = fetch_page(email, mode, f"{label}_head_recheck", form, 0, output_dir)
                requests.append({k: v for k, v in recheck.items() if k != "entries"} | {
                    "raw_entity_rows": len(recheck.get("entries", []))
                })
                time.sleep(1.05)
            results[mode][label] = {
                "form_type": form,
                "analysis": analyze_mode_form(pages, recheck, form),
            }

    semantics = evaluate_owner_filter_semantics(results)
    all_requests_succeeded = all(x.get("status") == "ATOM_PARSED" and x.get("http_status") == 200 for x in requests)
    structural_errors = sum(
        results[mode][label]["analysis"]["target_structural_error_total"]
        for mode in MODES for label in FORMS
    )
    result = {
        "phase": 307,
        "status": "PASS_AUDIT" if all_requests_succeeded and structural_errors == 0 else "PARTIAL_OR_STRUCTURAL_FAILURE",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": {
            "count": COUNT,
            "step": STEP,
            "owner_modes": list(MODES),
            "only_offsets": list(ONLY_OFFSETS),
            "include_form4_control_offsets": list(INCLUDE_FORM4_OFFSETS),
            "exclude_control_offsets": [0],
            "exact_form_token_filter": True,
            "owner_only_page0_rechecked": True,
            "live_requests": len(requests),
        },
        "all_requests_succeeded": all_requests_succeeded,
        "target_structural_errors": structural_errors,
        "requests": requests,
        "mode_results": results,
        "semantics": semantics,
        "controls": {
            "strict_pit_admitted": False,
            "exact_first_public_timestamp_verified": False,
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
    (output_dir / "phase307_sec_rss_owner_filter_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase307_output")
    args = parser.parse_args()
    result = run_audit(os.environ.get("SEC_CONTACT_EMAIL", ""), Path(args.output))
    print(json.dumps(result["semantics"], indent=2, sort_keys=True))
    print("PHASE307_STATUS=" + result["status"])
    return 0 if result["status"] == "PASS_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
