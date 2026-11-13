"""Phase 355: reconcile Cboe Open-Close EOD participant volume to exchange totals.

Public one-day sample only. This is an accounting/schema diagnostic, not a
return test, point-in-time validation, or inference about informed traders.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import time
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SAMPLE_URL = "https://datashop.cboe.com/download/sample/218"
USER_AGENT = "Mozilla/5.0 (compatible; NuevaEstrategiaResearch/1.0)"
CAPACITY_ACTIONS = {
    "firm": ("open_buy", "close_buy", "open_sell", "close_sell"),
    "bd": ("open_buy", "close_buy", "open_sell", "close_sell"),
    "mm": ("buy", "sell"),
}
BUCKETS = ("lt_100", "100_199", "gt_199")
BUCKET_ACTIONS = ("open_buy", "close_buy", "open_sell", "close_sell")
VOLUME_FIELDS = []
for prefix, actions in CAPACITY_ACTIONS.items():
    for action in actions:
        VOLUME_FIELDS.append(f"{prefix}_{action}_vol")
for prefix in ("cust", "procust"):
    for bucket in BUCKETS:
        for action in BUCKET_ACTIONS:
            VOLUME_FIELDS.append(f"{prefix}_{bucket}_{action}_vol")
QTY_FIELDS = [field[:-4] + "_qty" for field in VOLUME_FIELDS]
BUCKET_PAIRS = [
    (f"{prefix}_{bucket}_{action}_qty", f"{prefix}_{bucket}_{action}_vol", bucket)
    for prefix in ("cust", "procust")
    for bucket in BUCKETS
    for action in BUCKET_ACTIONS
]
REQUIRED_FIELDS = [
    "quote_date", "underlying_symbol", "security_type", "option_symbol",
    "expiration_date", "strike_price", "call_put_flag", "series_type",
    "total_exchange_vol", "total_industry_vol",
] + VOLUME_FIELDS + QTY_FIELDS


def norm(value: str) -> str:
    return "_".join((value or "").replace("\ufeff", "").strip().lower().split())


def parse_nonnegative_int(value: str | None) -> int | None:
    if value is None or not str(value).strip():
        return None
    try:
        number = Decimal(str(value).replace(",", "").strip())
    except InvalidOperation:
        return None
    if not number.is_finite() or number != number.to_integral_value() or number < 0:
        return None
    return int(number)


def bucket_volume_valid(qty: int, volume: int, bucket: str) -> bool:
    if qty == 0:
        return volume == 0
    if bucket == "lt_100":
        return 0 <= volume < 100 * qty
    if bucket == "100_199":
        return 100 * qty <= volume <= 199 * qty
    if bucket == "gt_199":
        return volume >= 200 * qty
    raise ValueError(f"unknown size bucket: {bucket}")


def extract_eod_csv(payload: bytes) -> tuple[str, bytes]:
    found: list[tuple[str, bytes]] = []

    def scan(data: bytes, label: str, depth: int) -> None:
        if depth > 5:
            raise ValueError("nested ZIP depth exceeds safety limit")
        if data.startswith(b"PK\x03\x04"):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                bad = archive.testzip()
                if bad:
                    raise ValueError(f"ZIP CRC failure: {bad}")
                for member in archive.namelist():
                    if member.endswith("/"):
                        continue
                    scan(archive.read(member), f"{label}!{member}", depth + 1)
            return
        if label.lower().endswith(".csv") and "eod sample" in label.lower():
            found.append((label, data))

    scan(payload, "root.zip", 0)
    if len(found) != 1:
        raise ValueError(f"expected exactly one EOD sample CSV; found {len(found)}")
    return found[0]


def audit_csv(payload: bytes, member: str) -> dict:
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise ValueError("EOD CSV has no header")
    headers = [norm(x) for x in reader.fieldnames]
    if len(headers) != len(set(headers)):
        raise ValueError("duplicate normalized header")
    missing = sorted(set(REQUIRED_FIELDS) - set(headers))
    if missing:
        return {
            "status": "FAIL_REQUIRED_SCHEMA",
            "member": member,
            "column_count": len(headers),
            "missing_columns": missing,
        }

    rows = 0
    width_errors = 0
    missing_numeric = Counter()
    invalid_numeric = Counter()
    zero_numeric = Counter()
    exact_match = 0
    mismatches = 0
    comparable = 0
    abs_diffs: list[int] = []
    sum_exchange = 0
    sum_participant = 0
    group_totals = defaultdict(int)
    bucket_violations = Counter()
    bucket_comparable = Counter()
    exchange_gt_industry = 0
    exchange_industry_comparable = 0
    zero_exchange_with_participant = 0
    participant_with_zero_exchange = 0
    underlyings = set()
    quote_dates = set()
    series_keys = set()
    duplicate_keys = 0
    series_types = Counter()
    calls_puts = Counter()

    for raw in reader:
        rows += 1
        if None in raw or any(value is None for value in raw.values()):
            width_errors += 1
        row = {norm(k): (v or "").strip() for k, v in raw.items() if k is not None}
        if row.get("underlying_symbol"):
            underlyings.add(row["underlying_symbol"])
        if row.get("quote_date"):
            quote_dates.add(row["quote_date"])
        series_types[row.get("series_type") or "BLANK"] += 1
        calls_puts[row.get("call_put_flag") or "BLANK"] += 1
        key = tuple(row.get(k, "") for k in (
            "quote_date", "underlying_symbol", "option_symbol",
            "expiration_date", "strike_price", "call_put_flag", "series_type",
        ))
        if all(key):
            if key in series_keys:
                duplicate_keys += 1
            else:
                series_keys.add(key)

        parsed_volumes = {}
        all_volumes_valid = True
        for field in VOLUME_FIELDS:
            value = parse_nonnegative_int(row.get(field))
            if value is None:
                all_volumes_valid = False
                if not row.get(field):
                    missing_numeric[field] += 1
                else:
                    invalid_numeric[field] += 1
            else:
                parsed_volumes[field] = value
                if value == 0:
                    zero_numeric[field] += 1
                group = field.split("_", 1)[0]
                group_totals[group] += value

        exchange = parse_nonnegative_int(row.get("total_exchange_vol"))
        industry = parse_nonnegative_int(row.get("total_industry_vol"))
        if exchange is None:
            all_volumes_valid = False
            if not row.get("total_exchange_vol"):
                missing_numeric["total_exchange_vol"] += 1
            else:
                invalid_numeric["total_exchange_vol"] += 1
        elif exchange == 0:
            zero_numeric["total_exchange_vol"] += 1
        if industry is None:
            if not row.get("total_industry_vol"):
                missing_numeric["total_industry_vol"] += 1
            else:
                invalid_numeric["total_industry_vol"] += 1
        elif industry == 0:
            zero_numeric["total_industry_vol"] += 1

        if all_volumes_valid and exchange is not None:
            participant_sum = sum(parsed_volumes.values())
            comparable += 1
            sum_exchange += exchange
            sum_participant += participant_sum
            if participant_sum == exchange:
                exact_match += 1
            else:
                mismatches += 1
                abs_diffs.append(abs(participant_sum - exchange))
            if exchange == 0 and participant_sum > 0:
                zero_exchange_with_participant += 1
            if exchange > 0 and participant_sum == 0:
                participant_with_zero_exchange += 1

        if exchange is not None and industry is not None and industry > 0:
            exchange_industry_comparable += 1
            if exchange > industry:
                exchange_gt_industry += 1

        for qty_field, vol_field, bucket in BUCKET_PAIRS:
            qty = parse_nonnegative_int(row.get(qty_field))
            volume = parse_nonnegative_int(row.get(vol_field))
            if qty is None or volume is None:
                continue
            bucket_comparable[bucket] += 1
            if not bucket_volume_valid(qty, volume, bucket):
                bucket_violations[bucket] += 1

    match_rate = exact_match / comparable if comparable else None
    bucket_total = sum(bucket_comparable.values())
    bucket_violation_total = sum(bucket_violations.values())
    industry_violation_rate = (
        exchange_gt_industry / exchange_industry_comparable
        if exchange_industry_comparable else None
    )
    # These are predeclared accounting checks, not alpha criteria.
    accounting_pass = (
        rows > 0
        and width_errors == 0
        and comparable == rows
        and match_rate is not None and match_rate >= 0.995
        and bucket_total > 0 and bucket_violation_total == 0
        and exchange_industry_comparable == rows
        and exchange_gt_industry == 0
        and duplicate_keys == 0
    )
    return {
        "status": "PASS_ACCOUNTING_DIAGNOSTIC" if accounting_pass else "ACCOUNTING_EXCEPTIONS_FOUND",
        "member": member,
        "member_sha256": hashlib.sha256(payload).hexdigest(),
        "row_count": rows,
        "column_count": len(headers),
        "underlying_count": len(underlyings),
        "unique_series_count": len(series_keys),
        "duplicate_series_key_rows": duplicate_keys,
        "quote_dates": sorted(quote_dates),
        "series_type_counts": dict(sorted(series_types.items())),
        "call_put_counts": dict(sorted(calls_puts.items())),
        "row_width_errors": width_errors,
        "participant_volume_fields": len(VOLUME_FIELDS),
        "participant_volume_fields_present": len(set(VOLUME_FIELDS) & set(headers)),
        "participant_volume_comparable_rows": comparable,
        "participant_volume_exact_match_rows": exact_match,
        "participant_volume_mismatch_rows": mismatches,
        "participant_volume_exact_match_rate": match_rate,
        "sum_total_exchange_volume": sum_exchange,
        "sum_participant_side_volume": sum_participant,
        "sum_participant_minus_exchange": sum_participant - sum_exchange,
        "median_absolute_row_difference": (
            sorted(abs_diffs)[len(abs_diffs) // 2] if abs_diffs else 0
        ),
        "max_absolute_row_difference": max(abs_diffs) if abs_diffs else 0,
        "participant_volume_by_capacity": dict(sorted(group_totals.items())),
        "size_bucket_comparable_pairs": dict(sorted(bucket_comparable.items())),
        "size_bucket_violations": dict(sorted(bucket_violations.items())),
        "size_bucket_violation_total": bucket_violation_total,
        "exchange_gt_industry_rows": exchange_gt_industry,
        "exchange_industry_comparable_rows": exchange_industry_comparable,
        "exchange_gt_industry_rate": industry_violation_rate,
        "zero_exchange_with_participant_volume_rows": zero_exchange_with_participant,
        "participant_volume_with_zero_exchange_rows": participant_with_zero_exchange,
        "missing_numeric_cells": dict(sorted(missing_numeric.items())),
        "invalid_numeric_cells": dict(sorted(invalid_numeric.items())),
        "zero_numeric_cells": dict(sorted(zero_numeric.items())),
        "accounting_gate": {
            "participant_sum_vs_total_exchange_exact_match_rate_min": 0.995,
            "participant_sum_exact_match_pass": bool(match_rate is not None and match_rate >= 0.995),
            "customer_size_bucket_aggregate_bounds_pass": bucket_violation_total == 0,
            "exchange_volume_not_above_industry_pass": (
                exchange_industry_comparable == rows and exchange_gt_industry == 0
            ),
            "unique_series_keys_pass": duplicate_keys == 0,
            "overall_pass": accounting_pass,
        },
        "interpretation": (
            "Cboe EOD specification says total_exchange_vol counts both sides of a trade. "
            "Participant volume fields are also split by participant side; exact reconciliation "
            "is tested empirically, not assumed. Customer/Pro-Customer bucket bounds are "
            "aggregate arithmetic checks implied by per-trade size buckets. A pass validates "
            "one public C1 sample only, not historical coverage, PIT, licensing or alpha."
        ),
    }


def download(url: str, retries: int = 3) -> dict:
    last_error = None
    for attempt in range(retries):
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
        try:
            with urlopen(request, timeout=90) as response:
                payload = response.read()
                return {
                    "payload": payload,
                    "http_status": response.status,
                    "content_type": response.headers.get("Content-Type", ""),
                    "final_url": response.geturl(),
                }
        except HTTPError as error:
            last_error = f"HTTP {error.code}"
            if error.code not in (408, 429, 500, 502, 503, 504):
                raise
        except (URLError, TimeoutError, OSError) as error:
            last_error = f"{type(error).__name__}: {error}"
        if attempt + 1 < retries:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"download failed after {retries} attempts: {last_error}")


def run_audit() -> dict:
    sample = download(SAMPLE_URL)
    member, csv_payload = extract_eod_csv(sample["payload"])
    audit = audit_csv(csv_payload, member)
    return {
        "phase": 355,
        "status": "COMPLETED_DIAGNOSTIC",
        "retrieved_at_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "sample": {
            "url": SAMPLE_URL,
            "http_status": sample["http_status"],
            "content_type": sample["content_type"],
            "final_url": sample["final_url"],
            "archive_bytes": len(sample["payload"]),
            "archive_sha256": hashlib.sha256(sample["payload"]).hexdigest(),
        },
        "eod_accounting_audit": audit,
        "gates": {
            "historical_coverage_established": False,
            "historical_pit_admitted": False,
            "prospective_pit_admitted": False,
            "licensing_confirmed": False,
            "return_test_authorized": False,
            "alpha_admission": False,
            "holdout_used": False,
            "f80_frozen": True,
        },
        "decision": (
            "ACCOUNTING_GATE_PASS_ONE_C1_SAMPLE_ONLY"
            if audit["status"] == "PASS_ACCOUNTING_DIAGNOSTIC"
            else "ACCOUNTING_GATE_NOT_PASSED_REQUIRES_FIELD_LEVEL_REVIEW"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("phase355_output/audit.json"))
    args = parser.parse_args()
    try:
        result = run_audit()
    except Exception as error:
        result = {
            "phase": 355,
            "status": "AUDIT_EXECUTION_ERROR",
            "error_type": type(error).__name__,
            "error": str(error)[:500],
            "gates": {
                "historical_coverage_established": False,
                "historical_pit_admitted": False,
                "prospective_pit_admitted": False,
                "licensing_confirmed": False,
                "return_test_authorized": False,
                "alpha_admission": False,
                "holdout_used": False,
                "f80_frozen": True,
            },
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0 if result.get("status") == "COMPLETED_DIAGNOSTIC" else 2


if __name__ == "__main__":
    raise SystemExit(main())
