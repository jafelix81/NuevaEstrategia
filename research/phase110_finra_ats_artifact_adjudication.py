#!/usr/bin/env python3
"""Offline Phase 110 adjudication of a Phase 109 FINRA artifact."""
import argparse, csv, gzip, io, json, zipfile, hashlib
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

AGG = {"ATS_W_SMBL", "OTC_W_SMBL"}
FIRM = {"ATS_W_SMBL_FIRM", "OTC_W_SMBL_FIRM"}
BEARING = AGG | FIRM
KNOWN = BEARING | {"ATS_W_FIRM", "OTC_W_FIRM", "ATS_W_VOL_STATS", "OTC_W_VOL_STATS"}

def s(v):
    return "" if v is None else str(v).strip()

def d(v):
    return Decimal(s(v))

def family(st):
    return "ATS" if st.startswith("ATS_") else "OTC"

def knowledge_date(row):
    return max(
        date.fromisoformat(s(row["initialPublishedDate"])[:10]),
        date.fromisoformat(s(row["lastUpdateDate"])[:10]),
    )

def analyze_rows(rows):
    groups = {}
    counts, unknown, invalid, negative = Counter(), Counter(), Counter(), Counter()
    partition_counts, partition_mismatch = Counter(), []
    missing, na_rows, agg_total, firm_total = [], 0, 0, 0
    key_seen, key_collisions = set(), 0
    revisions, lags = defaultdict(list), defaultdict(list)

    for i, row in enumerate(rows):
        week = s(row.get("requested_week"))[:10]
        tier = s(row.get("requested_tier")).upper()
        partition_counts[(week, tier)] += 1
        if s(row.get("weekStartDate"))[:10] != week or s(row.get("tierIdentifier")).upper() != tier:
            partition_mismatch.append(i)

        st = s(row.get("summaryTypeCode")).upper()
        counts[st or "<blank>"] += 1
        if st not in KNOWN:
            unknown[st or "<blank>"] += 1

        for field in ("totalWeeklyShareQuantity", "totalWeeklyTradeCount"):
            try:
                value = d(row.get(field))
                if value < 0:
                    negative[field] += 1
            except Exception:
                invalid[field] += 1

        if st in AGG:
            agg_total += 1
            try:
                initial = date.fromisoformat(s(row["initialPublishedDate"])[:10])
                updated = knowledge_date(row)
                start = date.fromisoformat(s(row["weekStartDate"])[:10])
                revisions[tier].append((updated - initial).days)
                lags[tier].append((initial - start).days)
            except Exception:
                invalid["publication_dates"] += 1
        elif st in FIRM:
            firm_total += 1

        if st not in BEARING:
            continue
        symbol = s(row.get("issueSymbolIdentifier")).upper()
        if not symbol:
            if len(missing) < 25:
                missing.append({key: s(row.get(key)) for key in (
                    "requested_week", "requested_tier", "summaryTypeCode", "productTypeCode",
                    "marketParticipantName", "totalWeeklyShareQuantity", "totalWeeklyTradeCount"
                )})
            continue
        if symbol == "NA":
            na_rows += 1

        candidate_key = (
            symbol, s(row.get("weekStartDate"))[:10], tier, st,
            s(row.get("productTypeCode")).upper(), s(row.get("MPID")).upper(),
            s(row.get("firmCRDNumber")), s(row.get("lastReportedDate"))[:10],
        )
        if candidate_key in key_seen:
            key_collisions += 1
        key_seen.add(candidate_key)

        key = (week, tier, family(st), symbol)
        group = groups.setdefault(key, {
            "aggregate_qty": Decimal(0), "aggregate_trades": Decimal(0),
            "firm_qty": Decimal(0), "firm_trades": Decimal(0),
            "aggregate_rows": 0, "firm_rows": 0,
        })
        try:
            quantity = d(row.get("totalWeeklyShareQuantity"))
            trades = d(row.get("totalWeeklyTradeCount"))
        except Exception:
            continue
        if st in AGG:
            group["aggregate_qty"] += quantity
            group["aggregate_trades"] += trades
            group["aggregate_rows"] += 1
        else:
            group["firm_qty"] += quantity
            group["firm_trades"] += trades
            group["firm_rows"] += 1

    both = sum(g["aggregate_rows"] > 0 and g["firm_rows"] > 0 for g in groups.values())
    quantity_matches = sum(
        g["aggregate_rows"] > 0 and g["firm_rows"] > 0 and g["aggregate_qty"] == g["firm_qty"]
        for g in groups.values()
    )
    trade_matches = sum(
        g["aggregate_rows"] > 0 and g["firm_rows"] > 0 and g["aggregate_trades"] == g["firm_trades"]
        for g in groups.values()
    )
    mismatches = [
        key for key, g in groups.items()
        if not (g["aggregate_rows"] and g["firm_rows"]
                and g["aggregate_qty"] == g["firm_qty"]
                and g["aggregate_trades"] == g["firm_trades"])
    ]

    def quantile(values, probability):
        ordered = sorted(value for value in values if value > 0)
        return ordered[round((len(ordered) - 1) * probability)] if ordered else None

    revision_stats = {}
    for tier, values in revisions.items():
        positive = [value for value in values if value > 0]
        revision_stats[tier] = {
            "rows": len(values),
            "updated": len(positive),
            "updated_pct": 100 * len(positive) / len(values),
            "p50_days": quantile(values, 0.50),
            "p90_days": quantile(values, 0.90),
            "p95_days": quantile(values, 0.95),
            "max_days": max(positive) if positive else 0,
        }

    return {
        "rows_total": sum(partition_counts.values()),
        "partitions": {f"{week}|{tier}": count for (week, tier), count in sorted(partition_counts.items())},
        "partition_mismatch_rows": len(partition_mismatch),
        "summary_type_counts": dict(counts),
        "unknown_summary_types": dict(unknown),
        "numeric_invalid": dict(invalid),
        "negative_numeric": dict(negative),
        "aggregate_rows_total": agg_total,
        "firm_rows_total": firm_total,
        "symbol_groups": len(groups),
        "groups_with_both_levels": both,
        "quantity_matches": quantity_matches,
        "trade_matches": trade_matches,
        "total_mismatch_groups": mismatches,
        "missing_symbol_rows": len(missing),
        "missing_symbol_examples": missing,
        "valid_NA_ticker_rows": na_rows,
        "expanded_key_collision_groups": key_collisions,
        "publication_lag_days_by_tier": {tier: dict(Counter(values)) for tier, values in lags.items()},
        "revision_stats_by_tier": revision_stats,
        "updated_aggregate_rows": sum(sum(value > 0 for value in values) for values in revisions.values()),
        "aggregate_rows_in_revision_audit": sum(len(values) for values in revisions.values()),
        "max_revision_delay_days": max((max(values) for values in revisions.values()), default=0),
    }

def run(artifact_zip, output=None):
    with zipfile.ZipFile(artifact_zip) as archive:
        source = json.loads(archive.read("summary.json"))
        partitions = list(csv.DictReader(io.StringIO(archive.read("partition_summary.csv").decode())))
        pages = list(csv.DictReader(io.StringIO(archive.read("page_hashes.csv").decode())))
        symbols = list(csv.DictReader(io.StringIO(archive.read("symbol_reconciliation.csv").decode())))
        with archive.open("raw_rows.csv.gz") as compressed:
            with gzip.GzipFile(fileobj=compressed) as gz:
                with io.TextIOWrapper(gz, encoding="utf-8", newline="") as text_file:
                    result = analyze_rows(csv.DictReader(text_file))

    result.update({
        "phase": 110,
        "source_phase": 109,
        "artifact_sha256": hashlib.sha256(Path(artifact_zip).read_bytes()).hexdigest(),
        "source_raw_sha256": source.get("raw_rows_sha256"),
        "source_partitions_completed": source.get("partitions_completed"),
        "source_page_hashes": len(pages),
        "partition_summary_rows": len(partitions),
        "symbol_reconciliation_rows": len(symbols),
        "phase109_cohort_false": sum(row.get("all_cohorts_match") == "False" for row in symbols),
        "phase109_cohort_false_with_total_match": sum(
            row.get("all_cohorts_match") == "False"
            and row.get("total_quantity_match") == "True"
            and row.get("total_trades_match") == "True"
            for row in symbols
        ),
        "partition_total_mismatches": sum(row.get("record_total_match") != "True" for row in partitions),
        "page_hash_invalid": sum(len(s(row.get("sha256"))) != 64 for row in pages),
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "f80_changed": False,
    })
    if output:
        Path(output).write_text(json.dumps(result, indent=2))
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = run(args.artifact_zip, args.output)
    print(json.dumps(result, indent=2))
    assert result["rows_total"] == 968139
    assert result["source_partitions_completed"] == 10
    assert result["source_page_hashes"] == 199
    assert result["symbol_groups"] == 108425
    assert result["groups_with_both_levels"] == 108425
    assert result["quantity_matches"] == 108425
    assert result["trade_matches"] == 108425
    assert result["missing_symbol_rows"] == 2
    assert result["valid_NA_ticker_rows"] == 61
    assert result["expanded_key_collision_groups"] == 0
    assert result["phase109_cohort_false"] == 16
    assert result["phase109_cohort_false_with_total_match"] == 16
    assert result["partition_mismatch_rows"] == 0
    assert result["partition_total_mismatches"] == 0
    assert result["page_hash_invalid"] == 0
    assert not result["unknown_summary_types"]
    assert not result["numeric_invalid"]
    assert not result["negative_numeric"]
    assert not result["total_mismatch_groups"]

if __name__ == "__main__":
    main()
