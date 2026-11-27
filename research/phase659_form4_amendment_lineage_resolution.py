#!/usr/bin/env python3
"""Phase 659: resolve Form 4/A original-accession lineage without rewriting source ledgers.

The SEC source adjudications are frozen in an append-only JSON sidecar. This audit
only reads repository data and never contacts the SEC or downloads market prices.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

PHASE = 659


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader)


def canonical(row: dict) -> dict:
    fields = (
        "table_type", "row_index", "security_title", "transaction_date",
        "transaction_code", "shares", "price", "acquired_disposed_code",
        "exercise_date", "expiration_date", "underlying_security_title",
        "underlying_shares",
    )
    return {field: str(row.get(field, "") or "") for field in fields}


def ledger_canonical(row: dict) -> dict:
    return canonical({
        "table_type": row.get("table_type"),
        "row_index": row.get("row_index"),
        "security_title": row.get("security_title"),
        "transaction_date": row.get("transaction_date"),
        "transaction_code": row.get("transaction_code"),
        "shares": row.get("shares_numeric"),
        "price": row.get("price_per_share_numeric"),
        "acquired_disposed_code": row.get("acquired_disposed_code"),
        "exercise_date": row.get("exercise_date"),
        "expiration_date": row.get("expiration_date"),
        "underlying_security_title": row.get("underlying_security_title"),
        "underlying_shares": row.get("underlying_security_shares_numeric"),
    })


def decimal(value: str) -> Decimal:
    return Decimal(str(value).replace(",", "").strip())


def rounded_dollars(value: Decimal) -> str:
    return str(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def audit(transactions_path: Path, owners_path: Path, sidecar_path: Path) -> dict:
    tx_raw = transactions_path.read_bytes()
    owner_raw = owners_path.read_bytes()
    tx_rows = read_csv(transactions_path)
    owner_rows = read_csv(owners_path)
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))

    headers = [r for r in tx_rows if r.get("detail_type") == "filing_header"]
    transactions = [r for r in tx_rows if r.get("detail_type") == "transaction_row"]
    header_by_accession = {r.get("accession"): r for r in headers}
    if len(header_by_accession) != len(headers):
        raise ValueError("duplicate filing-header accession in source ledger")

    resolved = []
    repeated_rows = 0
    for item in sidecar["records"]:
        amendment = item["amendment_accession"]
        original = item["original_accession"]
        if amendment == original:
            raise ValueError(f"self-referential lineage: {amendment}")
        if amendment not in header_by_accession:
            raise ValueError(f"amendment accession missing from current ledger: {amendment}")
        if original in header_by_accession:
            raise ValueError(f"original accession unexpectedly already in current ledger: {original}")

        header = header_by_accession[amendment]
        expected_header = {
            "form": "4/A",
            "filing_date": item["amendment_filing_date"],
            "period_of_report": item["period_of_report"],
            "issuer_cik": item["issuer_cik"],
            "issuer_name": item["issuer_name"],
        }
        for key, expected in expected_header.items():
            if str(header.get(key, "")) != str(expected):
                raise ValueError(f"{amendment}: {key} mismatch; got {header.get(key)!r}, expected {expected!r}")
        if str(header.get("is_amendment", "")).lower() not in {"true", "1", "yes"}:
            raise ValueError(f"{amendment} is not marked as an amendment")
        stored_previous = str(header.get("previous_accession") or "").strip()
        if stored_previous and stored_previous != original:
            raise ValueError(f"{amendment}: conflicting stored previous_accession {stored_previous}")

        current_rows = [
            r for r in transactions
            if r.get("accession") == amendment
        ]
        current_rows = sorted(current_rows, key=lambda r: (r.get("table_type", ""), int(r.get("row_index") or 0)))
        expected_amendment_rows = sorted(
            item["amendment_transaction_rows"],
            key=lambda r: (r.get("table_type", ""), int(r.get("row_index") or 0)),
        )
        actual = [ledger_canonical(r) for r in current_rows]
        expected = [canonical(r) for r in expected_amendment_rows]
        if actual != expected:
            raise ValueError(f"{amendment}: current ledger transaction rows do not match adjudicated amendment rows")

        current_owners = sorted({
            str(r.get("owner_cik") or "").strip()
            for r in owner_rows
            if r.get("accession") == amendment and str(r.get("owner_cik") or "").strip()
        })
        if current_owners != sorted(item["amendment_owner_ciks"]):
            raise ValueError(f"{amendment}: amendment owner CIK set mismatch")

        if any(str(r.get("signal_eligible", "")).lower() in {"true", "1", "yes"} for r in current_rows):
            raise ValueError(f"{amendment}: source ledger contains a signal-eligible transaction row")
        if item.get("new_economic_event") is not False or item.get("signal_eligible") is not False:
            raise ValueError(f"{amendment}: sidecar cannot promote an amendment as a new signal")

        original_rows = sorted(
            item["original_transaction_rows"],
            key=lambda r: (r.get("table_type", ""), int(r.get("row_index") or 0)),
        )
        if len(original_rows) != len(expected_amendment_rows):
            raise ValueError(f"{amendment}: original/amendment row count differs")

        comparison = {
            "original_accession": original,
            "amendment_accession": amendment,
            "original_accession_present_in_current_first_seen_ledger": False,
            "original_accession_resolution": "VERIFIED_FROM_SEC_PRIMARY_INDEX_AND_OWNERSHIP_XML",
            "source_ledger_previous_accession_field": stored_previous or None,
            "sidecar_preserves_source_without_rewrite": True,
            "original_owner_ciks": sorted(item["original_owner_ciks"]),
            "amendment_owner_ciks": current_owners,
            "transaction_rows_original": len(original_rows),
            "transaction_rows_amendment": len(expected_amendment_rows),
            "transaction_rows_repeated_in_amendment": len(expected_amendment_rows),
            "lineage_classification": item["lineage_classification"],
            "new_economic_event": False,
            "signal_eligible": False,
            "source_urls": {
                "original_index": item["original_index_url"],
                "original_xml": item["original_xml_url"],
                "amendment_xml": item["amendment_xml_url"],
            },
            "source_evidence": item["source_evidence"],
        }

        if amendment == "0001104659-26-130067":
            original_row = original_rows[0]
            amended_row = expected_amendment_rows[0]
            original_gross = decimal(original_row["shares"]) * decimal(original_row["price"])
            amended_gross = decimal(amended_row["shares"]) * decimal(amended_row["price"])
            same_event_identity = all(
                original_row[field] == amended_row[field]
                for field in ("table_type", "security_title", "transaction_date", "transaction_code", "acquired_disposed_code")
            )
            if not same_event_identity:
                raise ValueError("Crescent original and amended rows do not identify the same underlying transaction")
            if rounded_dollars(original_gross) != item["reported_combined_investment_usd"]:
                raise ValueError("Crescent original row does not reconcile to the reported combined investment")
            if rounded_dollars(amended_gross) != item["reported_combined_investment_usd"]:
                raise ValueError("Crescent amended row does not reconcile to the reported combined investment")
            comparison["transaction_state_comparison"] = {
                "same_underlying_transaction_date": True,
                "original_shares": original_row["shares"],
                "amended_shares": amended_row["shares"],
                "shares_delta": str(decimal(amended_row["shares"]) - decimal(original_row["shares"])),
                "original_price_usd": original_row["price"],
                "amended_price_usd": amended_row["price"],
                "price_delta_usd": str(decimal(amended_row["price"]) - decimal(original_row["price"])),
                "original_row_implied_gross_usd": str(original_gross.quantize(Decimal("0.01"))),
                "amended_row_implied_gross_usd": str(amended_gross.quantize(Decimal("0.01"))),
                "gross_delta_usd": str((amended_gross - original_gross).quantize(Decimal("0.01"))),
                "both_round_to_reported_combined_investment_usd": item["reported_combined_investment_usd"],
                "interpretation": "Final NAV-based share-count/price update for the same September 1 investment; not a second purchase.",
            }
        else:
            if [canonical(r) for r in original_rows] != [canonical(r) for r in expected_amendment_rows]:
                raise ValueError("TRON original and amended transaction rows are not identical")
            added_owners = sorted(set(item["amendment_owner_ciks"]) - set(item["original_owner_ciks"]))
            if added_owners != ["0002075159"]:
                raise ValueError("TRON amendment does not resolve to the expected added joint reporting person")
            if any(r["transaction_code"] not in {"A", "M"} for r in original_rows):
                raise ValueError("TRON amendment includes an unexpected transaction code")
            comparison["transaction_state_comparison"] = {
                "original_and_amended_rows_identical": True,
                "added_reporting_owner_ciks": added_owners,
                "transaction_codes": sorted({r["transaction_code"] for r in original_rows}),
                "interpretation": "Joint-reporting-person update only; repeated award/exercise/conversion rows are not new market purchases.",
            }

        repeated_rows += len(expected_amendment_rows)
        resolved.append(comparison)

    return {
        "phase": PHASE,
        "audit_date": sidecar["audit_date"],
        "source": {
            "transaction_ledger_path": str(transactions_path),
            "transaction_ledger_sha256": hashlib.sha256(tx_raw).hexdigest(),
            "transaction_ledger_filing_headers": len(headers),
            "transaction_ledger_transaction_rows": len(transactions),
            "reporting_owners_path": str(owners_path),
            "reporting_owners_sha256": hashlib.sha256(owner_raw).hexdigest(),
        },
        "results": {
            "amendment_lineage_links_resolved": len(resolved),
            "amendment_transaction_rows_reviewed": repeated_rows,
            "new_economic_events_created": 0,
            "signal_eligible_rows": 0,
            "source_ledger_rows_rewritten": False,
            "source_ledger_previous_accession_fields_rewritten": False,
        },
        "lineage_resolutions": resolved,
        "controls": {
            "sec_network_requests_made_by_audit": False,
            "market_prices_downloaded": False,
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
    parser.add_argument("--transactions", required=True, type=Path)
    parser.add_argument("--owners", required=True, type=Path)
    parser.add_argument("--sidecar", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.transactions, args.owners, args.sidecar)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": PHASE,
        "lineage_links_resolved": result["results"]["amendment_lineage_links_resolved"],
        "amendment_rows_reviewed": result["results"]["amendment_transaction_rows_reviewed"],
        "new_economic_events_created": result["results"]["new_economic_events_created"],
        "signal_eligible_rows": result["results"]["signal_eligible_rows"],
        "output": str(args.output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
