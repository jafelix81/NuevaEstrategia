#!/usr/bin/env python3
"""SEC Latest Filings RSS start-offset pagination and accession-boundary audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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
    accession_rows_by_page = defaultdict(lambda: defaultdict(list))
    page_summaries = []
    structural_errors = 0
    for page in sorted(pages, key=lambda x: x["start"]):
        analysis = analyze_feed_snapshot(page["entries"], page["form_type"])
        structural_errors += sum(analysis[k] for k in (
            "orphan_entity_rows", "entry_id_link_accession_mismatches",
            "query_form_mismatches", "path_title_cik_mismatches",
            "duplicate_entity_rows", "accession_form_conflicts",
            "accession_updated_timestamp_conflicts",
        ))
        for entry in page["entries"]:
            accession = entry.get("accession_from_link", "")
            if not accession:
                continue
            row_pages[row_key(entry)].add(page["start"])
            accession_pages[accession].add(page["start"])
            accession_rows_by_page[page["start"]][accession].append(entry)
        page_summaries.append({
            "start": page["start"],
            "count": page["count"],
            "http_status": page["http_status"],
            "raw_entity_rows": len(page["entries"]),
            "unique_accessions": analysis["unique_accessions"],
            "raw_sha256": page["raw_sha256"],
            "newest_feed_updated": analysis["newest_feed_updated"],
            "oldest_feed_updated": analysis["oldest_feed_updated"],
            "feed_updated_order_nonincreasing": analysis["feed_updated_order_nonincreasing"],
            "entity_rows_per_accession": analysis["entity_rows_per_accession"],
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
    page_by_start = {x["start"]: x for x in pages}
    boundary_checks = []
    for left, right in ((0, 100), (100, 200)):
        if left not in page_by_start or right not in page_by_start:
            continue
        left_acc = {x.get("accession_from_link", "") for x in page_by_start[left]["entries"] if x.get("accession_from_link")}
        right_acc = {x.get("accession_from_link", "") for x in page_by_start[right]["entries"] if x.get("accession_from_link")}
        boundary_checks.append({
            "left_start": left,
            "right_start": right,
            "shared_accessions": sorted(left_acc & right_acc),
            "accession_split_count": len(left_acc & right_acc),
        })

    page0 = page_by_start.get(0)
    offset_effective = False
    if page0:
        base_keys = {row_key(x) for x in page0["entries"]}
        for page in pages:
            if page["start"] == 0:
                continue
            keys = {row_key(x) for x in page["entries"]}
            if keys != base_keys:
                offset_effective = True
                break

    return {
        "pages": page_summaries,
        "page_count": len(pages),
        "successful_pages": sum(x["http_status"] == 200 for x in pages),
        "unique_accessions_union": len(accession_pages),
        "unique_entity_rows_union": len(row_pages),
        "offset_parameter_effective": offset_effective,
        "distinct_page_hashes": len({x["raw_sha256"] for x in pages}),
        "accessions_seen_on_multiple_pages": len(split_accessions),
        "accession_page_membership": split_accessions,
        "entity_rows_repeated_across_pages": len(duplicate_entity_rows_across_pages),
        "boundary_checks": boundary_checks,
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
            "form4a_accession_boundary_splits": sum(x["accession_split_count"] for x in form_results["form4a"]["analysis"]["boundary_checks"]),
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
