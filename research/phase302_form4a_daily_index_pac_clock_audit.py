#!/usr/bin/env python3
"""Phase 302: live SEC daily-index and PAC/correction clock audit for 2023 Form 4/A.

The sample is inherited deterministically from Phase 301. This phase measures
only date-granular index sightings and SEC-HEADER acceptance chronology. It
does not infer exact first-public timestamps or admit strict PIT/alpha.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase283_sec_daily_index_parser as index_parser
import phase295_sec_form4_daily_index_pit_pilot as clock
import phase301_form4a_intermediate_validation as lineage

TARGET = "2023Q2"
ARCHIVE_HASHES = {
    "2022Q4": "6c6a909bd2eaaa0a24ccf5f0071b404670c115845d2939bc592bf3ce420dcdb9",
    "2023Q1": "0b476188f52a0862e71886eb31a81f6345fc6616403b52188484aef0438cfcfb",
    "2023Q2": "7e636787231ae0f00accf5c3627298402dedd1aefffd7c50fb48292e5d3a8fbb",
}
FEDERAL_HOLIDAYS = {
    "2022-10-10", "2022-11-11", "2022-11-24", "2022-12-26",
    "2023-01-02", "2023-01-16", "2023-02-20", "2023-05-29", "2023-06-19",
}
MAX_INDEX_FILES = 350
MAX_TOTAL_INDEX_BYTES = 500 * 1024 * 1024


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def is_business_day(day: date) -> bool:
    return day.weekday() < 5 and day.isoformat() not in FEDERAL_HOLIDAYS


def previous_business_day(day: date) -> date:
    cursor = day - timedelta(days=1)
    while not is_business_day(cursor):
        cursor -= timedelta(days=1)
    return cursor


def next_business_days(day: date, count: int) -> list[date]:
    found: list[date] = []
    cursor = day
    while len(found) < count:
        cursor += timedelta(days=1)
        if is_business_day(cursor):
            found.append(cursor)
    return found


def index_window_dates(filing_date: str, forward_business_days: int = 3) -> list[str]:
    """One prior business day, filing date, and next N business days.

    The prior date is a negative control. Filing date is retained even if it
    falls on a weekend/holiday; no date is substituted for a missing index.
    """
    filed = date.fromisoformat(filing_date)
    dates = {previous_business_day(filed), filed}
    dates.update(next_business_days(filed, forward_business_days))
    return [x.isoformat() for x in sorted(dates)]


def build_accession_clock(
    expected: dict[str, Any],
    sightings: list[dict[str, Any]],
    accession_quarantine: list[dict[str, Any]],
    window_complete: bool,
) -> dict[str, Any]:
    built = index_parser.build_accession_ledger(sightings)
    ledger = built["ledger"]
    if len(ledger) > 1:
        raise ValueError("accession_ledger_not_unique")
    row = ledger[0] if ledger else None
    issuer = str(int(expected["issuer_cik"]))
    identity_match = bool(
        row
        and row["form_type"] == expected["document_type"]
        and row["filing_date"] == expected["filing_date"]
        and any(entity["cik"] == issuer for entity in row["index_entities"])
    )
    first_date = row["first_daily_index_date"] if row else None
    lag = row["first_index_lag_days"] if row else None
    if row and identity_match and window_complete:
        status = "INDEX_IDENTITY_MATCH_WINDOW_COMPLETE"
    elif row and identity_match:
        status = "INDEX_IDENTITY_MATCH_WINDOW_INCOMPLETE"
    elif row:
        status = "INDEX_IDENTITY_MISMATCH"
    elif built["quarantine"]:
        status = "INDEX_LEDGER_CONFLICT"
    elif window_complete:
        status = "NO_MATCH_WINDOW_COMPLETE"
    else:
        status = "NO_MATCH_WINDOW_INCOMPLETE"
    return {
        "accession": expected["accession"],
        "document_type": expected["document_type"],
        "filing_date": expected["filing_date"],
        "index_window_dates": expected["index_window_dates"],
        "index_window_complete": window_complete,
        "index_status": status,
        "daily_index_identity_match": identity_match,
        "first_observed_index_date_within_window": first_date,
        "first_observed_index_lag_days": lag,
        "first_index_date_is_window_verified": bool(row and identity_match and window_complete),
        "same_filing_date_index_observed": bool(row and lag == 0),
        "later_index_date_observed": bool(row and lag is not None and lag > 0),
        "index_sighting_dates": row["all_daily_index_dates"] if row else [],
        "index_entity_count": row["index_entity_count"] if row else 0,
        "index_row_count": row["index_rows"] if row else 0,
        "pre_filing_negative_control_seen": any(
            q.get("reason") == "index_date_precedes_filing_date"
            for q in accession_quarantine
        ),
        "ledger_quarantine": built["quarantine"],
        "accession_quarantine": accession_quarantine,
    }


def pair_clock(parent: dict[str, Any] | None, child: dict[str, Any] | None) -> dict[str, Any]:
    if not parent or not child:
        return {"status": "PAIR_DOCUMENT_MISSING"}
    if not parent.get("header_reconciled") or not child.get("header_reconciled"):
        return {"status": "HEADER_INCOMPLETE"}
    if not parent.get("index_window_complete") or not child.get("index_window_complete"):
        return {"status": "INDEX_WINDOW_INCOMPLETE"}
    parent_date = parent.get("first_observed_index_date_within_window")
    child_date = child.get("first_observed_index_date_within_window")
    if not parent_date or not child_date:
        return {"status": "INDEX_SIGHTING_MISSING"}
    parent_acceptance = parent.get("acceptance_datetime_et")
    child_acceptance = child.get("acceptance_datetime_et")
    if not parent_acceptance or not child_acceptance:
        return {"status": "ACCEPTANCE_TIME_MISSING"}
    if datetime.fromisoformat(parent_acceptance) > datetime.fromisoformat(child_acceptance):
        return {"status": "ACCEPTANCE_ORDER_CONFLICT"}
    if child_date < parent_date:
        return {"status": "AMENDMENT_INDEX_PRECEDES_CANDIDATE_PARENT"}
    if child_date == parent_date:
        return {"status": "SAME_INDEX_DATE_INTRADAY_ORDER_UNRESOLVED"}
    return {"status": "PARENT_INDEX_DATE_PRECEDES_AMENDMENT"}


def make_sample(periods: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    classified = lineage.classify(periods)
    selected = [
        row for row in lineage.sample_cases(classified)
        if row["status"] in {"unique_owner_overlap", "ambiguous_multiple_owner_overlaps"}
    ]
    unique_count = sum(row["status"] == "unique_owner_overlap" for row in selected)
    ambiguous_count = sum(row["status"] == "ambiguous_multiple_owner_overlaps" for row in selected)
    if (unique_count, ambiguous_count) != (24, 8):
        raise ValueError(f"phase301_sample_drift:unique={unique_count}:ambiguous={ambiguous_count}")

    docs: dict[str, dict[str, Any]] = {}
    cases: list[dict[str, Any]] = []
    for i, row in enumerate(selected, 1):
        child = row["child"]
        docs[child["accession"]] = lineage.doc_record(child)
        if row["status"] == "unique_owner_overlap":
            parents = [row["parent"]]
        else:
            # Keep every candidate from the pinned Phase 301 sample; never
            # choose a winner from an ambiguous owner-overlap set.
            parents = list(row["owner_candidates"])
        for parent in parents:
            docs[parent["accession"]] = lineage.doc_record(parent)
        cases.append({
            "sample_id": f"P302-{i:03d}",
            "lineage_status": row["status"],
            "sample_reason": row["sample_reason"],
            "child_accession": child["accession"],
            "candidate_parent_accessions": [p["accession"] for p in parents],
            "candidate_parent_count": len(parents),
            "issuer_cik": child["issuer"],
            "original_submission_date": child["orig_date"],
        })
    return cases, [docs[key] for key in sorted(docs)]


def run_audit(email: str, output_dir: Path) -> dict[str, Any]:
    if not email or "@" not in email or any(ch.isspace() for ch in email):
        return {
            "phase": 302,
            "status": "BLOCKED_MISSING_SEC_CONTACT_EMAIL",
            "raw_sec_requests": 0,
            "strict_pit_admitted": False,
            "alpha_test": False,
            "holdout_used": False,
            "f80_frozen": True,
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_root = output_dir / "raw"
    archive_root = raw_root / "archives"
    submission_root = raw_root / "submissions"
    index_root = raw_root / "daily-index"
    for folder in (archive_root, submission_root, index_root):
        folder.mkdir(parents=True, exist_ok=True)

    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    periods_to_load = ("2022Q4", "2023Q1", "2023Q2")
    archive_paths = {p: archive_root / f"{p.lower()}_form345.zip" for p in periods_to_load}
    archive_meta: dict[str, dict[str, Any]] = {}
    for period in periods_to_load:
        archive_meta[period] = lineage.download_archive(period, archive_paths[period], user_agent)
        if archive_meta[period]["sha256"] != ARCHIVE_HASHES[period]:
            raise ValueError(f"archive_hash_mismatch:{period}")

    periods = lineage.load_periods(archive_paths)
    cases, documents = make_sample(periods)
    expected_by_accession = {x["accession"]: x for x in documents}
    windows = {
        x["accession"]: index_window_dates(x["filing_date"])
        for x in documents
    }
    for document in documents:
        document["index_window_dates"] = windows[document["accession"]]
    all_index_dates = sorted({day for values in windows.values() for day in values})
    if len(all_index_dates) > MAX_INDEX_FILES:
        raise ValueError(f"index_file_budget_exceeded:{len(all_index_dates)}")

    manifest = {
        "phase": 302,
        "target_period": TARGET,
        "loaded_periods": list(periods_to_load),
        "bulk_archive_sha256": {p: archive_meta[p]["sha256"] for p in periods_to_load},
        "sample_case_count": len(cases),
        "unique_lineage_cases": sum(x["lineage_status"] == "unique_owner_overlap" for x in cases),
        "ambiguous_lineage_cases": sum(x["lineage_status"] == "ambiguous_multiple_owner_overlaps" for x in cases),
        "document_count": len(documents),
        "sample_cases": cases,
        "documents": documents,
        "index_window_rule": "prior business day negative control + filing date + next three business days; no filing-date or acceptance-time fallback",
        "controls": {
            "strict_pit_admitted": False,
            "first_public_timestamp_verified": False,
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
    (output_dir / "phase302_sample_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    downloads: list[dict[str, Any]] = []
    submission_results: dict[str, dict[str, Any]] = {}
    for expected in documents:
        item: dict[str, Any] = {
            "accession": expected["accession"],
            "document_type": expected["document_type"],
            "filing_date": expected["filing_date"],
            "issuer_cik": expected["issuer_cik"],
            "downloaded": False,
            "header_reconciled": False,
        }
        try:
            dl = lineage.base.download_document(expected, submission_root, user_agent)
            downloads.append(dl)
            item["downloaded"] = bool(dl.get("downloaded"))
            if item["downloaded"]:
                raw_path = submission_root / f"{expected['accession'].replace('-', '')}.txt"
                payload = raw_path.read_bytes()
                item["raw_file"] = str(raw_path.relative_to(output_dir))
                item["bytes"] = len(payload)
                item["sha256"] = sha(payload)
                header = clock.parse_form4_submission_header(
                    payload, expected["accession"], expected["document_type"]
                )
                filed_expected = expected["filing_date"].replace("-", "")
                item["header_reconciled"] = header["FILED AS OF DATE"] == filed_expected
                item["acceptance_datetime_et"] = header["acceptance_datetime_et"]
                item["acceptance_datetime_utc"] = header["acceptance_datetime_utc"]
                item["acceptance_raw"] = header["ACCEPTANCE-DATETIME"]
                item["acceptance_date_matches_filed_date"] = header["acceptance_date_matches_filed_date"]
                item["acceptance_hour_et"] = int(header["ACCEPTANCE-DATETIME"][8:10])
                item["acceptance_after_1600_et"] = item["acceptance_hour_et"] >= 16
                item["acceptance_after_2200_et"] = item["acceptance_hour_et"] >= 22
                item["submission_header_status"] = "RECONCILED" if item["header_reconciled"] else "FILED_DATE_MISMATCH"
            else:
                item["submission_header_status"] = "DOWNLOAD_FAILED"
        except Exception as exc:
            item["submission_header_status"] = "PARSE_OR_DOWNLOAD_ERROR"
            item["error_code"] = type(exc).__name__ + ":" + str(exc)[:180]
        submission_results[expected["accession"]] = item
        time.sleep(0.2)

    targets = set(expected_by_accession)
    sightings: dict[str, list[dict[str, Any]]] = {acc: [] for acc in targets}
    accession_quarantine: dict[str, list[dict[str, Any]]] = {acc: [] for acc in targets}
    index_file_results: list[dict[str, Any]] = []
    total_index_bytes = 0
    budget_stopped = False

    for index_date in all_index_dates:
        item: dict[str, Any] = {
            "index_date": index_date,
            "url": clock.index_url(index_date),
            "status": "NOT_REQUESTED_BUDGET" if budget_stopped else "PENDING",
        }
        if budget_stopped:
            index_file_results.append(item)
            continue
        try:
            payload, headers = clock._fetch(item["url"], user_agent)
            if total_index_bytes + len(payload) > MAX_TOTAL_INDEX_BYTES:
                budget_stopped = True
                item["status"] = "TOTAL_BYTE_BUDGET_STOPPED"
                index_file_results.append(item)
                continue
            parsed = index_parser.parse_daily_form_index(
                payload, f"form.{date.fromisoformat(index_date):%Y%m%d}.idx"
            )
            raw_path = index_root / f"form.{date.fromisoformat(index_date):%Y%m%d}.idx"
            raw_path.write_bytes(payload)
            total_index_bytes += len(payload)
            target_rows = [r for r in parsed["records"] if r["accession"] in targets]
            for row in target_rows:
                if index_date in windows[row["accession"]]:
                    sightings[row["accession"]].append(row)
            for q in parsed["quarantine"]:
                if q.get("accession") in targets:
                    accession_quarantine[q["accession"]].append(q)
            item.update({
                "status": "DOWNLOADED_AND_PARSED",
                "raw_file": str(raw_path.relative_to(output_dir)),
                "bytes": len(payload),
                "sha256": sha(payload),
                "response_headers": headers,
                "form4_rows_seen": parsed["counts"]["form4_rows_seen"],
                "malformed_rows": parsed["counts"]["malformed_rows"],
                "quarantined_rows": len(parsed["quarantine"]),
                "target_accession_rows": len(target_rows),
            })
        except clock.RetrievalError as exc:
            item.update({"status": "HTTP_OR_RETRIEVAL_ERROR", "error_code": str(exc)})
        except Exception as exc:
            item.update({"status": "INDEX_PARSE_OR_WRITE_ERROR", "error_code": type(exc).__name__ + ":" + str(exc)[:180]})
        index_file_results.append(item)
        time.sleep(0.25)

    status_by_date = {x["index_date"]: x["status"] for x in index_file_results}
    accession_results: dict[str, dict[str, Any]] = {}
    for expected in documents:
        acc = expected["accession"]
        window_complete = all(status_by_date.get(day) == "DOWNLOADED_AND_PARSED" for day in windows[acc])
        idx = build_accession_clock(
            {**expected, "index_window_dates": windows[acc]},
            sightings[acc],
            accession_quarantine[acc],
            window_complete,
        )
        accession_results[acc] = {**submission_results[acc], **idx}

    case_results: list[dict[str, Any]] = []
    for case in cases:
        child = accession_results.get(case["child_accession"])
        if case["lineage_status"] == "unique_owner_overlap":
            parent_acc = case["candidate_parent_accessions"][0]
            parent = accession_results.get(parent_acc)
            comparison = pair_clock(parent, child)
            case_results.append({
                **case,
                "assigned_parent_accession": parent_acc,
                "pair_clock": comparison,
            })
        else:
            candidate_clocks = [
                {
                    "accession": acc,
                    "index_status": accession_results.get(acc, {}).get("index_status"),
                    "first_observed_index_date": accession_results.get(acc, {}).get("first_observed_index_date_within_window"),
                    "acceptance_datetime_et": accession_results.get(acc, {}).get("acceptance_datetime_et"),
                }
                for acc in case["candidate_parent_accessions"]
            ]
            case_results.append({
                **case,
                "assigned_parent_accession": None,
                "pair_clock": {"status": "AMBIGUOUS_PARENT_SET_NOT_ASSIGNED"},
                "candidate_parent_clocks": candidate_clocks,
            })

    pair_status_counts = Counter(
        row["pair_clock"]["status"]
        for row in case_results if row["lineage_status"] == "unique_owner_overlap"
    )
    doc_rows = list(accession_results.values())
    observed = [x for x in doc_rows if x.get("first_observed_index_date_within_window")]
    verified = [x for x in doc_rows if x.get("first_index_date_is_window_verified")]
    lags = [int(x["first_observed_index_lag_days"]) for x in verified if x.get("first_observed_index_lag_days") is not None]
    downloaded_index = sum(x["status"] == "DOWNLOADED_AND_PARSED" for x in index_file_results)
    index_errors = sum(x["status"] == "HTTP_OR_RETRIEVAL_ERROR" for x in index_file_results)
    index_parse_errors = sum(x["status"] == "INDEX_PARSE_OR_WRITE_ERROR" for x in index_file_results)
    header_pass = sum(x.get("header_reconciled") is True for x in doc_rows)
    summary = {
        "sample_cases": len(cases),
        "unique_lineage_cases": sum(x["lineage_status"] == "unique_owner_overlap" for x in cases),
        "ambiguous_lineage_cases": sum(x["lineage_status"] == "ambiguous_multiple_owner_overlaps" for x in cases),
        "sample_documents": len(documents),
        "submission_downloaded": sum(x.get("downloaded") is True for x in doc_rows),
        "submission_header_reconciled": header_pass,
        "index_files_expected": len(all_index_dates),
        "index_files_downloaded": downloaded_index,
        "index_file_http_or_retrieval_errors": index_errors,
        "index_file_parse_or_write_errors": index_parse_errors,
        "index_total_bytes": total_index_bytes,
        "accessions_with_observed_index": len(observed),
        "accessions_with_window_verified_index": len(verified),
        "accessions_without_observed_index": len(doc_rows) - len(observed),
        "same_filing_date_index_observed": sum(x.get("same_filing_date_index_observed") is True for x in doc_rows),
        "later_index_date_observed": sum(x.get("later_index_date_observed") is True for x in doc_rows),
        "pre_filing_negative_control_seen": sum(x.get("pre_filing_negative_control_seen") is True for x in doc_rows),
        "acceptance_after_1600_et": sum(x.get("acceptance_after_1600_et") is True for x in doc_rows),
        "acceptance_after_2200_et": sum(x.get("acceptance_after_2200_et") is True for x in doc_rows),
        "verified_index_lag_days": {
            "n": len(lags),
            "min": min(lags) if lags else None,
            "median": sorted(lags)[len(lags) // 2] if lags else None,
            "max": max(lags) if lags else None,
            "counts": {str(k): lags.count(k) for k in sorted(set(lags))},
        },
        "unique_pair_clock_status_counts": dict(sorted(pair_status_counts.items())),
        "ambiguous_parent_assignments": 0,
    }
    submissions_complete = (
        summary["submission_downloaded"] == summary["sample_documents"]
        and summary["submission_header_reconciled"] == summary["sample_documents"]
    )
    parser_clean = index_parse_errors == 0
    result = {
        "phase": 302,
        "status": (
            "COMPLETED_2023_FORM4A_DAILY_INDEX_PAC_CLOCK_AUDIT"
            if submissions_complete and parser_clean
            else "PARTIAL_2023_FORM4A_DAILY_INDEX_PAC_CLOCK_AUDIT"
        ),
        "audit_as_of_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source": "SEC EDGAR Form 345 quarterly archives, complete-submission text and historical daily form indexes",
        "archive_metadata": archive_meta,
        "index_file_results": index_file_results,
        "accessions": doc_rows,
        "cases": case_results,
        "summary": summary,
        "limitations": [
            "Daily index records are date-granular and do not provide exact first-public timestamps.",
            "A first observed date is window-verified only when every requested date in that accession window was successfully retrieved and parsed.",
            "A same-index-date original/amendment pair cannot be ordered intraday from the daily index, even when SEC acceptance timestamps are ordered.",
            "SEC-HEADER acceptance time is not itself exact first-public receipt.",
            "The sample is purposive/stratified and is not a prevalence estimate.",
            "Unique parent candidates remain metadata-corroborated, not authoritative accession foreign-key links.",
            "Ambiguous parent candidates are preserved without choosing a winner.",
            "No return, alpha, bootstrap/LOO, chronological OOS or holdout test is performed.",
        ],
        "controls": {
            "strict_pit_admitted": False,
            "first_public_timestamp_verified": False,
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
            "data_purchase": False,
            "vendor_contact": False,
        },
        "decision": (
            "Treat a complete-window earliest daily-index date as a conservative date-granular "
            "knowledge bound only. Do not use acceptance time or filing date as a fallback. "
            "Same-index-date original/amendment pairs remain intraday-unordered. Strict PIT and "
            "alpha remain closed pending broader historical coverage, effective-dated security "
            "identity and owner/transaction attribution."
        ),
    }
    (output_dir / "phase302_validation_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"phase": 302, "status": result["status"], "summary": summary, "controls": result["controls"]}, indent=2), flush=True)
    return 0 if submissions_complete and parser_clean else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--contact-email", required=True)
    args = parser.parse_args()
    return run_audit(args.contact_email.strip(), args.output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
