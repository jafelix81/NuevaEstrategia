#!/usr/bin/env python3
"""Phase 249: apply the preregistered Cboe EOD flow contract to the real public sample.

The sample is a single-date, 20% C1 EOD sample. This is an implementation and
cross-sectional measurement audit only: no return labels, PIT reconstruction,
or alpha test are performed. Raw rows and underlying symbols are never written.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Iterable

from research.phase168_cboe_openclose_eod_public_sample_audit import (
    SAMPLE_URL,
    _csv_members,
    audit_archive,
    bucket_columns,
    download_sample,
    expected_columns_eod,
    parse_member_name,
)
from research.phase248_cboe_openclose_feature_contract import aggregate_underlying_rows

VOLUME_FIELDS = [name for name in bucket_columns() if name.endswith("_vol")]
FEATURE_SPECS = [
    ("customer_open_all", "customer", "open", None),
    ("customer_open_lt_100", "customer", "open", "lt_100"),
    ("customer_open_100_199", "customer", "open", "100_199"),
    ("customer_open_gt_199", "customer", "open", "gt_199"),
    ("pro_customer_open_all", "pro_customer", "open", None),
    ("pro_customer_open_lt_100", "pro_customer", "open", "lt_100"),
    ("pro_customer_open_100_199", "pro_customer", "open", "100_199"),
    ("pro_customer_open_gt_199", "pro_customer", "open", "gt_199"),
    ("customer_close_all", "customer", "close", None),
    ("pro_customer_close_all", "pro_customer", "close", None),
    ("firm_open_all", "firm", "open", None),
    ("broker_dealer_open_all", "broker_dealer", "open", None),
]


def _integer(value: object, field: str) -> int:
    raw = str(value if value is not None else "").strip().replace(",", "")
    if not raw:
        raise ValueError(f"BLANK_NUMERIC_FIELD:{field}")
    number = Decimal(raw)
    if not number.is_finite() or number != number.to_integral_value() or number < 0:
        raise ValueError(f"INVALID_NONNEGATIVE_INTEGER:{field}")
    return int(number)


def _date(value: object) -> str:
    raw = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError("INVALID_QUOTE_DATE")


def _quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 6)


def _feature_summary(items: list[dict]) -> dict[str, object]:
    net = [int(x["signed_directional_net_contracts"]) for x in items]
    imbalance = [float(x["directional_imbalance"]) for x in items if x["directional_imbalance"] is not None]
    net_share = [float(x["net_share_of_c1_volume"]) for x in items if x["net_share_of_c1_volume"] is not None]
    gross_share = [
        float(Decimal(int(x["gross_capacity_contracts"])) / Decimal(int(x["total_c1_contracts"])))
        for x in items if int(x["total_c1_contracts"]) > 0
    ]
    return {
        "underlying_groups": len(items),
        "positive_net_groups": sum(value > 0 for value in net),
        "negative_net_groups": sum(value < 0 for value in net),
        "zero_net_groups": sum(value == 0 for value in net),
        "defined_imbalance_groups": len(imbalance),
        "median_directional_imbalance": round(median(imbalance), 6) if imbalance else None,
        "p10_directional_imbalance": _quantile(imbalance, 0.10),
        "p90_directional_imbalance": _quantile(imbalance, 0.90),
        "median_net_share_of_c1_volume": round(median(net_share), 8) if net_share else None,
        "median_gross_capacity_share_of_c1_volume": round(median(gross_share), 8) if gross_share else None,
    }


def analyze_rows(
    rows: Iterable[dict[str, str]],
    *,
    member_name: str,
    member_sha256: str,
    archive_sha256: str,
    archive_bytes: int,
    retrieved_at_utc: str,
) -> dict[str, object]:
    rows = list(rows)
    if not rows:
        raise ValueError("EMPTY_EOD_SAMPLE")

    quote_dates = {_date(row.get("quote_date")) for row in rows}
    if len(quote_dates) != 1:
        raise ValueError("MIXED_QUOTE_DATES")
    quote_date = next(iter(quote_dates))
    if quote_date < "2019-10-07":
        raise ValueError("PRE_PRIMARY_HISTORY_START")

    security_counts: Counter[str] = Counter()
    series_counts: Counter[str] = Counter()
    all_underlyings: dict[str, set[str]] = defaultdict(set)
    primary_underlyings: dict[str, set[str]] = defaultdict(set)
    duplicate_keys: set[tuple[str, ...]] = set()
    seen_keys: set[tuple[str, ...]] = set()
    reconciliation_exact = 0
    reconciliation_mismatch = 0
    flex_excluded = 0
    non_equity_etf_excluded = 0
    primary_rows = 0
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    for row in rows:
        date_value = _date(row.get("quote_date"))
        if date_value != quote_date:
            raise ValueError("MIXED_QUOTE_DATES")
        underlying = str(row.get("underlying_symbol") or "").strip().upper()
        if not underlying:
            raise ValueError("MISSING_UNDERLYING")
        security_type = str(row.get("security_type") or "").strip()
        if security_type not in {"1", "2", "3", "4"}:
            raise ValueError("INVALID_SECURITY_TYPE")
        series_type = str(row.get("series_type") or "").strip().upper()
        if series_type not in {"S", "N", "F"}:
            raise ValueError("INVALID_SERIES_TYPE")
        security_counts[security_type] += 1
        series_counts[series_type] += 1
        all_underlyings[security_type].add(underlying)

        key_fields = (
            underlying,
            security_type,
            str(row.get("option_symbol") or "").strip(),
            str(row.get("expiration_date") or "").strip(),
            str(row.get("strike_price") or "").strip(),
            str(row.get("call_put_flag") or "").strip().upper(),
            series_type,
        )
        if any(not item for item in key_fields):
            raise ValueError("INCOMPLETE_OPTION_SERIES_KEY")
        if key_fields in seen_keys:
            duplicate_keys.add(key_fields)
        seen_keys.add(key_fields)

        total_exchange = _integer(row.get("total_exchange_vol"), "total_exchange_vol")
        participant_total = sum(_integer(row.get(field), field) for field in VOLUME_FIELDS)
        if participant_total == total_exchange:
            reconciliation_exact += 1
        else:
            reconciliation_mismatch += 1

        if security_type not in {"1", "2"}:
            non_equity_etf_excluded += 1
            continue
        if series_type == "F":
            flex_excluded += 1
            continue
        primary_rows += 1
        primary_underlyings[security_type].add(underlying)
        groups[(security_type, underlying)].append(row)

    if duplicate_keys:
        raise ValueError("DUPLICATE_OPTION_SERIES_KEYS")
    if reconciliation_mismatch:
        raise ValueError("PARTICIPANT_VOLUME_RECONCILIATION_FAILED")
    if not groups:
        raise ValueError("NO_PRIMARY_EQUITY_ETF_GROUPS")

    feature_values: dict[str, list[dict]] = {name: [] for name, *_ in FEATURE_SPECS}
    aggregation_errors: Counter[str] = Counter()
    for (_security_type, _underlying), group_rows in groups.items():
        for name, capacity, action, size_bucket in FEATURE_SPECS:
            try:
                feature_values[name].append(
                    aggregate_underlying_rows(group_rows, capacity, action, size_bucket)
                )
            except ValueError as exc:
                aggregation_errors[str(exc)] += 1

    feature_groups_expected = len(groups) * len(FEATURE_SPECS)
    feature_groups_built = sum(len(values) for values in feature_values.values())
    feature_gate_pass = feature_groups_built == feature_groups_expected and not aggregation_errors

    return {
        "phase": 249,
        "status": "REAL_SAMPLE_FEATURE_REPROCESS_PASS_NO_PIT_NO_ALPHA" if feature_gate_pass else "FAIL_FEATURE_AGGREGATION",
        "source": "Cboe C1 Open-Close EOD public 20% sample",
        "sample_date": quote_date,
        "sample_member": member_name.rsplit("/", 1)[-1],
        "sample_member_sha256": member_sha256,
        "sample_archive_sha256": archive_sha256,
        "sample_archive_bytes": archive_bytes,
        "retrieved_at_utc": retrieved_at_utc,
        "rows": len(rows),
        "security_type_row_counts": dict(sorted(security_counts.items())),
        "series_type_row_counts": dict(sorted(series_counts.items())),
        "unique_underlyings_all_by_security_type": {key: len(value) for key, value in sorted(all_underlyings.items())},
        "primary_equity_etf": {
            "rows_after_flex_exclusion": primary_rows,
            "underlying_groups": len(groups),
            "underlying_groups_by_security_type": {key: len(value) for key, value in sorted(primary_underlyings.items())},
            "flex_rows_excluded": flex_excluded,
            "index_and_warrant_rows_excluded": non_equity_etf_excluded,
        },
        "participant_volume_reconciliation": {
            "exact_rows": reconciliation_exact,
            "mismatch_rows": reconciliation_mismatch,
            "exact_rate": round(reconciliation_exact / len(rows), 8),
        },
        "feature_aggregation": {
            "specifications": [name for name, *_ in FEATURE_SPECS],
            "expected_underlying_feature_groups": feature_groups_expected,
            "built_underlying_feature_groups": feature_groups_built,
            "quarantined_aggregation_errors": dict(sorted(aggregation_errors.items())),
            "complete": feature_gate_pass,
            "cross_sectional_diagnostics": {
                name: _feature_summary(values) for name, values in feature_values.items()
            },
        },
        "limitations": {
            "single_trade_date": True,
            "public_sample_fraction": "20_percent",
            "full_exchange_history_coverage_proven": False,
            "inactive_delisted_underlying_coverage_proven": False,
            "historical_first_receipt_proven": False,
            "preliminary_final_vintage_history_proven": False,
            "strict_pit_admitted": False,
            "returns_tested": False,
            "alpha_admission": False,
            "raw_rows_persisted": False,
            "raw_symbols_persisted": False,
            "f80_frozen": True,
            "consumed_holdout_used": False,
            "production_changed": False,
            "universe_changed": False,
        },
        "decision": (
            "Real-sample implementation diagnostic only. A one-day 20% public sample cannot "
            "establish historical continuity, point-in-time availability, return prediction or alpha."
        ),
    }


def parse_eod_rows(member_name: str, payload: bytes) -> list[dict[str, str]]:
    decoded = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    headers = [str(value or "").strip().lower() for value in (reader.fieldnames or [])]
    expected = expected_columns_eod()
    if len(headers) != len(set(headers)):
        raise ValueError("DUPLICATE_EOD_HEADERS")
    if set(headers) != set(expected):
        raise ValueError("EOD_HEADER_CONTRACT_MISMATCH")
    rows = []
    for raw in reader:
        if None in raw:
            raise ValueError("EOD_ROW_EXTRA_FIELDS")
        rows.append({str(key).strip().lower(): str(value or "").strip() for key, value in raw.items()})
    return rows


def run_live() -> dict[str, object]:
    retrieved = datetime.now(timezone.utc).isoformat()
    raw_zip, headers, final_url = download_sample(SAMPLE_URL)
    archive = audit_archive(raw_zip, headers, retrieved_at_utc=retrieved, final_url=final_url)
    if not str(archive.get("status", "")).startswith("PASS_"):
        raise ValueError("PHASE168_ARCHIVE_GATE_FAILED")
    candidates = []
    for member_name, payload in _csv_members(raw_zip):
        try:
            metadata = parse_member_name(member_name)
        except ValueError:
            continue
        if metadata["exchange"] == "C1" and metadata["file_kind"] == "SAMPLE_UNSPECIFIED":
            candidates.append((member_name, payload, metadata))
    if len(candidates) != 1:
        raise ValueError("C1_EOD_SAMPLE_MEMBER_NOT_UNIQUE")
    member_name, member_payload, metadata = candidates[0]
    rows = parse_eod_rows(member_name, member_payload)
    result = analyze_rows(
        rows,
        member_name=member_name,
        member_sha256=hashlib.sha256(member_payload).hexdigest(),
        archive_sha256=hashlib.sha256(raw_zip).hexdigest(),
        archive_bytes=len(raw_zip),
        retrieved_at_utc=retrieved,
    )
    result["source_url"] = SAMPLE_URL
    result["source_final_url"] = f"{final_url.split('?', 1)[0]}"
    result["http_last_modified"] = headers.get("Last-Modified")
    result["http_etag"] = headers.get("ETag")
    result["archive_schema_audit"] = {
        "phase168_status": archive.get("status"),
        "eod_member_count": archive.get("eod_member_count"),
        "intraday_member_count": archive.get("intraday_member_count"),
        "schema_failure_count": archive.get("schema_failure_count"),
    }
    result["member_filename_date"] = metadata["quote_date"]
    if result["sample_date"] != metadata["quote_date"]:
        raise ValueError("MEMBER_FILENAME_AND_ROW_DATE_MISMATCH")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase249_output/phase249_cboe_openclose_real_sample.json")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = run_live()
    except Exception as exc:
        result = {
            "phase": 249,
            "status": "BLOCKED_OR_FAILED_REAL_SAMPLE_REPROCESS",
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
            "strict_pit_admitted": False,
            "returns_tested": False,
            "alpha_admission": False,
            "f80_frozen": True,
            "consumed_holdout_used": False,
            "raw_rows_persisted": False,
            "raw_symbols_persisted": False,
        }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "REAL_SAMPLE_FEATURE_REPROCESS_PASS_NO_PIT_NO_ALPHA" else 2


if __name__ == "__main__":
    raise SystemExit(main())
