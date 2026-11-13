#!/usr/bin/env python3
"""Phase 377: full CFTC TFF Futures Only coverage and contract-key audit.

One read-only Socrata snapshot; no raw rows are written. This is source
feasibility only: it does not construct a feature or use forward returns.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests

DATASET_ID = "gpe5-46if"
RESOURCE_URL = f"https://publicreporting.cftc.gov/resource/{DATASET_ID}.json"
META_URL = f"https://publicreporting.cftc.gov/api/views/{DATASET_ID}.json"
MAX_ROWS = 50000
CODE_FIELD = "cftc_contract_market_code"
DATE_FIELD = "report_date_as_yyyy_mm_dd"
NAME_FIELD = "market_and_exchange_names"
CONTRACT_FIELD = "contract_market_name"
CANDIDATE_CODES = {
    "13874A": "E-MINI S&P 500",
    "209742": "NASDAQ-100 STOCK INDEX (MINI)",
    "239742": "RUSSELL 2000 STOCK INDEX (MINI)",
    "124603": "DOW JONES INDUSTRIAL AVG - x $5",
}
RELATED_PATTERNS = ("S&P 500", "NASDAQ-100", "NASDAQ 100", "RUSSELL 2000", "DOW JONES")
CATEGORY_PREFIXES = {
    "dealer": "dealer",
    "asset_manager": "asset_mgr",
    "leveraged_money": "lev_money",
    "other_reportables": "other_rept",
    "non_reportables": "nonrept",
}


def norm(value):
    return str(value or "").strip().upper()


def parse_report_date(value):
    if value is None or str(value).strip() == "":
        raise ValueError("missing report date")
    return date.fromisoformat(str(value).strip()[:10])


def numeric(value):
    if value is None or str(value).strip() in ("", ".", "NULL", "null"):
        return None
    try:
        d = Decimal(str(value).replace(",", "").strip())
    except InvalidOperation as exc:
        raise ValueError(f"invalid numeric value: {value!r}") from exc
    if not d.is_finite():
        raise ValueError(f"non-finite numeric value: {value!r}")
    return d


def resolve_position_fields(field_names):
    names = [str(x).lower() for x in field_names]
    resolved = {}
    for category, prefix in CATEGORY_PREFIXES.items():
        resolved[category] = {}
        for side in ("long", "short", "spread"):
            if category == "non_reportables" and side == "spread":
                resolved[category][side] = None
                continue
            matches = [
                f for f in names
                if prefix in f and "positions" in f and side in f
                and not any(token in f for token in
                            ("change", "percent", "trader", "concentration"))
            ]
            preferred = [f for f in matches if f.endswith("_all")]
            chosen = preferred if preferred else matches
            resolved[category][side] = chosen[0] if len(chosen) == 1 else None
    return resolved


def _weekly_coverage(dates):
    dates = sorted(set(dates))
    if not dates:
        return {
            "observed_weeks": 0, "expected_weekly_anchors": 0,
            "coverage_pct": None, "missing_week_count": 0,
            "missing_week_examples": [], "max_gap_days": None,
            "non_tuesday_count": 0,
        }
    expected = []
    cursor = dates[0]
    while cursor <= dates[-1]:
        expected.append(cursor)
        cursor += timedelta(days=7)
    missing = sorted(set(expected) - set(dates))
    gaps = [(b - a).days for a, b in zip(dates, dates[1:])]
    return {
        "observed_weeks": len(dates),
        "expected_weekly_anchors": len(expected),
        "coverage_pct": round(100 * len(dates) / len(expected), 6),
        "missing_week_count": len(missing),
        "missing_week_examples": [x.isoformat() for x in missing[:20]],
        "max_gap_days": max(gaps) if gaps else 0,
        "non_tuesday_count": sum(x.weekday() != 1 for x in dates),
    }


def _field_missingness(rows, field_map):
    fields = sorted({
        field for category in field_map.values()
        for field in category.values() if field
    })
    out = {}
    for field in fields:
        out[field] = sum(
            1 for row in rows
            if row.get(field) is None
            or str(row.get(field)).strip() in ("", ".", "NULL", "null")
        )
    return out


def _oi_reconciliation(rows, field_map):
    oi_field = "open_interest_all"
    required = []
    for category in field_map.values():
        required.extend([category.get("long"), category.get("short")])
        if category.get("spread"):
            required.append(category["spread"])
    if not all(required) or not oi_field:
        return {"available": False, "checked_rows": 0, "exact_both_sides": 0}
    checked = exact = 0
    max_abs_residual = Decimal(0)
    for row in rows:
        try:
            values = [numeric(row.get(x)) for x in required]
            oi = numeric(row.get(oi_field))
        except ValueError:
            continue
        if oi is None or any(x is None for x in values):
            continue
        # CFTC instructs users to add spread positions to both long and short
        # sides when reconciling open interest.
        long_total = Decimal(0)
        short_total = Decimal(0)
        valid = True
        for category in field_map.values():
            try:
                long_v = numeric(row.get(category.get("long"))) if category.get("long") else None
                short_v = numeric(row.get(category.get("short"))) if category.get("short") else None
                spread_v = numeric(row.get(category.get("spread"))) if category.get("spread") else Decimal(0)
            except ValueError:
                valid = False
                break
            if long_v is None or short_v is None or spread_v is None:
                valid = False
                break
            long_total += long_v + spread_v
            short_total += short_v + spread_v
        if not valid:
            continue
        checked += 1
        r = max(abs(long_total - oi), abs(short_total - oi))
        if r == 0:
            exact += 1
        if r > max_abs_residual:
            max_abs_residual = r
    return {
        "available": True,
        "checked_rows": checked,
        "exact_both_sides": exact,
        "exact_both_sides_pct": round(100 * exact / checked, 6) if checked else None,
        "max_absolute_residual_contracts": str(max_abs_residual),
        "diagnostic_only": True,
    }


def _candidate_summary(rows, code, display_name, field_map):
    subset = [r for r in rows if norm(r.get(CODE_FIELD)) == code]
    dates_by_row = []
    invalid_dates = 0
    key_counts = Counter()
    names = set()
    contract_names = set()
    exchanges = set()
    for row in subset:
        try:
            d = parse_report_date(row.get(DATE_FIELD))
            dates_by_row.append(d)
            key_counts[(d.isoformat(), code)] += 1
        except ValueError:
            invalid_dates += 1
        if norm(row.get(NAME_FIELD)):
            names.add(str(row.get(NAME_FIELD)).strip())
        if norm(row.get(CONTRACT_FIELD)):
            contract_names.add(str(row.get(CONTRACT_FIELD)).strip())
        if norm(row.get("cftc_market_code")):
            exchanges.add(norm(row.get("cftc_market_code")))
    dates = sorted(set(dates_by_row))
    duplicate_keys = [
        {"report_date": k[0], "rows": v}
        for k, v in key_counts.items() if v > 1
    ]
    missingness = _field_missingness(subset, field_map)
    nonpositive_oi = 0
    invalid_position_values = 0
    for row in subset:
        oi = numeric(row.get("open_interest_all"))
        if oi is None or oi <= 0:
            nonpositive_oi += 1
        for field in missingness:
            try:
                numeric(row.get(field))
            except ValueError:
                invalid_position_values += 1
    return {
        "code": code,
        "expected_label": display_name,
        "row_count": len(subset),
        "first_report_date": dates[0].isoformat() if dates else None,
        "last_report_date": dates[-1].isoformat() if dates else None,
        "weekly_coverage": _weekly_coverage(dates),
        "invalid_report_dates": invalid_dates,
        "duplicate_report_date_code_groups": len(duplicate_keys),
        "duplicate_examples": duplicate_keys[:10],
        "market_exchange_name_variants": sorted(names),
        "contract_name_variants": sorted(contract_names),
        "market_code_variants": sorted(exchanges),
        "position_field_missing_cells": missingness,
        "nonpositive_or_missing_open_interest_rows": nonpositive_oi,
        "invalid_position_numeric_cells": invalid_position_values,
        "open_interest_reconciliation": _oi_reconciliation(subset, field_map),
        "missing_weeks_are_not_zero": True,
    }


def build_summary(rows, field_names, metadata=None, count_before=None, count_after=None,
                  metadata_updated_before=None, metadata_updated_after=None):
    fields = set(field_names)
    required = {CODE_FIELD, DATE_FIELD, NAME_FIELD, CONTRACT_FIELD, "open_interest_all"}
    missing_required = sorted(required - fields)
    field_map = resolve_position_fields(fields)
    category_fields_complete = all(
        field_map[c]["long"] and field_map[c]["short"]
        and (c == "non_reportables" or field_map[c]["spread"])
        for c in CATEGORY_PREFIXES
    )
    id_values = [str(r.get("id", "")).strip() for r in rows if r.get("id") not in (None, "")]
    id_duplicate_count = len(id_values) - len(set(id_values))
    all_dates = []
    for row in rows:
        try:
            all_dates.append(parse_report_date(row.get(DATE_FIELD)))
        except ValueError:
            pass
    related = defaultdict(lambda: {"rows": 0, "first": None, "last": None})
    for row in rows:
        code = norm(row.get(CODE_FIELD))
        name = str(row.get(CONTRACT_FIELD) or row.get(NAME_FIELD) or "").strip()
        upper = name.upper()
        if any(p in upper for p in RELATED_PATTERNS):
            key = (code, name)
            item = related[key]
            item["rows"] += 1
            try:
                d = parse_report_date(row.get(DATE_FIELD))
                item["first"] = d.isoformat() if item["first"] is None else min(item["first"], d.isoformat())
                item["last"] = d.isoformat() if item["last"] is None else max(item["last"], d.isoformat())
            except ValueError:
                pass
    candidates = {
        code: _candidate_summary(rows, code, label, field_map)
        for code, label in CANDIDATE_CODES.items()
    }
    related_series = []
    for (code, name), item in sorted(related.items()):
        related_series.append({
            "code": code, "name": name, **item,
            "non_additive_comparison_warning": code == "13874+",
        })
    snapshot_stable = (
        count_before is not None and count_after is not None
        and count_before == count_after
        and metadata_updated_before is not None
        and metadata_updated_before == metadata_updated_after
    )
    candidate_codes_present = all(
        candidates[code]["row_count"] > 0 for code in CANDIDATE_CODES
    )
    candidate_keys_unique = all(
        candidates[code]["duplicate_report_date_code_groups"] == 0
        for code in CANDIDATE_CODES
    )
    return {
        "phase": 377,
        "source": "CFTC TFF Futures Only Socrata dataset",
        "dataset_id": DATASET_ID,
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "schema_field_count": len(fields),
        "required_schema_fields_missing": missing_required,
        "position_fields": field_map,
        "position_category_schema_complete": category_fields_complete,
        "reported_count_before": count_before,
        "retrieved_row_count": len(rows),
        "reported_count_after": count_after,
        "row_count_reconciled": count_before == len(rows) == count_after,
        "metadata_rows_updated_before": metadata_updated_before,
        "metadata_rows_updated_after": metadata_updated_after,
        "snapshot_stable_during_retrieval": snapshot_stable,
        "dataset_first_report_date": min(all_dates).isoformat() if all_dates else None,
        "dataset_last_report_date": max(all_dates).isoformat() if all_dates else None,
        "dataset_distinct_report_dates": len(set(all_dates)),
        "id_duplicate_count_diagnostic_only": id_duplicate_count,
        "candidate_natural_key": "(report_date_as_yyyy_mm_dd, cftc_contract_market_code)",
        "candidate_natural_key_duplicate_groups_all_dataset": sum(
            1 for n in Counter(
                (str(r.get(DATE_FIELD) or "")[:10], norm(r.get(CODE_FIELD)))
                for r in rows
            ).values() if n > 1
        ),
        "candidate_contracts": candidates,
        "candidate_codes_present_gate": candidate_codes_present,
        "candidate_report_date_code_unique_gate": candidate_keys_unique,
        "related_equity_index_series": related_series[:100],
        "cftc_13874_plus_is_separate_consolidated_series": True,
        "missing_contract_weeks_are_not_zero_or_forward_filled": True,
        "historical_actual_release_dates_beyond_13_months": "NOT_AVAILABLE_PER_CFTC_FAQ",
        "historical_pit_status": "SCHEDULE_PROXY_ONLY_BEFORE_VERIFIED_RELEASE_DATE_WINDOW",
        "position_accounting": "diagnostic only; add spreads to both sides per CFTC guidance",
        "metadata_snapshot_sha256": hashlib.sha256(
            json.dumps(metadata or {}, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "raw_rows_retained": False,
        "raw_ids_retained": False,
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_changed": False,
        "production_changed": False,
        "research_disposition": (
            "CFTC_TFF_COVERAGE_AUDIT_COMPLETE_REVIEW_CONTRACT_CONTINUITY_AND_PIT"
            if not missing_required and category_fields_complete
            and count_before == len(rows) == count_after and snapshot_stable
            and candidate_codes_present and candidate_keys_unique
            else "CFTC_TFF_COVERAGE_AUDIT_INCOMPLETE"
        ),
    }


def request_json(session, url, params=None):
    last_error = None
    for attempt in range(4):
        try:
            response = session.get(url, params=params, timeout=90)
            if response.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"transient HTTP {response.status_code}")
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            if attempt == 3:
                break
            time.sleep(2 ** attempt)
    raise RuntimeError(f"CFTC request failed: {type(last_error).__name__}: {last_error}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase377_cftc_tff_full_coverage_audit")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "NuevaEstrategia-Phase377/1.0 research-only",
    })
    meta_before = request_json(session, META_URL)
    count_before_payload = request_json(
        session, RESOURCE_URL, {"$select": "count(*) as row_count"}
    )
    count_before = int(count_before_payload[0]["row_count"])
    if count_before <= 0 or count_before > MAX_ROWS:
        raise RuntimeError(
            f"unexpected TFF row count {count_before}; single-snapshot limit is {MAX_ROWS}"
        )

    rows = request_json(session, RESOURCE_URL, {
        "$limit": str(MAX_ROWS),
        "$order": f"{DATE_FIELD} ASC,{CODE_FIELD} ASC,id ASC",
    })
    if not isinstance(rows, list):
        raise RuntimeError("CFTC resource response was not a JSON row array")
    count_after_payload = request_json(
        session, RESOURCE_URL, {"$select": "count(*) as row_count"}
    )
    count_after = int(count_after_payload[0]["row_count"])
    meta_after = request_json(session, META_URL)

    columns = meta_before.get("columns") or []
    field_names = [
        str(column.get("fieldName"))
        for column in columns if column.get("fieldName")
    ]
    if not field_names:
        raise RuntimeError("CFTC metadata did not expose fieldName schema")
    before_stamp = meta_before.get("rowsUpdatedAt")
    after_stamp = meta_after.get("rowsUpdatedAt")
    summary = build_summary(
        rows, field_names, metadata=meta_before,
        count_before=count_before, count_after=count_after,
        metadata_updated_before=before_stamp,
        metadata_updated_after=after_stamp,
    )
    summary["metadata_column_count"] = len(columns)
    summary["metadata_name"] = meta_before.get("name")
    summary["metadata_rows_updated_at"] = before_stamp
    summary["expected_history_start_from_cftc_faq"] = "2006-06-13"
    summary["candidate_code_semantics"] = (
        "codes are tested as separate contract-market series; 13874+ consolidated "
        "must not be added to 13874A E-mini"
    )
    summary["api_query_count"] = 4

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    if not summary["row_count_reconciled"] or not summary["snapshot_stable_during_retrieval"]:
        raise SystemExit("CFTC TFF snapshot/count stability gate failed")
    if summary["required_schema_fields_missing"] or not summary["position_category_schema_complete"]:
        raise SystemExit("CFTC TFF schema gate failed")


if __name__ == "__main__":
    main()
