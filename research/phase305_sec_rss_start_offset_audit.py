#!/usr/bin/env python3
"""SEC Latest Filings RSS start-offset pagination and accession-boundary audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from research.phase303_sec_latest_filings_rss_probe import BASE, fetch, parse_atom
from research.phase304_sec_rss_count_cap_audit import analyze_feed_snapshot

OFFSETS = (0, 99, 100, 101, 200, 500, 1000)
COUNT = 100
FORMS = {"form4": "4", "form4a": "4/A"}


def exact_form_type(title: str) -> str:
    """Extract the complete form token before the spaced title separator.

    Examples: '4 - Issuer', '4/A - Owner', '40-APP/A - Filer',
    '424B5 - Issuer'. The SEC type=4 query is a prefix filter, so this
    exact token is required before counting Form 4 rows.
    """
    match = re.match(r"^\s*(.*?)\s+-\s+", title or "")
    return match.group(1).strip().upper() if match else ""


def row_key(entry: dict) -> tuple:
    return (
        entry.get("accession_from_link", ""),
        entry.get("entity_role_from_title", ""),
        entry.get("entity_cik_from_title", ""),
        entry.get("link", ""),
    )


def analyze_offset_pages(pages: list[dict]) -> dict:
    row_pages = defaultdict(set)
    accession_pages = defaultdict(set)
    page_summaries = []
    structural_errors = 0
    normalized_pages = []

    for page in sorted(pages, key=lambda x: x["start"]):
        # Correct the legacy Phase 303 numeric-prefix parser. Keep every raw
        # row, but only target the exact requested form in accession analysis.
        entries = []
        for original in page["entries"]:
            entry = dict(original)
            entry["form_type_from_title"] = exact_form_type(entry.get("title", ""))
            entries.append(entry)
        target_entries = [x for x in entries if x.get("form_type_from_title") == page["form_type"]]
        form_distribution = dict(sorted(Counter(x.get("form_type_from_title", "") or "UNPARSED" for x in entries).items()))
        analysis = analyze_feed_snapshot(target_entries, page["form_type"])
        structural_errors += sum(analysis[k] for k in (
            "orphan_entity_rows", "entry_id_link_accession_mismatches",
            "query_form_mismatches", "path_title_cik_mismatches",
            "duplicate_entity_rows", "accession_form_conflicts",
            "accession_updated_timestamp_conflicts",
        ))
        for entry in target_entries:
            accession = entry.get("accession_from_link", "")
            if not accession:
                continue
            row_pages[row_key(entry)].add(page["start"])
            accession_pages[accession].add(page["start"])
        normalized_pages.append({**page, "entries": entries, "target_entries": target_entries})
        page_summaries.append({
            "start": page["start"],
            "count": page["count"],
            "http_status": page["http_status"],
            "raw_entity_rows": len(entries),
            "target_entity_rows": len(target_entries),
            "non_target_entity_rows": len(entries) - len(target_entries),
            "form_type_distribution": form_distribution,
            "target_unique_accessions": analysis["unique_accessions"],
            "raw_sha256": page["raw_sha256"],
            "newest_target_feed_updated": analysis["newest_feed_updated"],
            "oldest_target_feed_updated": analysis["oldest_feed_updated"],
            "target_feed_updated_order_nonincreasing": analysis["feed_updated_order_nonincreasing"],
            "target_entity_rows_per_accession": analysis["entity_rows_per_accession"],
        })

    split_accessions = {
        accession: sorted(starts)
        for accession, starts in accession_pages.items()
        if len(starts) > 1
    }
    duplicate_entity_rows_across_pages = {
        str(key): sorted(starts)
        for key, starts in row_pages.items()
        if len(starts) > 1
    }
    page_by_start = {x["start"]: x for x in normalized_pages}
    boundary_checks = []
    for left, right in ((0, 100), (100, 200)):
        if left not in page_by_start or right not in page_by_start:
            continue
        left_acc = {x.get("accession_from_link", "") for x in page_by_start[left]["target_entries"] if x.get("accession_from_link")}
        right_acc = {x.get("accession_from_link", "") for x in page_by_start[right]["target_entries"] if x.get("accession_from_link")}
        boundary_checks.append({
            "left_start": left,
            "right_start": right,
            "shared_accessions": sorted(left_acc & right_acc),
            "accession_split_count": len(left_acc & right_acc),
        })

    row_offset_overlap_checks = []
    for left, right in ((0, 99), (99, 100), (100, 101)):
        if left not in page_by_start or right not in page_by_start:
            continue
        left_rows = {row_key(x) for x in page_by_start[left]["target_entries"]}
        right_rows = {row_key(x) for x in page_by_start[right]["target_entries"]}
        shared = len(left_rows & right_rows)
        expected = max(0, COUNT - abs(right - left))
        row_offset_overlap_checks.append({
            "left_start": left,
            "right_start": right,
            "shared_entity_rows": shared,
            "expected_if_start_is_entity_row_offset": expected,
            "matches_entity_row_offset_semantics": shared == expected,
        })

    page0 = page_by_start.get(0)
    offset_effective = False
    if page0:
        base_keys = {row_key(x) for x in page0["target_entries"]}
        for page in normalized_pages:
            if page["start"] == 0:
                continue
            keys = {row_key(x) for x in page["target_entries"]}
            if keys != base_keys:
                offset_effective = True
                break

    return {
        "pages": page_summaries,
        "page_count": len(normalized_pages),
        "successful_pages": sum(x["http_status"] == 200 for x in normalized_pages),
        "raw_entity_rows_union_not_deduplicated": sum(len(x["entries"]) for x in normalized_pages),
        "unique_accessions_union": len(accession_pages),
        "unique_entity_rows_union": len(row_pages),
        "offset_parameter_effective": offset_effective,
        "distinct_page_hashes": len({x["raw_sha256"] for x in normalized_pages}),
        "accessions_seen_on_multiple_pages": len(split_accessions),
        "accession_page_membership": split_accessions,
        "entity_rows_repeated_across_pages": len(duplicate_entity_rows_across_pages),
        "boundary_checks": boundary_checks,
        "row_offset_overlap_checks": row_offset_overlap_checks,
        "row_offset_semantics_supported": bool(row_offset_overlap_checks) and all(x["matches_entity_row_offset_semantics"] for x in row_offset_overlap_checks),
        "non_target_form_rows": sum(x["non_target_entity_rows"] for x in page_summaries),
        "non_target_form_types": sorted({
            form for page in page_summaries for form, count in page["form_type_distribution"].items()
            if form not in {page_by_start[page["start"]]["form_type"]} and count
        }),
        "structural_error_count": structural_errors,
    }

def run_audit(email: str, output_dir: Path) -> dict:
    if not email or "@" not in email or any(ch.isspace() for ch in email):
        raise ValueError("SEC_CONTACT_EMAIL_missing_or_invalid")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    form_results = {}
    total_requests = 0

    for label, form in FORMS.items():
        pages = []
        for start in OFFSETS:
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
                "start": start,
                "count": COUNT,
                "form_type": form,
                "requested_url": url,
                "poll_started_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "PENDING",
            }
            try:
                payload, headers = fetch(url, user_agent)
                entries = parse_atom(payload)
                raw_path = raw_dir / f"{label}_start{start}_count{COUNT}.atom"
                raw_path.write_bytes(payload)
                item.update({
                    "status": "ATOM_PARSED",
                    "poll_completed_at_utc": datetime.now(timezone.utc).isoformat(),
                    "http_status": headers["http_status"],
                    "response_headers": headers,
                    "raw_file": str(raw_path.relative_to(output_dir)),
                    "raw_sha256": hashlib.sha256(payload).hexdigest(),
                    "entries": entries,
                })
                pages.append(item)
            except (HTTPError, URLError, TimeoutError, ValueError, Exception) as exc:
                item.update({
                    "status": "QUERY_FAILED",
                    "poll_completed_at_utc": datetime.now(timezone.utc).isoformat(),
                    "http_status": getattr(exc, "code", None),
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:240],
                    "entries": [],
                    "raw_sha256": "",
                })
                pages.append(item)
            total_requests += 1
            time.sleep(1.1)

        analysis = analyze_offset_pages(pages)
        form_results[label] = {
            "form_type": form,
            "requests": [
                {k: v for k, v in page.items() if k != "entries"}
                | {"raw_entity_rows": len(page["entries"]), "unique_accessions": len({x.get("accession_from_link") for x in page["entries"] if x.get("accession_from_link")})}
                for page in pages
            ],
            "analysis": analysis,
        }

    all_success = all(
        all(x["status"] == "ATOM_PARSED" for x in result["requests"])
        for result in form_results.values()
    )
    structural_errors = sum(x["analysis"]["structural_error_count"] for x in form_results.values())
    result = {
        "phase": 305,
        "status": "PASS_OFFSET_AUDIT" if all_success and structural_errors == 0 else "PARTIAL_OR_STRUCTURAL_FAILURE",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_count_per_page": COUNT,
        "requested_start_offsets": list(OFFSETS),
        "total_requests": total_requests,
        "form_results": form_results,
        "summary": {
            "all_requests_succeeded": all_success,
            "structural_error_count": structural_errors,
            "form4_offset_effective": form_results["form4"]["analysis"]["offset_parameter_effective"],
            "form4a_offset_effective": form_results["form4a"]["analysis"]["offset_parameter_effective"],
            "form4_unique_accessions_union": form_results["form4"]["analysis"]["unique_accessions_union"],
            "form4_unique_entity_rows_union": form_results["form4"]["analysis"]["unique_entity_rows_union"],
            "form4a_unique_accessions_union": form_results["form4a"]["analysis"]["unique_accessions_union"],
            "form4a_unique_entity_rows_union": form_results["form4a"]["analysis"]["unique_entity_rows_union"],
            "form4_accession_boundary_splits": sum(x["accession_split_count"] for x in form_results["form4"]["analysis"]["boundary_checks"]),
            "form4_non_target_form_rows": form_results["form4"]["analysis"]["non_target_form_rows"],
            "form4_non_target_form_types": form_results["form4"]["analysis"]["non_target_form_types"],
            "form4_row_offset_semantics_supported": form_results["form4"]["analysis"]["row_offset_semantics_supported"],
            "form4_row_offset_overlap_checks": form_results["form4"]["analysis"]["row_offset_overlap_checks"],
            "form4a_accession_boundary_splits": sum(x["accession_split_count"] for x in form_results["form4a"]["analysis"]["boundary_checks"]),
            "form4a_non_target_form_rows": form_results["form4a"]["analysis"]["non_target_form_rows"],
        },
        "controls": {
            "exact_first_public_timestamp_verified": False,
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
        },
    }
    (output_dir / "phase305_rss_start_offset_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase305_output")
    args = parser.parse_args()
    result = run_audit(os.environ.get("SEC_CONTACT_EMAIL", ""), Path(args.output))
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    for label, item in result["form_results"].items():
        print(label, json.dumps({
            "offset_effective": item["analysis"]["offset_parameter_effective"],
            "pages": item["analysis"]["pages"],
            "boundary_checks": item["analysis"]["boundary_checks"],
            "unique_accessions_union": item["analysis"]["unique_accessions_union"],
            "unique_entity_rows_union": item["analysis"]["unique_entity_rows_union"],
        }, sort_keys=True))
    if result["status"] != "PASS_OFFSET_AUDIT":
        raise SystemExit(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
