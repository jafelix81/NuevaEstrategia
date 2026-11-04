#!/usr/bin/env python3
"""Incremental Phase 69 Form 144 scan for ten newly mapped fund registrants.

This is an identity/data assembly gate only. It does not calculate returns.
Existing Phase 67 rows are reclassified only when a new registrant CIK occurs
in the same master-index accession pair.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from research.phase50_form144_global_index_pilot import (
    MAPPER_URL, SEC_TICKERS_URL, SEC_EXCHANGE_URL, SEC_MUTUAL_FUNDS_URL,
    current_cik_candidates, fetch_bytes, fetch_json, load_universe,
    norm_cik, parse_master_index, records, ticker_variants,
)
from research.phase64_form144_master_pair_cross_quarter_audit import (
    build_pair_rows, parse_quarter,
)
from research.phase67_form144_full_candidate_role_resolution import (
    DEFAULT_QUARTERS, FORMS, START_DATE, index_row_invalid, process_row, stable_key, write_csv,
)

BASE_RUN_ID = 41828139052
BASE_ARTIFACT_ID = 13327123059
BASE_ROWS = 21648
BASE_EVENTS = 21634
NEW_FUND_REGISTRANT_CIKS = {
    "0001579982", "0001174610", "0001100663", "0001540305", "0001064642",
    "0001137360", "0000923202", "0000734383", "0000857489", "0001064641",
}
EXPECTED_LEGACY_UNRESOLVED_TICKERS = {
    "ARKF", "ARKG", "ARKK", "ARKQ", "ARKW", "BITO", "IEFA", "IWM", "JETS",
    "KRE", "OIH", "SMH", "SOXX", "VEA", "VNQ", "VWO", "XBI", "XLB", "XLE",
    "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY",
}
OUT_DIR = Path("phase69_form144_fund_registrant_scan")


def read_csv(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def validate_base(summary: dict, rows: list[dict], events: list[dict]) -> None:
    expected = {
        "data_gate": "PASS",
        "current_candidate_cik_count": 309,
        "current_tickers_with_cik_mapping": 308,
        "candidate_rows_processed": BASE_ROWS,
        "issuer_event_rows": BASE_EVENTS,
        "filer_only_false_positive_rows": 14,
        "unresolved_rows": 0,
        "xml_candidate_fetch_or_processing_errors": 0,
    }
    bad = {k: (summary.get(k), v) for k, v in expected.items() if summary.get(k) != v}
    if bad or len(rows) != BASE_ROWS or len(events) != BASE_EVENTS:
        raise ValueError("Phase 67 baseline artifact failed strict validation: " + json.dumps(bad))
    if len(summary.get("current_tickers_unresolved", [])) != 27:
        raise ValueError("Phase 67 baseline must contain the preregistered 27 unresolved tickers")
    if len({r.get("accession") for r in rows}) != len(rows):
        raise ValueError("Duplicate accession in Phase 67 baseline")
    if any(not r.get("candidate_role_status") for r in rows):
        raise ValueError("Unclassified Phase 67 baseline row")


def load_base(base_dir: Path):
    summary = json.loads((base_dir / "summary.json").read_text(encoding="utf-8"))
    rows = read_csv(base_dir / "candidate_role_resolution.csv")
    events = read_csv(base_dir / "issuer_event_raw.csv")
    validate_base(summary, rows, events)
    return summary, rows, events


def legacy_cik_candidates(tickers: list[str]):
    """Recreate the pre-Phase-68 mapper, intentionally excluding the SEC 'symbol' field."""
    mapping = {}
    source_errors = []

    def add(ticker, cik):
        if not ticker or not cik:
            return
        ticker = str(ticker).strip().upper()
        cik = norm_cik(cik)
        if ticker and cik:
            mapping.setdefault(ticker, set()).add(cik)

    for url, source in (
        (SEC_TICKERS_URL, "company_tickers"),
        (SEC_EXCHANGE_URL, "company_tickers_exchange"),
        (SEC_MUTUAL_FUNDS_URL, "company_tickers_mf"),
    ):
        try:
            for row in records(fetch_json(url, sec=True)):
                # Deliberately reproduce the old Phase 67 field list; do not read 'symbol'.
                ticker = row.get("ticker") or row.get("classTicker") or row.get("class_ticker")
                add(ticker, row.get("cik_str") or row.get("cik"))
        except Exception as exc:
            source_errors.append({"source": source, "error": str(exc)})
    try:
        mapper = fetch_json(MAPPER_URL, sec=False)
        for ticker, cik in mapper.items():
            add(ticker, cik)
    except Exception as exc:
        source_errors.append({"source": "sec_cik_mapper_fallback", "error": str(exc)})

    cik_to_tickers = {}
    unresolved = []
    for ticker in tickers:
        found = None
        for alias in ticker_variants(ticker):
            if mapping.get(alias):
                found = mapping[alias]
                break
        if not found:
            unresolved.append(ticker)
            continue
        for cik in found:
            cik_to_tickers.setdefault(cik, set()).add(ticker)
    return {cik: sorted(values) for cik, values in cik_to_tickers.items()}, unresolved, source_errors


def validate_legacy_snapshot(legacy_map: dict, unresolved: list[str], source_errors: list[dict]) -> None:
    if len(legacy_map) != 309:
        raise ValueError(f"Expected 309 legacy CIKs, got {len(legacy_map)}")
    if set(unresolved) != EXPECTED_LEGACY_UNRESOLVED_TICKERS:
        raise ValueError("Legacy unresolved ticker names differ from the Phase 67 snapshot")
    if source_errors:
        raise ValueError("Legacy mapping source errors: " + json.dumps(source_errors))


def derive_new_ciks(expanded_ciks: set[str], legacy_ciks: set[str]) -> set[str]:
    if len(expanded_ciks) != 319 or len(legacy_ciks) != 309:
        raise ValueError("Expected 319 expanded and 309 legacy candidate CIKs")
    if legacy_ciks - expanded_ciks:
        raise ValueError("Legacy Phase 67 CIKs missing from expanded Phase 68 map")
    difference = expanded_ciks - legacy_ciks
    if difference != NEW_FUND_REGISTRANT_CIKS:
        raise ValueError("Live CIK-set difference does not equal the ten preregistered fund registrants: "
                         + json.dumps({"actual": sorted(difference),
                                       "expected": sorted(NEW_FUND_REGISTRANT_CIKS)}))
    return difference


def audit_overlap(base: dict, expanded: dict) -> dict:
    fields = ("xml_issuer_cik", "xml_filer_cik", "master_index_ciks", "form", "filing_date")
    diffs = {k: [base.get(k, ""), expanded.get(k, "")]
             for k in fields if str(base.get(k, "")) != str(expanded.get(k, ""))}
    return {
        "accession": expanded.get("accession", ""),
        "identity_consistent": not diffs,
        "identity_differences_json": json.dumps(diffs, sort_keys=True),
        "old_candidate_ciks": base.get("candidate_ciks_in_pair", ""),
        "new_candidate_ciks": expanded.get("candidate_ciks_in_pair", ""),
        "old_candidate_tickers": base.get("candidate_tickers", ""),
        "new_candidate_tickers": expanded.get("candidate_tickers", ""),
        "old_role_status": base.get("candidate_role_status", ""),
        "new_role_status": expanded.get("candidate_role_status", ""),
        "xml_issuer_cik": expanded.get("xml_issuer_cik", ""),
        "xml_filer_cik": expanded.get("xml_filer_cik", ""),
    }


def merge_rows(base_rows: list[dict], incremental_rows: list[dict]):
    inc = {r["accession"]: r for r in incremental_rows}
    if len(inc) != len(incremental_rows):
        raise ValueError("Duplicate incremental accession")
    merged, overlaps = [], []
    for old in base_rows:
        replacement = inc.pop(old["accession"], None)
        if replacement is None:
            merged.append(old)
        else:
            overlaps.append(audit_overlap(old, replacement))
            merged.append(replacement)
    merged.extend(inc.values())
    if len({r["accession"] for r in merged}) != len(merged):
        raise ValueError("Duplicate accession after expanded merge")
    return merged, overlaps


def merge_events(base_events: list[dict], incremental_rows: list[dict],
                 incremental_events: list[dict]) -> list[dict]:
    inc_rows = {r["accession"]: r for r in incremental_rows}
    inc_events = {e["accession"]: e for e in incremental_events}
    if len(inc_rows) != len(incremental_rows) or len(inc_events) != len(incremental_events):
        raise ValueError("Duplicate incremental accession in event merge")
    merged, base_seen = [], set()
    for old in base_events:
        acc = old["accession"]
        base_seen.add(acc)
        if acc not in inc_rows:
            merged.append(old)
        elif acc in inc_events:
            merged.append(inc_events.pop(acc))
        # If expanded identity says filer-only/unresolved, remove the old issuer event.
    for acc, event in inc_events.items():
        if acc not in base_seen:
            merged.append(event)
    if len({e["accession"] for e in merged}) != len(merged):
        raise ValueError("Duplicate issuer event after expanded merge")
    return merged


def write_mapping(path: Path, tickers, details):
    rows = []
    for ticker in tickers:
        item = details[ticker]
        rows.append({
            "ticker": ticker,
            "ciks": ";".join(item.get("ciks") or []),
            "sources": ";".join(item.get("sources") or []),
            "fund_classes_json": json.dumps(item.get("fund_classes") or [], sort_keys=True),
        })
    write_csv(path, rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", required=True)
    parser.add_argument("--quarters", default=DEFAULT_QUARTERS)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--controls-per-form-quarter", type=int, default=10)
    parser.add_argument("--output", default=str(OUT_DIR))
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    base_summary, base_rows, base_events = load_base(Path(args.base_dir))
    tickers = load_universe()
    details, cik_to_tickers, unresolved, source_errors = current_cik_candidates(tickers)
    expanded_ciks = set(cik_to_tickers)
    legacy_cik_to_tickers, legacy_unresolved, legacy_errors = legacy_cik_candidates(tickers)
    new_ciks = derive_new_ciks(expanded_ciks, set(legacy_cik_to_tickers))
    if len(tickers) != 335 or unresolved or source_errors:
        raise ValueError("Phase 68 current map must resolve 335/335 with zero source errors")
    validate_legacy_snapshot(legacy_cik_to_tickers, legacy_unresolved, legacy_errors)

    all_accessions, quarter_data = set(), []
    for token in [x.strip() for x in args.quarters.split(",") if x.strip()]:
        year, quarter = parse_quarter(token)
        url = f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/master.idx"
        idx = parse_master_index(fetch_bytes(url, sec=True, timeout=90, retries=5))
        idx = [r for r in idx if r.get("filing_date") and r["filing_date"] >= START_DATE
               and (r.get("form") in FORMS or r.get("metadata_conflict"))]
        pairs = build_pair_rows(idx, expanded_ciks, cik_to_tickers, year, quarter)
        all_accessions.update(r["accession"] for r in pairs if r.get("accession"))
        candidates = [r for r in pairs
                      if set(r.get("master_index_ciks") or []) & new_ciks
                      and r.get("pair_class") != "control"]
        controls = []
        for form in FORMS:
            pool = [r for r in pairs if r.get("pair_class") == "control"
                    and r.get("form") == form and not index_row_invalid(r)]
            controls.extend(sorted(pool, key=stable_key)[:args.controls_per_form_quarter])
        quarter_data.append((token, candidates, controls, len(pairs)))
        print(json.dumps({"stage":"INDEX_COMPLETE","quarter":token,"index_accessions":len(pairs),
                          "new_cik_candidates":len(candidates),"controls":len(controls)},sort_keys=True),flush=True)

    inc_rows, inc_events, errors, controls = [], [], [], []
    for token, candidates, q_controls, _ in quarter_data:
        work = [(r, False) for r in candidates] + [(r, True) for r in q_controls]
        q_rows, q_events, q_errors, q_control_rows = [], [], [], []
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(process_row, row, all_accessions, is_control):(row,is_control)
                       for row,is_control in work}
            for n, future in enumerate(as_completed(futures), start=1):
                row, is_control = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = {
                        "row":{"quarter":token,"accession":row.get("accession",""),
                               "form":row.get("form") or "","filing_date":row.get("filing_date") or "",
                               "candidate_role_status":"control_processing_error" if is_control else "unresolved_processing_error",
                               "role_resolved":False},
                        "event":None,
                        "error":{"accession":row.get("accession",""),
                                 "error":type(exc).__name__+":"+str(exc)[:240]},
                        "control":is_control,
                    }
                (q_control_rows if is_control else q_rows).append(result["row"])
                if result.get("event"): q_events.append(result["event"])
                if result.get("error"): q_errors.append(result["error"])
                if n % 500 == 0:
                    print(json.dumps({"stage":"QUARTER_PROGRESS","quarter":token,
                                      "completed":n,"total":len(work)},sort_keys=True),flush=True)
        inc_rows.extend(q_rows); inc_events.extend(q_events); errors.extend(q_errors); controls.extend(q_control_rows)
        print(json.dumps({"stage":"QUARTER_COMPLETE","quarter":token,"candidate_rows":len(q_rows),
                          "issuer_events":len(q_events),"errors":len(q_errors)},sort_keys=True),flush=True)
        write_csv(out/"incremental_candidate_role_resolution_checkpoint.csv",inc_rows)
        write_csv(out/"incremental_issuer_event_raw_checkpoint.csv",inc_events)
        write_csv(out/"xml_errors_checkpoint.csv",errors)

    expanded_rows, overlaps = merge_rows(base_rows, inc_rows)
    expanded_events = merge_events(base_events, inc_rows, inc_events)
    status = Counter(r.get("candidate_role_status","") for r in inc_rows)
    parsed = [r for r in inc_rows if r.get("xml_issuer_cik")]
    attempted = [r for r in inc_rows if r.get("candidate_role_status") != "unresolved_index_metadata_invalid"]
    failed = sum(r.get("candidate_role_status") in {"unresolved_xml_fetch_error","unresolved_processing_error"}
                 for r in attempted)
    resolved = sum(str(r.get("role_resolved","")).lower()=="true" for r in inc_rows)
    controls_ok = not controls or all(r.get("candidate_role_status")=="control_pair_concordant" for r in controls)
    overlaps_ok = all(x["identity_consistent"] for x in overlaps)
    pair_ok = sum(str(r.get("xml_both_ciks_in_master_pair","")).lower()=="true" for r in parsed)
    distinct_ok = sum(str(r.get("xml_ciks_distinct","")).lower()=="true" for r in parsed)
    form_ok = sum(str(r.get("xml_form_matches_index","")).lower()=="true" for r in parsed)
    gates = {
        "phase67_baseline_pass": base_summary.get("data_gate")=="PASS",
        "current_universe_335_mapped": len(tickers)==335 and not unresolved,
        "expanded_cik_count_319": len(expanded_ciks)==319,
        "ten_preregistered_new_fund_ciks_present": len(new_ciks)==10,
        "legacy_309_cik_set_exactly_reproduced": len(legacy_cik_to_tickers)==309
            and not (set(legacy_cik_to_tickers)-expanded_ciks)
            and (expanded_ciks-set(legacy_cik_to_tickers))==NEW_FUND_REGISTRANT_CIKS,
        "legacy_27_unresolved_ticker_names_match": set(legacy_unresolved)==EXPECTED_LEGACY_UNRESOLVED_TICKERS,
        "incremental_xml_fetch_success_ge_99_5pct": not attempted or (len(attempted)-failed)/len(attempted)>=0.995,
        "incremental_role_resolution_ge_99_9pct": not inc_rows or resolved/len(inc_rows)>=0.999,
        "incremental_pair_concordance_ge_99_9pct": not parsed or pair_ok/len(parsed)>=0.999,
        "incremental_distinct_ciks_ge_99_9pct": not parsed or distinct_ok/len(parsed)>=0.999,
        "incremental_form_match_ge_99_9pct": not parsed or form_ok/len(parsed)>=0.999,
        "overlap_xml_identity_unchanged": overlaps_ok,
        "control_pair_concordance_100pct": controls_ok,
        "no_duplicate_expanded_accessions": len(expanded_rows)==len({r["accession"] for r in expanded_rows}),
        "no_filer_only_rows_in_expanded_event_panel": all(
            e.get("candidate_role_status") not in {"filer_only_false_positive","ambiguous_pair_filer_only_false_positive"}
            for e in expanded_events),
        "no_incremental_xml_processing_errors": len(errors)==0,
        "all_incremental_rows_classified": all(bool(r.get("candidate_role_status")) for r in inc_rows),
        "mapping_source_errors_zero": not source_errors,
    }
    summary = {
        "phase":"69-incremental-form144-fund-registrant-scan",
        "status":"COMPLETE",
        "data_gate":"PASS" if all(gates.values()) else "FAIL",
        "base_run_id":BASE_RUN_ID,
        "base_artifact_id":BASE_ARTIFACT_ID,
        "base_candidate_rows":len(base_rows),
        "base_issuer_event_rows":len(base_events),
        "current_universe_tickers":len(tickers),
        "expanded_candidate_cik_count":len(expanded_ciks),
        "new_fund_registrant_ciks":sorted(new_ciks),
        "incremental_candidate_accessions":len(inc_rows),
        "incremental_new_accessions":len(inc_rows)-len(overlaps),
        "incremental_overlap_accessions":len(overlaps),
        "overlap_identity_conflicts":sum(not x["identity_consistent"] for x in overlaps),
        "incremental_issuer_events":len(inc_events),
        "incremental_new_registrant_issuer_events":sum(e.get("xml_issuer_cik") in new_ciks for e in inc_events),
        "incremental_filer_only_false_positives":status.get("filer_only_false_positive",0)+status.get("ambiguous_pair_filer_only_false_positive",0),
        "incremental_unresolved_rows":len(inc_rows)-resolved,
        "incremental_xml_errors":len(errors),
        "incremental_role_status_counts":dict(status),
        "expanded_candidate_rows":len(expanded_rows),
        "expanded_issuer_event_rows":len(expanded_events),
        "expanded_unique_issuer_ciks":len({e.get("xml_issuer_cik") for e in expanded_events}),
        "expanded_role_status_counts":dict(Counter(r.get("candidate_role_status","") for r in expanded_rows)),
        "expanded_filer_only_false_positives":sum(r.get("candidate_role_status") in {"filer_only_false_positive","ambiguous_pair_filer_only_false_positive"} for r in expanded_rows),
        "expanded_unresolved_rows":sum(str(r.get("role_resolved","")).lower()!="true" for r in expanded_rows),
        "control_rows":len(controls),
        "control_concordance_rate":sum(r.get("candidate_role_status")=="control_pair_concordant" for r in controls)/len(controls) if controls else None,
        "gate_checks":gates,
        "mapping_source_errors":source_errors,
        "legacy_mapping_unresolved_count":len(legacy_unresolved),
        "legacy_mapping_unresolved_tickers":sorted(legacy_unresolved),
        "legacy_mapping_source_errors":legacy_errors,
        "historical_pit_f80_universe_gate":"NOT_TESTED",
        "fund_series_class_to_security_class_gate":"NOT_TESTED",
        "accepted_timestamp_gate":"NOT_TESTED; filing-date conservative rule only",
        "amendment_lineage_gate":"PARTIAL; previousAccessionNumber is not assumed to be the immediate predecessor",
        "forward_returns_used":False,
        "economic_test_authorized":False,
        "limitations":[
            "The ten new CIKs are current fund registrants, not historical security identities.",
            "A trust-level CIK event is not assigned to every ticker sharing that registrant.",
            "Fund series/class and Form 144 security-class attribution remain unresolved.",
            "Historical F80 membership, delisted predecessor issuers and first-publication timestamps remain untested.",
            "Form 144 is a proposed sale-order notice, not proof of execution; 144/A is not a new event by default.",
        ],
    }
    write_mapping(out/"ticker_mapping.csv",tickers,details)
    write_csv(out/"incremental_candidate_role_resolution.csv",inc_rows)
    write_csv(out/"incremental_issuer_event_raw.csv",inc_events)
    write_csv(out/"overlap_reclassification.csv",overlaps)
    write_csv(out/"expanded_candidate_role_resolution.csv",expanded_rows)
    write_csv(out/"expanded_issuer_event_raw.csv",expanded_events)
    write_csv(out/"expanded_filer_only_false_positives.csv",[
        r for r in expanded_rows if r.get("candidate_role_status") in
        {"filer_only_false_positive","ambiguous_pair_filer_only_false_positive"}])
    write_csv(out/"expanded_unresolved_candidates.csv",[
        r for r in expanded_rows if str(r.get("role_resolved","")).lower()!="true"])
    write_csv(out/"xml_fetch_and_processing_errors.csv",errors)
    write_csv(out/"control_validation.csv",controls)
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2),flush=True)
    if summary["data_gate"]!="PASS":
        raise RuntimeError("Phase 69 incremental fund registrant gate failed; inspect artifacts")


if __name__ == "__main__":
    main()
