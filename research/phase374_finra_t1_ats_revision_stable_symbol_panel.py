#!/usr/bin/env python3
"""Phase 374: revision-stable FINRA T1 ATS symbol-week panel audit.

Reuses Phase 371's full-partition retrieval and metadata parsing, but separates
publication-schedule variation from post-publication revisions. A 21- or
22-calendar-day initial publication lag is treated as a schedule-consistent
date (the latter can reflect a market holiday); the actual initialPublishedDate
remains the only candidate knowledge date. A symbol-week is eligible only when
every ATS_W_SMBL and ATS_W_SMBL_FIRM row has valid dates, lastUpdateDate equals
initialPublishedDate, and all rows share one initialPublishedDate.

For eligible symbol-weeks, aggregate CTS/UTP symbol rows may be combined only
when productTypeCode values are distinct/nonmissing and the combined shares and
trades exactly reconcile to firm rows. Concentration is calculated only when
participant identities are unique and complete and no De Minimis bucket exists.

This is data-feasibility only: no direction, beneficial-owner inference,
returns, alpha, OOS, bootstrap, LOO, or holdout test.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import research.phase371_finra_t1_ats_monthly_coverage_audit as P371

START_MONTH = (2022, 1)
END_MONTH = (2025, 11)
ALLOWED_PUBLICATION_LAGS = {21, 22}
SYMBOL_TYPES = {"ATS_W_SMBL", "ATS_W_SMBL_FIRM"}


def analyze_revision_stable_symbols(rows, week, record_total, pages):
    aggregate = defaultdict(list)
    firms = defaultdict(list)
    publication_lags = Counter()
    update_gaps = Counter()
    missing_invalid_date_rows = 0
    all_symbol_rows = []

    for row in rows:
        typ = P371.norm(row.get("summaryTypeCode"))
        if typ not in SYMBOL_TYPES:
            continue
        symbol = P371.norm(row.get("issueSymbolIdentifier"))
        if not symbol:
            continue
        all_symbol_rows.append(row)
        if typ == "ATS_W_SMBL":
            aggregate[symbol].append(row)
        else:
            firms[symbol].append(row)

        week_date = P371.parse_date(row.get("weekStartDate") or row.get("historicalWeek"))
        pub_date = P371.parse_date(row.get("initialPublishedDate"))
        update_date = P371.parse_date(row.get("lastUpdateDate"))
        if week_date is None or pub_date is None or update_date is None:
            missing_invalid_date_rows += 1
            continue
        publication_lags[str((pub_date - week_date).days)] += 1
        update_gaps[str((update_date - pub_date).days)] += 1

    symbols = set(aggregate) | set(firms)
    stable_symbols = 0
    stable_mapped_symbols = 0
    stable_concentration_symbols = 0
    bridge_mapped_symbols = 0
    bridge_missing_symbols = 0
    bridge_ambiguous_symbols = 0
    bridge_invalid_numeric_symbols = 0
    bridge_mismatched_symbols = 0
    missing_identity_rows = 0
    duplicate_participant_keys = 0
    de_minimis_rows = 0
    total_aggregate_shares = 0
    mapped_aggregate_shares = 0
    stable_mapped_shares = 0
    stable_concentration_shares = 0
    all_participant_keys = set()
    stable_hhi_rows = []
    revised_symbols = 0
    publication_schedule_review_symbols = 0
    symbol_revision_gap_counts = Counter()

    for symbol in symbols:
        ar = aggregate.get(symbol, [])
        fr = firms.get(symbol, [])
        symbol_rows = ar + fr
        pub_dates = set()
        row_dates_valid = True
        row_revision_stable = True
        row_schedule_ok = True
        positive_gap = False

        for row in symbol_rows:
            week_date = P371.parse_date(row.get("weekStartDate") or row.get("historicalWeek"))
            pub_date = P371.parse_date(row.get("initialPublishedDate"))
            update_date = P371.parse_date(row.get("lastUpdateDate"))
            if week_date is None or pub_date is None or update_date is None:
                row_dates_valid = False
                row_revision_stable = False
                row_schedule_ok = False
                continue
            pub_dates.add(pub_date)
            lag = (pub_date - week_date).days
            gap = (update_date - pub_date).days
            if lag not in ALLOWED_PUBLICATION_LAGS:
                row_schedule_ok = False
            if gap != 0:
                row_revision_stable = False
                if gap > 0:
                    positive_gap = True
            symbol_revision_gap_counts[str(gap)] += 1

        same_publication_date = len(pub_dates) == 1
        stable_date_group = (
            bool(symbol_rows)
            and row_dates_valid
            and row_revision_stable
            and row_schedule_ok
            and same_publication_date
        )
        if stable_date_group:
            stable_symbols += 1
        if positive_gap:
            revised_symbols += 1
        if not row_schedule_ok:
            publication_schedule_review_symbols += 1

        if not ar or not fr:
            bridge_missing_symbols += 1
            continue

        product_types = [P371.norm(x.get("productTypeCode")) for x in ar]
        if any(not p for p in product_types) or len(set(product_types)) != len(product_types):
            bridge_ambiguous_symbols += 1
            continue

        a_shares = P371.sum_field(ar, "totalWeeklyShareQuantity")
        a_trades = P371.sum_field(ar, "totalWeeklyTradeCount")
        f_shares = P371.sum_field(fr, "totalWeeklyShareQuantity")
        f_trades = P371.sum_field(fr, "totalWeeklyTradeCount")
        if None in (a_shares, a_trades, f_shares, f_trades):
            bridge_invalid_numeric_symbols += 1
            continue

        total_aggregate_shares += a_shares
        if a_shares != f_shares or a_trades != f_trades:
            bridge_mismatched_symbols += 1
            continue

        bridge_mapped_symbols += 1
        mapped_aggregate_shares += a_shares
        if not stable_date_group:
            continue

        stable_mapped_symbols += 1
        stable_mapped_shares += a_shares

        shares_by_participant = defaultdict(int)
        participant_keys = []
        valid_identity = True
        has_de_minimis = False
        for row in fr:
            name = P371.norm(row.get("marketParticipantName"))
            if "DE MINIMIS" in name:
                de_minimis_rows += 1
                has_de_minimis = True
                valid_identity = False
                continue
            key = P371.participant_key(row)
            if not key:
                missing_identity_rows += 1
                valid_identity = False
                continue
            shares = P371.parse_int(row.get("totalWeeklyShareQuantity"))
            if shares is None:
                valid_identity = False
                continue
            participant_keys.append(key)
            shares_by_participant[key] += shares
            all_participant_keys.add(key)

        counts = Counter(participant_keys)
        duplicate_participant_keys += sum(1 for n in counts.values() if n > 1)
        if (
            valid_identity
            and not has_de_minimis
            and len(participant_keys) == len(set(participant_keys))
            and sum(shares_by_participant.values()) == a_shares
            and a_shares > 0
        ):
            weights = sorted((v / a_shares for v in shares_by_participant.values()), reverse=True)
            stable_hhi_rows.append({
                "hhi": sum(w * w for w in weights),
                "top1_share": weights[0] if weights else 0.0,
                "top3_share": sum(weights[:3]),
                "participant_count": len(weights),
            })
            stable_concentration_symbols += 1
            stable_concentration_shares += a_shares

    stable_concentration_stats = P371.concentration_stats(stable_hhi_rows)
    symbol_bridge_gate = (
        bool(bridge_mapped_symbols)
        and bridge_missing_symbols == 0
        and bridge_ambiguous_symbols == 0
        and bridge_invalid_numeric_symbols == 0
        and bridge_mismatched_symbols == 0
    )
    stable_concentration_gate = (
        stable_concentration_symbols == stable_mapped_symbols
        and stable_concentration_symbols > 0
    )

    return {
        "week": week,
        "rows": len(rows),
        "record_total": record_total,
        "pages": pages,
        "retrieval_count_match": len(rows) == record_total,
        "ats_symbol_rows": len(all_symbol_rows),
        "aggregate_symbols": len(aggregate),
        "firm_symbols": len(firms),
        "union_symbols": len(symbols),
        "revision_stable_symbols": stable_symbols,
        "revised_symbols": revised_symbols,
        "publication_schedule_review_symbols": publication_schedule_review_symbols,
        "missing_invalid_date_rows": missing_invalid_date_rows,
        "publication_lag_days_counts": dict(sorted(publication_lags.items())),
        "update_gap_days_counts": dict(sorted(update_gaps.items())),
        "symbol_revision_gap_days_counts": dict(sorted(symbol_revision_gap_counts.items())),
        "bridge_mapped_symbols": bridge_mapped_symbols,
        "bridge_missing_symbols": bridge_missing_symbols,
        "bridge_ambiguous_symbols": bridge_ambiguous_symbols,
        "bridge_invalid_numeric_symbols": bridge_invalid_numeric_symbols,
        "bridge_mismatched_symbols": bridge_mismatched_symbols,
        "symbol_bridge_gate": "PASS" if symbol_bridge_gate else "FAIL_OR_REVIEW",
        "revision_stable_mapped_symbols": stable_mapped_symbols,
        "revision_stable_concentration_symbols": stable_concentration_symbols,
        "revision_stable_share_volume_coverage_pct": round(
            100 * stable_concentration_shares / mapped_aggregate_shares, 6
        ) if mapped_aggregate_shares else None,
        "revision_stable_symbol_coverage_pct": round(
            100 * stable_concentration_symbols / bridge_mapped_symbols, 6
        ) if bridge_mapped_symbols else None,
        "total_aggregate_shares_mapped": mapped_aggregate_shares,
        "revision_stable_concentration_shares": stable_concentration_shares,
        "stable_missing_identity_rows": missing_identity_rows,
        "stable_duplicate_participant_keys": duplicate_participant_keys,
        "stable_de_minimis_rows": de_minimis_rows,
        "stable_unique_participant_keys": len(all_participant_keys),
        "stable_broker_dealer_reporting_concentration": stable_concentration_stats,
        "stable_concentration_gate": "PASS" if stable_concentration_gate else "FAIL_OR_REVIEW",
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase374_finra_t1_ats_revision_stable_symbol_panel")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    session = __import__("requests").Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Data-API-Version": "1",
        "User-Agent": "SmartMoneyResearch-Phase374/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    metadata, _ = P371.request_json(session, P371.META_URL)
    partition_payload, _ = P371.request_json(session, P371.PARTITIONS_URL)
    fields, records, unique = P371.parse_partition_payload(partition_payload)
    selected, missing_months = P371.select_monthly_weeks(
        unique, start=START_MONTH, end=END_MONTH
    )
    if missing_months:
        raise RuntimeError(f"Missing monthly T1 partitions: {missing_months}")

    partitions = []
    errors = []
    for week in selected:
        try:
            rows, total, pages = P371.fetch_partition(session, week)
            partitions.append(analyze_revision_stable_symbols(rows, week, total, pages))
        except Exception as exc:
            errors.append({"week": week, "error_type": type(exc).__name__})

    summary = {
        "phase": 374,
        "source": "FINRA OTCMarket weeklySummaryHistoric",
        "audit_timestamp_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "partition_fields": list(fields),
        "raw_partition_records": len(records),
        "unique_partition_pairs": len(unique),
        "expected_months": len(selected),
        "selected_weeks": selected,
        "missing_months": missing_months,
        "expected_partitions": len(selected),
        "completed_partitions": len(partitions),
        "total_rows": sum(x["rows"] for x in partitions),
        "total_pages": sum(x["pages"] for x in partitions),
        "errors": errors,
        "all_partitions_complete": len(partitions) == len(selected) and not errors
            and all(x["retrieval_count_match"] for x in partitions),
        "all_symbol_bridges_pass": bool(partitions)
            and all(x["symbol_bridge_gate"] == "PASS" for x in partitions),
        "all_stable_concentration_gates_pass": bool(partitions)
            and all(x["stable_concentration_gate"] == "PASS" for x in partitions),
        "revision_stable_symbol_groups": sum(x["revision_stable_symbols"] for x in partitions),
        "revised_symbol_groups": sum(x["revised_symbols"] for x in partitions),
        "revision_stable_concentration_symbols": sum(
            x["revision_stable_concentration_symbols"] for x in partitions
        ),
        "unique_participant_keys_union_count": len({
            (x["stable_unique_participant_keys"], x["week"]) for x in partitions
        }),
        "pit_availability_established": False,
        "historical_signal_test_authorized": False,
        "forward_returns_used": False,
        "holdout_used": False,
        "f80_changed": False,
        "production_changed": False,
        "raw_rows_retained": False,
        "raw_identifiers_retained": False,
        "metadata_retrieved": bool(metadata),
        "publication_lag_policy": "accept 21/22 calendar days as schedule-consistent; use each row's actual initialPublishedDate; no intraday timestamp inferred",
        "revision_policy": "exclude the entire symbol-week from concentration if any ATS_W_SMBL or ATS_W_SMBL_FIRM row has missing/invalid dates or lastUpdateDate != initialPublishedDate",
        "research_disposition": "REVISION_STABLE_SYMBOL_PANEL_DIAGNOSTIC_ONLY",
        "partitions": partitions,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "partitions"}, indent=2), flush=True)
    for item in partitions:
        print(
            f"PARTITION={item['week']}|SYMBOLS={item['union_symbols']}|"
            f"STABLE={item['revision_stable_concentration_symbols']}|"
            f"REVISION={item['revised_symbols']}|"
            f"SHARE_COVERAGE={item['revision_stable_share_volume_coverage_pct']}",
            flush=True,
        )


if __name__ == "__main__":
    main()
