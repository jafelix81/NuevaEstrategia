from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def parse_utc(value: str) -> datetime:
    token = str(value or "").strip()
    if not token:
        raise ValueError("timestamp_missing")
    if token.endswith("Z"):
        token = token[:-1] + "+00:00"
    parsed = datetime.fromisoformat(token)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp_must_be_timezone_aware")
    return parsed.astimezone(timezone.utc)


def as_bool(value: str) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile_requires_values")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def build_summary(
    events: list[dict[str, str]],
    feed_observations: list[dict[str, str]],
    state: dict,
    workflow_text: str,
    source_hashes: dict[str, str] | None = None,
) -> dict:
    if not events:
        raise ValueError("event_ledger_empty")
    if not feed_observations:
        raise ValueError("feed_observation_ledger_empty")

    required_event_fields = {
        "first_seen_poll_run_id",
        "first_seen_interval_status",
        "first_seen_interval_lower_bound_utc",
        "first_seen_interval_upper_bound_utc",
        "research_observation_eligible",
        "signal_eligible",
    }
    if not required_event_fields.issubset(events[0]):
        raise ValueError("event_schema_missing_required_fields")

    statuses = Counter(row["first_seen_interval_status"] for row in events)
    bounded = [row for row in events if row["first_seen_interval_status"] == "BOUNDED_METADATA_ONLY"]
    baseline = [row for row in events if row["first_seen_interval_status"] == "INITIAL_BASELINE_NO_LOWER_BOUND"]
    unknown_statuses = set(statuses) - {"BOUNDED_METADATA_ONLY", "INITIAL_BASELINE_NO_LOWER_BOUND"}
    if unknown_statuses:
        raise ValueError(f"unexpected_interval_status:{','.join(sorted(unknown_statuses))}")

    if any(as_bool(row["research_observation_eligible"]) for row in events):
        raise ValueError("research_observation_eligibility_must_remain_false")
    if any(as_bool(row["signal_eligible"]) for row in events):
        raise ValueError("signal_eligibility_must_remain_false")

    widths_by_run: dict[str, list[float]] = defaultdict(list)
    bounds_by_run: dict[str, dict[str, list[str] | int]] = {}
    all_widths: list[float] = []
    for row in bounded:
        lower = parse_utc(row["first_seen_interval_lower_bound_utc"])
        upper = parse_utc(row["first_seen_interval_upper_bound_utc"])
        if upper < lower:
            raise ValueError("negative_first_seen_interval")
        width = (upper - lower).total_seconds() / 3600.0
        run_id = row["first_seen_poll_run_id"]
        all_widths.append(width)
        widths_by_run[run_id].append(width)
        item = bounds_by_run.setdefault(run_id, {"count": 0, "lower_bounds": [], "upper_bounds": []})
        item["count"] = int(item["count"]) + 1
        item["lower_bounds"].append(row["first_seen_interval_lower_bound_utc"])
        item["upper_bounds"].append(row["first_seen_interval_upper_bound_utc"])

    if not all_widths:
        raise ValueError("no_bounded_events")

    poll_rows: dict[str, list[datetime]] = defaultdict(list)
    for row in feed_observations:
        run_id = str(row.get("poll_run_id", "")).strip()
        if not run_id:
            raise ValueError("feed_observation_missing_poll_run_id")
        poll_rows[run_id].append(parse_utc(row["response_received_at_utc"]))

    poll_intervals = []
    for run_id, receipts in poll_rows.items():
        poll_intervals.append({
            "run_id": run_id,
            "poll_start_utc": min(receipts).isoformat().replace("+00:00", "Z"),
            "poll_end_utc": max(receipts).isoformat().replace("+00:00", "Z"),
            "feed_observation_rows": len(receipts),
        })
    poll_intervals.sort(key=lambda item: item["poll_start_utc"])

    gaps = []
    for previous, current in zip(poll_intervals, poll_intervals[1:]):
        gap_hours = (
            parse_utc(current["poll_start_utc"]) - parse_utc(previous["poll_end_utc"])
        ).total_seconds() / 3600.0
        if gap_hours < 0:
            raise ValueError("overlapping_poll_receipt_windows")
        gaps.append({
            "from_run_id": previous["run_id"],
            "to_run_id": current["run_id"],
            "hours_between_prior_poll_end_and_next_poll_start": round(gap_hours, 6),
        })

    by_run = {}
    for run_id, item in bounds_by_run.items():
        widths = widths_by_run[run_id]
        by_run[run_id] = {
            "event_count": item["count"],
            "lower_bound_utc": min(item["lower_bounds"]),
            "upper_bound_min_utc": min(item["upper_bounds"]),
            "upper_bound_max_utc": max(item["upper_bounds"]),
            "interval_width_hours_min": round(min(widths), 6),
            "interval_width_hours_max": round(max(widths), 6),
        }

    cron_match = re.search(r'cron\s*:\s*"([^"]+)"', workflow_text)
    cron = cron_match.group(1) if cron_match else None
    event_runs = Counter(row.get("first_seen_poll_run_id", "") for row in events)
    eligibility = {
        "research_observation_eligible_rows": sum(as_bool(row["research_observation_eligible"]) for row in events),
        "signal_eligible_rows": sum(as_bool(row["signal_eligible"]) for row in events),
        "all_events_research_ineligible": all(not as_bool(row["research_observation_eligible"]) for row in events),
        "all_events_signal_ineligible": all(not as_bool(row["signal_eligible"]) for row in events),
    }

    return {
        "phase": 498,
        "audit_scope": "SEC Form 4/4-A collector cadence and first-seen interval-censoring only",
        "source_hashes": source_hashes or {},
        "collector": {
            "declared_schedule_cron_utc": cron,
            "schedule_interpretation": "hourly on weekdays at minute 17" if cron == "17 * * * 1-5" else "see declared cron",
            "successful_poll_count_in_ledger": len(poll_intervals),
            "poll_receipt_windows": poll_intervals,
            "gaps_between_prior_poll_end_and_next_poll_start": gaps,
            "observed_poll_gap_hours": [x["hours_between_prior_poll_end_and_next_poll_start"] for x in gaps],
            "latest_persisted_poll_run_id": state.get("last_poll_run_id"),
            "latest_persisted_poll_end_utc": state.get("last_poll_ended_utc"),
        },
        "event_ledger": {
            "total_rows": len(events),
            "rows_by_first_seen_poll_run_id": dict(event_runs),
            "rows_by_interval_status": dict(statuses),
            "initial_baseline_without_lower_bound_rows": len(baseline),
            "bounded_metadata_only_rows": len(bounded),
            "bounded_rows_by_poll_run_id": by_run,
            "interval_width_hours": {
                "min": round(min(all_widths), 6),
                "p25": round(quantile(all_widths, 0.25), 6),
                "median": round(quantile(all_widths, 0.50), 6),
                "p75": round(quantile(all_widths, 0.75), 6),
                "p90": round(quantile(all_widths, 0.90), 6),
                "max": round(max(all_widths), 6),
                "at_most_1_hour": sum(x <= 1 for x in all_widths),
                "at_most_2_hours": sum(x <= 2 for x in all_widths),
                "over_6_hours": sum(x > 6 for x in all_widths),
            },
        },
        "eligibility": eligibility,
        "decision": {
            "disposition": "TIMING_BOUND_ONLY_NO_SIGNAL_PROMOTION",
            "collector_receipt_is_an_upper_bound_not_exact_publication": True,
            "nominal_hourly_cadence_demonstrated": False,
            "same_day_intraday_use_authorized": False,
            "historical_security_identity_verified": False,
            "historical_f80_membership_verified": False,
            "alpha_test_authorized": False,
            "f80_changed": False,
            "production_changed": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--feed-observations", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    hashes = {
        "events_csv_sha256": sha256(args.events),
        "feed_observations_csv_sha256": sha256(args.feed_observations),
        "state_json_sha256": sha256(args.state),
        "workflow_yaml_sha256": sha256(args.workflow),
    }
    summary = build_summary(
        read_csv(args.events),
        read_csv(args.feed_observations),
        json.loads(args.state.read_text(encoding="utf-8")),
        args.workflow.read_text(encoding="utf-8"),
        hashes,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / "summary.json"
    target.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PHASE498_CADENCE_AUDIT=PASS")
    print("EVENT_ROWS=", summary["event_ledger"]["total_rows"])
    print("BOUNDED_ROWS=", summary["event_ledger"]["bounded_metadata_only_rows"])
    print("POLL_GAPS_HOURS=", summary["collector"]["observed_poll_gap_hours"])
    print("INTERVAL_WIDTH_HOURS=", summary["event_ledger"]["interval_width_hours"])
    print("SIGNAL_ELIGIBLE=", summary["eligibility"]["signal_eligible_rows"])


if __name__ == "__main__":
    main()
