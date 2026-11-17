"""Reproduce the first successful post-migration SEC Form 144 capture audit.

This is a read-only audit of the committed append-only ledgers for run 44179257367.
It does not infer trade execution, public availability, historical F80 membership,
or signal eligibility.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "research" / "data" / "sec_form144_first_seen"
RUN_ID = "44179257367"


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        return fields, list(reader)


def _true(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def audit(root: Path = ROOT, run_id: str = RUN_ID) -> dict[str, Any]:
    data = root / "research" / "data" / "sec_form144_first_seen"
    event_fields, events = _read_csv(data / "events.csv")
    _, observations = _read_csv(data / "feed_observations.csv")
    _, reconciliations = _read_csv(data / "acceptance_reconciliation.csv")
    state = json.loads((data / "state.json").read_text(encoding="utf-8"))

    run_events = [row for row in events if row.get("first_seen_poll_run_id") == run_id]
    run_observations = [row for row in observations if row.get("poll_run_id") == run_id]
    run_reconciliations = [
        row for row in reconciliations if row.get("reconciliation_run_id") == run_id
    ]
    feed_144 = [row for row in run_events if row.get("feed_name") == "144"]
    feed_144a = [row for row in run_events if row.get("feed_name") == "144A"]
    eligible = [row for row in run_events if _true(row.get("research_observation_eligible"))]
    candidate_matches = [row for row in run_events if _true(row.get("candidate_issuer_match"))]

    observation_counts = Counter(row.get("feed_name", "") for row in run_observations)
    acceptance_deltas = [_number(row.get("feed_updated_minus_acceptance_seconds"))
                         for row in run_reconciliations]
    acceptance_deltas = [value for value in acceptance_deltas if value is not None]
    receipt_lags = [_number(row.get("first_seen_upper_minus_acceptance_seconds"))
                    for row in run_reconciliations]
    receipt_lags = [value for value in receipt_lags if value is not None]
    eligible_accessions = {row["accession"] for row in eligible}
    eligible_reconciliations = [
        row for row in run_reconciliations if row.get("accession") in eligible_accessions
    ]
    eligible_receipt_lags = [
        value for row in eligible_reconciliations
        if (value := _number(row.get("first_seen_upper_minus_acceptance_seconds"))) is not None
    ]

    return {
        "run_id": run_id,
        "event_header_fields": len(event_fields),
        "event_rows_total": len(events),
        "feed_observation_rows_total": len(observations),
        "acceptance_reconciliation_rows_total": len(reconciliations),
        "new_event_rows": len(run_events),
        "new_event_rows_by_feed": {
            "144": len(feed_144),
            "144A": len(feed_144a),
        },
        "new_event_xml_resolved": sum(row.get("xml_status") == "retrieved" for row in run_events),
        "new_event_candidate_matches": len(candidate_matches),
        "candidate_matches_on_gap_contaminated_144_feed": sum(
            row.get("feed_name") == "144"
            and row.get("first_seen_interval_status") == "POSSIBLE_FEED_WINDOW_GAP"
            for row in candidate_matches
        ),
        "research_observation_eligible_rows": len(eligible),
        "eligible_rows_all_from_144a_feed": all(row.get("feed_name") == "144A" for row in eligible),
        "eligible_rows_all_parent_linked": all(bool(row.get("previous_accession")) for row in eligible),
        "eligible_candidate_matches": sum(_true(row.get("candidate_issuer_match")) for row in eligible),
        "eligible_rows_signal_eligible": sum(_true(row.get("signal_eligible")) for row in eligible),
        "eligible_rows_public_availability_certified": sum(
            _true(row.get("public_availability_certified")) for row in eligible
        ),
        "feed_observation_rows_appended": len(run_observations),
        "feed_observation_rows_by_feed": {
            "144": observation_counts.get("144", 0),
            "144A": observation_counts.get("144A", 0),
        },
        "acceptance_reconciliations_added": len(run_reconciliations),
        "acceptance_reconciliation_unresolved": sum(
            not row.get("acceptance_utc") for row in run_reconciliations
        ),
        "feed_updated_equals_acceptance_all_rows": (
            len(acceptance_deltas) == len(run_reconciliations)
            and all(value == 0 for value in acceptance_deltas)
        ),
        "receipt_lag_seconds_min": min(receipt_lags) if receipt_lags else None,
        "receipt_lag_seconds_max": max(receipt_lags) if receipt_lags else None,
        "eligible_receipt_lag_seconds_min": min(eligible_receipt_lags) if eligible_receipt_lags else None,
        "eligible_receipt_lag_seconds_max": max(eligible_receipt_lags) if eligible_receipt_lags else None,
        "feed_144_rows_all_gap_quarantined": all(
            row.get("first_seen_interval_status") == "POSSIBLE_FEED_WINDOW_GAP"
            and not row.get("first_seen_interval_lower_bound_utc")
            and not _true(row.get("research_observation_eligible"))
            for row in feed_144
        ),
        "feed_144a_rows_all_bounded": all(
            row.get("first_seen_interval_status") == "BOUNDED_BY_SUCCESSIVE_SUCCESSFUL_POLLS"
            and bool(row.get("first_seen_interval_lower_bound_utc"))
            and _true(row.get("research_observation_eligible"))
            for row in feed_144a
        ),
        "feed_144a_rows_all_amendment_linked": all(
            row.get("form") == "144/A" and bool(row.get("previous_accession"))
            for row in feed_144a
        ),
        "all_new_rows_cross_feed_provenance_complete": all(
            _true(row.get("cross_feed_provenance_complete")) for row in run_events
        ),
        "all_new_rows_signal_ineligible": all(
            not _true(row.get("signal_eligible")) for row in run_events
        ),
        "all_new_rows_public_availability_uncertified": all(
            not _true(row.get("public_availability_certified")) for row in run_events
        ),
        "all_new_rows_historical_f80_membership_unverified": all(
            not _true(row.get("historical_f80_membership_verified")) for row in run_events
        ),
        "all_new_rows_intraday_unauthorized": all(
            not _true(row.get("same_day_intraday_use_authorized")) for row in run_events
        ),
        "state_poll_status": state.get("last_poll_status"),
        "state_complete_poll_count": state.get("complete_poll_count"),
        "state_last_poll_run_id": state.get("last_poll_attempt_run_id"),
        "state_gap_by_feed": state.get("last_poll_possible_gap_by_feed"),
    }


def main() -> None:
    print(json.dumps(audit(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
