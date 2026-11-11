"""Phase 279: SEC Insider Transactions bulk-history and PIT feasibility gate.

Documentation-only, fail-closed source audit. No SEC requests or archive downloads.
"""
from __future__ import annotations

from typing import Any

SOURCE_URL = "https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets"
README_URL = "https://www.sec.gov/files/insider_transactions_readme.pdf"
COVERAGE_START = "2006-01"
COVERAGE_END = "2026-09"
EXPECTED_QUARTERS = 83

TABLE_KEYS = {
    "SUBMISSION": ["ACCESSION_NUMBER"],
    "REPORTINGOWNER": ["ACCESSION_NUMBER", "RPTOWNERCIK"],
    "NONDERIV_TRANS": ["ACCESSION_NUMBER", "NONDERIV_TRANS_SK"],
    "NONDERIV_HOLDING": ["ACCESSION_NUMBER", "NONDERIV_HOLDING_SK"],
    "DERIV_TRANS": ["ACCESSION_NUMBER", "DERIV_TRANS_SK"],
    "DERIV_HOLDING": ["ACCESSION_NUMBER", "DERIV_HOLDING_SK"],
    "FOOTNOTES": ["ACCESSION_NUMBER", "FOOTNOTE_ID"],
    "OWNER_SIGNATURE": ["ACCESSION_NUMBER", "OWNERSIGNATURENAME"],
}

SUBMISSION_FIELDS = {
    "ACCESSION_NUMBER", "FILING_DATE", "PERIOD_OF_REPORT", "DATE_OF_ORIG_SUB",
    "DOCUMENT_TYPE", "ISSUERCIK", "ISSUERNAME", "ISSUERTRADINGSYMBOL", "REMARKS",
}
NONDERIV_TRANSACTION_FIELDS = {
    "ACCESSION_NUMBER", "NONDERIV_TRANS_SK", "SECURITY_TITLE", "TRANS_DATE",
    "TRANS_CODE", "TRANS_TIMELINESS", "TRANS_SHARES", "TRANS_PRICEPERSHARE",
    "TRANS_ACQUIRED_DISP_CD", "DIRECT_INDIRECT_OWNERSHIP", "NATURE_OF_OWNERSHIP",
}

GATES = {
    "bulk_history_documented": True,
    "raw_archive_bytes_verified": False,
    "representative_archive_schema_verified": False,
    "edgar_acceptance_time_join_verified": False,
    "first_public_receipt_verified": False,
    "amendment_accession_lineage_verified": False,
    "multi_owner_transaction_attribution_verified": False,
    "effective_dated_security_class_identity_verified": False,
    "historical_active_delisted_universe_coverage_verified": False,
    "strict_pit_admitted": False,
    "alpha_test_authorized": False,
    "holdout_used": False,
    "f80_frozen": True,
    "production_changed": False,
    "universe_changed": False,
    "capital_changed": False,
}


def quarter_labels(start_year: int = 2006, start_quarter: int = 1,
                   end_year: int = 2026, end_quarter: int = 3) -> list[str]:
    if not (1 <= start_quarter <= 4 and 1 <= end_quarter <= 4):
        raise ValueError("quarter must be 1..4")
    if (start_year, start_quarter) > (end_year, end_quarter):
        raise ValueError("start must not exceed end")
    out: list[str] = []
    year, quarter = start_year, start_quarter
    while (year, quarter) <= (end_year, end_quarter):
        out.append(f"{year}Q{quarter}")
        if quarter == 4:
            year, quarter = year + 1, 1
        else:
            quarter += 1
    return out


def build_result() -> dict[str, Any]:
    quarters = quarter_labels()
    return {
        "phase": 279,
        "status": "DOCUMENTED_LONG_HISTORY_CANDIDATE_SCHEMA_AND_PIT_GATES_OPEN",
        "source": {
            "name": "SEC Insider Transactions Data Sets",
            "url": SOURCE_URL,
            "readme_url": README_URL,
            "coverage_start": COVERAGE_START,
            "coverage_end": COVERAGE_END,
            "quarterly_archives": len(quarters),
            "first_archive": quarters[0],
            "last_archive": quarters[-1],
            "sec_listed_zip_size_mb_sum": 887.43,
            "sec_listed_zip_size_mb_min": 7.59,
            "sec_listed_zip_size_mb_max": 16.51,
            "data_types": ["Form 3", "Form 3/A", "Form 4", "Form 4/A", "Form 5", "Form 5/A"],
            "as_filed": True,
            "includes_amendments": True,
            "refresh_frequency": "quarterly",
            "archive_bytes_downloaded": False,
        },
        "documented_tables": TABLE_KEYS,
        "schema_contract": {
            "submission_fields_documented": sorted(SUBMISSION_FIELDS),
            "nonderiv_transaction_fields_documented": sorted(NONDERIV_TRANSACTION_FIELDS),
            "submission_has_acceptance_datetime": False,
            "transaction_table_has_reporting_owner_cik": False,
            "transaction_table_has_permanent_security_id": False,
            "footnotes_table_available": True,
            "aff10b5one": {
                "present_in_documented_readme": False,
                "sec_page_note": "2023-2025 archives updated in July 2025 to include AFF10B5ONE; future datasets processed similarly",
                "missing_means_false": False,
                "submission_level_not_transaction_level": True,
                "checkbox_alone_proves_discretionary_trading": False,
            },
        },
        "pit_and_identity": {
            "filing_date_is_date_only": True,
            "period_of_report_is_knowledge_time": False,
            "date_of_orig_sub_is_parent_accession": False,
            "acceptance_time_requires_accession_join": True,
            "acceptance_time_is_exact_first_public_receipt": False,
            "multi_owner_transaction_join_requires_raw_xml_or_exclusion": True,
            "aff10b5one_must_not_be_broadcast_as_line_level_plan_label": True,
            "issuer_ticker_is_permanent_security_identity": False,
            "security_title_is_sufficient_class_identity": False,
            "form4a_is_new_transaction_signal": False,
            "amendments_must_remain_separate_vintages": True,
            "transaction_code_p_alone_proves_open_market": False,
            "explicit_footnote_review_required": True,
        },
        "recommended_next_gate": [
            "Acquire 2006Q1, 2012Q1, 2023Q2, 2025Q3 and 2026Q3 archives with immutable ZIP hashes and metadata manifests.",
            "Reconcile sampled ACCESSION_NUMBER and DOCUMENT_TYPE values to original EDGAR filing indices and accepted timestamps.",
            "Verify the post-July-2025 AFF10B5ONE column and distinguish absent, null, false and true across schema eras.",
            "Use FOOTNOTES to reproduce the Phase 271 explicit open-market screen; keep plan, compensation, private-purchase and mechanical exclusions separate.",
            "For accessions with multiple reporting owners, parse original ownership XML or exclude transaction-to-owner attribution; do not create a many-to-many join.",
            "Resolve issuer CIK, as-filed ticker and SECURITY_TITLE to effective-dated security/class identity including delisted names.",
            "Preserve every Form 4/A as a new knowledge-time vintage and reconcile DATE_OF_ORIG_SUB without treating it as a parent accession.",
        ],
        "gates": dict(GATES),
        "controls": {
            "raw_sec_requests": 0,
            "raw_archives_downloaded": 0,
            "vendor_contact": False,
            "purchase_or_license": False,
            "returns_tested": False,
            "bootstrap_loo_tested": False,
            "chronological_oos_tested": False,
            "legacy_holdout_reused": False,
        },
    }


def validate_result(result: dict[str, Any]) -> None:
    source = result["source"]
    if source["quarterly_archives"] != EXPECTED_QUARTERS:
        raise ValueError("unexpected quarterly archive count")
    if source["first_archive"] != "2006Q1" or source["last_archive"] != "2026Q3":
        raise ValueError("unexpected archive endpoints")
    if set(result["documented_tables"]) != set(TABLE_KEYS):
        raise ValueError("table inventory mismatch")
    if result["documented_tables"] != TABLE_KEYS:
        raise ValueError("table keys mismatch")
    gates = result["gates"]
    if gates["strict_pit_admitted"] or gates["alpha_test_authorized"]:
        raise ValueError("source cannot be admitted by a documentation-only audit")
    if not gates["f80_frozen"] or gates["production_changed"] or gates["holdout_used"]:
        raise ValueError("research controls violated")
    if result["schema_contract"]["submission_has_acceptance_datetime"]:
        raise ValueError("acceptance datetime is not in documented SUBMISSION schema")
    if result["schema_contract"]["transaction_table_has_reporting_owner_cik"]:
        raise ValueError("transaction-owner attribution cannot be assumed from flattened tables")
    if result["schema_contract"]["transaction_table_has_permanent_security_id"]:
        raise ValueError("no permanent security identifier is documented in transaction rows")
    if result["pit_and_identity"]["transaction_code_p_alone_proves_open_market"]:
        raise ValueError("P code alone does not prove open-market execution")
    if result["controls"]["raw_sec_requests"] != 0 or result["controls"]["raw_archives_downloaded"] != 0:
        raise ValueError("documentation-only audit unexpectedly accessed SEC data")


def main() -> dict[str, Any]:
    result = build_result()
    validate_result(result)
    return result


if __name__ == "__main__":
    import json
    print(json.dumps(main(), indent=2, sort_keys=True))
