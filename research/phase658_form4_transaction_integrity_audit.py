#!/usr/bin/env python3
"""Phase 658: offline integrity and amendment-state audit of the live Form 4 ledger.

This module never contacts the SEC, downloads prices, or changes the source ledger.
All thresholds are diagnostic review triggers; raw source rows are retained.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

PHASE = 658
LATE_DISCLOSURE_THRESHOLD_DAYS = 30
EXTREME_PRICE_REVIEW_THRESHOLD = Decimal("10000")
ELIGIBILITY_FIELDS = (
    "research_observation_eligible",
    "signal_eligible",
    "public_availability_certified",
    "same_day_intraday_use_authorized",
    "security_identity_verified",
    "historical_f80_membership_verified",
    "owner_attribution_verified",
    "transaction_semantics_verified",
    "economic_event_new_trade_authorized",
)

MANUAL_ADJUDICATIONS = [
    {
        "accession": "0002125667-26-000005",
        "symbol": "SHMD",
        "classification": "SOURCE_DOCUMENT_CHRONOLOGY_AND_PRICE_INCONSISTENCY",
        "filing_date": "2026-11-25",
        "period_of_report": "2026-11-24",
        "transaction_date_in_table": "2006-11-25",
        "shares": 60000,
        "reported_price_per_share_usd": 1731429,
        "transaction_code": "P",
        "disposition": "Quarantine from transaction-value aggregation and any signal review; preserve the raw filing and row.",
        "sec_index_url": "https://www.sec.gov/Archives/edgar/data/1987240/000212566726000005/0002125667-26-000005-index.htm",
        "sec_primary_document_url": "https://www.sec.gov/Archives/edgar/data/1987240/000212566726000005/xslF345X06/primary_doc.xml"
    },
    {
        "accession": "0001104659-26-130067",
        "symbol": "N/A",
        "classification": "FORM4A_FINAL_NAV_VALUE_UPDATE_NOT_A_SECOND_TRADE",
        "filing_date": "2026-11-19",
        "period_of_report": "2026-09-01",
        "original_filing_date": "2026-09-03",
        "reporting_owner_count": 5,
        "transaction_code": "P",
        "reported_shares": "207178.32",
        "reported_price_per_share_usd": "26.47",
        "disposition": "Treat as a state/value update to the September 1 investment, not as a second purchase event. No owner-to-line attribution or F80 security identity is established.",
        "sec_index_url": "https://www.sec.gov/Archives/edgar/data/1954360/000110465926130067/0001104659-26-130067-index.htm",
        "sec_primary_document_url": "https://www.sec.gov/Archives/edgar/data/1626970/000110465926130067/xslF345X06/tm2630207-1_4aseq1.xml"
    },
    {
        "accession": "0001493152-26-053612",
        "symbol": "TRON",
        "classification": "FORM4A_REPORTING_PERSON_UPDATE_NO_NEW_ECONOMIC_EVENT",
        "filing_date": "2026-11-23",
        "period_of_report": "2025-08-27",
        "original_filing_date": "2026-04-08",
        "reporting_owner_count": 2,
        "transaction_rows": 4,
        "transaction_codes": ["A", "M"],
        "disposition": "The amendment says it solely adds Bravemorning as a joint reporting person and makes no other changes. Do not count the repeated A/M rows as new trades.",
        "sec_index_url": "https://www.sec.gov/Archives/edgar/data/1956744/000149315226053612/0001493152-26-053612-index.htm",
        "sec_primary_document_url": "https://www.sec.gov/Archives/edgar/data/1956744/000149315226053612/xslF345X06/ownership.xml"
    },
    {
        "accession": "0001493152-26-053593",
        "symbol": "BNAI",
        "classification": "STALE_FORM4_GRANTS_AND_OPTION_EXERCISE_NOT_OPEN_MARKET_TRADE",
        "filing_date": "2026-11-20",
        "period_of_report": "2025-05-09",
        "transaction_codes": ["A", "M"],
        "transaction_lags_days": [560, 485, 192, 192],
        "disposition": "Retain only at its actual filing/first-seen time. The source describes incentive-plan grants and an option exercise; do not treat these A/M rows as discretionary P/S trades.",
        "sec_index_url": "https://www.sec.gov/Archives/edgar/data/1838163/000149315226053593/0001493152-26-053593-index.htm",
        "sec_primary_document_url": "https://www.sec.gov/Archives/edgar/data/1838163/000149315226053593/xslF345X06/ownership.xml"
    }
]


def _truth(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _date(value: str | None) -> date | None:
    token = str(value or "").strip()
    if not token:
        return None
    try:
        return date.fromisoformat(token[:10])
    except ValueError:
        return None


def _decimal(value: str | None) -> Decimal | None:
    token = str(value or "").strip()
    if not token:
        return None
    try:
        number = Decimal(token)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def summarize_rows(rows: list[dict[str, str]], source_sha256: str | None = None,
                   source_path: str | None = None) -> dict:
    headers = [row for row in rows if row.get("detail_type") == "filing_header"]
    transactions = [row for row in rows if row.get("detail_type") == "transaction_row"]

    forms = Counter(str(row.get("form") or "UNKNOWN") for row in headers)
    by_code: dict[str, dict] = defaultdict(
        lambda: {"rows": 0, "accessions": set(), "symbols": set(),
                 "ten_b5_yes_rows": 0, "ten_b5_no_rows": 0}
    )
    owner_status = Counter()
    eligibility_true = Counter()
    chronology_anomalies = []
    extreme_price_reviews = []
    late_disclosures = []
    transaction_after_filing = []

    for row in transactions:
        code = str(row.get("transaction_code") or "BLANK")
        item = by_code[code]
        item["rows"] += 1
        accession = str(row.get("accession") or "")
        symbol = str(row.get("issuer_trading_symbol_normalized") or "")
        if accession:
            item["accessions"].add(accession)
        if symbol:
            item["symbols"].add(symbol)

        flag = str(row.get("aff10b5one_filing_flag") or "").strip().lower()
        if flag == "yes":
            item["ten_b5_yes_rows"] += 1
        elif flag == "no":
            item["ten_b5_no_rows"] += 1

        owner_status[str(row.get("owner_attribution_status") or "UNKNOWN")] += 1
        for field in ELIGIBILITY_FIELDS:
            if _truth(row.get(field)):
                eligibility_true[field] += 1

        transaction_date = _date(row.get("transaction_date"))
        period_date = _date(row.get("period_of_report"))
        filing_date = _date(row.get("filing_date"))

        if transaction_date and period_date and transaction_date < period_date:
            chronology_anomalies.append({
                "accession": accession,
                "symbol": symbol,
                "transaction_code": code,
                "transaction_date": transaction_date.isoformat(),
                "period_of_report": period_date.isoformat(),
                "days_before_period_of_report": (period_date - transaction_date).days,
            })

        if transaction_date and filing_date:
            lag_days = (filing_date - transaction_date).days
            if lag_days > LATE_DISCLOSURE_THRESHOLD_DAYS:
                late_disclosures.append({
                    "accession": accession,
                    "symbol": symbol,
                    "transaction_code": code,
                    "transaction_date": transaction_date.isoformat(),
                    "filing_date": filing_date.isoformat(),
                    "filing_lag_days": lag_days,
                })
            elif lag_days < 0:
                transaction_after_filing.append({
                    "accession": accession,
                    "symbol": symbol,
                    "transaction_code": code,
                    "transaction_date": transaction_date.isoformat(),
                    "filing_date": filing_date.isoformat(),
                    "days_after_filing": -lag_days,
                })

        price = _decimal(row.get("price_per_share_numeric"))
        if price is not None and (price > EXTREME_PRICE_REVIEW_THRESHOLD or price < 0):
            extreme_price_reviews.append({
                "accession": accession,
                "symbol": symbol,
                "transaction_code": code,
                "transaction_date": row.get("transaction_date") or None,
                "shares": row.get("shares_numeric") or None,
                "price_per_share_numeric": str(price),
                "review_trigger": "price_above_10000_or_negative",
            })

    tx_by_accession = Counter(str(row.get("accession") or "") for row in transactions)
    amendment_lineage_gaps = []
    for row in headers:
        if _truth(row.get("is_amendment")) and not str(row.get("previous_accession") or "").strip():
            accession = str(row.get("accession") or "")
            amendment_lineage_gaps.append({
                "accession": accession,
                "form": row.get("form"),
                "issuer_name": row.get("issuer_name"),
                "symbol": row.get("issuer_trading_symbol_normalized"),
                "filing_date": row.get("filing_date"),
                "period_of_report": row.get("period_of_report"),
                "transaction_rows": tx_by_accession.get(accession, 0),
                "previous_accession_stored": False,
            })

    code_summary = {}
    for code, item in sorted(by_code.items()):
        code_summary[code] = {
            "rows": item["rows"],
            "unique_accessions": len(item["accessions"]),
            "unique_symbol_strings": len(item["symbols"]),
            "ten_b5_yes_rows": item["ten_b5_yes_rows"],
            "ten_b5_no_rows": item["ten_b5_no_rows"],
        }

    return {
        "phase": PHASE,
        "source": {
            "path": source_path,
            "sha256": source_sha256,
            "filing_header_rows": len(headers),
            "transaction_rows": len(transactions),
            "unique_accessions": len({str(row.get("accession") or "") for row in headers if row.get("accession")}),
            "unique_symbol_strings": len({str(row.get("issuer_trading_symbol_normalized") or "") for row in transactions if row.get("issuer_trading_symbol_normalized")}),
            "form_counts": dict(sorted(forms.items())),
        },
        "diagnostic_thresholds": {
            "late_disclosure_calendar_days": LATE_DISCLOSURE_THRESHOLD_DAYS,
            "extreme_price_review_usd_per_share": str(EXTREME_PRICE_REVIEW_THRESHOLD),
            "thresholds_are_review_triggers_not_automatic_row_deletions": True,
        },
        "transaction_codes": code_summary,
        "owner_attribution_status_rows": dict(sorted(owner_status.items())),
        "eligibility_true_row_counts": {field: eligibility_true.get(field, 0) for field in ELIGIBILITY_FIELDS},
        "anomalies": {
            "transaction_date_precedes_period_of_report": chronology_anomalies,
            "extreme_price_review": extreme_price_reviews,
            "filing_lag_over_30_calendar_days": late_disclosures,
            "transaction_date_after_filing_date": transaction_after_filing,
            "amendment_without_stored_previous_accession": amendment_lineage_gaps,
        },
        "manual_source_adjudications": MANUAL_ADJUDICATIONS,
        "controls": {
            "raw_source_rows_deleted": False,
            "market_price_series_downloaded": False,
            "forward_returns_inspected": False,
            "event_study_run": False,
            "oos_run": False,
            "bootstrap_run": False,
            "loo_run": False,
            "holdout_touched": False,
            "signal_promoted": False,
            "incremental_alpha_demonstrated": False,
            "f80_top20_partial50_baseline_c20_frozen": True,
            "paid_data_or_vendor_contact": False,
            "data_budget_usd": 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transactions", required=True, help="Path to transaction_details.csv")
    parser.add_argument("--output-dir", required=True, help="Directory for the JSON audit output")
    args = parser.parse_args()

    source = Path(args.transactions)
    raw = source.read_bytes()
    decoded = raw.decode("utf-8-sig")
    reader = csv.DictReader(decoded.splitlines())
    if not reader.fieldnames:
        raise ValueError("Transaction ledger has no header.")
    required = {"detail_type", "accession", "form", "is_amendment", "previous_accession",
                "filing_date", "period_of_report", "transaction_date", "transaction_code",
                "issuer_trading_symbol_normalized", "price_per_share_numeric",
                "aff10b5one_filing_flag", "owner_attribution_status"}
    missing = required - set(reader.fieldnames)
    if missing:
        raise ValueError(f"Transaction ledger missing required fields: {sorted(missing)}")
    rows = list(reader)
    summary = summarize_rows(rows, hashlib.sha256(raw).hexdigest(), str(source))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "summary.json"
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": PHASE,
        "filing_header_rows": summary["source"]["filing_header_rows"],
        "transaction_rows": summary["source"]["transaction_rows"],
        "chronology_anomalies": len(summary["anomalies"]["transaction_date_precedes_period_of_report"]),
        "extreme_price_reviews": len(summary["anomalies"]["extreme_price_review"]),
        "late_disclosure_rows": len(summary["anomalies"]["filing_lag_over_30_calendar_days"]),
        "amendment_lineage_gaps": len(summary["anomalies"]["amendment_without_stored_previous_accession"]),
        "signal_eligible_rows": summary["eligibility_true_row_counts"]["signal_eligible"],
        "output": str(output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
