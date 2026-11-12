#!/usr/bin/env python3
"""Phase 345: regime-aware Form 4 identity replication across six SEC bulk cohorts.

Reuses the immutable Phase 342 and Phase 343 artifacts. Re-runs original Form 4
and prior-periodic XBRL identity checks for 2006Q1, 2012Q1, 2023Q1, 2023Q2
and 2025Q3; reuses the already verified 2026Q3 raw retrieval. This is an
identity/coverage audit, not a probability-sample prevalence estimate or alpha test.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from research import phase342_sec_insider_bulk_sample_audit as p342
from research import phase343_form4_candidate_specific_identity_audit as p343

PHASE342_RUN = 43265704634
PHASE343_RUN = 43286198150
PERIODS = ("2006Q1", "2012Q1", "2023Q1", "2023Q2", "2025Q3", "2026Q3")
REPROCESS = ("2006Q1", "2012Q1", "2023Q1", "2023Q2", "2025Q3")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def candidate_key(row: dict) -> tuple:
    return (
        str(row.get("accession", "")),
        p343.norm(str(row.get("security_title", ""))),
        p343.canonical_sec_date(row.get("transaction_date", "")),
        p343.decimal_key(row.get("transaction_shares", row.get("shares", ""))),
        p343.sec_bulk_price_key(row.get("transaction_price_per_share", row.get("price_per_share", ""))),
    )


def regime_required(candidate: dict) -> bool:
    filing = p342.parse_sec_date(candidate.get("filing_date", ""))
    if filing is None:
        raise ValueError("candidate_filing_date_unparseable_for_aff_regime")
    required = filing >= p342.CHECKBOX_EFFECTIVE
    supplied = candidate.get("aff_gate_required")
    if isinstance(supplied, str):
        supplied = supplied.strip().lower() in {"true", "1", "yes"}
    if bool(supplied) != required:
        raise ValueError(
            f"aff10b5one_regime_mismatch:{candidate.get('accession')}:{filing}:{supplied}:{required}"
        )
    return required


def verify_candidate_row_regime_aware(candidate, xml_rows, raw_rows, footnotes,
                                      owner_count, aff_value):
    """Phase 343 exact transaction match with the SEC checkbox effective-date regime."""
    required = regime_required(candidate)
    key = p343.phase342_candidate_tx_key(candidate)
    matches = [
        row for row in xml_rows
        if row.get("transaction_kind") == "NON_DERIVATIVE" and p343.tx_key_xml(row) == key
    ]
    if len(matches) != 1:
        return {
            "xml_match_status": "NO_MATCH" if not matches else "MULTIPLE_IDENTICAL_XML_ROWS",
            "xml_match_count": len(matches), "xml_transaction_index": "",
            "raw_purchase_screen_pass": False, "raw_footnote_ids": [],
            "raw_missing_footnote_ids": [], "aff_gate_required": required,
        }

    tx = matches[0]
    index = int(tx["transaction_index"])
    raw_row = raw_rows.get(("NON_DERIVATIVE", index), {})
    fn = footnotes.get(index, {})
    footnote_text = " ".join(fn.get("footnote_texts", []))
    flags = p342.classify_purchase_row({
        "DOCUMENT_TYPE": "4", "TRANS_FORM_TYPE": "4",
        "TRANS_CODE": tx.get("transaction_code", ""),
        "TRANS_ACQUIRED_DISP_CD": tx.get("acquired_disposed", ""),
        "DIRECT_INDIRECT_OWNERSHIP": tx.get("direct_or_indirect", ""),
        "SECURITY_TITLE": tx.get("security_title", ""),
    }, footnote_text, owner_count, aff_value, require_known_false=required)

    if fn.get("missing_footnote_ids"):
        flags["explicit_open_market"] = False
    passed = all(bool(flags.get(k)) for k in p343.BOOL_FLAGS)
    if required:
        passed = passed and p342.normalize_aff(aff_value) == "false"

    return {
        "xml_match_status": "UNIQUE_EXACT_TRANSACTION_ROW",
        "xml_match_count": 1,
        "xml_transaction_index": index,
        "raw_purchase_screen_pass": passed,
        "raw_purchase_screen_flags": flags,
        "raw_security_title": tx.get("security_title", ""),
        "raw_transaction_date": tx.get("transaction_date", ""),
        "raw_transaction_code": tx.get("transaction_code", ""),
        "raw_transaction_shares": tx.get("shares", ""),
        "raw_transaction_price_per_share": tx.get("price_per_share", ""),
        "raw_direct_or_indirect": tx.get("direct_or_indirect", ""),
        "raw_nature_of_ownership": raw_row.get("nature", ""),
        "raw_footnote_ids": fn.get("footnote_ids", []),
        "raw_missing_footnote_ids": fn.get("missing_footnote_ids", []),
        "raw_footnote_texts": fn.get("footnote_texts", []),
        "aff_gate_required": required,
        "aff_status_as_filed": p342.normalize_aff(aff_value),
    }


def augment_result(result: dict, period: str, candidates: list[dict]) -> dict:
    queues = defaultdict(list)
    for candidate in candidates:
        queues[candidate_key(candidate)].append(candidate)
    for row in result.get("candidate_rows", []):
        key = candidate_key(row)
        matches = queues.get(key, [])
        if not matches:
            raise ValueError(f"candidate_result_row_not_in_bulk_archive:{period}:{key}")
        candidate = matches.pop(0)
        row["period"] = period
        row["aff_gate_required"] = regime_required(candidate)
        row["aff10b5one_bulk"] = candidate.get("aff10b5one", "unknown")
    if any(queues.values()):
        raise ValueError(f"bulk_candidates_missing_from_identity_result:{period}")

    for group in result.get("event_units", []):
        group["period"] = period
    for accession in result.get("accessions", []):
        accession["period"] = period

    required = [x for x in candidates if regime_required(x)]
    not_required = [x for x in candidates if not regime_required(x)]
    rows = result.get("candidate_rows", [])
    result["phase"] = 345
    result["status"] = "COMPLETED_MULTIQUARTER_FORM4_IDENTITY_AUDIT"
    result["sources"]["period"] = period
    result["sources"]["bulk_archive"] = p342.ARCHIVES[period]["url"]
    result["summary"].update({
        "period": period,
        "aff_gate_required_rows": len(required),
        "aff_gate_not_required_rows": len(not_required),
        "aff_bulk_unknown_rows": sum(p342.normalize_aff(x.get("aff10b5one")) == "unknown" for x in candidates),
        "aff_gate_regime_revalidated": True,
        "xbrl_anchor_document_statuses": dict(sorted(Counter(
            x.get("anchor_document_status", "") for x in rows if x.get("anchor_status") == "SELECTED"
        ).items())),
    })
    result["controls"].update({
        "multi_quarter_non_contiguous_candidate_cohorts": True,
        "cohort_is_not_probability_sample": True,
        "pooled_identity_coverage_is_not_market_prevalence": True,
        "aff10b5one_checkbox_effective_date_applied_by_actual_filing_date": True,
        "pre_effective_missing_checkbox_is_unknown_not_false": True,
        "post_effective_checkbox_requires_explicit_false": True,
        "no_returns_or_alpha_test": True,
    })
    return result


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                if isinstance(v, (dict, list)) else v
                for k, v in row.items()
            })


def load_phase342(input_dir: Path):
    result_path = input_dir / "phase342" / "phase342_output" / "phase342_sec_insider_bulk_sample_audit.json"
    if not result_path.is_file():
        raise FileNotFoundError("phase342_cross_run_artifact_missing")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("phase") != 342 or result.get("status") != "COMPLETED_SIX_ARCHIVE_SCHEMA_AND_HIGH_PRECISION_SCREEN_AUDIT":
        raise ValueError("phase342_artifact_contract_invalid")
    return result


def load_2026q3(input_dir: Path, output_dir: Path, phase342_result: dict):
    source = input_dir / "phase343" / "phase343_output"
    result_path = source / "phase343_candidate_identity_audit.json"
    if not result_path.is_file():
        raise FileNotFoundError("phase343_cross_run_artifact_missing")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("phase") != 343 or result.get("status") != "COMPLETED_CANDIDATE_SPECIFIC_EVENT_TIME_IDENTITY_AUDIT":
        raise ValueError("phase343_artifact_contract_invalid")
    target = output_dir / "2026Q3"
    shutil.copytree(source, target, dirs_exist_ok=True)
    archive_path = input_dir / "phase342" / "phase342_input" / "2026q3_form345.zip"
    candidates = phase342_result["archives"]["2026Q3"]["candidate_events"]
    if sha256_bytes(archive_path.read_bytes()) != phase342_result["archives"]["2026Q3"]["zip_sha256"]:
        raise ValueError("2026Q3_archive_sha256_mismatch")
    augmented = augment_result(result, "2026Q3", candidates)
    (target / "phase345_2026Q3_candidate_identity_audit.json").write_text(
        json.dumps(augmented, indent=2, sort_keys=True) + "\\n", encoding="utf-8"
    )
    write_csv(target / "phase345_2026Q3_candidate_rows.csv", augmented["candidate_rows"])
    write_csv(target / "phase345_2026Q3_accessions.csv", augmented["accessions"])
    write_csv(target / "phase345_2026Q3_event_units.csv", augmented["event_units"])
    return augmented


def run(input_dir: Path, output_dir: Path, email: str):
    if not email or "@" not in email or any(ch.isspace() for ch in email):
        raise RuntimeError("BLOCKED_MISSING_OR_INVALID_SEC_CONTACT_EMAIL")
    phase342_result = load_phase342(input_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}
    p343_originals = {
        "EXPECTED_ARCHIVE_SHA256": p343.EXPECTED_ARCHIVE_SHA256,
        "EXPECTED": p343.EXPECTED,
        "audit_archive": p343.audit_archive,
        "verify_candidate_row": p343.verify_candidate_row,
        "archive_entry": p343.ARCHIVES.get("2026Q3"),
    }
    try:
        p343.verify_candidate_row = verify_candidate_row_regime_aware
        for period in REPROCESS:
            archive_path = input_dir / "phase342" / "phase342_input" / p342.ARCHIVES[period]["filename"]
            if not archive_path.is_file():
                raise FileNotFoundError(f"phase342_archive_missing:{period}")
            archive_digest = sha256_bytes(archive_path.read_bytes())
            expected_digest = phase342_result["archives"][period]["zip_sha256"]
            if archive_digest != expected_digest:
                raise ValueError(f"phase342_archive_hash_mismatch:{period}")

            counts = phase342_result["archives"][period]
            events = counts["candidate_events"]
            expected = (
                int(counts["candidate_rows"]),
                int(counts["candidate_accessions"]),
                int(counts["candidate_issuer_ciks"]),
                len({(x["issuer_cik"], x["filing_date"]) for x in events}),
            )
            p343.EXPECTED_ARCHIVE_SHA256 = archive_digest
            p343.EXPECTED = expected
            p343.ARCHIVES["2026Q3"] = p342.ARCHIVES[period]
            p343.audit_archive = lambda path, _ignored, period=period: p342.audit_archive(path, period)
            period_dir = output_dir / period / "identity_audit"
            result = p343.run(archive_path, period_dir, email)
            result = augment_result(result, period, events)

            legacy_archive = period_dir / "2026q3_form345_source.zip"
            if legacy_archive.exists():
                legacy_archive.rename(period_dir / f"{period.lower()}_form345_source.zip")
            for suffix in ("candidate_identity_audit.json", "candidate_rows.csv", "accessions.csv", "event_units.csv"):
                old = period_dir / f"phase343_{suffix}"
                if old.exists():
                    old.unlink()
            (period_dir / f"phase345_{period}_candidate_identity_audit.json").write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            write_csv(period_dir / f"phase345_{period}_candidate_rows.csv", result["candidate_rows"])
            write_csv(period_dir / f"phase345_{period}_accessions.csv", result["accessions"])
            write_csv(period_dir / f"phase345_{period}_event_units.csv", result["event_units"])
            all_results[period] = result
            print(f"PHASE345_PERIOD={period} rows={expected[0]} accessions={expected[1]} "
                  f"identity_rows={result['summary']['event_time_identity_rows']} "
                  f"event_units_complete={result['summary']['event_time_identity_event_units_complete']}",
                  flush=True)
    finally:
        p343.EXPECTED_ARCHIVE_SHA256 = p343_originals["EXPECTED_ARCHIVE_SHA256"]
        p343.EXPECTED = p343_originals["EXPECTED"]
        p343.audit_archive = p343_originals["audit_archive"]
        p343.verify_candidate_row = p343_originals["verify_candidate_row"]
        if p343_originals["archive_entry"] is not None:
            p343.ARCHIVES["2026Q3"] = p343_originals["archive_entry"]

    all_results["2026Q3"] = load_2026q3(input_dir, output_dir, phase342_result)

    summary_rows = []
    for period in PERIODS:
        result = all_results[period]
        s = result["summary"]
        summary_rows.append({
            "period": period,
            "candidate_rows": s["candidate_rows"],
            "candidate_accessions": s["candidate_accessions"],
            "candidate_issuer_ciks": s["candidate_issuer_ciks"],
            "event_units": s["issuer_cik_filing_date_event_units"],
            "form4_retrieved": s["form4_accessions_retrieved"],
            "symbol_reconciled": s["form4_symbol_bulk_xml_reconciled"],
            "transaction_rows_exact": s["candidate_rows_unique_xml_transaction_match"],
            "purchase_screen_rows_revalidated": s["candidate_rows_raw_purchase_screen_revalidated"],
            "prior_periodic_anchors": s["event_units_with_prior_periodic_anchor"],
            "fresh_anchors_le_365d": s["event_units_with_fresh_anchor_le_365d"],
            "anchors_with_context_triples": s["unique_periodic_anchors_with_xbrl_context_triples"],
            "event_identity_rows": s["event_time_identity_rows"],
            "event_identity_row_pct": s["event_time_identity_coverage_pct_rows"],
            "complete_event_units": s["event_time_identity_event_units_complete"],
            "event_unit_pct": s["event_time_identity_coverage_pct_event_units"],
            "aff_gate_required_rows": s["aff_gate_required_rows"],
            "aff_gate_not_required_rows": s["aff_gate_not_required_rows"],
            "aff_bulk_unknown_rows": s["aff_bulk_unknown_rows"],
        })

    xbrl_periods = [r for r in summary_rows if r["period"] != "2006Q1"]
    total_rows = sum(r["candidate_rows"] for r in xbrl_periods)
    total_identity = sum(r["event_identity_rows"] for r in xbrl_periods)
    total_events = sum(r["event_units"] for r in xbrl_periods)
    total_complete_events = sum(r["complete_event_units"] for r in xbrl_periods)
    aggregate = {
        "phase": 345,
        "status": "COMPLETED_MULTIQUARTER_FORM4_IDENTITY_AUDIT",
        "source_periods": list(PERIODS),
        "reprocessed_periods": list(REPROCESS),
        "reused_verified_period": "2026Q3",
        "phase342_run_id": PHASE342_RUN,
        "phase343_run_id": PHASE343_RUN,
        "periods": summary_rows,
        "xbrl_era_descriptive_aggregate_excluding_2006": {
            "candidate_rows": total_rows,
            "event_identity_rows": total_identity,
            "row_identity_pct": 100 * total_identity / total_rows if total_rows else None,
            "event_units": total_events,
            "complete_event_units": total_complete_events,
            "complete_event_unit_pct": 100 * total_complete_events / total_events if total_events else None,
            "warning": "Non-contiguous, screen-selected candidate cohorts; not market-wide prevalence or a probability-sample estimate.",
        },
        "controls": {
            "all_source_archives_sha256_verified": True,
            "phase343_2026q3_raw_results_reused_without_refetch": True,
            "pre_effective_checkbox_unknown_not_false": True,
            "post_effective_checkbox_requires_explicit_false": True,
            "same_day_or_future_periodic_anchors_excluded": True,
            "fresh_anchor_max_age_days": 365,
            "no_fuzzy_security_matching": True,
            "no_return_or_alpha_test": True,
            "no_bootstrap_or_loo": True,
            "no_chronological_oos": True,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "parameters_changed": False,
            "data_purchased": False,
            "vendor_contacted": False,
        },
    }
    (output_dir / "phase345_multiquarter_identity_summary.json").write_text(
        json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(output_dir / "phase345_multiquarter_identity_summary.csv", summary_rows)
    print("PHASE345_STATUS=" + aggregate["status"])
    print("PHASE345_AGGREGATE=" + json.dumps(aggregate["xbrl_era_descriptive_aggregate_excluding_2006"], sort_keys=True))
    return aggregate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--email", default="")
    args = parser.parse_args()
    run(args.input_dir, args.output_dir, args.email)


if __name__ == "__main__":
    main()
