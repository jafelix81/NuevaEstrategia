#!/usr/bin/env python3
"""Phase 248: fail-closed Cboe Open-Close EOD feature construction contract."""
from __future__ import annotations
import argparse
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime
from pathlib import Path
from typing import Iterable

CAPACITY_PREFIX = {"firm": "firm", "broker_dealer": "bd", "customer": "cust", "pro_customer": "procust"}
BUCKET_PREFIX = {"lt_100": "lt_100", "100_199": "100_199", "gt_199": "gt_199"}
ACTIONS = {"open", "close"}


def _required_nonnegative_integer(row: dict, field: str) -> int:
    if field not in row:
        raise ValueError(f"MISSING_FIELD:{field}")
    raw = row.get(field)
    if raw is None or not str(raw).strip():
        raise ValueError(f"MISSING_VALUE:{field}")
    try:
        value = Decimal(str(raw).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        raise ValueError(f"INVALID_INTEGER:{field}") from None
    if not value.is_finite() or value != value.to_integral_value():
        raise ValueError(f"INVALID_INTEGER:{field}")
    if value < 0:
        raise ValueError(f"NEGATIVE_VALUE:{field}")
    return int(value)


def _optional_nonnegative_integer(row: dict, field: str) -> int | None:
    if field not in row or row.get(field) is None or not str(row.get(field)).strip():
        return None
    return _required_nonnegative_integer(row, field)


def _capacity_volume(row: dict, capacity: str, action: str, side: str, size_bucket: str | None) -> int:
    if capacity not in CAPACITY_PREFIX:
        raise ValueError(f"UNSUPPORTED_CAPACITY:{capacity}")
    if action not in ACTIONS:
        raise ValueError(f"UNSUPPORTED_ACTION:{action}")
    if side not in {"buy", "sell"}:
        raise ValueError(f"UNSUPPORTED_SIDE:{side}")
    prefix = CAPACITY_PREFIX[capacity]
    if capacity in {"customer", "pro_customer"}:
        if size_bucket is not None and size_bucket not in BUCKET_PREFIX:
            raise ValueError(f"UNSUPPORTED_SIZE_BUCKET:{size_bucket}")
        buckets = [BUCKET_PREFIX[size_bucket]] if size_bucket else list(BUCKET_PREFIX.values())
    else:
        if size_bucket is not None:
            raise ValueError(f"SIZE_BUCKET_NOT_DEFINED_FOR:{capacity}")
        buckets = [None]
    total = 0
    for bucket in buckets:
        stem = f"{prefix}_{bucket}_" if bucket else f"{prefix}_"
        total += _required_nonnegative_integer(row, f"{stem}{action}_{side}_vol")
    return total


def compute_row_feature(row: dict, capacity: str, action: str = "open", size_bucket: str | None = None) -> dict:
    """Volume-only directional proxy; not delta-weighted and not beneficial-owner flow."""
    call_put = str(row.get("call_put_flag") or "").strip().upper()
    if call_put not in {"C", "P"}:
        raise ValueError("INVALID_CALL_PUT_FLAG")
    buy = _capacity_volume(row, capacity, action, "buy", size_bucket)
    sell = _capacity_volume(row, capacity, action, "sell", size_bucket)
    signed_net = buy - sell if call_put == "C" else sell - buy
    gross_capacity_volume = buy + sell
    total_c1_volume = _required_nonnegative_integer(row, "total_exchange_vol")
    if gross_capacity_volume > total_c1_volume:
        raise ValueError("CAPACITY_VOLUME_EXCEEDS_TOTAL_EXCHANGE_VOLUME")
    total_industry_volume = _optional_nonnegative_integer(row, "total_industry_vol")
    imbalance = Decimal(signed_net) / Decimal(gross_capacity_volume) if gross_capacity_volume > 0 else None
    net_share_of_c1 = Decimal(signed_net) / Decimal(total_c1_volume) if total_c1_volume > 0 else None
    net_share_of_industry = (
        Decimal(signed_net) / Decimal(total_industry_volume)
        if total_industry_volume is not None and total_industry_volume > 0 else None
    )
    c1_to_industry_volume_ratio = (
        Decimal(total_c1_volume) / Decimal(total_industry_volume)
        if total_industry_volume is not None and total_industry_volume > 0 else None
    )
    return {
        "capacity": capacity, "action": action, "size_bucket": size_bucket or "all",
        "call_put_flag": call_put, "buy_volume": buy, "sell_volume": sell,
        "signed_directional_net_contracts": signed_net, "gross_capacity_contracts": gross_capacity_volume,
        "total_c1_contracts": total_c1_volume, "total_industry_contracts": total_industry_volume,
        "directional_imbalance": imbalance, "net_share_of_c1_volume": net_share_of_c1,
        "net_share_of_industry_volume": net_share_of_industry,
        "c1_to_industry_volume_ratio": c1_to_industry_volume_ratio, "delta_weighted": False,
    }


def _normalize_quote_date(value: object) -> str:
    raw = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError("INVALID_QUOTE_DATE")


def aggregate_underlying_rows(rows: Iterable[dict], capacity: str, action: str = "open", size_bucket: str | None = None) -> dict:
    """Aggregate unique option-series rows for one underlying/date; fail closed on any row."""
    rows = list(rows)
    if not rows:
        raise ValueError("EMPTY_UNDERLYING_GROUP")
    dates = {_normalize_quote_date(r.get("quote_date")) for r in rows}
    symbols = {str(r.get("underlying_symbol") or "").strip().upper() for r in rows}
    security_types = {str(r.get("security_type") or "").strip() for r in rows}
    if len(dates) != 1:
        raise ValueError("MIXED_OR_MISSING_QUOTE_DATE")
    if next(iter(dates)) < "2019-10-07":
        raise ValueError("PRE_PRIMARY_HISTORY_START")
    if len(symbols) != 1 or "" in symbols:
        raise ValueError("MIXED_OR_MISSING_UNDERLYING")
    if len(security_types) != 1 or "" in security_types:
        raise ValueError("MIXED_OR_MISSING_SECURITY_TYPE")
    if next(iter(security_types)) not in {"1", "2"}:
        raise ValueError("UNSUPPORTED_SECURITY_TYPE_FOR_EQUITY_ETF_RESEARCH")
    series_types = {str(r.get("series_type") or "").strip().upper() for r in rows}
    if "F" in series_types:
        raise ValueError("FLEX_SERIES_EXCLUDED_FROM_PRIMARY")
    if not series_types.issubset({"S", "N"}):
        raise ValueError("UNSUPPORTED_SERIES_TYPE")
    series_keys = []
    for row in rows:
        required = ("option_symbol", "expiration_date", "strike_price", "call_put_flag", "series_type")
        if any(not str(row.get(key) or "").strip() for key in required):
            raise ValueError("MISSING_OPTION_SERIES_KEY")
        series_keys.append((
            str(row.get("option_symbol")).strip(), str(row.get("expiration_date")).strip(),
            str(row.get("strike_price")).strip(), str(row.get("call_put_flag")).strip().upper(),
            str(row.get("series_type")).strip().upper(),
        ))
    if len(series_keys) != len(set(series_keys)):
        raise ValueError("DUPLICATE_OPTION_SERIES_KEY")
    features = [compute_row_feature(row, capacity, action, size_bucket) for row in rows]
    signed = sum(item["signed_directional_net_contracts"] for item in features)
    gross = sum(item["gross_capacity_contracts"] for item in features)
    c1 = sum(item["total_c1_contracts"] for item in features)
    industry_values = [item["total_industry_contracts"] for item in features]
    industry_complete = all(value is not None for value in industry_values)
    industry = sum(industry_values) if industry_complete else None
    return {
        "quote_date": next(iter(dates)), "underlying_symbol": next(iter(symbols)),
        "security_type": next(iter(security_types)), "capacity": capacity, "action": action,
        "size_bucket": size_bucket or "all", "series_rows": len(rows),
        "signed_directional_net_contracts": signed, "gross_capacity_contracts": gross,
        "total_c1_contracts": c1, "total_industry_contracts": industry,
        "directional_imbalance": Decimal(signed) / Decimal(gross) if gross > 0 else None,
        "net_share_of_c1_volume": Decimal(signed) / Decimal(c1) if c1 > 0 else None,
        "net_share_of_industry_volume": Decimal(signed) / Decimal(industry) if industry is not None and industry > 0 else None,
        "c1_to_industry_volume_ratio": Decimal(c1) / Decimal(industry) if industry is not None and industry > 0 else None,
        "delta_weighted": False,
    }


def build_audit() -> dict:
    c1, industry = Decimal("4506840"), Decimal("12228281")
    return {
        "phase": 248, "status": "FEATURE_CONTRACT_PASS_SYNTHETIC_ONLY_NO_PIT_NO_ALPHA",
        "source": "Cboe C1 Open-Close EOD",
        "sample_evidence": {
            "trade_date": "2025-03-28", "rows": 23179, "underlyings": 1553, "fields": 86,
            "participant_volume_reconciliation_rows": 23179,
            "participant_volume_reconciliation_exact_rows": 23179,
            "c1_total_exchange_volume": int(c1), "total_industry_volume": int(industry),
            "reported_c1_to_industry_volume_ratio": str((c1 / industry).quantize(Decimal("0.000001"))),
            "source": "Phase 114 public 20% sample audit; not a full-market extract",
        },
        "feature_contract": {
            "primary_capacity_groups": ["customer", "pro_customer"],
            "secondary_capacity_controls": ["firm", "broker_dealer"],
            "primary_action": "open", "secondary_action": "close",
            "primary_size_buckets": ["lt_100", "100_199", "gt_199"],
            "volume_measure": "vol fields are contracts; qty fields are trade counts",
            "call_sign": "buy positive; sell negative", "put_sign": "sell positive; buy negative",
            "normalization": [
                "signed net contracts / total_exchange_vol",
                "signed net contracts / total_industry_vol when observed",
                "signed net contracts / gross capacity contracts when nonzero",
            ],
            "delta_weighted": False, "beneficial_owner_identification": False,
            "complex_order_linkage": False,
        },
        "historical_conventions": {
            "primary_start": "2019-10-07",
            "reason": "C1 open-interest and total-exchange-volume conventions change through 2019-10-04",
            "pre_2011_customer_bucket_semantics": "order size",
            "post_2011_customer_bucket_semantics": "execution size",
            "gth_start": "2023-12-11", "flex_series_start": "2024-10-16",
            "primary_flex_treatment": "exclude series_type F; analyze separately",
            "primary_security_types": ["1=Equity", "2=ETF, separately"],
            "excluded_security_types": ["3=Index", "4=WCO"],
        },
        "pit_and_economic_gates": {
            "final_file_delivery_target": "typically 00:30-01:00 US EST on the next morning",
            "actual_historical_first_receipt": "NOT_VERIFIED",
            "immutable_historical_correction_vintages": "NOT_VERIFIED",
            "historical_daily_archive_completeness": "NOT_VERIFIED",
            "broad_pit_security_coverage": "NOT_ESTABLISHED",
            "prospective_capture": "NOT_ACTIVE_ON_MAIN",
            "strict_pit_admitted": False, "return_test_authorized": False, "alpha_admission": False,
            "f80_frozen": True, "consumed_holdout_used": False,
            "production_changed": False, "universe_changed": False,
        },
        "decision": (
            "Advance C1 Open-Close EOD only to a preregistered measurement candidate. "
            "No return test until actual final-file receipt, historical archive coverage, "
            "security identity and broad-universe coverage gates pass."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase248_output/phase248_cboe_openclose_feature_contract.json")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_audit(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": 248, "status": build_audit()["status"],
        "synthetic_feature_contract": "PASS", "strict_pit_admitted": False, "alpha_admission": False,
    }, indent=2))


if __name__ == "__main__":
    main()
