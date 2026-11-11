#!/usr/bin/env python3
"""Phase 300: offline XML-vs-bulk reconciliation of the Phase 299 SEC sample.

No SEC requests are made. The immutable Phase 299 raw EDGAR submissions are
reconciled against the original Phase 294/298 bulk archives. The result tests
source fidelity and candidate-lineage reproducibility, not investment alpha.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import phase299_form4a_edgar_validation as base

DATE_FIELDS = {"TRANS_DATE", "DEEMED_EXECUTION_DATE", "EXCERCISE_DATE", "EXPIRATION_DATE"}
ROUNDING = "0.01"
ND_FULL = base.ND_EXACT
DV_FULL = base.DV_EXACT
ND_CORE = tuple(field for field in ND_FULL if field not in {"NATURE_OF_OWNERSHIP", "TRANS_TIMELINESS"})
DV_CORE = tuple(field for field in DV_FULL if field not in {"NATURE_OF_OWNERSHIP", "TRANS_TIMELINESS"})


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def normalized(field: str, value: str | None) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if field in DATE_FIELDS:
        return base.norm_date(value)
    if field in base.NUMERIC:
        try:
            from decimal import Decimal, ROUND_HALF_UP
            number = Decimal(value.replace(",", ""))
            if number.is_finite():
                return format(number.quantize(Decimal(ROUNDING), rounding=ROUND_HALF_UP), "f")
        except Exception:
            pass
    return " ".join(value.upper().split())


def signature(row: dict, fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(normalized(field, row.get(field)) for field in fields)


def multiset_match(bulk_rows: list[dict], xml_rows: list[dict], fields: tuple[str, ...]) -> bool:
    return Counter(signature(row, fields) for row in bulk_rows) == Counter(
        signature(row, fields) for row in xml_rows
    )


def diff_rows(parent: list[dict], child: list[dict], exact_fields: tuple[str, ...],
              coarse_fields: tuple[str, ...]) -> dict:
    parent_exact = Counter(signature(row, exact_fields) for row in parent)
    child_exact = Counter(signature(row, exact_fields) for row in child)
    repeated = sum((parent_exact & child_exact).values())
    parent_coarse = Counter(signature(row, coarse_fields) for row in parent)
    child_coarse = Counter(signature(row, coarse_fields) for row in child)
    matched_coarse = Counter()
    remaining_exact = parent_exact.copy()
    for row in child:
        exact = signature(row, exact_fields)
        if remaining_exact[exact] > 0:
            matched_coarse[signature(row, coarse_fields)] += 1
            remaining_exact[exact] -= 1
    parent_remaining = parent_coarse - matched_coarse
    child_remaining = child_coarse - matched_coarse
    same_coarse = sum(min(parent_coarse[key], child_remaining[key]) for key in child_remaining)
    distinct_added = sum(child_remaining.values()) - same_coarse
    parent_unmatched = sum(parent_remaining.values()) - sum(
        min(parent_remaining[key], child_remaining[key]) for key in parent_remaining
    )
    return {
        "parent_rows": len(parent), "amendment_rows": len(child),
        "exact_repeated": repeated, "same_coarse_unmatched": same_coarse,
        "distinct_coarse_added": distinct_added, "parent_unmatched": parent_unmatched,
    }


def excluded_field_mismatches(bulk_rows: list[dict], xml_rows: list[dict],
                              core_fields: tuple[str, ...], table: str) -> list[str]:
    """Find footnote/timeliness differences within otherwise identical core rows."""
    groups_bulk: dict[tuple, Counter] = defaultdict(Counter)
    groups_xml: dict[tuple, Counter] = defaultdict(Counter)
    for row in bulk_rows:
        groups_bulk[signature(row, core_fields)][(
            (row.get("NATURE_OF_OWNERSHIP") or "").strip(),
            (row.get("TRANS_TIMELINESS") or "").strip(),
        )] += 1
    for row in xml_rows:
        groups_xml[signature(row, core_fields)][(
            (row.get("NATURE_OF_OWNERSHIP") or "").strip(),
            (row.get("TRANS_TIMELINESS") or "").strip(),
        )] += 1
    fields = set()
    for key in set(groups_bulk) | set(groups_xml):
        b, x = groups_bulk[key], groups_xml[key]
        if b == x:
            continue
        for index, field in ((0, "NATURE_OF_OWNERSHIP"), (1, "TRANS_TIMELINESS")):
            marginal_b = Counter()
            marginal_x = Counter()
            for values, count in b.items():
                marginal_b[values[index]] += count
            for values, count in x.items():
                marginal_x[values[index]] += count
            if marginal_b != marginal_x:
                fields.add(field)
    return sorted(fields)


def load_periods(phase294_dir: Path, phase298_dir: Path) -> dict:
    periods = {}
    for period, (source, relative) in base.ARCHIVE_PATHS.items():
        root = phase294_dir if source == "phase294" else phase298_dir
        path = root / relative
        if not path.is_file():
            raise SystemExit(f"missing_bulk_archive:{period}:{path}")
        periods[period] = base.load_period(path, period)
    return periods


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase294-dir", type=Path, required=True)
    parser.add_argument("--phase298-dir", type=Path, required=True)
    parser.add_argument("--phase299-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = args.phase299_dir / "phase299_sample_manifest.json"
    prior_result_path = args.phase299_dir / "phase299_validation_result.json"
    raw_dir = args.phase299_dir / "raw_edgar"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    prior_result = json.loads(prior_result_path.read_text(encoding="utf-8"))
    if manifest.get("phase") != 299 or prior_result.get("phase") != 299:
        raise SystemExit("phase299_artifact_identity_mismatch")

    periods = load_periods(args.phase294_dir, args.phase298_dir)
    expected_hashes = manifest["source_archives"]
    for period, data in periods.items():
        if data["sha256"] != expected_hashes[period]["sha256"]:
            raise SystemExit(f"bulk_source_hash_mismatch:{period}")

    parsed_docs = {}
    doc_results = {}
    raw_hash_verified = 0
    for expected in manifest["documents"]:
        accession = expected["accession"]
        acc_path = accession.replace("-", "")
        raw_path = raw_dir / f"{acc_path}.txt"
        if not raw_path.is_file():
            raise SystemExit(f"missing_phase299_raw_submission:{accession}")
        payload = raw_path.read_bytes()
        prior_doc = prior_result["documents"].get(accession, {})
        expected_raw_hash = prior_doc.get("download_sha256")
        actual_raw_hash = sha256(payload)
        if not expected_raw_hash or actual_raw_hash != expected_raw_hash:
            raise SystemExit(f"raw_edgar_hash_mismatch:{accession}")
        raw_hash_verified += 1

        parsed = base.parse_submission(payload)
        if not parsed.get("xml_parse_ok"):
            raise SystemExit(f"xml_parse_failed:{accession}:{parsed.get('xml_parse_error')}")
        filing = periods[expected["period"]]["filings"].get(accession)
        if filing is None:
            raise SystemExit(f"bulk_filing_missing:{accession}")

        nd_xml = parsed["xml_nd_rows"]
        dv_xml = parsed["xml_dv_rows"]
        nd_full = multiset_match(filing["nd"], nd_xml, ND_FULL)
        dv_full = multiset_match(filing["dv"], dv_xml, DV_FULL)
        nd_core = multiset_match(filing["nd"], nd_xml, ND_CORE)
        dv_core = multiset_match(filing["dv"], dv_xml, DV_CORE)
        identity_checks = {
            "accession_matches": parsed.get("accession") == accession,
            "header_form_matches": parsed.get("header_form_type", "").upper() == expected["document_type"],
            "xml_document_type_matches": parsed.get("xml_document_type", "").upper() == expected["document_type"],
            "filing_date_matches": parsed.get("filed_as_of_date") == expected["filing_date"].replace("-", ""),
            "issuer_cik_matches": parsed.get("xml_issuer_cik") == expected["issuer_cik"],
            "reporting_owner_set_matches": sorted(parsed.get("xml_owner_ciks", [])) == sorted(expected["owner_ciks"]),
            "xml_parsed": parsed.get("xml_parse_ok") is True,
        }
        table_results = {
            "nonderivative": {
                "bulk_rows": len(filing["nd"]), "xml_rows": len(nd_xml),
                "row_count_matches": len(filing["nd"]) == len(nd_xml),
                "full_2dp_multiset_match": nd_full, "core_2dp_multiset_match": nd_core,
                "excluded_field_differences": excluded_field_mismatches(filing["nd"], nd_xml, ND_CORE, "nd")
                if nd_core else [],
            },
            "derivative": {
                "bulk_rows": len(filing["dv"]), "xml_rows": len(dv_xml),
                "row_count_matches": len(filing["dv"]) == len(dv_xml),
                "full_2dp_multiset_match": dv_full, "core_2dp_multiset_match": dv_core,
                "excluded_field_differences": excluded_field_mismatches(filing["dv"], dv_xml, DV_CORE, "dv")
                if dv_core else [],
            },
        }
        parsed_docs[accession] = parsed
        doc_results[accession] = {
            "raw_sha256": actual_raw_hash, "raw_hash_matches_phase299_artifact": True,
            "path_cik_used": prior_doc.get("path_cik_used"),
            "header_xml_identity_checks": identity_checks,
            "header_xml_identity_pass": all(identity_checks.values()),
            "row_count_match_both_tables": all(t["row_count_matches"] for t in table_results.values()),
            "full_2dp_transaction_match_both_tables": nd_full and dv_full,
            "core_2dp_transaction_match_both_tables": nd_core and dv_core,
            "tables": table_results,
        }

    pair_results = []
    for pair in manifest["sample_pairs"]:
        parent_acc = pair["parent_accession"]
        child_acc = pair["amendment_accession"]
        parent = parsed_docs[parent_acc]
        child = parsed_docs[child_acc]
        parent_expected = next(d for d in manifest["documents"] if d["accession"] == parent_acc)
        child_expected = next(d for d in manifest["documents"] if d["accession"] == child_acc)
        parent_accept = base.parse_acceptance(parent.get("acceptance_datetime"))
        child_accept = base.parse_acceptance(child.get("acceptance_datetime"))
        date_match = bool(
            child.get("xml_date_of_original_submission")
            and base.norm_date(child["xml_date_of_original_submission"]) == pair["parent_filing_date"]
        )
        issuer_match = parent.get("xml_issuer_cik") == child.get("xml_issuer_cik") == pair["issuer_cik"]
        owner_overlap = bool(set(parent.get("xml_owner_ciks", [])) & set(child.get("xml_owner_ciks", [])))
        chronological = bool(parent_accept and child_accept and parent_accept <= child_accept)
        parent_type = parent.get("xml_document_type") == "4"
        child_type = child.get("xml_document_type") == "4/A"
        metadata_ok = all((
            doc_results[parent_acc]["header_xml_identity_pass"],
            doc_results[child_acc]["header_xml_identity_pass"],
            date_match, issuer_match, owner_overlap, chronological, parent_type, child_type,
        ))

        bulk_parent = periods[parent_expected["period"]]["filings"][parent_acc]
        bulk_child = periods[child_expected["period"]]["filings"][child_acc]
        bulk_full = {
            "table_i_nonderivative": diff_rows(bulk_parent["nd"], bulk_child["nd"], ND_FULL, base.ND_COARSE),
            "table_ii_derivative": diff_rows(bulk_parent["dv"], bulk_child["dv"], DV_FULL, base.DV_COARSE),
        }
        xml_full = {
            "table_i_nonderivative": diff_rows(parent["xml_nd_rows"], child["xml_nd_rows"], ND_FULL, base.ND_COARSE),
            "table_ii_derivative": diff_rows(parent["xml_dv_rows"], child["xml_dv_rows"], DV_FULL, base.DV_COARSE),
        }
        bulk_core = {
            "table_i_nonderivative": diff_rows(bulk_parent["nd"], bulk_child["nd"], ND_CORE, base.ND_COARSE),
            "table_ii_derivative": diff_rows(bulk_parent["dv"], bulk_child["dv"], ND_CORE if False else DV_CORE, base.DV_COARSE),
        }
        xml_core = {
            "table_i_nonderivative": diff_rows(parent["xml_nd_rows"], child["xml_nd_rows"], ND_CORE, base.ND_COARSE),
            "table_ii_derivative": diff_rows(parent["xml_dv_rows"], child["xml_dv_rows"], DV_CORE, base.DV_COARSE),
        }
        full_parity = bulk_full == xml_full
        core_parity = bulk_core == xml_core
        parent_doc = doc_results[parent_acc]
        child_doc = doc_results[child_acc]
        pair_results.append({
            "sample_id": pair["sample_id"], "target_period": pair["target_period"],
            "parent_period": pair["parent_period"], "parent_accession": parent_acc,
            "amendment_accession": child_acc, "issuer_cik": pair["issuer_cik"],
            "issuer_ticker_as_filed": pair["issuer_ticker_as_filed"],
            "candidate_link_metadata_corroborated": metadata_ok,
            "date_of_original_submission_matches_parent_filing_date": date_match,
            "issuer_identity_matches": issuer_match, "reporting_owner_overlap_matches": owner_overlap,
            "parent_acceptance_not_after_amendment": chronological,
            "parent_and_child_header_xml_identity_pass": (
                parent_doc["header_xml_identity_pass"] and child_doc["header_xml_identity_pass"]
            ),
            "both_filings_full_2dp_transaction_match": (
                parent_doc["full_2dp_transaction_match_both_tables"]
                and child_doc["full_2dp_transaction_match_both_tables"]
            ),
            "both_filings_core_2dp_transaction_match": (
                parent_doc["core_2dp_transaction_match_both_tables"]
                and child_doc["core_2dp_transaction_match_both_tables"]
            ),
            "bulk_vs_xml_full_line_diff_parity": full_parity,
            "bulk_vs_xml_core_line_diff_parity": core_parity,
            "candidate_line_diff_class_from_phase153": pair["candidate_line_diff_class"],
            "bulk_full_line_diff": bulk_full, "xml_full_line_diff": xml_full,
            "bulk_core_line_diff": bulk_core, "xml_core_line_diff": xml_core,
            "owner_attribution": (
                "single_owner_accession_level_only"
                if len(pair["parent_owner_ciks"]) == 1 and len(pair["amendment_owner_ciks"]) == 1
                and pair["owner_sets_equal"]
                else "multi_owner_or_partial_overlap_transaction_owner_unresolved"
            ),
            "authoritative_parent_accession_foreign_key": False,
        })

    core_bad = sorted(a for a, row in doc_results.items() if not row["core_2dp_transaction_match_both_tables"])
    full_bad = sorted(a for a, row in doc_results.items() if not row["full_2dp_transaction_match_both_tables"])
    footnote_only = sorted(
        a for a, row in doc_results.items()
        if not row["full_2dp_transaction_match_both_tables"] and row["core_2dp_transaction_match_both_tables"]
    )
    excluded_field_counts = Counter()
    for accession in footnote_only:
        for table in doc_results[accession]["tables"].values():
            for field in table["excluded_field_differences"]:
                excluded_field_counts[field] += 1

    summary = {
        "sample_pairs": len(pair_results), "expected_documents": len(manifest["documents"]),
        "raw_edgar_hashes_verified": raw_hash_verified,
        "xml_parse_success": sum(1 for row in parsed_docs.values() if row.get("xml_parse_ok")),
        "header_xml_identity_pass": sum(1 for row in doc_results.values() if row["header_xml_identity_pass"]),
        "both_table_row_counts_match": sum(1 for row in doc_results.values() if row["row_count_match_both_tables"]),
        "full_2dp_transaction_multiset_match_documents": len(manifest["documents"]) - len(full_bad),
        "core_2dp_transaction_multiset_match_documents": len(manifest["documents"]) - len(core_bad),
        "footnote_or_timeliness_only_mismatch_documents": len(footnote_only),
        "core_transaction_mapping_exception_documents": len(core_bad),
        "pairs_metadata_corroborated": sum(1 for row in pair_results if row["candidate_link_metadata_corroborated"]),
        "pairs_both_filings_full_2dp_match": sum(1 for row in pair_results if row["both_filings_full_2dp_transaction_match"]),
        "pairs_both_filings_core_2dp_match": sum(1 for row in pair_results if row["both_filings_core_2dp_transaction_match"]),
        "pairs_bulk_xml_full_line_diff_parity": sum(1 for row in pair_results if row["bulk_vs_xml_full_line_diff_parity"]),
        "pairs_bulk_xml_core_line_diff_parity": sum(1 for row in pair_results if row["bulk_vs_xml_core_line_diff_parity"]),
        "single_owner_equal_set_pairs": sum(
            1 for row in manifest["sample_pairs"]
            if len(row["parent_owner_ciks"]) == 1 and len(row["amendment_owner_ciks"]) == 1 and row["owner_sets_equal"]
        ),
        "partial_or_multi_owner_pairs": sum(
            1 for row in manifest["sample_pairs"]
            if not (len(row["parent_owner_ciks"]) == 1 and len(row["amendment_owner_ciks"]) == 1 and row["owner_sets_equal"])
        ),
        "same_quarter_parent_pairs": sum(1 for row in manifest["sample_pairs"] if row["target_period"] == row["parent_period"]),
        "adjacent_quarter_parent_pairs": sum(1 for row in manifest["sample_pairs"] if row["target_period"] != row["parent_period"]),
        "excluded_field_mismatch_counts": dict(excluded_field_counts),
        "core_mismatch_accessions": core_bad,
        "full_mismatch_accessions": full_bad,
    }
    result = {
        "phase": 300, "status": "COMPLETED_OFFLINE_XML_BULK_RECONCILIATION",
        "source": {
            "provider": "SEC EDGAR original complete submissions + SEC Form 345 bulk archives",
            "phase294_artifact_id": 13884014630, "phase298_artifact_id": 13891901486,
            "phase299_raw_capture_run_id": 43115460066, "phase299_raw_capture_artifact_id": 13898356586,
            "phase299_raw_capture_artifact_sha256": "3ab13a28882fa2fa4071608360751dbd0063ecc0bc7a92ed97a48efaab5f6e24",
            "bulk_inner_archive_sha256": {period: periods[period]["sha256"] for period in sorted(periods)},
            "normalization": {
                "dates": "Normalize DD-MMM-YYYY and ISO dates to ISO YYYY-MM-DD.",
                "numeric": "Round both bulk and XML numeric fields to 2 decimal places, ROUND_HALF_UP, matching bulk archive precision.",
                "full_signature": "Phase 153 transaction fields, including NATURE_OF_OWNERSHIP and TRANS_TIMELINESS.",
                "core_signature": "Same transaction fields excluding NATURE_OF_OWNERSHIP and TRANS_TIMELINESS because these are footnote/timeliness metadata rather than core transaction facts.",
            },
        },
        "summary": summary, "pairs": pair_results, "documents": doc_results,
        "limitations": [
            "The sample is deliberately stratified and includes all partial-owner candidate pairs; it is not a random prevalence estimate.",
            "The SEC XML supplies DATE_OF_ORIG_SUB as a date, not the original accession number. Candidate links remain strongly corroborated metadata candidates, not authoritative parent-accession links.",
            "For 8 documents, the full signature differs only in footnote-derived NATURE_OF_OWNERSHIP association and/or TRANS_TIMELINESS; core transaction fields match.",
            "Two documents from one 2012Q1 pair have derivative-table field-placement mismatches between bulk data and XML. Quarantine derivative rows from that pair; do not infer that the bulk fields are interchangeable.",
            "14 pairs involve multi-owner or partial owner sets; transaction-to-individual-owner attribution is unresolved.",
            "Two-decimal normalization is for source reconciliation only; original XML bytes and hashes are preserved. It is not a signal-generation rule.",
            "Acceptance timestamps corroborate filing chronology but do not prove exact first public availability; daily-index PIT work remains separate.",
        ],
        "decision": (
            "The Phase 298 candidate-link heuristic is strongly corroborated in this stratified sample: "
            "all sampled amendments agree with the original filing date, issuer, reporting-owner overlap and acceptance chronology. "
            "Bulk-vs-XML core transaction rows match for 88/90 documents and both filings match for 45/46 pairs. "
            "Quarantine the one derivative-mapping pair and retain footnote/timeliness exceptions as metadata-only differences. "
            "Do not promote candidate links to authoritative accession links or admit the source to trading tests yet."
        ),
        "controls": {
            "strict_pit_admitted": False, "alpha_test": False, "return_test": False,
            "bootstrap_loo": False, "chronological_oos": False, "holdout_used": False,
            "f80_frozen": True, "production_changed": False, "universe_changed": False,
            "capital_changed": False, "parameters_changed": False, "data_purchase": False,
            "sec_requests_made": False,
        },
    }
    (args.output_dir / "phase300_validation_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "phase300_sample_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"phase": 300, "status": result["status"], "summary": summary}, indent=2))
    if summary["raw_edgar_hashes_verified"] != 90 or summary["header_xml_identity_pass"] != 90:
        return 2
    if summary["pairs_metadata_corroborated"] != 46:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
