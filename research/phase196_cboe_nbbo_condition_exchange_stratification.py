#!/usr/bin/env python3
"""Phase 196: one-day Cboe NBBO-side decomposition by trade condition and exchange.

Descriptive measurement only. quote_datetime is ignored; no participant identity,
aggressor certainty, PIT admission or alpha is inferred. Only non-identifying
aggregate counts, contract volumes and hashes are stored.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from research.phase194_cboe_option_trades_daily_flow_sample_audit import (
    audit_archive,
    classify_trade_vs_nbbo,
    csv_members,
    parse_decimal,
    parse_integer,
)
from research.phase195_cboe_trade_condition_exchange_mapping_audit import (
    CONDITION_XLSX_URL,
    EXCHANGE_CSV_URL,
    SAMPLE_URL,
    MAX_FILE_BYTES,
    DownloadError,
    _fetch,
    parse_condition_mapping,
    parse_exchange_mapping_csv,
)


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def condition_bucket(name: str) -> str:
    value = clean(name).lower()
    if value in {"regular", "normal"}:
        return "regular"
    if value == "autoexecution":
        return "auto_execution"
    if value == "intermarketsweep":
        return "intermarket_sweep"
    if value.startswith("singleg"):
        if "flr" in value:
            return "single_leg_floor"
        return "single_leg_auction_or_cross"
    if value.startswith("multleg"):
        return "multi_leg"
    if value.startswith("stkopt"):
        return "stock_option"
    return "unclassified"


def new_group() -> dict[str, object]:
    return {
        "rows": 0,
        "contract_volume": 0,
        "at_ask_contract_volume": 0,
        "at_bid_contract_volume": 0,
        "at_ask_price_times_contracts_no_multiplier": Decimal("0"),
        "at_bid_price_times_contracts_no_multiplier": Decimal("0"),
        "nbbo_class_rows": Counter(),
        "nbbo_class_contract_volume": Counter(),
    }


def add_to_group(group: dict[str, object], size: int, price: Decimal, quote_class: str) -> None:
    group["rows"] = int(group["rows"]) + 1
    group["contract_volume"] = int(group["contract_volume"]) + size
    group["nbbo_class_rows"][quote_class] += 1
    group["nbbo_class_contract_volume"][quote_class] += size
    price_size = price * size
    if quote_class == "at_ask_candidate":
        group["at_ask_contract_volume"] = int(group["at_ask_contract_volume"]) + size
        group["at_ask_price_times_contracts_no_multiplier"] += price_size
    elif quote_class == "at_bid_candidate":
        group["at_bid_contract_volume"] = int(group["at_bid_contract_volume"]) + size
        group["at_bid_price_times_contracts_no_multiplier"] += price_size


def serialize_group(group: dict[str, object]) -> dict[str, object]:
    ask = int(group["at_ask_contract_volume"])
    bid = int(group["at_bid_contract_volume"])
    volume = int(group["contract_volume"])
    return {
        "rows": int(group["rows"]),
        "contract_volume": volume,
        "at_ask_contract_volume": ask,
        "at_bid_contract_volume": bid,
        "candidate_signed_contract_volume_at_ask_minus_bid": ask - bid,
        "other_nbbo_class_contract_volume": volume - ask - bid,
        "at_ask_price_times_contracts_no_multiplier": str(group["at_ask_price_times_contracts_no_multiplier"]),
        "at_bid_price_times_contracts_no_multiplier": str(group["at_bid_price_times_contracts_no_multiplier"]),
        "candidate_signed_price_times_contracts_no_multiplier": str(
            group["at_ask_price_times_contracts_no_multiplier"]
            - group["at_bid_price_times_contracts_no_multiplier"]
        ),
        "nbbo_class_rows": dict(sorted(group["nbbo_class_rows"].items())),
        "nbbo_class_contract_volume": dict(sorted(group["nbbo_class_contract_volume"].items())),
    }


def stratify_archive(
    raw_zip: bytes,
    condition_mapping: dict[str, object],
    exchange_mapping: dict[str, object],
    retrieved_at_utc: str | None = None,
) -> dict[str, object]:
    row_audit = audit_archive(raw_zip, retrieved_at_utc)
    if not row_audit["daily_flow_measurement_candidate"]:
        raise ValueError("phase194_daily_sample_gate_failed")

    members = csv_members(raw_zip)
    base_members = [
        (name, payload) for name, payload in members
        if "underlyingoptionstrades_" in name.lower()
        and "calcs" not in name.lower()
    ]
    if len(base_members) != 1:
        raise ValueError("base_trade_member_not_unique")

    condition_lookup = condition_mapping["mapping_by_id"]
    exchange_lookup = exchange_mapping["mapping_by_id"]
    condition_groups: dict[int, dict[str, object]] = defaultdict(new_group)
    exchange_groups: dict[int, dict[str, object]] = defaultdict(new_group)
    pair_groups: dict[tuple[int, int], dict[str, object]] = defaultdict(new_group)
    bucket_groups: dict[str, dict[str, object]] = defaultdict(new_group)
    totals = new_group()
    unmapped_conditions: set[int] = set()
    unmapped_exchanges: set[int] = set()
    strict_side_eligible_rows = 0
    invalid_rows = 0

    member_name, member_payload = base_members[0]
    decoded = member_payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    for raw_row in reader:
        row = {str(k).strip().lower(): v for k, v in raw_row.items() if k is not None}
        if not any(clean(value) for value in row.values()):
            continue
        try:
            condition_id = parse_integer(row.get("trade_condition_id"), "trade_condition_id")
            exchange_id = parse_integer(row.get("exchange_id"), "exchange_id")
            size = parse_integer(row.get("trade_size"), "trade_size")
            price = parse_decimal(row.get("trade_price"), "trade_price")
            bid = parse_decimal(row.get("best_bid"), "best_bid", blank_ok=True)
            ask = parse_decimal(row.get("best_ask"), "best_ask", blank_ok=True)
            if condition_id is None or exchange_id is None or size is None or price is None:
                raise ValueError("required_trade_measure_missing")
            if condition_id < 0 or exchange_id < 0 or size <= 0 or price < 0:
                raise ValueError("trade_measure_out_of_range")
        except (TypeError, ValueError):
            invalid_rows += 1
            continue

        condition_entry = condition_lookup.get(condition_id)
        exchange_entry = exchange_lookup.get(exchange_id)
        if condition_entry is None:
            unmapped_conditions.add(condition_id)
            continue
        if exchange_entry is None:
            unmapped_exchanges.add(exchange_id)
            continue

        quote_class = classify_trade_vs_nbbo(price, bid, ask)
        condition_name = clean(condition_entry.get("name"))
        bucket = condition_bucket(condition_name)
        add_to_group(totals, size, price, quote_class)
        add_to_group(condition_groups[condition_id], size, price, quote_class)
        add_to_group(exchange_groups[exchange_id], size, price, quote_class)
        add_to_group(pair_groups[(condition_id, exchange_id)], size, price, quote_class)
        add_to_group(bucket_groups[bucket], size, price, quote_class)

        if (
            bucket == "regular"
            and condition_entry.get("message_type") == "trade"
            and "option" in clean(condition_entry.get("security_types")).lower()
        ):
            strict_side_eligible_rows += 1

    if invalid_rows or unmapped_conditions or unmapped_exchanges:
        raise ValueError("invalid_or_unmapped_sample_rows")

    base_audit = next(
        item for item in row_audit["member_audits"]
        if "underlyingoptionstrades_" in item["member_basename"].lower()
        and "calcs" not in item["member_basename"].lower()
    )
    if int(totals["rows"]) != int(base_audit["valid_trade_rows"]):
        raise ValueError("stratified_row_count_mismatch")

    condition_rows = []
    for code, group in sorted(condition_groups.items()):
        entry = condition_lookup[code]
        item = {"id": code, "name": clean(entry.get("name")), "bucket": condition_bucket(clean(entry.get("name")))}
        item.update(serialize_group(group))
        condition_rows.append(item)

    exchange_rows = []
    for code, group in sorted(exchange_groups.items()):
        entry = exchange_lookup[code]
        item = {"id": code, "name": clean(entry.get("name"))}
        item.update(serialize_group(group))
        exchange_rows.append(item)

    pair_rows = []
    for (condition_id, exchange_id), group in sorted(pair_groups.items()):
        item = {
            "condition_id": condition_id,
            "condition_name": clean(condition_lookup[condition_id].get("name")),
            "exchange_id": exchange_id,
            "exchange_name": clean(exchange_lookup[exchange_id].get("name")),
        }
        item.update(serialize_group(group))
        pair_rows.append(item)

    bucket_rows = []
    for bucket, group in sorted(bucket_groups.items()):
        item = {"bucket": bucket}
        item.update(serialize_group(group))
        bucket_rows.append(item)

    pair_row_sum = sum(int(x["rows"]) for x in pair_rows)
    pair_volume_sum = sum(int(x["contract_volume"]) for x in pair_rows)
    condition_row_sum = sum(int(x["rows"]) for x in condition_rows)
    exchange_row_sum = sum(int(x["rows"]) for x in exchange_rows)
    condition_volume_sum = sum(int(x["contract_volume"]) for x in condition_rows)
    exchange_volume_sum = sum(int(x["contract_volume"]) for x in exchange_rows)
    total = serialize_group(totals)

    reconciliation = {
        "condition_rows_sum_matches": condition_row_sum == total["rows"],
        "exchange_rows_sum_matches": exchange_row_sum == total["rows"],
        "condition_exchange_rows_sum_matches": pair_row_sum == total["rows"],
        "condition_volume_sum_matches": condition_volume_sum == total["contract_volume"],
        "exchange_volume_sum_matches": exchange_volume_sum == total["contract_volume"],
        "condition_exchange_volume_sum_matches": pair_volume_sum == total["contract_volume"],
        "phase194_row_count_matches": total["rows"] == base_audit["valid_trade_rows"],
        "phase194_contract_volume_matches": total["contract_volume"] == base_audit["trade_size_sum_contracts"],
        "phase194_at_ask_matches": total["at_ask_contract_volume"] == base_audit["at_ask_contract_volume"],
        "phase194_at_bid_matches": total["at_bid_contract_volume"] == base_audit["at_bid_contract_volume"],
        "all_observed_ids_mapped": not unmapped_conditions and not unmapped_exchanges,
    }
    if not all(reconciliation.values()):
        raise ValueError("cross_tab_reconciliation_failed")

    return {
        "phase": 196,
        "status": "STRATIFIED_SAMPLE_DIAGNOSTIC_PASS",
        "audit_as_of_utc": retrieved_at_utc or datetime.now(timezone.utc).isoformat(),
        "sample_date": base_audit["market_date_min"],
        "sample_url": SAMPLE_URL,
        "sample_archive_sha256": hashlib.sha256(raw_zip).hexdigest(),
        "sample_archive_bytes": len(raw_zip),
        "sample_member_basename": member_name.replace("\\", "/").rsplit("/", 1)[-1],
        "sample_member_sha256": hashlib.sha256(member_payload).hexdigest(),
        "sample_core_trade_rows_sha256": base_audit["core_trade_rows_sha256"],
        "totals": total,
        "condition_groups": condition_rows,
        "exchange_groups": exchange_rows,
        "condition_exchange_cells": pair_rows,
        "condition_bucket_groups": bucket_rows,
        "diagnostic_concentration": {
            "largest_absolute_condition_candidate_net": max(
                condition_rows,
                key=lambda x: abs(x["candidate_signed_contract_volume_at_ask_minus_bid"]),
            ) if condition_rows else None,
            "largest_absolute_exchange_candidate_net": max(
                exchange_rows,
                key=lambda x: abs(x["candidate_signed_contract_volume_at_ask_minus_bid"]),
            ) if exchange_rows else None,
        },
        "mapping_reconciliation": {
            "condition_mapping_rows": condition_mapping["row_count"],
            "condition_mapping_headers": condition_mapping["headers"],
            "condition_mapping_effective_date_fields": condition_mapping["effective_date_fields"],
            "exchange_mapping_rows": exchange_mapping["row_count"],
            "exchange_mapping_headers": exchange_mapping["headers"],
            "unmapped_condition_ids": sorted(unmapped_conditions),
            "unmapped_exchange_ids": sorted(unmapped_exchanges),
            "strict_side_eligible_rows": strict_side_eligible_rows,
            "message_type_field_present": any("message" in clean(h).lower() for h in condition_mapping["headers"]),
            "historical_effective_dates_verified": False,
        },
        "reconciliation": reconciliation,
        "interpretation": {
            "candidate_net_is_exact_at_ask_minus_exact_at_bid_only": True,
            "quote_datetime_used": False,
            "quote_datetime_semantics_assigned": False,
            "trade_conditions_are_participant_identities": False,
            "exchange_is_participant_identity": False,
            "institutional_or_informed_flow_claimed": False,
            "historical_mapping_pit_verified": False,
            "first_receipt_verified": False,
            "historical_coverage_verified": False,
            "strict_pit_admitted": False,
            "signed_flow_feature_admitted": False,
            "alpha_admission": False,
            "return_test_run": False,
            "holdout_used": False,
            "production_changed": False,
            "data_purchase": False,
            "vendor_contact": False,
            "raw_archive_persisted": False,
            "raw_trade_rows_persisted": False,
            "raw_symbols_persisted": False,
            "raw_contracts_persisted": False,
            "raw_clock_values_persisted": False,
            "f80_frozen": True,
        },
        "decision": (
            "This one-underlying, one-day sample decomposes the Phase 194 at-ask-minus-at-bid "
            "proxy by current trade-condition and exchange labels. It is a measurement diagnostic, "
            "not a signed institutional-flow feature or predictive test. Current mappings have no "
            "effective dates and were published after the sample date; no historical PIT admission."
        ),
    }


def run_audit() -> dict[str, object]:
    condition_bytes, condition_headers = _fetch(CONDITION_XLSX_URL, 15 * 1024 * 1024)
    exchange_bytes, exchange_headers = _fetch(EXCHANGE_CSV_URL, 5 * 1024 * 1024)
    sample_bytes, sample_headers = _fetch(SAMPLE_URL, MAX_FILE_BYTES)
    condition_mapping = parse_condition_mapping(condition_bytes)
    exchange_mapping = parse_exchange_mapping_csv(exchange_bytes)
    result = stratify_archive(sample_bytes, condition_mapping, exchange_mapping)
    result["condition_mapping"] = {
        "url": CONDITION_XLSX_URL,
        "sha256": hashlib.sha256(condition_bytes).hexdigest(),
        "bytes": len(condition_bytes),
        "last_modified": condition_headers.get("last_modified", ""),
        "response_date": condition_headers.get("date", ""),
    }
    result["exchange_mapping"] = {
        "url": EXCHANGE_CSV_URL,
        "sha256": hashlib.sha256(exchange_bytes).hexdigest(),
        "bytes": len(exchange_bytes),
        "last_modified": exchange_headers.get("last_modified", ""),
        "response_date": exchange_headers.get("date", ""),
    }
    result["sample_response_headers"] = {
        "http_status": sample_headers.get("http_status", ""),
        "content_type": sample_headers.get("content_type", ""),
        "date": sample_headers.get("date", ""),
        "last_modified": sample_headers.get("last_modified", ""),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase196_output")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = run_audit()
    except (DownloadError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        result = {
            "phase": 196,
            "status": "DOWNLOAD_OR_RECONCILIATION_FAILED",
            "error_code": exc.code if isinstance(exc, DownloadError) else str(exc),
            "strict_pit_admitted": False,
            "alpha_admission": False,
            "holdout_used": False,
            "production_changed": False,
            "data_purchase": False,
            "vendor_contact": False,
            "f80_frozen": True,
        }
    path = output_dir / "phase196_cboe_nbbo_condition_exchange_stratification.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
