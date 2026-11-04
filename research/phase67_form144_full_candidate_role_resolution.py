#!/usr/bin/env python3
"""Resolve every current-CIK candidate Form 144/144-A accession to XML issuer/filer roles.

This is an identity/event-data assembly gate only. It does not calculate returns.
The current CIK map is a candidate set, not a point-in-time F80 security master.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from research.phase50_form144_global_index_pilot import (
    current_cik_candidates, fetch_bytes, load_universe, parse_master_index,
)
from research.phase64_form144_master_pair_cross_quarter_audit import (
    build_pair_rows, classify_xml_identity, parse_quarter,
)
from research.phase65_form144_event_field_coverage_audit import (
    extract_acquisition_lots, extract_prior_sales, extract_sale_tranches,
    fetch_and_parse, normalize_accession,
)

DEFAULT_QUARTERS = (
    "2023Q2,2023Q3,2023Q4,2024Q1,2024Q2,2024Q3,2024Q4,"
    "2025Q1,2025Q2,2025Q3,2025Q4,2026Q1,2026Q2,2026Q3"
)
START_DATE = "2023-04-13"
FORMS = ("144", "144/A")
OUT_DIR = Path("phase67_form144_full_candidate_resolution")


def stable_key(row):
    token = "{}:{}:{}:{}".format(
        row.get("year"), row.get("quarter"), row.get("form"), row.get("accession")
    )
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def index_row_invalid(row):
    # parse_master_index sets metadata_conflict when archive paths differ too.
    # Multiple archive-path CIKs are expected for this two-entity master-index design;
    # only unresolved form/date metadata prevents XML role resolution.
    return row.get("form") not in FORMS or not row.get("filing_date")


def classify_candidate_identity(pair_class, candidate_ciks, identity, metadata_conflict=False):
    """Return an explicit issuer/filer/unresolved classification; never infer issuer from filer."""
    candidates = set(candidate_ciks or [])
    issuer = str(identity.get("xml_issuer_cik") or "")
    filer = str(identity.get("xml_filer_cik") or "")
    both = bool(identity.get("both_xml_ciks_in_pair"))
    distinct = bool(identity.get("xml_ciks_distinct"))
    form_ok = bool(identity.get("xml_form_matches_index"))

    base = {
        "candidate_is_issuer": bool(issuer and issuer in candidates),
        "candidate_is_filer": bool(filer and filer in candidates),
        "xml_issuer_cik": issuer,
        "xml_filer_cik": filer,
        "xml_both_ciks_in_master_pair": both,
        "xml_ciks_distinct": distinct,
        "xml_form_matches_index": form_ok,
    }
    if metadata_conflict or not both or not distinct or not form_ok:
        return {**base, "candidate_role_status": "unresolved_identity_or_index_mismatch",
                "role_resolved": False, "include_as_issuer_event": False}
    if pair_class == "unique_candidate":
        candidate = next(iter(candidates), "")
        if candidate and candidate == issuer:
            status = "issuer_match"
            include = True
        elif candidate and candidate == filer:
            status = "filer_only_false_positive"
            include = False
        else:
            status = "unresolved_candidate_not_in_xml_roles"
            include = False
        return {**base, "candidate_role_status": status, "role_resolved": status in
                ("issuer_match", "filer_only_false_positive"),
                "include_as_issuer_event": include}
    if pair_class == "ambiguous":
        if issuer and issuer in candidates:
            status = "ambiguous_pair_issuer_match"
            include = True
            resolved = True
        elif filer and filer in candidates:
            status = "ambiguous_pair_filer_only_false_positive"
            include = False
            resolved = True
        else:
            status = "ambiguous_pair_unresolved"
            include = False
            resolved = False
        return {**base, "candidate_role_status": status, "role_resolved": resolved,
                "include_as_issuer_event": include}
    return {**base, "candidate_role_status": "unresolved_unknown_pair_class",
            "role_resolved": False, "include_as_issuer_event": False}


def classify_control(identity, metadata_conflict=False):
    ok = (
        not metadata_conflict
        and bool(identity.get("both_xml_ciks_in_pair"))
        and bool(identity.get("xml_ciks_distinct"))
        and bool(identity.get("xml_form_matches_index"))
    )
    return "control_pair_concordant" if ok else "control_pair_mismatch"


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fields = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_quarter_data(tokens, candidate_ciks, cik_to_tickers):
    quarter_data = []
    all_accessions = set()
    for token in tokens:
        year, quarter = parse_quarter(token)
        url = "https://www.sec.gov/Archives/edgar/full-index/{}/QTR{}/master.idx".format(year, quarter)
        index_rows = parse_master_index(fetch_bytes(url, sec=True, timeout=90, retries=5))
        index_rows = [
            row for row in index_rows
            if row.get("filing_date") and row["filing_date"] >= START_DATE
            and (row.get("form") in FORMS or row.get("metadata_conflict"))
        ]
        pair_rows = build_pair_rows(index_rows, candidate_ciks, cik_to_tickers, year, quarter)
        all_accessions.update(row["accession"] for row in pair_rows if row.get("accession"))
        candidates = [
            row for row in pair_rows
            if row["pair_class"] in ("unique_candidate", "ambiguous")
        ]
        controls = []
        for form in FORMS:
            pool = [row for row in pair_rows
                    if row["pair_class"] == "control" and row.get("form") == form
                    and not index_row_invalid(row)]
            for row in sorted(pool, key=stable_key)[:10]:
                controls.append(dict(row))
        quarter_data.append({
            "token": token, "year": year, "quarter": quarter,
            "pair_rows": pair_rows, "candidates": candidates, "controls": controls,
            "index_accessions": len(pair_rows),
        })
        print(json.dumps({
            "stage": "INDEX_COMPLETE", "quarter": token,
            "index_accessions": len(pair_rows),
            "candidate_accessions": len(candidates),
            "controls_selected": len(controls),
        }, sort_keys=True), flush=True)
    return quarter_data, all_accessions


def process_row(row, all_accessions, is_control=False):
    base = {
        "quarter": "{}Q{}".format(row.get("year"), row.get("quarter")),
        "accession": row.get("accession", ""),
        "form": row.get("form") or "",
        "filing_date": row.get("filing_date") or "",
        "master_index_ciks": ";".join(row.get("master_index_ciks") or []),
        "candidate_ciks_in_pair": ";".join(row.get("candidate_ciks_in_pair") or []),
        "candidate_tickers": ";".join(row.get("candidate_tickers") or []),
        "pair_class": row.get("pair_class") or "",
        "parser_metadata_conflict_flag": bool(row.get("metadata_conflict")),
        "archive_path_cik_conflict": bool(row.get("archive_path_cik_conflict")),
        "index_metadata_invalid": index_row_invalid(row),
    }
    index_invalid = index_row_invalid(row)
    if index_invalid:
        status = "control_index_metadata_invalid" if is_control else "unresolved_index_metadata_invalid"
        return {"row": {**base, "candidate_role_status": status, "role_resolved": False},
                "event": None, "error": None, "control": is_control}
    parsed, root, xml_url, error = fetch_and_parse(row)
    if parsed is None or root is None:
        status = "control_xml_fetch_error" if is_control else "unresolved_xml_fetch_error"
        return {"row": {**base, "xml_url": xml_url or "", "candidate_role_status": status,
                        "role_resolved": False},
                "event": None,
                "error": {**base, "error": error or "XML_PARSE_FAILED"},
                "control": is_control}

    identity = classify_xml_identity(row, parsed)
    if is_control:
        status = classify_control(identity, index_invalid)
        return {"row": {**base, "xml_url": xml_url or "",
                        "xml_issuer_cik": identity["xml_issuer_cik"],
                        "xml_filer_cik": identity["xml_filer_cik"],
                        "xml_both_ciks_in_master_pair": identity["both_xml_ciks_in_pair"],
                        "xml_ciks_distinct": identity["xml_ciks_distinct"],
                        "xml_form_matches_index": identity["xml_form_matches_index"],
                        "candidate_role_status": status,
                        "role_resolved": status == "control_pair_concordant"},
                "event": None, "error": None, "control": True}

    role = classify_candidate_identity(
        row.get("pair_class"), row.get("candidate_ciks_in_pair") or [],
        identity, index_invalid
    )
    result = {
        **base, "xml_url": xml_url or "",
        **role,
        "issuer_name": parsed.get("issuer_name") or "",
        "seller_name": parsed.get("seller_name") or "",
        "relationships": ";".join(parsed.get("relationships") or []),
        "previous_accession": parsed.get("previous_accession") or "",
        "previous_accession_normalized": normalize_accession(parsed.get("previous_accession")) or "",
        "previous_accession_in_14q_census": bool(
            normalize_accession(parsed.get("previous_accession"))
            and normalize_accession(parsed.get("previous_accession")) in all_accessions
        ),
        "notice_date": parsed.get("notice_date") or "",
        "mentions_10b5_1": bool(parsed.get("mentions_10b5_1")),
        "plan_adoption_dates": ";".join(parsed.get("plan_adoption_dates") or []),
    }
    if not role["include_as_issuer_event"]:
        return {"row": result, "event": None, "error": None, "control": False}

    sale = extract_sale_tranches(root)
    acquisitions = extract_acquisition_lots(root)
    past_sales = extract_prior_sales(root)
    units = [x.get("units_numeric") for x in sale]
    values = [x.get("value_numeric") for x in sale]
    outstanding = [x.get("outstanding_numeric") for x in sale]
    units_total = sum(units) if units and all(x is not None for x in units) else None
    value_total = sum(values) if values and all(x is not None for x in values) else None
    event = {
        **result,
        "sale_tranche_count": len(sale),
        "sale_units_total": units_total,
        "sale_value_total": value_total,
        "sale_units_all_numeric": bool(sale) and all(x is not None for x in units),
        "sale_value_all_numeric": bool(sale) and all(x is not None for x in values),
        "sale_outstanding_all_numeric": bool(sale) and all(x is not None for x in outstanding),
        "sale_tranches_json": json.dumps(sale, sort_keys=True),
        "acquisition_lot_count": len(acquisitions),
        "acquisition_lots_json": json.dumps(acquisitions, sort_keys=True),
        "past_sales_count": len(past_sales),
        "past_sales_json": json.dumps(past_sales, sort_keys=True),
    }
    return {"row": result, "event": event, "error": None, "control": False}


def summarize(rows, events, errors, controls, index_summaries, candidate_counts, mapping):
    status_counts = Counter(row.get("candidate_role_status", "") for row in rows)
    parsed = [row for row in rows if row.get("xml_issuer_cik")]
    role_resolved = sum(bool(row.get("role_resolved")) for row in rows)
    pair_ok = sum(bool(row.get("xml_both_ciks_in_master_pair")) for row in parsed)
    distinct_ok = sum(bool(row.get("xml_ciks_distinct")) for row in parsed)
    form_ok = sum(bool(row.get("xml_form_matches_index")) for row in parsed)
    attempted = [row for row in rows if row.get("candidate_role_status") != "unresolved_index_metadata_conflict"]
    failed_statuses = {"unresolved_xml_fetch_error", "unresolved_processing_error"}
    fetch_success = len(attempted) - sum(row.get("candidate_role_status") in failed_statuses for row in attempted)
    duplicates = len(rows) - len({row.get("accession") for row in rows})
    by_form = {}
    for form in FORMS:
        subset = [row for row in rows if row.get("form") == form]
        subevents = [row for row in events if row.get("form") == form]
        by_form[form] = {
            "candidate_rows": len(subset),
            "xml_fetch_errors": sum(row.get("candidate_role_status") == "unresolved_xml_fetch_error" for row in subset),
            "role_resolved_rows": sum(bool(row.get("role_resolved")) for row in subset),
            "issuer_events": sum(row.get("candidate_role_status") in
                                 ("issuer_match", "ambiguous_pair_issuer_match") for row in subset),
            "filer_only_false_positives": sum(row.get("candidate_role_status") in
                                              ("filer_only_false_positive",
                                               "ambiguous_pair_filer_only_false_positive")
                                              for row in subset),
            "unresolved_rows": sum(not bool(row.get("role_resolved")) for row in subset),
            "event_rows_with_sale_tranches": sum(int(row.get("sale_tranche_count") or 0) > 0 for row in subevents),
            "event_rows_sale_units_numeric": sum(bool(row.get("sale_units_all_numeric")) for row in subevents),
            "event_rows_sale_value_numeric": sum(bool(row.get("sale_value_all_numeric")) for row in subevents),
        }
    gates = {
        "candidate_xml_fetch_success_ge_99_5pct": bool(attempted) and fetch_success / len(attempted) >= 0.995,
        "candidate_role_resolution_ge_99_9pct": bool(rows) and role_resolved / len(rows) >= 0.999,
        "xml_pair_concordance_ge_99_9pct": bool(parsed) and pair_ok / len(parsed) >= 0.999,
        "xml_ciks_distinct_ge_99_9pct": bool(parsed) and distinct_ok / len(parsed) >= 0.999,
        "xml_form_match_ge_99_9pct": bool(parsed) and form_ok / len(parsed) >= 0.999,
        "no_duplicate_candidate_accessions": duplicates == 0,
        "no_filer_only_rows_in_issuer_event_panel": all(
            event.get("candidate_role_status") not in
            ("filer_only_false_positive", "ambiguous_pair_filer_only_false_positive")
            for event in events
        ),
        "all_candidate_rows_explicitly_classified": all(bool(row.get("candidate_role_status")) for row in rows),
    }
    return {
        "phase": "67-form144-full-candidate-role-resolution",
        "status": "COMPLETE",
        "data_gate": "PASS" if all(gates.values()) else "FAIL",
        "quarters": [x["quarter"] for x in index_summaries],
        "index_census": index_summaries,
        "current_candidate_cik_count": mapping["candidate_cik_count"],
        "current_tickers_with_cik_mapping": mapping["mapped_tickers"],
        "current_tickers_unresolved": mapping["unresolved_tickers"],
        "candidate_counts": candidate_counts,
        "candidate_rows_processed": len(rows),
        "candidate_role_status_counts": dict(status_counts),
        "candidate_role_resolution_rate": role_resolved / len(rows) if rows else None,
        "xml_fetch_attempted_rows": len(attempted),
        "xml_fetch_success_rate": fetch_success / len(attempted) if attempted else None,
        "xml_pair_concordance_rate": pair_ok / len(parsed) if parsed else None,
        "xml_ciks_distinct_rate": distinct_ok / len(parsed) if parsed else None,
        "xml_form_match_rate": form_ok / len(parsed) if parsed else None,
        "issuer_event_rows": len(events),
        "filer_only_false_positive_rows": status_counts.get("filer_only_false_positive", 0)
            + status_counts.get("ambiguous_pair_filer_only_false_positive", 0),
        "unresolved_rows": len(rows) - role_resolved,
        "control_validation_rows": len(controls),
        "control_concordance_rate": (
            sum(row.get("candidate_role_status") == "control_pair_concordant" for row in controls)
            / len(controls) if controls else None
        ),
        "duplicate_candidate_accessions": duplicates,
        "by_form": by_form,
        "gate_checks": gates,
        "historical_pit_f80_universe_gate": "NOT_TESTED",
        "accepted_timestamp_gate": "NOT_TESTED; filing-date conservative rule only",
        "amendment_lineage_gate": "PARTIAL; previousAccessionNumber is a reference, not immediate predecessor",
        "economic_test_authorized": False,
        "forward_returns_used": False,
        "identity_rule": "Only XML issuerCik in the current candidate CIK set enters issuer_event_raw.csv. XML filer CIK is retained separately. Filer-only matches are excluded.",
        "limitations": [
            "Current ticker/CIK map is not historical F80 membership and leaves unresolved tickers.",
            "A current CIK candidate set cannot recover predecessor issuers or securities that delisted before current mapping.",
            "Filing date is not an accepted timestamp; no same-day close is used.",
            "Form 144 is a proposed sale-order notice, not proof of execution; 144/A is not a new event by default.",
            "No forward returns or alpha tests are performed."
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quarters", default=DEFAULT_QUARTERS)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--controls-per-form-quarter", type=int, default=10)
    parser.add_argument("--output", default=str(OUT_DIR))
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    tickers = load_universe()
    ticker_details, cik_to_tickers, unresolved, mapping_errors = current_cik_candidates(tickers)
    candidate_ciks = set(cik_to_tickers)
    tokens = [x.strip() for x in args.quarters.split(",") if x.strip()]
    quarter_data, all_accessions = build_quarter_data(tokens, candidate_ciks, cik_to_tickers)

    all_rows, all_events, all_errors, all_controls = [], [], [], []
    candidate_counts = {}
    index_summaries = []
    for item in quarter_data:
        candidate_rows = item["candidates"]
        controls = []
        for form in FORMS:
            pool = [row for row in item["pair_rows"]
                    if row["pair_class"] == "control" and row.get("form") == form
                    and not index_row_invalid(row)]
            controls.extend(sorted(pool, key=stable_key)[:args.controls_per_form_quarter])
        work = [(row, False) for row in candidate_rows] + [(row, True) for row in controls]
        quarter_rows, quarter_events, quarter_errors, quarter_controls = [], [], [], []
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(process_row, row, all_accessions, is_control): (row, is_control)
                       for row, is_control in work}
            for index, future in enumerate(as_completed(futures), start=1):
                row, is_control = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = {
                        "row": {
                            "quarter": item["token"], "accession": row.get("accession", ""),
                            "form": row.get("form") or "", "filing_date": row.get("filing_date") or "",
                            "pair_class": row.get("pair_class") or "",
                            "candidate_role_status": "control_processing_error" if is_control else "unresolved_processing_error",
                            "role_resolved": False,
                        },
                        "event": None,
                        "error": {"accession": row.get("accession", ""), "error": type(exc).__name__ + ":" + str(exc)[:240]},
                        "control": is_control,
                    }
                target = quarter_controls if is_control else quarter_rows
                target.append(result["row"])
                if result.get("event"):
                    quarter_events.append(result["event"])
                if result.get("error"):
                    quarter_errors.append(result["error"])
                if index % 500 == 0:
                    print(json.dumps({"stage": "QUARTER_PROGRESS", "quarter": item["token"],
                                      "completed": index, "total": len(work)}, sort_keys=True), flush=True)
        all_rows.extend(quarter_rows)
        all_events.extend(quarter_events)
        all_errors.extend(quarter_errors)
        all_controls.extend(quarter_controls)
        candidate_counts[item["token"]] = {
            "index_accessions": item["index_accessions"],
            "candidate_accessions": len(candidate_rows),
            "unique_candidate_accessions": sum(x["pair_class"] == "unique_candidate" for x in candidate_rows),
            "ambiguous_candidate_accessions": sum(x["pair_class"] == "ambiguous" for x in candidate_rows),
            "controls_processed": len(quarter_controls),
        }
        index_summaries.append({"quarter": item["token"], **candidate_counts[item["token"]]})
        write_csv(out / "candidate_role_resolution_checkpoint.csv", all_rows)
        write_csv(out / "issuer_event_raw_checkpoint.csv", all_events)
        write_csv(out / "xml_fetch_and_processing_errors_checkpoint.csv", all_errors)
        write_csv(out / "control_validation_checkpoint.csv", all_controls)
        print(json.dumps({"stage": "QUARTER_COMPLETE", "quarter": item["token"],
                          **candidate_counts[item["token"]],
                          "candidate_role_status_counts": dict(Counter(x["candidate_role_status"] for x in quarter_rows)),
                          "issuer_events": len(quarter_events), "errors": len(quarter_errors)}, sort_keys=True), flush=True)

    summary = summarize(all_rows, all_events, all_errors, all_controls, index_summaries,
                        candidate_counts, {
                            "candidate_cik_count": len(candidate_ciks),
                            "mapped_tickers": sum(bool(ticker_details[t]["ciks"]) for t in tickers),
                            "unresolved_tickers": unresolved,
                        })
    summary["mapping_source_errors"] = mapping_errors
    summary["xml_candidate_fetch_or_processing_errors"] = len(all_errors)
    write_csv(out / "candidate_role_resolution.csv", all_rows)
    write_csv(out / "issuer_event_raw.csv", all_events)
    write_csv(out / "filer_only_false_positives.csv", [
        row for row in all_rows if row.get("candidate_role_status") in
        ("filer_only_false_positive", "ambiguous_pair_filer_only_false_positive")
    ])
    write_csv(out / "unresolved_candidates.csv", [row for row in all_rows if not row.get("role_resolved")])
    write_csv(out / "xml_fetch_and_processing_errors.csv", all_errors)
    write_csv(out / "control_validation.csv", all_controls)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if summary["data_gate"] != "PASS":
        raise RuntimeError("Phase 67 full candidate role-resolution gate failed; inspect artifacts")


if __name__ == "__main__":
    main()
