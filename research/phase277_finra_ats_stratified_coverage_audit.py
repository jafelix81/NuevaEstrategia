#!/usr/bin/env python3
"""Phase 277: stratified multi-year FINRA ATS/off-exchange coverage audit.

Fetches eight previously unsampled historical weeks (T1/T2), fully pages each
partition, hashes every response page, and emits metadata-only diagnostics.
It deliberately does not save raw symbol rows, infer a natural key, reconstruct
first-published value vintages, calculate returns, or admit alpha.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median
from typing import Any

import requests

from research.phase100_finra_ats_revalidation import (
    BASE,
    FIELDS,
    KNOWN_SUMMARY_TYPES,
    SYMBOL_AGGREGATES,
    SYMBOL_BEARING_TYPES,
    fetch_partition,
    validate_partition_rows,
)

ROOT = Path(__file__).resolve().parents[1]
PRIOR_RESULT = ROOT / "research" / "phase264_finra_ats_final_artifact_adjudication_result.json"
OUT = Path("phase277_finra_ats_stratified_coverage_audit")
AUDIT_DATE = date(2026, 11, 10)
WEEKS = (
    "2022-04-04", "2022-10-03",
    "2023-04-03", "2023-10-02",
    "2024-04-01", "2024-10-07",
    "2025-04-07", "2025-07-07",
)
TIERS = ("T1", "T2")
EXPECTED_PRIOR_ARTIFACT_SHA256 = "803c58a5301df8b505b487c5367a449696c6bc467cab39121c50eda762d1f3e9"
HEX = set("0123456789abcdef")


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _day(value: Any) -> date | None:
    raw = _clean(value)
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _nonnegative_decimal(value: Any) -> Decimal | None:
    raw = _clean(value).replace(",", "")
    if not raw:
        return None
    try:
        number = Decimal(raw)
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number < 0:
        return None
    return number


def _base_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        _clean(row.get("issueSymbolIdentifier")).upper(),
        _clean(row.get("weekStartDate"))[:10],
        _clean(row.get("tierIdentifier")).upper(),
        _clean(row.get("summaryTypeCode")).upper(),
        _clean(row.get("productTypeCode")).upper(),
    )


def _payload(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(_clean(row.get(field)) for field in FIELDS)


def _validate_pages(rows: list[dict], week: str, tier: str, pages: list[dict]) -> int:
    if not pages:
        raise ValueError("NO_PAGE_METADATA")
    expected_offset = 0
    expected_total = int(pages[0]["record_total"])
    for page_number, page in enumerate(pages):
        if int(page.get("page", -1)) != page_number:
            raise ValueError("NONCONTIGUOUS_PAGE_NUMBER")
        if int(page.get("offset", -1)) != expected_offset:
            raise ValueError("NONCONTIGUOUS_PAGE_OFFSET")
        if int(page.get("record_total", -1)) != expected_total:
            raise ValueError("RECORD_TOTAL_CHANGED")
        count = int(page.get("rows", -1))
        if count < 0:
            raise ValueError("NEGATIVE_PAGE_ROW_COUNT")
        digest = _clean(page.get("sha256")).lower()
        if len(digest) != 64 or not set(digest).issubset(HEX):
            raise ValueError("INVALID_PAGE_SHA256")
        if _clean(page.get("week")) != week or _clean(page.get("tier")).upper() != tier:
            raise ValueError("PAGE_PARTITION_MISMATCH")
        expected_offset += count
    if expected_offset != len(rows) or len(rows) != expected_total:
        raise ValueError("RECORD_TOTAL_NOT_RECONCILED")
    return expected_total


def analyze_partition(
    rows: list[dict[str, Any]], week: str, tier: str, pages: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, set[str]]]:
    """Return metadata-only diagnostics plus in-memory symbol-token sets."""
    record_total = _validate_pages(rows, week, tier, pages)
    partition_problems = validate_partition_rows(rows, week, tier)
    type_counts = Counter()
    missing_symbol = Counter()
    unknown_types = Counter()
    invalid_quantity_fields = 0
    aggregate_rows = 0
    publication_lags: list[int] = []
    revision_rows = 0
    reported_after_publish = 0
    missing_publication = 0
    missing_update = 0
    symbols: dict[str, set[str]] = {name: set() for name in SYMBOL_AGGREGATES}
    base_groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        st = _clean(row.get("summaryTypeCode")).upper() or "<MISSING>"
        type_counts[st] += 1
        if st not in KNOWN_SUMMARY_TYPES:
            unknown_types[st] += 1
        symbol = _clean(row.get("issueSymbolIdentifier")).upper()
        if st in SYMBOL_BEARING_TYPES and not symbol:
            missing_symbol[st] += 1
        if st not in SYMBOL_AGGREGATES:
            continue

        aggregate_rows += 1
        if symbol:
            symbols[st].add(symbol)
        base_groups[_base_key(row)].append(row)

        for field in ("totalWeeklyShareQuantity", "totalWeeklyTradeCount"):
            if _nonnegative_decimal(row.get(field)) is None:
                invalid_quantity_fields += 1

        pub = _day(row.get("initialPublishedDate"))
        updated = _day(row.get("lastUpdateDate"))
        reported = _day(row.get("lastReportedDate"))
        week_day = _day(week)
        if pub is None:
            missing_publication += 1
        elif week_day is not None:
            publication_lags.append((pub - week_day).days)
        if updated is None:
            missing_update += 1
        elif pub is not None and updated > pub:
            revision_rows += 1
        if reported is not None and pub is not None and reported > pub:
            reported_after_publish += 1

    duplicate_groups = [group for group in base_groups.values() if len(group) > 1]
    conflicting_groups = [
        group for group in duplicate_groups if len({_payload(row) for row in group}) > 1
    ]
    exact_duplicate_groups = len(duplicate_groups) - len(conflicting_groups)
    split_by_last_reported = sum(
        1 for group in duplicate_groups
        if len({_clean(row.get("lastReportedDate"))[:10] for row in group}) > 1
    )
    extended_groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if _clean(row.get("summaryTypeCode")).upper() in SYMBOL_AGGREGATES:
            extended_groups[_base_key(row) + (_clean(row.get("lastReportedDate"))[:10],)].append(row)
    extended_duplicate_groups = sum(1 for group in extended_groups.values() if len(group) > 1)

    minimum_delay = 14 if tier == "T1" else 28
    early_publications = sum(1 for lag in publication_lags if lag < minimum_delay)
    ats = symbols.get("ATS_W_SMBL", set())
    otc = symbols.get("OTC_W_SMBL", set())
    union = ats | otc
    intersection = ats & otc
    jaccard = len(intersection) / len(union) if union else None

    summary = {
        "week": week,
        "tier": tier,
        "rows_total": len(rows),
        "api_record_total": record_total,
        "api_record_total_reconciled": record_total == len(rows),
        "page_count": len(pages),
        "unique_request_ids": len({
            _clean(page.get("request_id")) for page in pages if _clean(page.get("request_id"))
        }),
        "symbol_aggregate_rows": aggregate_rows,
        "ats_unique_symbol_tokens": len(ats),
        "otc_unique_symbol_tokens": len(otc),
        "union_unique_symbol_tokens": len(union),
        "ats_otc_intersection_tokens": len(intersection),
        "ats_otc_jaccard": round(jaccard, 6) if jaccard is not None else None,
        "summary_type_counts": dict(sorted(type_counts.items())),
        "unknown_summary_type_rows": sum(unknown_types.values()),
        "missing_symbol_bearing_rows": sum(missing_symbol.values()),
        "missing_symbol_by_type": dict(sorted(missing_symbol.items())),
        "invalid_or_negative_quantity_fields": invalid_quantity_fields,
        "initial_published_date_nonnull_pct": round(
            100 * (aggregate_rows - missing_publication) / aggregate_rows, 4
        ) if aggregate_rows else 0.0,
        "last_update_date_missing_rows": missing_update,
        "post_initial_publication_update_rows": revision_rows,
        "post_initial_publication_update_pct": round(
            100 * revision_rows / aggregate_rows, 4
        ) if aggregate_rows else 0.0,
        "last_reported_after_initial_publish_rows": reported_after_publish,
        "publication_lag_days_min": min(publication_lags) if publication_lags else None,
        "publication_lag_days_median": median(publication_lags) if publication_lags else None,
        "publication_lag_days_max": max(publication_lags) if publication_lags else None,
        "publication_before_tier_minimum_delay_rows": early_publications,
        "base_duplicate_key_groups": len(duplicate_groups),
        "conflicting_base_duplicate_groups": len(conflicting_groups),
        "exact_base_duplicate_groups": exact_duplicate_groups,
        "duplicate_groups_split_by_last_reported_date": split_by_last_reported,
        "extended_key_duplicate_groups_after_last_reported": extended_duplicate_groups,
        "partition_validation_problem_count": len(partition_problems),
        "partition_validation_examples": partition_problems[:5],
        "page_sha256": [page["sha256"] for page in pages],
    }
    return summary, symbols


def _prior_context(path: Path) -> dict[str, Any]:
    prior = json.loads(path.read_text(encoding="utf-8"))
    if prior.get("phase") != 264:
        raise ValueError("UNEXPECTED_PHASE264_RESULT")
    upstream = prior.get("upstream", {})
    if upstream.get("artifact_zip_sha256") != EXPECTED_PRIOR_ARTIFACT_SHA256:
        raise ValueError("PHASE264_ARTIFACT_HASH_MISMATCH")
    sample = prior.get("sample", {})
    if sample.get("partitions_completed") != 10 or sample.get("partitions_expected") != 10:
        raise ValueError("PHASE264_SAMPLE_NOT_COMPLETE")
    return prior


def build_result(
    partitions: list[dict[str, Any]], prior: dict[str, Any]
) -> dict[str, Any]:
    expected = len(WEEKS) * len(TIERS)
    if len(partitions) != expected:
        raise ValueError(f"EXPECTED_{expected}_PARTITIONS_GOT_{len(partitions)}")
    if len({(p["week"], p["tier"]) for p in partitions}) != expected:
        raise ValueError("DUPLICATE_OR_MISSING_PARTITION")
    partitions = sorted(partitions, key=lambda p: (p["week"], p["tier"]))
    old = prior["sample"]
    old_integrity = prior["row_integrity"]
    old_dupes = prior["duplicate_audit"]

    new_rows = sum(int(p["rows_total"]) for p in partitions)
    new_agg = sum(int(p["symbol_aggregate_rows"]) for p in partitions)
    new_revisions = sum(int(p["post_initial_publication_update_rows"]) for p in partitions)
    new_missing = sum(int(p["missing_symbol_bearing_rows"]) for p in partitions)
    new_conflicts = sum(int(p["conflicting_base_duplicate_groups"]) for p in partitions)
    new_invalid = sum(int(p["invalid_or_negative_quantity_fields"]) for p in partitions)
    new_unknown = sum(int(p["unknown_summary_type_rows"]) for p in partitions)
    old_agg = int(old["symbol_aggregate_rows"])
    old_revisions = int(old["post_initial_publication_update_rows"])
    combined_agg = old_agg + new_agg
    combined_revisions = old_revisions + new_revisions

    per_week = []
    for week in WEEKS:
        pair = {p["tier"]: p for p in partitions if p["week"] == week}
        if set(pair) != set(TIERS):
            raise ValueError(f"MISSING_TIER_FOR_WEEK:{week}")
        per_week.append({
            "week": week,
            "t1_union_symbol_tokens": pair["T1"]["union_unique_symbol_tokens"],
            "t2_union_symbol_tokens": pair["T2"]["union_unique_symbol_tokens"],
            "t1_rows": pair["T1"]["rows_total"],
            "t2_rows": pair["T2"]["rows_total"],
        })

    all_pages = [
        {
            "week": p["week"], "tier": p["tier"], "page": i,
            "sha256": digest,
        }
        for p in partitions for i, digest in enumerate(p["page_sha256"])
    ]
    gates = {
        "all_16_partitions_present": len(partitions) == expected,
        "all_api_record_totals_reconciled": all(p["api_record_total_reconciled"] for p in partitions),
        "all_page_hashes_valid": all(
            len(h["sha256"]) == 64 and set(h["sha256"]).issubset(HEX) for h in all_pages
        ),
        "no_unknown_summary_types": new_unknown == 0,
        "no_missing_symbol_bearing_rows": new_missing == 0,
        "no_invalid_or_negative_quantity_fields": new_invalid == 0,
        "no_conflicting_base_duplicate_groups": new_conflicts == 0,
        "at_least_99pct_initial_publication_dates": all(
            p["initial_published_date_nonnull_pct"] >= 99.0 for p in partitions
        ),
    }
    return {
        "phase": 277,
        "audit_date": AUDIT_DATE.isoformat(),
        "status": "STRATIFIED_SAMPLE_COMPLETE_DIAGNOSTIC_ONLY" if all(gates.values()) else "STRATIFIED_SAMPLE_COMPLETE_WITH_EXCEPTIONS",
        "source": {
            "dataset": "FINRA OTCMarket weeklySummaryHistoric",
            "endpoint": BASE,
            "request_mode": "synchronous paginated; no FINRA_API_TOKEN supplied",
            "fields": FIELDS,
            "historical_window_rule": "Selected weeks are between one and five years before the audit date; the historic endpoint is intended for older-than-one-year historical data.",
            "weeks_new": list(WEEKS),
            "tiers": list(TIERS),
            "partitions_expected": expected,
            "prior_phase264_weeks": old["weeks"],
            "combined_sample_weeks": sorted(set(old["weeks"]) | set(WEEKS)),
            "combined_sample_week_count": len(set(old["weeks"]) | set(WEEKS)),
            "selection_note": "Eight new quarterly-spaced weeks; all are distinct from Phase 264's five weeks. This is a stratified sample, not a continuous panel or random sample.",
        },
        "new_sample": {
            "partitions_completed": len(partitions),
            "rows_total": new_rows,
            "symbol_aggregate_rows": new_agg,
            "post_initial_publication_update_rows": new_revisions,
            "post_initial_publication_update_pct": round(100 * new_revisions / new_agg, 4) if new_agg else None,
            "missing_symbol_bearing_rows": new_missing,
            "conflicting_base_duplicate_groups": new_conflicts,
            "invalid_or_negative_quantity_fields": new_invalid,
            "unknown_summary_type_rows": new_unknown,
            "partitions": partitions,
            "per_week": per_week,
            "page_hashes": all_pages,
        },
        "combined_phase264_phase277": {
            "partitions": int(old["partitions_completed"]) + len(partitions),
            "sampled_weeks": len(set(old["weeks"]) | set(WEEKS)),
            "rows_total": int(old["rows_total"]) + new_rows,
            "symbol_aggregate_rows": combined_agg,
            "post_initial_publication_update_rows": combined_revisions,
            "post_initial_publication_update_pct": round(
                100 * combined_revisions / combined_agg, 4
            ) if combined_agg else None,
            "missing_symbol_bearing_rows": int(old_integrity["missing_symbol_errors"]) + new_missing,
            "conflicting_base_duplicate_groups": int(old_dupes["conflicting_groups"]) + new_conflicts,
            "note": "Combined counts pool two separate retrieval waves; duplicate counts are groups, not rows. This does not resolve the natural grain or original publication vintages.",
        },
        "gates": gates,
        "pit": {
            "strict_pit_admitted": False,
            "current_snapshot_revision_history_reconstructed": False,
            "reason": "initialPublishedDate/lastUpdateDate are fields in the current historical snapshot; no immutable as-first-published values or first-receipt archive is available.",
            "safe_research_boundary": "Do not use a current revised value before max(initialPublishedDate,lastUpdateDate), and then execute no earlier than the next XNYS session; this is only a conservative current-snapshot rule, not vintage reconstruction.",
        },
        "identity_and_coverage": {
            "broad_universe_coverage_established": False,
            "symbol_tokens_are_permanent_security_ids": False,
            "delisted_or_reused_symbol_continuity_verified": False,
            "t1_t2_and_ats_otc_counts_are_activity_coverage_diagnostics_only": True,
        },
        "economic_interpretation": {
            "source_role": "off-exchange activity/context",
            "aggressor_direction_known": False,
            "beneficial_owner_known": False,
            "informed_trader_identity_known": False,
            "alpha_test_authorized": False,
            "forward_returns_used": False,
            "bootstrap_loo_oos_used": False,
            "holdout_used": False,
        },
        "decision": "Use the broader sample only to characterize temporal stability and row/revision integrity. Retain FINRA ATS/OTC as context-only. Do not construct a stock-selection feature or run returns until natural grain, missing-symbol exceptions, historical value vintages and point-in-time security identity are resolved.",
        "controls": {
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "vendor_contacted": False,
            "data_purchased": False,
        },
    }


def run() -> dict[str, Any]:
    if not PRIOR_RESULT.exists():
        raise FileNotFoundError(f"Missing prior adjudication: {PRIOR_RESULT}")
    prior = _prior_context(PRIOR_RESULT)
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "SmartMoneyResearch-Phase277/1.0",
    })
    partitions: list[dict[str, Any]] = []
    page_manifest: list[dict[str, Any]] = []
    for week in WEEKS:
        for tier in TIERS:
            print(f"[Phase 277] fetch week={week} tier={tier}", flush=True)
            rows, pages = fetch_partition(session, week, tier, use_async=False)
            summary, _symbols = analyze_partition(rows, week, tier, pages)
            partitions.append(summary)
            for page in pages:
                page_manifest.append({
                    "week": week, "tier": tier, "page": page["page"],
                    "offset": page["offset"], "rows": page["rows"],
                    "record_total": page["record_total"],
                    "request_id": page.get("request_id"),
                    "sha256": page["sha256"],
                    "request_attempts": page.get("request_attempts"),
                })
            print(
                f"[Phase 277] complete week={week} tier={tier} "
                f"rows={len(rows)} record_total={summary['api_record_total']} "
                f"pages={len(pages)} revisions={summary['post_initial_publication_update_rows']} "
                f"conflicts={summary['conflicting_base_duplicate_groups']}",
                flush=True,
            )
    result = build_result(partitions, prior)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    with (OUT / "partition_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "week", "tier", "rows_total", "api_record_total", "page_count",
            "symbol_aggregate_rows", "ats_unique_symbol_tokens", "otc_unique_symbol_tokens",
            "union_unique_symbol_tokens", "missing_symbol_bearing_rows",
            "post_initial_publication_update_rows", "post_initial_publication_update_pct",
            "invalid_or_negative_quantity_fields", "base_duplicate_key_groups",
            "conflicting_base_duplicate_groups", "duplicate_groups_split_by_last_reported_date",
            "extended_key_duplicate_groups_after_last_reported",
            "initial_published_date_nonnull_pct", "publication_lag_days_median",
            "partition_validation_problem_count",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in result["new_sample"]["partitions"]:
            writer.writerow({field: row.get(field) for field in fields})
    with (OUT / "page_hashes.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["week", "tier", "page", "offset", "rows", "record_total", "request_id", "sha256", "request_attempts"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(page_manifest)
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return result


if __name__ == "__main__":
    run()
