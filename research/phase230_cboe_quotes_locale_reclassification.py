#!/usr/bin/env python3
"""Phase 230: metadata-level reclassification of the Cboe Option Quotes sample date gate."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_ARCHIVE_SHA256 = "7645a6cc94f1a984e98264a4b494f748e373c30ecde85de25ceadb83a5c56782"
EXPECTED_PHASE175_ARTIFACT_SHA256 = "7a3f988b6edb6e41e987399f94b85122ae7b712b8922326203e03087e877ea7f"
EXPECTED_PHASE175_SUMMARY_SHA256 = "c69f4aa08b220d00a11903339d57c60a0deb6c84492286487d0fff74440f831d"


def _count(data: dict[str, Any], key: str) -> int:
    return int(data.get(key, 0))


def audit(payload: dict[str, Any], source_summary_sha256: str | None = None) -> dict[str, Any]:
    if source_summary_sha256 is not None and source_summary_sha256 != EXPECTED_PHASE175_SUMMARY_SHA256:
        raise ValueError("phase175_summary_sha_mismatch")
    if payload.get("phase") != 175 or payload.get("download_status") != "PASS":
        raise ValueError("phase175_source_not_complete")
    if payload.get("archive_sha256") != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("cboe_sample_archive_sha_mismatch")
    members = payload.get("members", [])
    if len(members) != 5 or payload.get("data_member_count") != 5:
        raise ValueError("unexpected_sample_member_count")
    if not payload.get("date_locale_diagnostic_complete"):
        raise ValueError("date_locale_diagnostic_incomplete")

    total_rows = original_invalid = expiration_unique = expiration_ambiguous = 0
    timestamp_unique = timestamp_ambiguous = timestamp_unparsed = 0
    originally_failed_unique = originally_failed_ambiguous = 0
    expiration_formats: dict[str, int] = {}
    quote_formats: dict[str, int] = {}
    member_summary = []
    for member in members:
        diagnostic = member.get("date_locale_diagnostics") or {}
        if not diagnostic.get("diagnostic_complete"):
            raise ValueError("member_locale_diagnostic_incomplete")
        rows = _count(diagnostic, "populated_rows")
        total_rows += rows
        original_bad = _count(member, "invalid_contract_rows")
        original_invalid += original_bad
        expiration = diagnostic.get("expiration_interpretation_counts", {})
        quote_datetime = diagnostic.get("quote_datetime_interpretation_counts", {})
        exp_unique = _count(expiration, "single_format_interpretation") + _count(expiration, "equivalent_multiple_formats")
        exp_ambiguous = _count(expiration, "ambiguous_multiple_interpretations")
        exp_unparsed = _count(expiration, "no_parse") + _count(expiration, "missing")
        qdt_unique = _count(quote_datetime, "single_format_interpretation") + _count(quote_datetime, "equivalent_multiple_formats")
        qdt_ambiguous = _count(quote_datetime, "ambiguous_multiple_interpretations")
        qdt_unparsed = _count(quote_datetime, "no_parse") + _count(quote_datetime, "missing")
        if exp_unique + exp_ambiguous + exp_unparsed != rows:
            raise ValueError("expiration_interpretation_counts_do_not_sum_to_rows")
        if qdt_unique + qdt_ambiguous + qdt_unparsed != rows:
            raise ValueError("quote_datetime_interpretation_counts_do_not_sum_to_rows")
        expiration_unique += exp_unique
        expiration_ambiguous += exp_ambiguous
        timestamp_unique += qdt_unique
        timestamp_ambiguous += qdt_ambiguous
        timestamp_unparsed += qdt_unparsed
        if original_bad:
            originally_failed_unique += exp_unique
            originally_failed_ambiguous += exp_ambiguous
        for key, value in diagnostic.get("expiration_candidate_format_counts", {}).items():
            expiration_formats[key] = expiration_formats.get(key, 0) + int(value)
        for key, value in diagnostic.get("quote_datetime_candidate_format_counts", {}).items():
            quote_formats[key] = quote_formats.get(key, 0) + int(value)
        member_summary.append({
            "member_index": member.get("member_index"),
            "header_columns": member.get("header_columns"),
            "populated_rows": rows,
            "phase174_invalid_contract_rows": original_bad,
            "expiration_unique_interpretation_rows": exp_unique,
            "expiration_ambiguous_rows": exp_ambiguous,
            "quote_datetime_unique_interpretation_rows": qdt_unique,
            "quote_datetime_ambiguous_rows": qdt_ambiguous,
            "quote_datetime_formats": diagnostic.get("quote_datetime_candidate_format_counts", {}),
            "quote_datetime_min": diagnostic.get("quote_datetime_min_unique_interpretation"),
            "quote_datetime_max": diagnostic.get("quote_datetime_max_unique_interpretation"),
            "expiration_min_unique": diagnostic.get("expiration_min_unique_interpretation"),
            "expiration_max_unique": diagnostic.get("expiration_max_unique_interpretation"),
        })

    if total_rows != 115617 or original_invalid != 94607:
        raise ValueError("unexpected_phase174_row_or_failure_totals")
    if (expiration_unique, expiration_ambiguous) != (112313, 3304):
        raise ValueError("unexpected_expiration_reclassification_totals")
    if (timestamp_unique, timestamp_ambiguous, timestamp_unparsed) != (115617, 0, 0):
        raise ValueError("unexpected_quote_datetime_interpretation_totals")
    if (originally_failed_unique, originally_failed_ambiguous) != (91303, 3304):
        raise ValueError("unexpected_original_failure_reclassification")

    return {
        "phase": 230,
        "status": "DATE_LOCALE_RECLASSIFICATION_COMPLETE_FULL_ROW_GATE_NOT_RECOMPUTED",
        "source": {
            "product": "Cboe Option Quotes / Option Quote Intervals",
            "sample_url": payload.get("sample_url"),
            "archive_sha256": payload.get("archive_sha256"),
            "archive_bytes": payload.get("archive_bytes"),
            "phase175_run_id": 42562292743,
            "phase175_artifact_id": 13649604168,
            "phase175_artifact_zip_sha256": EXPECTED_PHASE175_ARTIFACT_SHA256,
            "phase175_condensed_summary_sha256": EXPECTED_PHASE175_SUMMARY_SHA256,
            "phase174_run_id": 42562292847,
            "phase174_artifact_id": 13650205761,
        },
        "counts": {
            "data_members": len(members),
            "populated_row_instances": total_rows,
            "phase174_iso_only_invalid_contract_row_instances": original_invalid,
            "expiration_unique_interpretation_row_instances_all_members": expiration_unique,
            "expiration_ambiguous_row_instances_all_members": expiration_ambiguous,
            "expiration_unparsed_or_missing_row_instances": 0,
            "originally_failed_rows_with_unique_expiration_interpretation": originally_failed_unique,
            "originally_failed_rows_still_ambiguous": originally_failed_ambiguous,
            "quote_datetime_unique_interpretation_row_instances": timestamp_unique,
            "quote_datetime_ambiguous_row_instances": timestamp_ambiguous,
            "quote_datetime_unparsed_or_missing_row_instances": timestamp_unparsed,
        },
        "format_counts": {
            "expiration_candidate_formats": dict(sorted(expiration_formats.items())),
            "quote_datetime_candidate_formats": dict(sorted(quote_formats.items())),
            "schema_variants": payload.get("schema_variant_counts", {}),
        },
        "members": member_summary,
        "interpretation": {
            "phase174_failed_94607_rows_because_expiration_parser_only_accepted_iso_extended_dates": True,
            "91303_of_those_row_instances_have_one_unique_non_iso_expiration_interpretation": True,
            "3304_row_instances_remain_ambiguous_and_must_be_quarantined": True,
            "all_115617_quote_datetime_values_have_one_unique_candidate_interpretation": True,
            "2023_sample_members_use_us_slash_minute_timestamps_while_2022_member_uses_iso_seconds": True,
            "this_is_a_metadata_level_reclassification_not_a_full_raw_row_reparse": True,
            "row_level_contract_keys_duplicates_and_numeric_gates_were_not_recomputed": True,
            "112313_counts_row_instances_across_five_members_not_unique_contracts": True,
        },
        "limitations": [
            "No raw sample rows, symbols, strikes, roots, expirations, or contract keys were retained by Phase 174/175; unique contracts cannot be counted or deduplicated here.",
            "The 3304 ambiguous expiration row instances have multiple distinct locale interpretations and are not assigned a date.",
            "The sample contains only five members spanning two quote dates; it does not establish historical coverage, interval continuity, inactive/delisted-underlying coverage, or first receipt.",
            "A full parser rerun with unique-only locale handling is still required before any sample-level row/schema gate can be marked passed.",
            "First-receipt vintages, immutable corrections, licensing, and broad point-in-time universe coverage remain unverified."
        ],
        "admission": {
            "sample_schema_admitted": False,
            "strict_pit_admitted": False,
            "alpha_admitted": False,
            "forward_returns_tested": False,
            "bootstrap_loo_tested": False,
            "chronological_oos_tested": False,
            "final_holdout_used": False,
            "production_changed": False,
            "universe_changed": False,
            "f80_changed": False,
            "f80_status": "FROZEN",
            "legacy_holdout_status": "CONSUMED_NOT_PRISTINE",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase175-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_bytes = args.phase175_json.read_bytes()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    result = audit(json.loads(source_bytes), source_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
