#!/usr/bin/env python3
"""Phase 247: SEC N-PORT flattened-table UNIT/BALANCE schema contract."""
from __future__ import annotations
import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

AUDIT_DATE = "2026-11-09"


def parse_long_equity_share_balance(row):
    # The SEC flat-file column is UNIT; "units" is the raw XML element name.
    if "UNIT" not in row:
        if "UNITS" in row:
            return None, "XML_ALIAS_USED_AS_FLAT_COLUMN"
        return None, "MISSING_UNIT_COLUMN"
    unit = str(row.get("UNIT") or "").strip().upper()
    alias = str(row.get("UNITS") or "").strip().upper()
    if alias and unit and alias != unit:
        return None, "UNIT_ALIAS_CONFLICT"
    if unit != "NS":
        return None, "NOT_NUMBER_OF_SHARES"
    if str(row.get("ASSET_CAT") or "").strip().upper() != "EC":
        return None, "NOT_EQUITY_ASSET"
    if str(row.get("PAYOFF_PROFILE") or "").strip().upper() != "LONG":
        return None, "NOT_EXPLICIT_LONG"
    raw = row.get("BALANCE")
    if raw is None or not str(raw).strip():
        return None, "MISSING_BALANCE"
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError):
        return None, "INVALID_BALANCE"
    if not value.is_finite():
        return None, "NONFINITE_BALANCE"
    if value <= 0:
        return None, "NONPOSITIVE_BALANCE"
    return value, "ELIGIBLE_LONG_EQUITY_SHARES"


def legacy_phase27o_share_balance(row):
    # Reproduce the old flattened-TSV lookup to make the defect testable.
    unit = str(row.get("UNITS") or "").strip().upper()
    try:
        balance = Decimal(str(row.get("BALANCE") or "0").strip())
    except (InvalidOperation, ValueError):
        return Decimal("0")
    return balance if balance > 0 and unit == "NS" else Decimal("0")


def build_audit():
    return {
        "phase": 247,
        "audit_date": AUDIT_DATE,
        "status": "LEGACY_NPORT_FLOW_PILOT_SCHEMA_DEFECT_CONFIRMED_NO_ALPHA",
        "official_flattened_table_contract": {
            "table": "FUND_REPORTED_HOLDING",
            "balance_field": "BALANCE",
            "unit_field": "UNIT",
            "share_unit_code_observed_in_official_xml": "NS",
            "equity_asset_category": "EC",
            "long_payoff_profile": "LONG"
        },
        "legacy_phase27o_audit": {
            "branch": "phase27o-nport-pit-flow-correction",
            "workflow": ".github/workflows/fase27o_nport_pit_flow_correction.yml",
            "script_called": "Nueva_Estrategia_Fase27N_SEC_NPORT_PIT_FlowPilot.py",
            "reads_sec_flattened_tsv": True,
            "unit_lookup_used_by_script": "UNITS",
            "official_flattened_unit_field": "UNIT",
            "root_cause": "The raw XML tag spelling was used as the flattened TSV column name.",
            "consequence": "The documented TSV has no UNITS column; the NS test never succeeds and share balances remain zero.",
            "downstream_consequence": "The ranker requires positive prior and current share balances and cannot form valid share-growth candidates.",
            "workflow_output_independently_verified": False,
            "legacy_branch_modified_or_rerun": False
        },
        "official_history_and_publication": {
            "dataset_period": "2019-10 through 2026-09",
            "quarterly_archives_listed_as_of_2026_11_09": 28,
            "dataset_refresh_frequency": "quarterly",
            "listed_archive_size_mb_min": 228.89,
            "listed_archive_size_mb_max": 690.83,
            "public_filings_only": True,
            "includes_as_filed_amendments": True,
            "complete_acceptance_metadata_in_dataset": False,
            "current_public_regime": "Only the third month of each fund fiscal quarter is public upon filing; first and second month reports remain nonpublic.",
            "current_filing_deadline": "60 days after fiscal quarter end",
            "large_fund_amendment_compliance": "2027-11-17",
            "small_fund_amendment_compliance": "2028-05-18"
        },
        "pit_requirements": {
            "report_date_is_knowledge_time": False,
            "compiled_zip_is_live_pit_feed": False,
            "accession_is_vintage_key": True,
            "preserve_original_and_each_amendment": True,
            "obtain_accession_level_accepted_and_filing_dates": True,
            "amendments_are_state_corrections_not_new_trades": True,
            "fund_key": ["CIK", "SERIES_ID"],
            "holding_key": ["ACCESSION_NUMBER", "HOLDING_ID"],
            "security_identity": "Effective-dated CUSIP/ISIN crosswalk; ticker corroborative only"
        },
        "research_disposition": {
            "phase27k_zero_ticker_output": "Identifier-filter defect; not evidence against N-PORT.",
            "phase27l_coverage": "267-324 distinct frozen-universe tickers across eight annual snapshots; not a full census.",
            "phase27o": "Quarantine pending corrected flattened-schema parser and full validation.",
            "next_design": "Asynchronous per-series public-report events; amendments state-only; aggregate after actual dissemination.",
            "strict_pit_admitted": False,
            "alpha_test_authorized": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "holdout_used": False
        },
        "sources": [
            "https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets",
            "https://www.sec.gov/files/nport_readme.pdf",
            "https://www.sec.gov/files/formn-port.pdf",
            "https://www.sec.gov/Archives/edgar/data/1100663/000100472626010078/primary_doc.xml",
            "https://www.sec.gov/Archives/edgar/data/1424958/0001145549-25-044643-index.htm",
            "https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/determine-status-my-filing",
            "https://www.federalregister.gov/documents/2025/04/22/2025-06861/form-n-port-and-form-n-cen-reporting-guidance-on-open-end-fund-liquidity-risk-management-programs-delay-of"
        ]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase247_output/phase247_nport_unit_field_contract.json")
    args = parser.parse_args()
    payload = build_audit()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": 247,
        "status": payload["status"],
        "official_flat_field": "UNIT",
        "legacy_lookup_field": "UNITS",
        "strict_pit_admitted": payload["research_disposition"]["strict_pit_admitted"],
        "alpha_test_authorized": payload["research_disposition"]["alpha_test_authorized"]
    }, indent=2))


if __name__ == "__main__":
    main()
