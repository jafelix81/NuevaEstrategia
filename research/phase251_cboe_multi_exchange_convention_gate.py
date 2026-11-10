#!/usr/bin/env python3
"""Phase 251: exchange-aware Cboe Open-Close EOD measurement eligibility.

This is a deterministic convention/aggregation contract. It does not download
vendor data, establish historical first receipt, admit PIT, or test returns.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable

from research.phase250_cboe_openclose_convention_gate import (
    compute_directional_feature,
    parse_date,
)

EXCHANGE_HISTORY_START = {
    "C1": date(2005, 1, 3),
    "BZX": date(2018, 1, 2),
    "C2": date(2018, 1, 2),
    "EDGX": date(2018, 1, 2),
}
POST_MIGRATION_START = date(2011, 1, 2)
CURRENT_PARTICIPANT_CODE_START = date(2019, 10, 1)
C1_CURRENT_VOLUME_START = date(2019, 10, 7)
C1_OI_SHIFT_END = date(2019, 10, 4)
C2_OI_SHIFT_END = date(2018, 5, 11)
C2_INDUSTRY_VOLUME_DOUBLE_END = date(2018, 5, 11)
C1_GTH_START = date(2023, 12, 11)
FLEX_SERIES_START = date(2024, 10, 16)
SUPPORTED_SECURITY_TYPES = {"1", "2"}


def classify_exchange_date(exchange: object, value: object) -> dict[str, object]:
    """Return exchange-specific archive and convention state for one trade date."""
    venue = str(exchange or "").strip().upper()
    if venue not in EXCHANGE_HISTORY_START:
        raise ValueError("UNSUPPORTED_EXCHANGE")
    trade_date = parse_date(value)
    history_start = EXCHANGE_HISTORY_START[venue]
    history_available = trade_date >= history_start
    if not history_available:
        return {
            "exchange": venue,
            "quote_date": trade_date.isoformat(),
            "history_available": False,
            "history_start": history_start.isoformat(),
            "post_migration_feature_eligible": False,
            "schema_regime": "BEFORE_ADVERTISED_DATASHOP_HISTORY",
            "participant_code_regime": "UNKNOWN",
            "total_exchange_volume_multiplier": 1,
            "total_industry_volume_multiplier": "1",
            "open_interest_convention": "NOT_AVAILABLE",
            "previous_close_scope": "NOT_AVAILABLE",
            "gth_included": False,
            "flex_schema_active": False,
            "strict_pit_admitted": False,
        }

    if venue == "C1" and trade_date < POST_MIGRATION_START:
        schema_regime = "C1_LEGACY_CUSTOMER_FIRM_ORDER_SIZE"
        feature_eligible = False
    else:
        schema_regime = "POST_2011_CAPACITY_EXECUTION_SIZE"
        feature_eligible = True

    c1_old_volume = venue == "C1" and trade_date < C1_CURRENT_VOLUME_START
    c1_old_oi = venue == "C1" and trade_date <= C1_OI_SHIFT_END
    c2_old_oi = venue == "C2" and trade_date <= C2_OI_SHIFT_END
    c2_old_industry = venue == "C2" and trade_date <= C2_INDUSTRY_VOLUME_DOUBLE_END

    if c1_old_oi or c2_old_oi:
        oi_convention = "SHIFTED_ONE_DAY_AHEAD_REQUIRES_SEPARATE_ALIGNMENT"
    else:
        oi_convention = "CONSISTENT_START_OF_DAY_CONVENTION"

    if (venue == "C1" and trade_date <= C1_OI_SHIFT_END) or (
        venue == "C2" and trade_date <= C2_OI_SHIFT_END
    ):
        previous_close_scope = "EXCHANGE_ONLY"
    else:
        previous_close_scope = "INDUSTRY_WIDE"

    return {
        "exchange": venue,
        "quote_date": trade_date.isoformat(),
        "history_available": True,
        "history_start": history_start.isoformat(),
        "post_migration_feature_eligible": feature_eligible,
        "schema_regime": schema_regime,
        "participant_code_regime": (
            "LEGACY_W_CODE_MAY_APPEAR"
            if trade_date < CURRENT_PARTICIPANT_CODE_START
            else "CURRENT_CAPACITY_CODE_MAPPING"
        ),
        # C1's old Total Exchange Volume is (B+S)/2; multiply by two to
        # express it on the current both-sides scale. Other venues have no
        # documented Total Exchange Volume break in the cited specification.
        "total_exchange_volume_multiplier": 2 if c1_old_volume else 1,
        # C2 Total Industry Volume was doubled through 2018-05-11; this is
        # metadata only here and is never summed across exchange files.
        "total_industry_volume_multiplier": "0.5" if c2_old_industry else "1",
        "open_interest_convention": oi_convention,
        "previous_close_scope": previous_close_scope,
        "gth_included": venue == "C1" and trade_date >= C1_GTH_START,
        "flex_schema_active": trade_date >= FLEX_SERIES_START,
        "strict_pit_admitted": False,
        "consolidated_opra_coverage": False,
    }


def _nonnegative_integer(row: dict, field: str) -> int:
    raw = row.get(field)
    if raw is None or not str(raw).strip():
        raise ValueError("MISSING_TOTAL_EXCHANGE_VOLUME")
    try:
        number = Decimal(str(raw).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        raise ValueError("INVALID_TOTAL_EXCHANGE_VOLUME") from None
    if not number.is_finite() or number != number.to_integral_value() or number < 0:
        raise ValueError("INVALID_TOTAL_EXCHANGE_VOLUME")
    return int(number)


def _series_key(row: dict, exchange: str) -> tuple:
    required = ("option_symbol", "expiration_date", "strike_price", "call_put_flag", "series_type")
    if any(not str(row.get(field) or "").strip() for field in required):
        raise ValueError("MISSING_OPTION_SERIES_KEY")
    try:
        expiry = parse_date(row["expiration_date"]).isoformat()
        strike = Decimal(str(row["strike_price"]).strip())
    except (ValueError, InvalidOperation):
        raise ValueError("INVALID_OPTION_SERIES_KEY") from None
    if not strike.is_finite() or strike < 0:
        raise ValueError("INVALID_OPTION_SERIES_KEY")
    call_put = str(row["call_put_flag"]).strip().upper()
    if call_put not in {"C", "P"}:
        raise ValueError("INVALID_CALL_PUT_FLAG")
    series_type = str(row["series_type"]).strip().upper()
    if series_type == "F":
        raise ValueError("FLEX_SERIES_EXCLUDED_FROM_PRIMARY")
    if series_type not in {"S", "N"}:
        raise ValueError("UNSUPPORTED_SERIES_TYPE")
    return (
        exchange,
        str(row["option_symbol"]).strip().upper(),
        expiry,
        strike,
        call_put,
        series_type,
    )


def aggregate_multi_exchange_underlying_rows(
    rows: Iterable[dict],
    capacity: str,
    action: str = "open",
    size_bucket: str | None = None,
) -> dict[str, object]:
    """Aggregate observed venue-specific rows without treating missing venues as zero.

    The signed numerator and gross-capacity denominator are summed first;
    the imbalance is a ratio of sums, never an unweighted mean of venue ratios.
    Total Industry Volume and OI are not summed because they are series-level
    values repeated across exchange files and have exchange/date conventions.
    """
    rows = list(rows)
    if not rows:
        raise ValueError("EMPTY_UNDERLYING_GROUP")

    normalized = []
    dates = set()
    underlyings = set()
    security_types = set()
    seen_series = set()
    venue_row_counts: dict[str, int] = {}
    venue_volume: dict[str, int] = {}
    venue_multipliers: dict[str, int] = {}
    signed_total = 0
    gross_total = 0
    observed_series = set()

    for row in rows:
        exchange = str(row.get("exchange") or "").strip().upper()
        if not exchange:
            raise ValueError("MISSING_EXCHANGE")
        state = classify_exchange_date(exchange, row.get("quote_date"))
        if not state["history_available"]:
            raise ValueError("EXCHANGE_HISTORY_NOT_ADVERTISED")
        if not state["post_migration_feature_eligible"]:
            raise ValueError("LEGACY_C1_REQUIRES_SEPARATE_SCHEMA")

        trade_date = str(state["quote_date"])
        underlying = str(row.get("underlying_symbol") or "").strip().upper()
        security_type = str(row.get("security_type") or "").strip()
        if not underlying:
            raise ValueError("MISSING_UNDERLYING")
        if security_type not in SUPPORTED_SECURITY_TYPES:
            raise ValueError("UNSUPPORTED_SECURITY_TYPE_FOR_EQUITY_ETF_RESEARCH")

        key = _series_key(row, exchange)
        if key in seen_series:
            raise ValueError("DUPLICATE_OPTION_SERIES_WITHIN_EXCHANGE")
        seen_series.add(key)
        observed_series.add(key[1:])

        feature = compute_directional_feature(row, capacity, action, size_bucket)
        raw_exchange_volume = _nonnegative_integer(row, "total_exchange_vol")
        multiplier = int(state["total_exchange_volume_multiplier"])
        adjusted_exchange_volume = raw_exchange_volume * multiplier
        if int(feature["gross_capacity_contracts"]) > adjusted_exchange_volume:
            raise ValueError("CAPACITY_GROSS_EXCEEDS_CONVENTION_ADJUSTED_EXCHANGE_VOLUME")

        dates.add(trade_date)
        underlyings.add(underlying)
        security_types.add(security_type)
        signed_total += int(feature["signed_directional_net_contracts"])
        gross_total += int(feature["gross_capacity_contracts"])
        venue_row_counts[exchange] = venue_row_counts.get(exchange, 0) + 1
        venue_volume[exchange] = venue_volume.get(exchange, 0) + adjusted_exchange_volume
        venue_multipliers[exchange] = multiplier
        normalized.append((exchange, key))

    if len(dates) != 1:
        raise ValueError("MIXED_OR_MISSING_QUOTE_DATE")
    if len(underlyings) != 1:
        raise ValueError("MIXED_OR_MISSING_UNDERLYING")
    if len(security_types) != 1:
        raise ValueError("MIXED_OR_MISSING_SECURITY_TYPE")

    total_observed_cboe_volume = sum(venue_volume.values())
    imbalance = Decimal(signed_total) / Decimal(gross_total) if gross_total > 0 else None
    net_share = (
        Decimal(signed_total) / Decimal(total_observed_cboe_volume)
        if total_observed_cboe_volume > 0 else None
    )

    return {
        "status": "MEASUREMENT_CONTRACT_PASS_NO_PIT_NO_ALPHA",
        "quote_date": next(iter(dates)),
        "underlying_symbol": next(iter(underlyings)),
        "security_type": next(iter(security_types)),
        "capacity": capacity,
        "action": action,
        "size_bucket": size_bucket or "all",
        "venue_rows": len(rows),
        "venues_observed": sorted(venue_row_counts),
        "venue_row_counts": dict(sorted(venue_row_counts.items())),
        "unique_option_series_across_observed_venues": len(observed_series),
        "signed_directional_net_contracts": signed_total,
        "gross_capacity_contracts": gross_total,
        "observed_cboe_exchange_volume_adjusted": total_observed_cboe_volume,
        "directional_imbalance_ratio_of_sums": imbalance,
        "net_share_of_observed_cboe_exchange_volume": net_share,
        "total_exchange_volume_multiplier_by_venue": dict(sorted(venue_multipliers.items())),
        "total_industry_volume_aggregated": False,
        "open_interest_aggregated": False,
        "previous_close_used": False,
        "unobserved_venue_or_series_absence_is_zero": False,
        "venue_coverage_complete": False,
        "consolidated_opra_coverage": False,
        "strict_pit_admitted": False,
        "alpha_admission": False,
        "f80_frozen": True,
        "consumed_holdout_used": False,
        "production_changed": False,
        "universe_changed": False,
    }
