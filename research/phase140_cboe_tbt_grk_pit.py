#!/usr/bin/env python3
"""Cboe TBT/GRK semantic and temporal safeguards (research only)."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Any, Iterable

import pandas as pd

VALID_SIDE = {"B", "S"}
VALID_OPEN_CLOSE = {"O", "C"}
VALID_CAPACITY = {"MarketMaker", "Customer", "ProCustomer", "BrokerDealer", "Firm"}
JOIN_KEYS = ["trading_dt", "formatted_symbol", "price"]


def _flag(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip().upper()


def classify_tbt_row(row: dict[str, Any]) -> dict[str, Any]:
    """Keep undocumented values/missing flags unclassified; never infer."""
    side = _flag(row.get("side"))
    open_close = _flag(row.get("open_close"))
    capacity = str(row.get("capacity") or "").strip()
    return {
        "side": side if side in VALID_SIDE else None,
        "side_status": "CLASSIFIED" if side in VALID_SIDE else "UNCLASSIFIED",
        "open_close": open_close if open_close in VALID_OPEN_CLOSE else None,
        "open_close_status": "CLASSIFIED" if open_close in VALID_OPEN_CLOSE else "UNCLASSIFIED",
        "capacity": capacity if capacity in VALID_CAPACITY else None,
        "capacity_status": "CLASSIFIED" if capacity in VALID_CAPACITY else "UNKNOWN",
    }


def open_close_coverage(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return capacity-specific O/C coverage; do not assume missingness is random."""
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        capacity = str(row.get("capacity") or "").strip() or "UNKNOWN"
        item = counts.setdefault(capacity, {"rows": 0, "classified": 0, "unclassified": 0})
        item["rows"] += 1
        classified = _flag(row.get("open_close")) in VALID_OPEN_CLOSE
        item["classified" if classified else "unclassified"] += 1
    out = {}
    for capacity, item in sorted(counts.items()):
        n = item["rows"]
        out[capacity] = {
            **item,
            "unclassified_rate": item["unclassified"] / n if n else None,
        }
    return out


def _format_strike(value: Any) -> str:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("strike_price_invalid")
    if not number.is_finite() or number <= 0:
        raise ValueError("strike_price_invalid")
    return format(number.normalize(), "f")


def build_formatted_symbol(row: dict[str, Any]) -> str:
    """Build GRK key: OSI root + YYMMDD + C/P + strike."""
    root = str(row.get("osi_root") or "").strip()
    cp = str(row.get("call_put_flag") or "").strip().upper()
    expiry = str(row.get("expire_date") or "").strip()
    if not root:
        raise ValueError("osi_root_missing")
    if cp not in {"C", "P"}:
        raise ValueError("call_put_flag_invalid")
    try:
        expiry_date = datetime.fromisoformat(expiry[:10])
    except ValueError as exc:
        raise ValueError("expire_date_invalid") from exc
    return f"{root}{expiry_date:%y%m%d}{cp}{_format_strike(row.get('strike_price'))}"


def safe_grk_join(
    tbt: pd.DataFrame,
    grk: pd.DataFrame,
    *,
    direction: str = "backward",
    tolerance_seconds: int = 5,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Join GRK without group-first sorting; label forward matches post-trade only.

    Backward is the only event-time-causal direction. Forward reproduces Cboe's
    convenience join but is post-trade attribution, not a pre-trade snapshot.
    Naive timestamps may be joined descriptively but are not strict PIT.
    """
    if direction not in {"backward", "forward"}:
        raise ValueError("direction_must_be_backward_or_forward")
    if isinstance(tolerance_seconds, bool) or tolerance_seconds < 0:
        raise ValueError("tolerance_seconds_invalid")
    required = set(JOIN_KEYS + ["transact_time"])
    if not required.issubset(tbt.columns):
        raise ValueError("tbt_required_columns_missing")
    if not required.issubset(grk.columns):
        raise ValueError("grk_required_columns_missing")

    left, right = tbt.copy(), grk.copy()
    left["_tbt_time"] = pd.to_datetime(left["transact_time"], errors="coerce")
    right["_grk_time"] = pd.to_datetime(right["transact_time"], errors="coerce")
    if left["_tbt_time"].isna().any() or right["_grk_time"].isna().any():
        raise ValueError("invalid_transact_time")
    left_tz = getattr(left["_tbt_time"].dt, "tz", None)
    right_tz = getattr(right["_grk_time"].dt, "tz", None)
    if (left_tz is None) != (right_tz is None):
        raise ValueError("tbt_grk_timezone_awareness_mismatch")
    timezone_verified = left_tz is not None and right_tz is not None
    if timezone_verified:
        left["_tbt_time"] = left["_tbt_time"].dt.tz_convert("UTC")
        right["_grk_time"] = right["_grk_time"].dt.tz_convert("UTC")
    left["_asof_time"] = left["_tbt_time"]
    right["_asof_time"] = right["_grk_time"]
    right = right.rename(columns={"transact_time": "grk_transact_time"})

    # pandas.merge_asof requires the `on` key to be globally monotonic.
    # Sorting by `by` columns first (as in the published GRK Python example)
    # can violate that requirement and raise "left keys must be sorted".
    left = left.sort_values("_asof_time", kind="mergesort")
    right = right.sort_values("_asof_time", kind="mergesort")
    merged = pd.merge_asof(
        left, right, on="_asof_time", by=JOIN_KEYS,
        direction=direction, tolerance=pd.Timedelta(seconds=tolerance_seconds),
        suffixes=("", "_grk"),
    )
    merged["grk_lag_seconds"] = (
        merged["_grk_time"] - merged["_tbt_time"]
    ).dt.total_seconds()
    matched = merged["_grk_time"].notna()
    future = matched & (merged["grk_lag_seconds"] > 0)
    if direction == "backward" and future.any():
        raise AssertionError("backward_join_returned_future_greek")
    if direction == "forward" and (matched & (merged["grk_lag_seconds"] < 0)).any():
        raise AssertionError("forward_join_returned_past_greek")

    report = {
        "direction": direction,
        "matched_rows": int(matched.sum()),
        "unmatched_rows": int((~matched).sum()),
        "match_rate": float(matched.mean()) if len(merged) else 0.0,
        "future_matched_rows": int(future.sum()),
        "timezone_verified": timezone_verified,
        "event_time_causal": direction == "backward",
        "use_class": "PRE_OR_AT_TRADE" if direction == "backward" else "POST_TRADE_ATTRIBUTION_ONLY",
        "strict_pit_eligible": False,
        "strict_pit_blocker": "actual_first_file_receipt_time_and_immutable_vintage_not_in_join_inputs",
    }
    return merged.drop(columns=["_asof_time"]), report
