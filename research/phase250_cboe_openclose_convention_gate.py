#!/usr/bin/env python3
"""Phase 250: Cboe C1 EOD convention-aware directional feature eligibility.

This module separates the participant directional-imbalance feature from
volume/OI denominators whose historical conventions changed. It is a schema
and feature-eligibility contract, not a historical data loader or alpha test.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

POST_MIGRATION_START = date(2011, 1, 2)
CURRENT_VOLUME_CONVENTION_START = date(2019, 10, 7)
CURRENT_PARTICIPANT_CODE_START = date(2019, 10, 1)
GTH_START = date(2023, 12, 11)

CAPACITY_PREFIX = {
    "firm": "firm",
    "broker_dealer": "bd",
    "customer": "cust",
    "pro_customer": "procust",
}
SIZE_PREFIX = {
    "lt_100": "lt_100",
    "100_199": "100_199",
    "gt_199": "gt_199",
}
ACTIONS = {"open", "close"}


def parse_date(value: object) -> date:
    raw = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    raise ValueError("INVALID_QUOTE_DATE")


def classify_date(value: object) -> dict[str, object]:
    d = parse_date(value)
    if d < POST_MIGRATION_START:
        return {
            "quote_date": d.isoformat(),
            "eligible_for_post_migration_contract": False,
            "schema_regime": "PRE_2011_LEGACY_ORDER_SIZE",
            "participant_code_regime": "LEGACY_CUSTOMER_FIRM_ONLY",
            "volume_regime": "NOT_COMPARABLE_TO_POST_2011",
            "open_interest_eligible": False,
            "gth_included": False,
        }

    return {
        "quote_date": d.isoformat(),
        "eligible_for_post_migration_contract": True,
        "schema_regime": "POST_2011_EXECUTION_SIZE",
        "participant_code_regime": (
            "LEGACY_W_CODE_PRESENT"
            if d < CURRENT_PARTICIPANT_CODE_START
            else "CURRENT_PARTICIPANT_CODE_MAPPING"
        ),
        "volume_regime": (
            "PRE_2019_10_07_C1_VOLUME_AND_OI_CONVENTION"
            if d < CURRENT_VOLUME_CONVENTION_START
            else "CURRENT_C1_VOLUME_AND_OI_CONVENTION"
        ),
        "open_interest_eligible": d >= CURRENT_VOLUME_CONVENTION_START,
        "gth_included": d >= GTH_START,
    }


def _integer(row: dict, field: str) -> int:
    if field not in row or row.get(field) is None or not str(row.get(field)).strip():
        raise ValueError("MISSING_VOLUME:" + field)
    try:
        value = Decimal(str(row[field]).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        raise ValueError("INVALID_VOLUME:" + field) from None
    if not value.is_finite() or value != value.to_integral_value() or value < 0:
        raise ValueError("INVALID_NONNEGATIVE_INTEGER_VOLUME:" + field)
    return int(value)


def _capacity_volume(row: dict, capacity: str, action: str, side: str, size_bucket: str | None) -> int:
    if capacity not in CAPACITY_PREFIX:
        raise ValueError("UNSUPPORTED_CAPACITY")
    if action not in ACTIONS:
        raise ValueError("UNSUPPORTED_ACTION")
    if side not in {"buy", "sell"}:
        raise ValueError("UNSUPPORTED_SIDE")

    prefix = CAPACITY_PREFIX[capacity]
    if capacity in {"customer", "pro_customer"}:
        if size_bucket is not None and size_bucket not in SIZE_PREFIX:
            raise ValueError("UNSUPPORTED_SIZE_BUCKET")
        buckets = [SIZE_PREFIX[size_bucket]] if size_bucket else list(SIZE_PREFIX.values())
    else:
        if size_bucket is not None:
            raise ValueError("SIZE_BUCKET_NOT_DEFINED_FOR_CAPACITY")
        buckets = [None]

    total = 0
    for bucket in buckets:
        stem = f"{prefix}_{bucket}_" if bucket else f"{prefix}_"
        total += _integer(row, f"{stem}{action}_{side}_vol")
    return total


def compute_directional_feature(
    row: dict,
    capacity: str,
    action: str = "open",
    size_bucket: str | None = None,
) -> dict[str, object]:
    """Compute signed call/put opening or closing pressure without invalid denominators.

    Calls: buy minus sell. Puts: sell minus buy. The result is a capacity
    classification proxy, not beneficial-owner identity, aggressor side,
    delta exposure, or proof of informed trading.
    """
    d = parse_date(row.get("quote_date"))
    regime = classify_date(d.isoformat())
    if not regime["eligible_for_post_migration_contract"]:
        raise ValueError("PRE_2011_REQUIRES_SEPARATE_LEGACY_SCHEMA")
    call_put = str(row.get("call_put_flag") or "").strip().upper()
    if call_put not in {"C", "P"}:
        raise ValueError("INVALID_CALL_PUT_FLAG")

    buy = _capacity_volume(row, capacity, action, "buy", size_bucket)
    sell = _capacity_volume(row, capacity, action, "sell", size_bucket)
    signed = buy - sell if call_put == "C" else sell - buy
    gross = buy + sell
    imbalance = Decimal(signed) / Decimal(gross) if gross else None

    normalized = None
    normalization_status = "NOT_ELIGIBLE_PRE_2019_10_07_VOLUME_CONVENTION"
    if d >= CURRENT_VOLUME_CONVENTION_START:
        if row.get("total_exchange_vol") is None or not str(row.get("total_exchange_vol")).strip():
            normalization_status = "MISSING_TOTAL_EXCHANGE_VOLUME"
        else:
            total_c1 = _integer(row, "total_exchange_vol")
            if gross > total_c1:
                raise ValueError("CAPACITY_GROSS_EXCEEDS_CURRENT_C1_TOTAL_VOLUME")
            normalized = Decimal(signed) / Decimal(total_c1) if total_c1 else None
            normalization_status = "CURRENT_CONVENTION_NORMALIZATION_AVAILABLE"

    return {
        "quote_date": d.isoformat(),
        "capacity": capacity,
        "action": action,
        "size_bucket": size_bucket or "all",
        "call_put_flag": call_put,
        "buy_volume": buy,
        "sell_volume": sell,
        "signed_directional_net_contracts": signed,
        "gross_capacity_contracts": gross,
        "directional_imbalance": imbalance,
        "net_share_of_c1_volume": normalized,
        "normalization_status": normalization_status,
        "schema_regime": regime["schema_regime"],
        "participant_code_regime": regime["participant_code_regime"],
        "volume_regime": regime["volume_regime"],
        "open_interest_eligible": regime["open_interest_eligible"],
        "gth_included": regime["gth_included"],
        "beneficial_owner_identified": False,
        "delta_weighted": False,
    }
