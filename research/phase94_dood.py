"""Exact OptionMetrics DOOD formula and explicitly separate sensitivities.

This module is a deterministic calculation helper only. It does not fetch data,
infer trade direction, assign investor identity, or perform return tests.
"""

from math import isfinite
from typing import Iterable, Mapping, Any


def _validated_inputs(option_rows: Iterable[Mapping[str, Any]], underlying_share_volume: float):
    try:
        stock_volume = float(underlying_share_volume)
    except (TypeError, ValueError) as exc:
        raise ValueError("underlying_share_volume must be numeric") from exc
    if not isfinite(stock_volume) or stock_volume <= 0:
        raise ValueError("underlying_share_volume must be finite and strictly positive")

    rows = list(option_rows)
    for index, row in enumerate(rows):
        for key in ("delta", "ask_volume", "bid_volume"):
            if key not in row:
                raise ValueError(f"option row {index} is missing {key}")
            try:
                value = float(row[key])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"option row {index} has non-numeric {key}") from exc
            if not isfinite(value):
                raise ValueError(f"option row {index} has non-finite {key}")
            if key in ("ask_volume", "bid_volume") and value < 0:
                raise ValueError(f"option row {index} has negative {key}")
    return rows, stock_volume


def compute_published_dood(option_rows: Iterable[Mapping[str, Any]],
                           underlying_share_volume: float) -> float:
    """Replicate the published formula: sum(delta * (ask - bid)) / stock volume.

    The source paper does not multiply by a contract multiplier. Put deltas must
    retain their signed negative convention. Midpoint/unclassified volume is
    not included in ask_volume or bid_volume and must remain separately stored.
    """
    rows, stock_volume = _validated_inputs(option_rows, underlying_share_volume)
    numerator = sum(
        float(row["delta"]) *
        (float(row["ask_volume"]) - float(row["bid_volume"]))
        for row in rows
    )
    return numerator / stock_volume


def compute_multiplier_adjusted_dood(option_rows: Iterable[Mapping[str, Any]],
                                     underlying_share_volume: float) -> float:
    """Compute a separate delta-equivalent-share sensitivity; not published DOOD."""
    rows, stock_volume = _validated_inputs(option_rows, underlying_share_volume)
    numerator = 0.0
    for index, row in enumerate(rows):
        if "multiplier" not in row:
            raise ValueError(f"option row {index} is missing multiplier")
        try:
            multiplier = float(row["multiplier"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"option row {index} has non-numeric multiplier") from exc
        if not isfinite(multiplier) or multiplier <= 0:
            raise ValueError(f"option row {index} has invalid multiplier")
        numerator += (
            float(row["delta"]) * multiplier *
            (float(row["ask_volume"]) - float(row["bid_volume"]))
        )
    return numerator / stock_volume
