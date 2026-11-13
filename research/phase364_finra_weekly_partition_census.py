#!/usr/bin/env python3
"""Phase 364: census FINRA weekly-summary history and tier coverage.

Uses only FINRA metadata and partitions endpoints. It does not download trade
rows, construct signals, or use returns. Both the historical and current
weekly datasets are queried so the actual overlap, date range and tier set
(including any OTCE tier) are measured rather than assumed.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter, defaultdict
from datetime import date, timedelta, datetime, timezone
from pathlib import Path

import requests

BASE_URL = "https://api.finra.org"
GROUP = "otcmarket"
DATASETS = ("weeklySummaryHistoric", "weeklySummary")
EXPECTED_SAMPLE_WEEKS = ("2022-01-03", "2023-01-09", "2024-01-08", "2025-01-06", "2025-10-20")
DEFAULT_PARTITION_FIELDS = ("weekStartDate", "tierIdentifier")


def request_json(session, url):
    last_error = None
    for attempt in range(4):
        try:
            response = session.get(url, timeout=(20, 90))
            if response.status_code in {408, 429, 500, 502, 503, 504}:
                if attempt == 3:
                    response.raise_for_status()
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = float(retry_after) if retry_after else 3 * (2 ** attempt)
                except (TypeError, ValueError):
                    delay = 3 * (2 ** attempt)
                time.sleep(max(0, min(delay, 60)))
                continue
            response.raise_for_status()
            return response.json(), response.headers
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt == 3:
                raise
            time.sleep(min(3 * (2 ** attempt), 30))
    raise RuntimeError(f"Unable to retrieve JSON: {last_error}")


def _normalise_partition_object(value, fields):
    if isinstance(value, dict):
        return {str(k): v for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        if value and isinstance(value[0], (list, tuple, dict)):
            return None
        if len(value) == len(fields):
            return dict(zip(fields, value))
        if len(fields) == 1 and len(value) == 1:
            return {fields[0]: value[0]}
    if isinstance(value, str) and len(fields) == 1:
        return {fields[0]: value}
    return None


def parse_partition_payload(payload, fallback_fields=DEFAULT_PARTITION_FIELDS):
    declared_fields = tuple(payload.get("partitionFields") or ())
    fallback_fields = tuple(fallback_fields)
    if declared_fields and fallback_fields and declared_fields != fallback_fields:
        raise ValueError(
            f"Partitions/metadata field-order mismatch: {declared_fields} vs {fallback_fields}"
        )
    fields = declared_fields or fallback_fields
    available = payload.get("availablePartitions") or payload.get("partitions") or []
    records = []
    for item in available:
        versions = None
        if isinstance(item, dict):
            raw = item.get("partitions")
            versions = item.get("versions", item.get("version"))
            if isinstance(raw, list) and raw and isinstance(raw[0], (list, tuple, dict)):
                candidates = raw
            else:
                candidates = [raw] if raw is not None else [item]
        else:
            candidates = [item]

        for candidate in candidates:
            record = _normalise_partition_object(candidate, fields)
            if record is None:
                continue
            # Some responses carry partition fields alongside the nested value.
            if isinstance(item, dict):
                for field in fields:
                    if field in item and field not in record:
                        record[field] = item[field]
            week = record.get("weekStartDate") or record.get("historicalWeek")
            tier = record.get("tierIdentifier")
            if week is None or tier is None:
                continue
            if isinstance(versions, list):
                version_value = versions[0] if versions else None
                version_count = len(versions)
            else:
                version_value = versions
                version_count = int(versions is not None)
            records.append({
                "weekStartDate": str(week),
                "tierIdentifier": str(tier),
                "version_sample": version_value,
                "version_count": version_count,
            })

    # Stable de-duplication; retain the first version sample but count all raw records separately.
    seen = set()
    unique = []
    for record in records:
        key = (record["weekStartDate"], record["tierIdentifier"])
        if key not in seen:
            seen.add(key)
            unique.append(record)
    return fields, records, unique


def calendar_week(date_string):
    d = date.fromisoformat(date_string)
    return (d - timedelta(days=d.weekday())).isoformat()


def summarize_dataset(name, metadata, raw_partitions):
    metadata_partition_fields = tuple(metadata.get("partitionFields") or DEFAULT_PARTITION_FIELDS)
    fields, raw_records, records = parse_partition_payload(raw_partitions, metadata_partition_fields)
    by_tier = defaultdict(list)
    for row in records:
        by_tier[row["tierIdentifier"]].append(row["weekStartDate"])

    tier_summary = {}
    for tier, weeks in sorted(by_tier.items()):
        anchors = sorted({calendar_week(w) for w in weeks})
        gaps = []
        if anchors:
            current = date.fromisoformat(anchors[0])
            final = date.fromisoformat(anchors[-1])
            actual = {date.fromisoformat(x) for x in anchors}
            while current <= final:
                if current not in actual:
                    gaps.append(current.isoformat())
                current += timedelta(days=7)
        tier_summary[tier] = {
            "partition_pairs": len(weeks),
            "unique_calendar_weeks": len(anchors),
            "earliest_week": min(weeks),
            "latest_week": max(weeks),
            "missing_calendar_week_anchors": gaps,
            "missing_calendar_week_count": len(gaps),
        }

    metadata_fields = {
        str(f.get("name")): f
        for f in (metadata.get("fields") or [])
        if isinstance(f, dict) and f.get("name")
    }
    key_descriptions = {
        key: metadata_fields[key].get("description")
        for key in ("tierIdentifier", "initialPublishedDate", "lastUpdateDate", "lastReportedDate")
        if key in metadata_fields
    }
    sample_presence = {}
    present = {(r["weekStartDate"], r["tierIdentifier"]) for r in records}
    for week in EXPECTED_SAMPLE_WEEKS:
        sample_presence[week] = {
            tier: (week, tier) in present for tier in ("T1", "T2", "OTCE", "OTC")
        }

    return {
        "dataset": name,
        "partition_fields": list(metadata.get("partitionFields") or fields),
        "partition_fields_match_expected": tuple(metadata.get("partitionFields") or fields) == DEFAULT_PARTITION_FIELDS,
        "raw_partition_records": len(raw_records),
        "unique_partition_pairs": len(records),
        "duplicate_partition_pair_records": len(raw_records) - len(records),
        "earliest_week": min((r["weekStartDate"] for r in records), default=None),
        "latest_week": max((r["weekStartDate"] for r in records), default=None),
        "tier_summary": tier_summary,
        "sample_week_presence": sample_presence,
        "key_field_descriptions": key_descriptions,
        "metadata_field_names": sorted(metadata_fields),
        "totalNotionalSum_in_metadata": "totalNotionalSum" in metadata_fields,
        "totalNotionalSum_absent_from_metadata": "totalNotionalSum" not in metadata_fields,
    }, records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase364_finra_weekly_partition_census")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Data-API-Version": "1",
        "User-Agent": "SmartMoneyResearch-Phase364/1.0",
    })
    token = os.getenv("FINRA_API_TOKEN", "").strip()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    dataset_results = {}
    all_records = {}
    raw_payloads = {}
    raw_metadata = {}
    raw_headers = {}

    for dataset in DATASETS:
        metadata_url = f"{BASE_URL}/metadata/group/{GROUP}/name/{dataset}"
        partitions_url = f"{BASE_URL}/partitions/group/{GROUP}/name/{dataset}"
        metadata, metadata_headers = request_json(session, metadata_url)
        partitions, partition_headers = request_json(session, partitions_url)
        summary, records = summarize_dataset(dataset, metadata, partitions)
        if not records:
            raise RuntimeError(
                f"No partition combinations parsed for {dataset}; preserve raw response and revise parser before proceeding"
            )
        dataset_results[dataset] = summary
        all_records[dataset] = records
        raw_payloads[dataset] = partitions
        raw_metadata[dataset] = metadata
        raw_headers[dataset] = {
            "metadata": dict(metadata_headers),
            "partitions": dict(partition_headers),
        }

    key_sets = {
        name: {(r["weekStartDate"], r["tierIdentifier"]) for r in rows}
        for name, rows in all_records.items()
    }
    historic = key_sets["weeklySummaryHistoric"]
    current = key_sets["weeklySummary"]
    overlap = sorted(historic & current)
    combined = historic | current
    combined_by_tier = defaultdict(list)
    for week, tier in combined:
        combined_by_tier[tier].append(week)

    summary = {
        "phase": 364,
        "source": "FINRA OTCMarket weeklySummaryHistoric + weeklySummary",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "datasets": dataset_results,
        "combined": {
            "unique_partition_pairs": len(combined),
            "unique_weeks": len({week for week, _ in combined}),
            "earliest_week": min((week for week, _ in combined), default=None),
            "latest_week": max((week for week, _ in combined), default=None),
            "tiers": {
                tier: {
                    "partition_pairs": len(weeks),
                    "unique_weeks": len(set(weeks)),
                    "earliest_week": min(weeks),
                    "latest_week": max(weeks),
                }
                for tier, weeks in sorted(combined_by_tier.items())
            },
            "historic_current_overlap_pairs": len(overlap),
            "historic_current_overlap_sample": overlap[:100],
            "otce_present": "OTCE" in combined_by_tier,
            "otc_present": "OTC" in combined_by_tier,
            "t1_present": "T1" in combined_by_tier,
            "t2_present": "T2" in combined_by_tier,
        },
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_changed": False,
    }

    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "metadata.json").write_text(json.dumps(raw_metadata, indent=2), encoding="utf-8")
    (out / "partitions.json").write_text(json.dumps(raw_payloads, indent=2), encoding="utf-8")
    (out / "response_headers.json").write_text(json.dumps(raw_headers, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print(
        f"[Phase364] historic_pairs={dataset_results['weeklySummaryHistoric']['unique_partition_pairs']} "
        f"current_pairs={dataset_results['weeklySummary']['unique_partition_pairs']} "
        f"combined_pairs={len(combined)} tiers={sorted(combined_by_tier)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
