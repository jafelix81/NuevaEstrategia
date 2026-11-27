#!/usr/bin/env python3
"""Fail-closed Form 13F value-unit anomaly classifier.

This is a retrospective data-integrity check, not a trading feature. It compares
reported value/share ratios with same-report-date prices for ordinary common
stock. It never changes, rescales, or overwrites source values.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from statistics import median
from typing import Any, Iterable, Mapping

SCALE_FACTORS = (1, 1000)
DEFAULT_MIN_UNIQUE_CUSIPS = 4
DEFAULT_RELATIVE_ERROR_TOLERANCE = Decimal("0.005")
DEFAULT_MIN_CONSENSUS_FRACTION = Decimal("0.80")
COMMON_CLASSES = {"COM", "COMMON STOCK"}


def _positive_decimal(value: Any) -> Decimal | None:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not parsed.is_finite() or parsed <= 0:
        return None
    return parsed


def _score_scale(
    groups: list[dict[str, Decimal]],
    factor: int,
    tolerance: Decimal,
) -> dict[str, str]:
    errors = [
        abs(((group["value"] * Decimal(factor)) / group["shares"])
            / group["reference_price"] - Decimal(1))
        for group in groups
    ]
    consensus = Decimal(sum(error <= tolerance for error in errors)) / Decimal(len(errors))
    return {
        "median_abs_relative_error": format(median(errors), "f"),
        "consensus_fraction": format(consensus, "f"),
        "rows_within_tolerance": str(sum(error <= tolerance for error in errors)),
    }


def audit_value_scale(
    rows: Iterable[Mapping[str, Any]],
    *,
    report_date: str,
    min_unique_cusips: int = DEFAULT_MIN_UNIQUE_CUSIPS,
    relative_error_tolerance: Decimal = DEFAULT_RELATIVE_ERROR_TOLERANCE,
    min_consensus_fraction: Decimal = DEFAULT_MIN_CONSENSUS_FRACTION,
) -> dict[str, Any]:
    """Return a scale *candidate* without modifying or normalizing any row.

    Only ordinary common-stock rows with SH amounts, no put/call flag, a valid
    nine-character CUSIP, positive value/shares/reference price, and an exact
    reference_date == report_date are eligible. Duplicate CUSIPs are aggregated
    so separate discretion rows do not overweight one issuer/security.

    A filing-level candidate requires at least four unique CUSIPs, at least 80%
    of rows within the stated relative-error tolerance, and median error within
    tolerance. Ambiguous, mixed, or sparse samples fail closed.
    """
    if not report_date:
        raise ValueError("report_date is required")
    if min_unique_cusips < 1:
        raise ValueError("min_unique_cusips must be positive")
    if relative_error_tolerance <= 0 or relative_error_tolerance >= 1:
        raise ValueError("relative_error_tolerance must be between 0 and 1")
    if min_consensus_fraction <= 0 or min_consensus_fraction > 1:
        raise ValueError("min_consensus_fraction must be in (0, 1]")

    excluded: dict[str, int] = {}
    grouped: dict[str, dict[str, Decimal]] = {}
    source_rows = 0

    def exclude(reason: str) -> None:
        excluded[reason] = excluded.get(reason, 0) + 1

    for row in rows:
        source_rows += 1
        cusip = str(row.get("cusip", "")).strip().upper()
        title = str(row.get("title_of_class", "")).strip().upper()
        share_type = str(row.get("share_type", "")).strip().upper()
        put_call = str(row.get("put_call", "") or "").strip().upper()
        reference_date = str(row.get("reference_date", "")).strip()

        if len(cusip) != 9 or not cusip.isalnum():
            exclude("invalid_cusip")
            continue
        if title not in COMMON_CLASSES:
            exclude("non_common_class")
            continue
        if share_type != "SH":
            exclude("non_share_amount")
            continue
        if put_call:
            exclude("put_or_call")
            continue
        if reference_date != report_date:
            exclude("reference_date_mismatch")
            continue

        value = _positive_decimal(row.get("value"))
        shares = _positive_decimal(row.get("shares"))
        price = _positive_decimal(row.get("reference_price"))
        if value is None or shares is None or price is None:
            exclude("invalid_or_nonpositive_numeric")
            continue

        current = grouped.get(cusip)
        if current is None:
            grouped[cusip] = {
                "value": value,
                "shares": shares,
                "reference_price": price,
            }
        else:
            if current["reference_price"] != price:
                exclude("duplicate_cusip_price_conflict")
                del grouped[cusip]
                continue
            current["value"] += value
            current["shares"] += shares

    groups = [grouped[key] for key in sorted(grouped)]
    result: dict[str, Any] = {
        "report_date": report_date,
        "source_rows": source_rows,
        "eligible_unique_cusips": len(groups),
        "excluded_rows_by_reason": dict(sorted(excluded.items())),
        "candidate_scores": {},
        "status": "INSUFFICIENT_EVIDENCE",
        "scale_factor_candidate": None,
        "normalization_applied": False,
        "trading_signal_eligible": False,
        "warning": "Retrospective unit-integrity candidate only; not a trading feature.",
    }

    if len(groups) < min_unique_cusips:
        return result

    scores = {
        str(factor): _score_scale(groups, factor, relative_error_tolerance)
        for factor in SCALE_FACTORS
    }
    result["candidate_scores"] = scores

    passing = []
    for factor in SCALE_FACTORS:
        score = scores[str(factor)]
        median_error = Decimal(score["median_abs_relative_error"])
        consensus = Decimal(score["consensus_fraction"])
        if median_error <= relative_error_tolerance and consensus >= min_consensus_fraction:
            passing.append(factor)

    if len(passing) == 1:
        factor = passing[0]
        result["scale_factor_candidate"] = factor
        result["status"] = (
            "NEAREST_DOLLAR_CANDIDATE" if factor == 1
            else "LEGACY_THOUSANDS_CANDIDATE"
        )
    elif len(passing) > 1:
        result["status"] = "AMBIGUOUS_MULTIPLE_SCALE_MATCHES"
    else:
        result["status"] = "MIXED_OR_UNRESOLVED"

    return result
