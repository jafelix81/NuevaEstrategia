#!/usr/bin/env python3
"""Phase 141: Cboe OPRA-wide denominator and venue-share feasibility audit.

Research-only. No aggressor direction is inferred from NBBO location, no trade
conditions are excluded, and Cboe Open-Close two-sided volume is never used as
a one-sided contract-volume denominator.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping

# Official LiveVol exchange map observed in the Phase 112 public artifact.
# ID 5 is the legacy CBOE/C1 code; C2/BZX/EDGX are separate venue IDs.
C1_EXCHANGE_IDS = {"5"}
CBOE_FOUR_EXCHANGE_IDS = {"5", "42", "60", "65"}

OPTION_TRADE_REQUIRED = {
    "underlying_symbol", "market_date", "quote_datetime", "root",
    "expiration", "strike", "option_type", "exchange_id", "trade_size",
    "trade_condition_id", "canceled_trade_condition_id",
}
OPEN_CLOSE_BASE_REQUIRED = {
    "quote_date", "underlying_symbol", "option_symbol",
    "total_exchange_vol", "total_industry_vol",
}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _integer(value: Any, field: str, *, allow_blank: bool = False) -> int | None:
    raw = _text(value)
    if not raw and allow_blank:
        return None
    try:
        number = Decimal(raw.replace(",", ""))
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid_integer:{field}")
    if not number.is_finite() or number != number.to_integral_value():
        raise ValueError(f"invalid_integer:{field}")
    return int(number)


def _date(value: Any) -> str | None:
    raw = _text(value)
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def _clock_class(value: Any) -> str:
    raw = _text(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?", raw):
        return "full_datetime"
    if re.fullmatch(r"\d{2}:\d{2}:\d{2}(?:\.\d+)?", raw):
        return "time_only"
    if re.fullmatch(r"\d{2}:\d{2}\.\d+", raw):
        return "two_component_clock"
    return "unrecognized_or_blank"


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def audit_option_trade_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    exchange_volume: Counter[str] = Counter()
    exchange_rows: Counter[str] = Counter()
    conditions: Counter[str] = Counter()
    cancelled_conditions: Counter[str] = Counter()
    underlyings: set[str] = set()
    dates: set[str] = set()
    series: set[tuple[str, str, str, str, str]] = set()
    clock_formats: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    blank_rows = valid_rows = 0
    total_contracts = 0

    for row in rows:
        if not any(_text(v) for v in row.values()):
            blank_rows += 1
            continue
        missing = OPTION_TRADE_REQUIRED - set(row)
        if missing:
            errors["missing_required_columns"] += 1
            continue
        underlying = _text(row.get("underlying_symbol"))
        market_date = _date(row.get("market_date"))
        root = _text(row.get("root"))
        expiration = _text(row.get("expiration"))
        strike = _text(row.get("strike"))
        option_type = _text(row.get("option_type")).upper()
        try:
            exchange_id = _integer(row.get("exchange_id"), "exchange_id")
            size = _integer(row.get("trade_size"), "trade_size")
            condition = _integer(row.get("trade_condition_id"), "trade_condition_id", allow_blank=True)
            cancelled_condition = _integer(
                row.get("canceled_trade_condition_id"), "canceled_trade_condition_id", allow_blank=True
            )
        except ValueError as exc:
            errors[str(exc)] += 1
            continue
        if not underlying or not market_date or not root or not expiration or not strike:
            errors["missing_identity_or_date"] += 1
            continue
        if option_type not in {"C", "P"}:
            errors["invalid_option_type"] += 1
            continue
        if exchange_id is None or size is None or size <= 0:
            errors["invalid_exchange_or_size"] += 1
            continue
        if condition is None:
            errors["missing_trade_condition"] += 1
            continue

        ex = str(exchange_id)
        exchange_volume[ex] += size
        exchange_rows[ex] += 1
        conditions[str(condition)] += 1
        if cancelled_condition not in (None, 0):
            cancelled_conditions[str(cancelled_condition)] += 1
        underlyings.add(underlying)
        dates.add(market_date)
        series.add((underlying, root, expiration, strike, option_type))
        clock_formats[_clock_class(row.get("quote_datetime"))] += 1
        total_contracts += size
        valid_rows += 1

    c1_contracts = sum(exchange_volume[x] for x in C1_EXCHANGE_IDS)
    cboe_four_contracts = sum(exchange_volume[x] for x in CBOE_FOUR_EXCHANGE_IDS)
    return {
        "valid_trade_rows": valid_rows,
        "blank_padded_rows": blank_rows,
        "underlying_symbols": sorted(underlyings),
        "underlying_count": len(underlyings),
        "market_dates": sorted(dates),
        "unique_option_series": len(series),
        "exchange_ids_observed": sorted(exchange_volume, key=lambda x: int(x)),
        "exchange_rows": dict(sorted(exchange_rows.items(), key=lambda kv: int(kv[0]))),
        "exchange_contract_volume": dict(sorted(exchange_volume.items(), key=lambda kv: int(kv[0]))),
        "trade_condition_rows": dict(sorted(conditions.items(), key=lambda kv: int(kv[0]))),
        "nonzero_cancel_condition_rows": sum(cancelled_conditions.values()),
        "cancelled_condition_ids": dict(cancelled_conditions),
        "quote_datetime_formats": dict(clock_formats),
        "intraday_timestamp_conformance": (
            "FAIL_SAMPLE_FORMAT_CONFORMANCE"
            if clock_formats.get("full_datetime", 0) != valid_rows
            else "PASS_FORMAT_ONLY_NOT_PIT"
        ),
        "total_contract_volume": total_contracts,
        "c1_contract_volume": c1_contracts,
        "c1_volume_share": c1_contracts / total_contracts if total_contracts else None,
        "cboe_four_contract_volume": cboe_four_contracts,
        "cboe_four_volume_share": cboe_four_contracts / total_contracts if total_contracts else None,
        "errors": dict(errors),
        "broad_universe_coverage_proven": len(underlyings) > 1,
    }


def audit_open_close_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    buy_fields: set[str] = set()
    sell_fields: set[str] = set()
    materialized = []
    for row in rows:
        if not any(_text(v) for v in row.values()):
            continue
        materialized.append(row)
        buy_fields.update(k for k in row if k.endswith("_buy_vol"))
        sell_fields.update(k for k in row if k.endswith("_sell_vol"))
    if not materialized:
        raise ValueError("openclose_no_data_rows")
    if not buy_fields or not sell_fields:
        raise ValueError("openclose_participant_volume_fields_missing")

    required = OPEN_CLOSE_BASE_REQUIRED | buy_fields | sell_fields
    missing = required - set(materialized[0])
    if missing:
        raise ValueError("openclose_missing_required_columns")

    dates: set[str] = set()
    underlyings: set[str] = set()
    ratios: list[float] = []
    buy_total = sell_total = exchange_total = industry_total = 0
    reconciled_buy_total = reconciled_industry_total = 0
    equal_side_rows = exchange_reconciled_rows = denominator_rows = 0
    ratio_by_underlying: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])

    for row in materialized:
        date_value = _date(row.get("quote_date"))
        underlying = _text(row.get("underlying_symbol"))
        if not date_value or not underlying:
            raise ValueError("openclose_identity_or_date_invalid")
        dates.add(date_value)
        underlyings.add(underlying)
        buy = sum(_integer(row.get(field), field) or 0 for field in buy_fields)
        sell = sum(_integer(row.get(field), field) or 0 for field in sell_fields)
        exchange = _integer(row.get("total_exchange_vol"), "total_exchange_vol")
        industry = _integer(row.get("total_industry_vol"), "total_industry_vol")
        if exchange is None or industry is None or min(buy, sell, exchange, industry) < 0:
            raise ValueError("openclose_negative_or_missing_volume")
        buy_total += buy
        sell_total += sell
        exchange_total += exchange
        industry_total += industry
        if buy == sell:
            equal_side_rows += 1
        if exchange == buy + sell:
            exchange_reconciled_rows += 1
        if buy == sell and exchange == buy + sell:
            ratio_by_underlying[underlying][0] += buy
            ratio_by_underlying[underlying][1] += industry
            ratio_by_underlying[underlying][2] += 1
            if industry > 0:
                ratios.append(buy / industry)
                denominator_rows += 1
                reconciled_buy_total += buy
                reconciled_industry_total += industry

    weighted_share_proxy = (
        reconciled_buy_total / reconciled_industry_total
        if reconciled_industry_total else None
    )
    underlying_shares = [
        v[0] / v[1] for v in ratio_by_underlying.values() if v[1] > 0
    ]
    return {
        "valid_series_rows": len(materialized),
        "underlying_symbols": sorted(underlyings),
        "underlying_count": len(underlyings),
        "quote_dates": sorted(dates),
        "one_sided_buy_contract_volume": buy_total,
        "one_sided_sell_contract_volume": sell_total,
        "two_sided_total_exchange_volume": exchange_total,
        "reported_total_industry_volume": industry_total,
        "share_proxy_method": "one-sided buy volume / total_industry_vol, only on rows where buy=sell and total_exchange_vol=buy+sell",
        "volume_unit_note": "total_exchange_vol counts both sides of a trade; do not divide it directly by total_industry_vol as a market-share measure",
        "buy_equals_sell_rows": equal_side_rows,
        "total_exchange_equals_buy_plus_sell_rows": exchange_reconciled_rows,
        "weighted_one_sided_c1_share_proxy": weighted_share_proxy,
        "series_share_proxy_median": _quantile(ratios, 0.50),
        "series_share_proxy_p90": _quantile(ratios, 0.90),
        "underlying_share_proxy_median": _quantile(underlying_shares, 0.50),
        "share_proxy_rows": denominator_rows,
        "share_proxy_caveat": (
            "Descriptive only: the public sample is a 20% series sample. "
            "Cboe v1.3 specifies OPRA-sourced total_industry_vol in preliminary files "
            "and OCC-authoritative values in final files; preserve file version."
        ),
    }


def compare_sample_populations(
    option_trade_summary: Mapping[str, Any],
    open_close_summary: Mapping[str, Any],
) -> dict[str, Any]:
    trade_dates = set(option_trade_summary.get("market_dates", []))
    open_dates = set(open_close_summary.get("quote_dates", []))
    trade_underlyings = set(option_trade_summary.get("underlying_symbols", []))
    open_underlyings = set(open_close_summary.get("underlying_symbols", []))
    common_dates = sorted(trade_dates & open_dates)
    common_underlyings = sorted(trade_underlyings & open_underlyings)
    return {
        "common_dates": common_dates,
        "common_underlyings": common_underlyings,
        "same_date_underlying_overlap": bool(common_dates and common_underlyings),
        "direct_cross_source_reconciliation_allowed": bool(common_dates and common_underlyings),
        "contract_level_key_reconciliation_still_required": True,
        "reason": (
            "No common trade date; do not compare venue shares across different dates."
            if not common_dates else
            "Date and underlying overlap exist; reconcile option-series keys, trade conditions and population coverage before comparison."
        ),
    }


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def audit_files(option_trades_csv: str | Path, open_close_csv: str | Path) -> dict[str, Any]:
    trades = audit_option_trade_rows(read_csv(option_trades_csv))
    open_close = audit_open_close_rows(read_csv(open_close_csv))
    cross_source = compare_sample_populations(trades, open_close)
    trades.pop("underlying_symbols", None)
    open_close.pop("underlying_symbols", None)
    return {
        "phase": 141,
        "option_trades": trades,
        "open_close": open_close,
        "cross_source": cross_source,
        "decision": {
            "opra_daily_denominator": "CONDITIONAL_SAMPLE_PASS",
            "broad_universe_coverage": "NOT_PROVEN",
            "intraday_timestamp": "FAIL_PUBLIC_SAMPLE_CONFORMANCE",
            "strict_historical_pit": "UNVERIFIED",
            "alpha_test": "NOT_AUTHORIZED",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--option-trades-csv", required=True)
    parser.add_argument("--open-close-csv", required=True)
    parser.add_argument("--output", default="phase141_cboe_opra_venue_share_audit.json")
    args = parser.parse_args()
    result = audit_files(args.option_trades_csv, args.open_close_csv)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
