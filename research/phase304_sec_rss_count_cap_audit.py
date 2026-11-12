#!/usr/bin/env python3
"""SEC Latest Filings RSS count-cap and accession-grain coverage audit.

This is a one-time source-capacity audit. It does not infer exact first-public
availability, strict PIT, insider intent, or alpha.
"""
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
from urllib.request import Request, urlopen

from research.phase303_sec_latest_filings_rss_probe import (
    BASE, HOST, MAX_BYTES, accession_from_url, feed_updated_matches_acceptance,
    fetch, parse_acceptance_datetime, parse_atom,
)

COUNTS = (100, 200, 500, 1000)
FORMS = {"form4": "4", "form4a": "4/A"}


def accession_from_entry_id(value: str) -> str:
    match = re.search(r"accession-number=(\d{10}-\d{2}-\d{6})", value or "", re.I)
    if match:
        return match.group(1)
    return accession_from_url(value or "")


def analyze_feed_snapshot(entries: list[dict], expected_form: str) -> dict:
    grouped = defaultdict(list)
    orphan_rows = 0
    entry_id_link_mismatches = 0
    form_mismatches = 0
    path_title_cik_mismatches = 0
    for entry in entries:
        accession = entry.get("accession_from_link", "")
        if not accession:
            orphan_rows += 1
            continue
        if accession_from_entry_id(entry.get("entry_id", "")) != accession:
            entry_id_link_mismatches += 1
        if entry.get("form_type_from_title") != expected_form:
            form_mismatches += 1
        if not entry.get("path_cik_matches_title_entity", False):
            path_title_cik_mismatches += 1
        grouped[accession].append(entry)

    ledger = []
    duplicate_entity_rows = 0
    form_conflicts = 0
    updated_conflicts = 0
    for accession, rows in sorted(grouped.items()):
        forms = sorted({x.get("form_type_from_title", "") for x in rows})
        updated = sorted({x.get("feed_updated_raw", "") for x in rows if x.get("feed_updated_raw")})
        roles = sorted({x.get("entity_role_from_title", "") for x in rows if x.get("entity_role_from_title")})
        issuer_ciks = sorted({x.get("entity_cik_from_title", "") for x in rows if x.get("entity_role_from_title") == "Issuer"})
        reporting_ciks = sorted({x.get("entity_cik_from_title", "") for x in rows if x.get("entity_role_from_title") == "Reporting"})
        row_keys = [
            (x.get("entity_role_from_title", ""), x.get("entity_cik_from_title", ""), x.get("link", ""))
            for x in rows
        ]
        duplicate_entity_rows += len(row_keys) - len(set(row_keys))
        form_conflicts += int(len(forms) != 1)
        updated_conflicts += int(len(updated) > 1)
        ledger.append({
            "accession": accession,
            "entity_row_count": len(rows),
            "roles": roles,
            "issuer_ciks": issuer_ciks,
            "reporting_ciks": reporting_ciks,
            "form_types": forms,
            "feed_updated_values": updated,
            "duplicate_entity_rows": len(row_keys) - len(set(row_keys)),
        })

    timestamps = []
    for entry in entries:
        raw = entry.get("feed_updated_raw", "")
        if raw:
            try:
                timestamps.append(datetime.fromisoformat(raw))
            except ValueError:
                pass
    ordered = timestamps == sorted(timestamps, reverse=True)
    return {
        "expected_form": expected_form,
        "raw_entity_rows": len(entries),
        "unique_accessions": len(grouped),
        "orphan_entity_rows": orphan_rows,
        "entry_id_link_accession_mismatches": entry_id_link_mismatches,
        "query_form_mismatches": form_mismatches,
        "path_title_cik_mismatches": path_title_cik_mismatches,
        "duplicate_entity_rows": duplicate_entity_rows,
        "accession_form_conflicts": form_conflicts,
        "accession_updated_timestamp_conflicts": updated_conflicts,
        "entity_rows_per_accession": {str(k): v for k, v in sorted(Counter(len(v) for v in grouped.values()).items())},
        "accessions_with_issuer_and_reporting": sum(bool(x["issuer_ciks"]) and bool(x["reporting_ciks"]) for x in ledger),
        "feed_updated_order_nonincreasing": ordered,
        "oldest_feed_updated": min((x.isoformat() for x in timestamps), default=None),
        "newest_feed_updated": max((x.isoformat() for x in timestamps), default=None),
        "accession_ledger": ledger,
    }


def compare_snapshot_counts(snapshots: list[dict]) -> dict:
    ordered = sorted(snapshots, key=lambda x: x["requested_count"])
    comparisons = []
    for left, right in zip(ordered, ordered[1:]):
        a = set(left.get("accessions", []))
        b = set(right.get("accessions", []))
        comparisons.append({
            "smaller_count": left["requested_count"],
            "larger_count": right["requested_count"],
            "smaller_accessions": len(a),
            "larger_accessions": len(b),
            "smaller_set_subset_of_larger": a.issubset(b),
            "missing_from_larger": sorted(a - b),
        })
    return {
        "comparisons": comparisons,
        "nested_accession_sets": all(x["smaller_set_subset_of_larger"] for x in comparisons),
    }


def _capture_complete_submission(form_label: str, accession: str, rows: list[dict], user_agent: str, raw_dir: Path) -> dict:
    issuer = next((x for x in rows if x.get("entity_role_from_title") == "Issuer"), None)
    if issuer is None or not issuer.get("path_cik_from_link"):
        return {"form_label": form_label, "accession": accession, "status": "NO_ISSUER_PATH"}
    compact = accession.replace("-", "")
    issuer_cik = str(int(issuer["path_cik_from_link"]))
    url = f"https://www.sec.gov/Archives/edgar/data/{issuer_cik}/{compact}/{accession}.txt"
    item = {"form_label": form_label, "accession": accession, "url": url, "status": "PENDING"}
    try:
        payload, headers = fetch(url, user_agent)
        acceptance = parse_acceptance_datetime(payload)
        raw_path = raw_dir / f"submission_{form_label}_{compact}.txt"
        raw_path.write_bytes(payload)
        updated_values = sorted({x.get("feed_updated_raw", "") for x in rows if x.get("feed_updated_raw")})
        item.update({
            "status": "HEADER_PARSED" if acceptance else "ACCEPTANCE_HEADER_MISSING",
            "acceptance_datetime_et": acceptance,
            "feed_updated_values": updated_values,
            "feed_updated_equals_acceptance": any(feed_updated_matches_acceptance(x, acceptance) for x in updated_values),
            "response_headers": headers,
            "raw_file": str(raw_path.name),
            "complete_submission_sha256": hashlib.sha256(payload).hexdigest(),
        })
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        item.update({"status": "DOWNLOAD_FAILED", "error_type": type(exc).__name__, "error": str(exc)[:240]})
    return item


def run_audit(email: str, output_dir: Path) -> dict:
    if not email or "@" not in email or any(ch.isspace() for ch in email):
        raise ValueError("SEC_CONTACT_EMAIL_missing_or_invalid")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    all_results = []
    selected_by_form = {}
    for label, form in FORMS.items():
        snapshots = []
        for count in COUNTS:
            params = {"action": "getcurrent", "type": form, "owner": "include", "count": str(count), "output": "atom"}
            url = BASE + "?" + urlencode(params)
            started = datetime.now(timezone.utc)
            item = {
                "query_label": label,
                "form_type": form,
                "requested_count": count,
                "poll_started_at_utc": started.isoformat(),
                "requested_url": url,
                "status": "PENDING",
            }
            try:
                payload, headers = fetch(url, user_agent)
                completed = datetime.now(timezone.utc)
                entries = parse_atom(payload)
                raw_path = raw_dir / f"{label}_count{count}.atom"
                raw_path.write_bytes(payload)
                analysis = analyze_feed_snapshot(entries, form)
                item.update({
                    "status": "ATOM_PARSED",
                    "poll_completed_at_utc": completed.isoformat(),
                    "response_headers": headers,
                    "raw_file": str(raw_path.relative_to(output_dir)),
                    "raw_sha256": hashlib.sha256(payload).hexdigest(),
                    "analysis": {k: v for k, v in analysis.items() if k != "accession_ledger"},
                    "accessions": [x["accession"] for x in analysis["accession_ledger"]],
                })
                snapshots.append({
                    "requested_count": count,
                    "accessions": item["accessions"],
                    "analysis": analysis,
                    "entries": entries,
                })
            except (HTTPError, URLError, TimeoutError, ValueError, Exception) as exc:
                item.update({
                    "status": "QUERY_FAILED",
                    "poll_completed_at_utc": datetime.now(timezone.utc).isoformat(),
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:240],
                })
                # A rejected larger request is recorded; do not hammer higher limits.
                all_results.append(item)
                break
            all_results.append(item)
            time.sleep(1.1)
        selected_by_form[label] = snapshots

    crosschecks = []
    for label, snapshots in selected_by_form.items():
        if not snapshots:
            continue
        largest = max(snapshots, key=lambda x: x["requested_count"])
        entries_by_accession = defaultdict(list)
        for entry in largest["entries"]:
            if entry.get("accession_from_link"):
                entries_by_accession[entry["accession_from_link"]].append(entry)
        ranked = []
        for accession, rows in entries_by_accession.items():
            values = [datetime.fromisoformat(x["feed_updated_raw"]) for x in rows if x.get("feed_updated_raw")]
            if values:
                ranked.append((max(values), accession, rows))
        if not ranked:
            continue
        ranked.sort(key=lambda x: x[0])
        chosen = [ranked[0], ranked[-1]] if len(ranked) > 1 else [ranked[0]]
        for _, accession, rows in chosen:
            crosschecks.append(_capture_complete_submission(label, accession, rows, user_agent, raw_dir))
            time.sleep(1.1)

    form_summaries = {}
    for label, snapshots in selected_by_form.items():
        comparisons = compare_snapshot_counts([
            {"requested_count": x["requested_count"], "accessions": [z["accession"] for z in x["analysis"]["accession_ledger"]]}
            for x in snapshots
        ])
        largest = max(snapshots, key=lambda x: x["requested_count"]) if snapshots else None
        form_summaries[label] = {
            "successful_count_requests": [x["requested_count"] for x in snapshots],
            "raw_entity_rows_by_count": {str(x["requested_count"]): x["analysis"]["raw_entity_rows"] for x in snapshots},
            "unique_accessions_by_count": {str(x["requested_count"]): x["analysis"]["unique_accessions"] for x in snapshots},
            "nested_accession_sets": comparisons["nested_accession_sets"],
            "count_growth_comparisons": comparisons["comparisons"],
            "largest_successful_request": largest["requested_count"] if largest else None,
            "largest_successful_entity_rows": largest["analysis"]["raw_entity_rows"] if largest else None,
            "largest_successful_unique_accessions": largest["analysis"]["unique_accessions"] if largest else None,
            "largest_snapshot_analysis": {k: v for k, v in largest["analysis"].items() if k != "accession_ledger"} if largest else None,
            "accession_ledger": largest["analysis"]["accession_ledger"] if largest else [],
        }

    successful = [x for x in all_results if x["status"] == "ATOM_PARSED"]
    structural_errors = sum(
        x["analysis"][key]
        for x in successful
        for key in (
            "orphan_entity_rows", "entry_id_link_accession_mismatches",
            "query_form_mismatches", "path_title_cik_mismatches",
            "duplicate_entity_rows", "accession_form_conflicts",
            "accession_updated_timestamp_conflicts",
        )
    )
    base_forms_ok = all(
        any(x["status"] == "ATOM_PARSED" and x["query_label"] == label and x["requested_count"] == 100 for x in all_results)
        for label in FORMS
    )
    crosscheck_success = sum(x.get("status") == "HEADER_PARSED" for x in crosschecks)
    result = {
        "phase": 304,
        "status": "PASS_COUNT_CAP_AUDIT" if base_forms_ok and structural_errors == 0 else "PARTIAL_OR_STRUCTURAL_FAILURE",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "queries": all_results,
        "form_summaries": form_summaries,
        "complete_submission_crosschecks": crosschecks,
        "summary": {
            "requested_counts": list(COUNTS),
            "successful_atom_requests": len(successful),
            "query_failures": len(all_results) - len(successful),
            "structural_error_count": structural_errors,
            "base_100_request_passed_for_both_forms": base_forms_ok,
            "complete_submission_header_crosschecks": crosscheck_success,
            "feed_updated_equals_acceptance_crosschecks": sum(x.get("feed_updated_equals_acceptance") is True for x in crosschecks),
        },
        "controls": {
            "count_cap_and_accession_grain_only": True,
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
        },
    }
    (output_dir / "phase304_rss_count_cap_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase304_output")
    args = parser.parse_args()
    result = run_audit(os.environ.get("SEC_CONTACT_EMAIL", ""), Path(args.output))
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    for label, summary in result["form_summaries"].items():
        print(label, json.dumps({
            "successful_count_requests": summary["successful_count_requests"],
            "raw_entity_rows_by_count": summary["raw_entity_rows_by_count"],
            "unique_accessions_by_count": summary["unique_accessions_by_count"],
            "largest_successful_request": summary["largest_successful_request"],
            "nested_accession_sets": summary["nested_accession_sets"],
        }, sort_keys=True))
    if result["status"] != "PASS_COUNT_CAP_AUDIT":
        raise SystemExit(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
