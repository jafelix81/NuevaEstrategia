#!/usr/bin/env python3
"""Phase 197: Greek-normalized Cboe option-flow measurement diagnostic.

Uses the public CALCS sample only. It checks that enriched rows match the
base trade file, then measures exact-at-bid/ask delta and vega imbalances.
No quote_datetime interpretation, participant identity, PIT or alpha is inferred.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from research.phase170_cboe_option_trades_public_sample_audit import BASE_FIELDS, CALCS_FIELDS
from research.phase194_cboe_option_trades_daily_flow_sample_audit import (
    audit_archive,
    classify_trade_vs_nbbo,
    csv_members,
    download_sample,
    parse_decimal,
    parse_integer,
    parse_market_date,
    text_value,
)

ZERO = Decimal("0")


def empty_group() -> dict[str, object]:
    return {
        "rows": 0,
        "classified_rows": 0,
        "at_ask_rows": 0,
        "at_bid_rows": 0,
        "at_ask_contract_volume": 0,
        "at_bid_contract_volume": 0,
        "signed_underlying_delta_contracts": ZERO,
        "gross_delta_contracts": ZERO,
        "signed_option_demand_delta_contracts": ZERO,
        "signed_vega_contracts": ZERO,
        "gross_vega_contracts": ZERO,
    }


def add_measure(
    group: dict[str, object],
    size: int,
    side: int,
    delta: Decimal,
    vega: Decimal,
    option_type: str,
) -> None:
    group["rows"] = int(group["rows"]) + 1
    if side == 0:
        return
    group["classified_rows"] = int(group["classified_rows"]) + 1
    if side > 0:
        group["at_ask_rows"] = int(group["at_ask_rows"]) + 1
        group["at_ask_contract_volume"] = int(group["at_ask_contract_volume"]) + size
    else:
        group["at_bid_rows"] = int(group["at_bid_rows"]) + 1
        group["at_bid_contract_volume"] = int(group["at_bid_contract_volume"]) + size

    abs_delta = abs(delta)
    option_delta_sign = Decimal("1") if option_type == "C" else Decimal("-1")
    group["gross_delta_contracts"] += abs_delta * size
    group["signed_option_demand_delta_contracts"] += Decimal(side) * abs_delta * size
    group["signed_underlying_delta_contracts"] += (
        Decimal(side) * option_delta_sign * abs_delta * size
    )
    abs_vega = abs(vega)
    group["gross_vega_contracts"] += abs_vega * size
    group["signed_vega_contracts"] += Decimal(side) * abs_vega * size


def ratio(numerator: Decimal, denominator: Decimal) -> str | None:
    if denominator == ZERO:
        return None
    return format(numerator / denominator, ".8f")


def serialize_group(group: dict[str, object]) -> dict[str, object]:
    ask = int(group["at_ask_contract_volume"])
    bid = int(group["at_bid_contract_volume"])
    signed_delta = group["signed_underlying_delta_contracts"]
    gross_delta = group["gross_delta_contracts"]
    signed_option_delta = group["signed_option_demand_delta_contracts"]
    signed_vega = group["signed_vega_contracts"]
    gross_vega = group["gross_vega_contracts"]
    return {
        "rows": int(group["rows"]),
        "classified_rows": int(group["classified_rows"]),
        "at_ask_rows": int(group["at_ask_rows"]),
        "at_bid_rows": int(group["at_bid_rows"]),
        "at_ask_contract_volume": ask,
        "at_bid_contract_volume": bid,
        "candidate_signed_contract_volume_at_ask_minus_bid": ask - bid,
        "signed_underlying_delta_contracts_no_multiplier": str(signed_delta),
        "gross_delta_contracts_no_multiplier": str(gross_delta),
        "delta_imbalance_ratio": ratio(signed_delta, gross_delta),
        "signed_option_demand_delta_contracts_no_multiplier": str(signed_option_delta),
        "option_demand_delta_imbalance_ratio": ratio(signed_option_delta, gross_delta),
        "signed_vega_contracts_no_multiplier": str(signed_vega),
        "gross_vega_contracts_no_multiplier": str(gross_vega),
        "vega_imbalance_ratio": ratio(signed_vega, gross_vega),
    }


def dte_bucket(dte: int) -> str:
    if dte < 0:
        return "expired"
    if dte <= 7:
        return "0_7_days"
    if dte <= 30:
        return "8_30_days"
    if dte <= 90:
        return "31_90_days"
    return "91_plus_days"


def aggregate_trade_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    overall = empty_group()
    by_option_type = {"C": empty_group(), "P": empty_group()}
    by_dte_bucket: dict[str, dict[str, object]] = {}
    by_option_type_dte: dict[tuple[str, str], dict[str, object]] = {}
    nbbo_rows: Counter[str] = Counter()
    nbbo_contracts: Counter[str] = Counter()
    delta_sign_mismatch_rows = 0
    delta_nonzero_rows = 0
    negative_vega_rows = 0

    for row in rows:
        option_type = text_value(row.get("option_type")).upper()
        if option_type not in {"C", "P"}:
            raise ValueError("option_type_invalid")
        size = parse_integer(row.get("trade_size"), "trade_size")
        price = parse_decimal(row.get("trade_price"), "trade_price")
        bid = parse_decimal(row.get("best_bid"), "best_bid", blank_ok=True)
        ask = parse_decimal(row.get("best_ask"), "best_ask", blank_ok=True)
        delta = parse_decimal(row.get("trade_delta"), "trade_delta")
        vega = parse_decimal(row.get("trade_vega"), "trade_vega")
        dte = parse_integer(row.get("dte"), "dte")
        if size is None or size <= 0 or price is None or dte is None:
            raise ValueError("trade_measure_invalid")
        quote_class = classify_trade_vs_nbbo(price, bid, ask)
        side = 1 if quote_class == "at_ask_candidate" else -1 if quote_class == "at_bid_candidate" else 0
        nbbo_rows[quote_class] += 1
        nbbo_contracts[quote_class] += size
        add_measure(overall, size, side, delta, vega, option_type)
        add_measure(by_option_type[option_type], size, side, delta, vega, option_type)

        bucket = dte_bucket(dte)
        by_dte_bucket.setdefault(bucket, empty_group())
        by_option_type_dte.setdefault((option_type, bucket), empty_group())
        add_measure(by_dte_bucket[bucket], size, side, delta, vega, option_type)
        add_measure(by_option_type_dte[(option_type, bucket)], size, side, delta, vega, option_type)

        if delta != ZERO:
            delta_nonzero_rows += 1
            if (option_type == "C" and delta < ZERO) or (option_type == "P" and delta > ZERO):
                delta_sign_mismatch_rows += 1
        if vega < ZERO:
            negative_vega_rows += 1

    return {
        "overall": serialize_group(overall),
        "by_option_type": {
            key: serialize_group(value) for key, value in sorted(by_option_type.items())
        },
        "by_dte_bucket": {
            key: serialize_group(value) for key, value in sorted(by_dte_bucket.items())
        },
        "by_option_type_and_dte": {
            f"{key[0]}:{key[1]}": serialize_group(value)
            for key, value in sorted(by_option_type_dte.items())
        },
        "nbbo_class_rows": dict(sorted(nbbo_rows.items())),
        "nbbo_class_contract_volume": dict(sorted(nbbo_contracts.items())),
        "greek_sign_diagnostics": {
            "nonzero_delta_rows": delta_nonzero_rows,
            "raw_delta_sign_mismatch_rows_vs_call_put": delta_sign_mismatch_rows,
            "raw_delta_sign_concordance_ratio": (
                format(Decimal(delta_nonzero_rows - delta_sign_mismatch_rows) / delta_nonzero_rows, ".8f")
                if delta_nonzero_rows else None
            ),
            "negative_vega_rows": negative_vega_rows,
        },
    }


def audit_calcs_member(raw_zip: bytes) -> dict[str, object]:
    archive_audit = audit_archive(raw_zip)
    if not archive_audit["daily_flow_measurement_candidate"]:
        raise ValueError("phase194_daily_sample_gate_failed")

    members = csv_members(raw_zip)
    base_members = [
        (name, payload) for name, payload in members
        if "underlyingoptionstrades_" in name.lower()
        and "calcs" not in name.lower()
    ]
    calcs_members = [
        (name, payload) for name, payload in members
        if "underlyingoptionstradescalcs_" in name.lower()
    ]
    if len(base_members) != 1 or len(calcs_members) != 1:
        raise ValueError("base_and_calcs_members_not_unique")

    audit_by_name = {
        item["member_basename"].lower(): item
        for item in archive_audit["member_audits"]
    }
    base_name, base_payload = base_members[0]
    calcs_name, calcs_payload = calcs_members[0]
    base_audit = audit_by_name[base_name.replace("\\", "/").rsplit("/", 1)[-1].lower()]
    calcs_audit = audit_by_name[calcs_name.replace("\\", "/").rsplit("/", 1)[-1].lower()]
    if (
        base_audit["core_trade_rows_sha256"] != calcs_audit["core_trade_rows_sha256"]
        or base_audit["nonblank_trade_rows"] != calcs_audit["nonblank_trade_rows"]
    ):
        raise ValueError("base_calcs_core_rows_do_not_match")

    decoded = calcs_payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    headers = [text_value(x).lower() for x in (reader.fieldnames or [])]
    expected = set(BASE_FIELDS) | set(CALCS_FIELDS)
    if set(headers) != expected or len(headers) != len(expected):
        raise ValueError("calcs_schema_mismatch")

    core_digest = hashlib.sha256()
    seen_keys: set[tuple[str, int, int]] = set()
    contracts: set[tuple[str, ...]] = set()
    underlyings: set[str] = set()
    rows: list[dict[str, object]] = []
    blank_rows = 0
    internal_blank = False
    seen_blank = False
    adjusted_root_candidate_rows = 0
    delta_zero_rows = 0
    vega_zero_rows = 0
    iv_zero_rows = 0
    delta_out_of_range_rows = 0
    delta_nonblank_rows = 0
    vega_nonblank_rows = 0
    iv_nonblank_rows = 0
    sample_dates: set[date] = set()

    for raw_row in reader:
        row = {str(key).strip().lower(): value for key, value in raw_row.items() if key is not None}
        if all(not text_value(row.get(field)) for field in headers):
            blank_rows += 1
            seen_blank = True
            continue
        if seen_blank:
            internal_blank = True
        if raw_row.get(None):
            raise ValueError("calcs_csv_extra_fields")
        if any(row.get(field) is None for field in BASE_FIELDS):
            raise ValueError("calcs_core_field_missing")

        canonical = "\x1f".join(text_value(row.get(field)) for field in BASE_FIELDS)
        core_digest.update(canonical.encode("utf-8"))
        core_digest.update(b"\n")

        symbol = text_value(row.get("underlying_symbol"))
        root = text_value(row.get("root"))
        option_type = text_value(row.get("option_type")).upper()
        market_day = parse_market_date(row.get("market_date"))
        expiry = parse_market_date(row.get("expiration"))
        strike = parse_decimal(row.get("strike"), "strike")
        sequence = parse_integer(row.get("sequence_number"), "sequence_number")
        exchange = parse_integer(row.get("exchange_id"), "exchange_id")
        size = parse_integer(row.get("trade_size"), "trade_size")
        price = parse_decimal(row.get("trade_price"), "trade_price")
        condition = parse_integer(row.get("trade_condition_id"), "trade_condition_id")
        delta = parse_decimal(row.get("trade_delta"), "trade_delta")
        vega = parse_decimal(row.get("trade_vega"), "trade_vega")
        iv = parse_decimal(row.get("trade_iv"), "trade_iv")
        if (
            not symbol or not root or option_type not in {"C", "P"}
            or strike is None or strike <= ZERO
            or sequence is None or exchange is None or size is None or size <= 0
            or price is None or price < ZERO or condition is None
            or delta is None or vega is None or iv is None
        ):
            raise ValueError("calcs_trade_or_greek_invalid")

        delta_nonblank_rows += 1
        vega_nonblank_rows += 1
        iv_nonblank_rows += 1
        if delta == ZERO:
            delta_zero_rows += 1
        if vega == ZERO:
            vega_zero_rows += 1
        if iv == ZERO:
            iv_zero_rows += 1
        if abs(delta) > Decimal("1.000001"):
            delta_out_of_range_rows += 1
        if any(ch.isdigit() for ch in root):
            adjusted_root_candidate_rows += 1

        key = (market_day.isoformat(), sequence, exchange)
        if key in seen_keys:
            raise ValueError("duplicate_trade_key")
        seen_keys.add(key)
        sample_dates.add(market_day)
        underlyings.add(symbol)
        contracts.add((symbol, root, expiry.isoformat(), str(strike.normalize()), option_type))
        rows.append({
            "option_type": option_type,
            "trade_size": size,
            "trade_price": price,
            "best_bid": parse_decimal(row.get("best_bid"), "best_bid", blank_ok=True),
            "best_ask": parse_decimal(row.get("best_ask"), "best_ask", blank_ok=True),
            "trade_delta": delta,
            "trade_vega": vega,
            "dte": (expiry - market_day).days,
        })

    if internal_blank:
        raise ValueError("internal_blank_rows")
    if len(rows) != int(calcs_audit["nonblank_trade_rows"]):
        raise ValueError("calcs_row_count_mismatch")
    if core_digest.hexdigest() != calcs_audit["core_trade_rows_sha256"]:
        raise ValueError("calcs_core_digest_mismatch")
    if len(sample_dates) != 1:
        raise ValueError("sample_date_not_unique")

    measurements = aggregate_trade_rows(rows)
    return {
        "phase": 197,
        "status": "GREEK_NORMALIZED_SAMPLE_DIAGNOSTIC_PASS",
        "audit_as_of_utc": datetime.now(timezone.utc).isoformat(),
        "sample_date": min(sample_dates).isoformat(),
        "source": "Cboe Option Trades public CALCS sample",
        "sample_url": "https://datashop.cboe.com/download/sample/216",
        "sample_archive_sha256": hashlib.sha256(raw_zip).hexdigest(),
        "sample_archive_bytes": len(raw_zip),
        "base_member_sha256": hashlib.sha256(base_payload).hexdigest(),
        "calcs_member_sha256": hashlib.sha256(calcs_payload).hexdigest(),
        "base_core_trade_rows_sha256": base_audit["core_trade_rows_sha256"],
        "calcs_core_trade_rows_sha256": core_digest.hexdigest(),
        "base_calcs_core_rows_match": True,
        "rows": len(rows),
        "blank_padding_rows": blank_rows,
        "underlying_count": len(underlyings),
        "contract_count": len(contracts),
        "trade_key_count": len(seen_keys),
        "adjusted_root_candidate_rows": adjusted_root_candidate_rows,
        "greek_coverage": {
            "trade_delta_nonblank_rows": delta_nonblank_rows,
            "trade_vega_nonblank_rows": vega_nonblank_rows,
            "trade_iv_nonblank_rows": iv_nonblank_rows,
            "trade_delta_zero_rows": delta_zero_rows,
            "trade_vega_zero_rows": vega_zero_rows,
            "trade_iv_zero_rows": iv_zero_rows,
            "trade_delta_abs_gt_1_rows": delta_out_of_range_rows,
        },
        "measurements": measurements,
        "interpretation": {
            "exact_at_bid_ask_only": True,
            "option_type_sign_normalization_used": True,
            "trade_delta_raw_sign_verified": measurements["greek_sign_diagnostics"]["raw_delta_sign_mismatch_rows_vs_call_put"] == 0,
            "trade_vega_used_as_absolute_magnitude": True,
            "contract_multiplier_applied": False,
            "adjusted_deliverables_verified": False,
            "quote_datetime_used": False,
            "trade_condition_filter_applied": False,
            "trade_condition_semantics_historically_verified": False,
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
            "raw_rows_persisted": False,
            "raw_symbols_persisted": False,
            "raw_contracts_persisted": False,
            "raw_clock_values_persisted": False,
            "f80_frozen": True,
        },
        "decision": (
            "This is a one-day, one-underlying measurement diagnostic. Exact-at-ask is treated as "
            "candidate buyer initiation and exact-at-bid as candidate seller initiation; all other "
            "NBBO classes remain unclassified. Delta is signed by call/put type and vega is used "
            "as an absolute magnitude. Values are delta/vega contract units without a multiplier, "
            "not share or dollar exposure. Trade conditions, first receipt, historical coverage, "
            "adjusted deliverables and Greek timestamp semantics remain unverified. No feature or "
            "alpha is admitted."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase197_output")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = audit_calcs_member(download_sample())
    path = output_dir / "phase197_cboe_greek_normalized_flow_sample.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
