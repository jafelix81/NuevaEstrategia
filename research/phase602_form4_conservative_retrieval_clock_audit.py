#!/usr/bin/env python3
"""Offline audit of a conservative SEC Form 4 detail-retrieval knowledge clock.

The script does not fetch SEC documents, mutate ledgers, or authorize signals.
It asks whether a successfully parsed Form 4 detail row can be assigned a
conservative research-knowledge upper bound at the time the document was
retrieved, strictly after a bounded scheduled first-seen poll.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


TRUE = {"1", "true", "yes", "y"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.I)


def truth(value: object) -> bool:
    return str(value or "").strip().lower() in TRUE


def parse_utc(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def accession_token(value: object) -> str:
    return str(value or "").replace("-", "").strip()


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def quantiles(values: list[float]) -> dict | None:
    ordered = sorted(value for value in values if value == value)
    if not ordered:
        return None

    def at(p: float) -> float:
        return ordered[int((len(ordered) - 1) * p)]

    return {
        "n": len(ordered),
        "min": ordered[0],
        "p25": at(0.25),
        "median": at(0.50),
        "p75": at(0.75),
        "p95": at(0.95),
        "max": ordered[-1],
    }


def evaluate_detail(detail: dict[str, str], event: dict[str, str] | None) -> dict:
    """Return a fail-closed candidate classification and its conservative clock."""
    reasons: list[str] = []
    if event is None:
        return {
            "eligible": False,
            "reasons": ["event_missing_or_ambiguous"],
            "knowledge_time_upper_bound_utc": None,
        }

    if str(event.get("accession") or "") != str(detail.get("accession") or ""):
        reasons.append("accession_mismatch")
    if event.get("capture_mode") != "schedule":
        reasons.append("event_not_from_scheduled_capture")
    if event.get("first_seen_interval_status") != "BOUNDED_METADATA_ONLY":
        reasons.append("first_seen_interval_not_bounded")
    if not truth(event.get("first_seen_is_upper_bound_not_exact_receipt")):
        reasons.append("first_seen_upper_bound_semantics_missing")
    if not truth(event.get("event_metadata_interval_bounded")):
        reasons.append("event_metadata_interval_not_bounded")
    if not event.get("first_seen_poll_run_id"):
        reasons.append("poll_run_id_missing")

    lower = parse_utc(event.get("first_seen_interval_lower_bound_utc"))
    upper = parse_utc(event.get("first_seen_interval_upper_bound_utc"))
    first_seen = parse_utc(event.get("first_seen_at_utc"))
    feed_updated = parse_utc(event.get("feed_updated_utc"))
    if lower is None or upper is None or first_seen is None:
        reasons.append("first_seen_interval_clock_invalid")
    else:
        if lower >= upper:
            reasons.append("first_seen_interval_not_positive")
        if upper != first_seen:
            reasons.append("first_seen_upper_bound_not_equal_to_receipt")
    if feed_updated is None or (upper is not None and feed_updated > upper):
        reasons.append("feed_updated_clock_invalid")

    detail_upper = parse_utc(detail.get("first_seen_interval_upper_bound_utc"))
    detail_first_seen = parse_utc(detail.get("first_seen_at_utc"))
    retrieved = parse_utc(detail.get("detail_retrieved_at_utc"))
    if detail_upper is None or detail_first_seen is None or retrieved is None:
        reasons.append("detail_retrieval_clock_invalid")
    elif upper is not None:
        if detail_upper != upper or detail_first_seen != first_seen:
            reasons.append("detail_event_clock_mismatch")
        if retrieved < upper:
            reasons.append("detail_retrieved_before_first_seen_upper_bound")

    if detail.get("first_seen_interval_status") != event.get("first_seen_interval_status"):
        reasons.append("detail_event_interval_status_mismatch")
    if detail.get("first_seen_poll_run_id") != event.get("first_seen_poll_run_id"):
        reasons.append("detail_event_poll_run_mismatch")
    if not truth(detail.get("first_seen_is_upper_bound_not_exact_receipt")):
        reasons.append("detail_upper_bound_semantics_missing")

    if detail.get("parse_status") != "parsed" or str(detail.get("parse_error") or "").strip():
        reasons.append("detail_parse_not_clean")
    if not SHA256_RE.fullmatch(str(detail.get("xml_sha256") or "").strip()):
        reasons.append("xml_sha256_missing_or_invalid")
    if not SHA256_RE.fullmatch(str(detail.get("submission_sha256") or "").strip()):
        reasons.append("submission_sha256_missing_or_invalid")
    if not str(detail.get("xml_source") or "").strip():
        reasons.append("xml_source_missing")

    accession = accession_token(detail.get("accession"))
    parsed_url = urlparse(str(detail.get("filing_url") or ""))
    if parsed_url.scheme != "https" or parsed_url.hostname not in {"sec.gov", "www.sec.gov"}:
        reasons.append("filing_url_not_sec_archive")
    if not accession or accession not in parsed_url.path.replace("-", ""):
        reasons.append("filing_url_accession_mismatch")

    eligible = not reasons
    return {
        "eligible": eligible,
        "reasons": reasons,
        # This is deliberately later than the first-seen receipt and is not
        # represented as the SEC's exact first-publication timestamp.
        "knowledge_time_upper_bound_utc": (
            retrieved.isoformat().replace("+00:00", "Z") if eligible and retrieved else None
        ),
    }


def audit_ledgers(
    events: list[dict[str, str]],
    details: list[dict[str, str]],
    owners: list[dict[str, str]] | None = None,
    form144_details: list[dict[str, str]] | None = None,
) -> dict:
    event_index: dict[str, list[dict[str, str]]] = defaultdict(list)
    for event in events:
        if event.get("accession"):
            event_index[event["accession"]].append(event)

    duplicate_event_accessions = sorted(
        accession for accession, rows in event_index.items() if len(rows) != 1
    )
    classifications = []
    for detail in details:
        matching = event_index.get(str(detail.get("accession") or ""), [])
        event = matching[0] if len(matching) == 1 else None
        classifications.append((detail, evaluate_detail(detail, event)))

    eligible = [(row, result) for row, result in classifications if result["eligible"]]
    reasons = Counter(
        reason
        for _, result in classifications
        for reason in result["reasons"]
    )
    bounded_events = [
        row for row in events
        if row.get("first_seen_interval_status") == "BOUNDED_METADATA_ONLY"
    ]
    poll_intervals = []
    for row in bounded_events:
        lower = parse_utc(row.get("first_seen_interval_lower_bound_utc"))
        upper = parse_utc(row.get("first_seen_interval_upper_bound_utc"))
        if lower and upper and upper >= lower:
            poll_intervals.append((upper - lower).total_seconds() / 3600.0)

    retrieval_delays = []
    for row, result in eligible:
        upper = parse_utc(row.get("first_seen_interval_upper_bound_utc"))
        retrieved = parse_utc(row.get("detail_retrieved_at_utc"))
        if upper and retrieved:
            retrieval_delays.append((retrieved - upper).total_seconds() / 3600.0)

    transaction_rows = [
        row for row, result in eligible
        if row.get("detail_type") == "transaction_row"
    ]
    eligible_accessions = {row.get("accession") for row, _ in eligible if row.get("accession")}
    transaction_accessions = {
        row.get("accession") for row in transaction_rows if row.get("accession")
    }
    transaction_codes = Counter(
        row.get("transaction_code") or "UNKNOWN" for row in transaction_rows
    )

    owner_rows = owners or []
    owner_accessions = {row.get("accession") for row in owner_rows if row.get("accession")}
    owner_link_status = Counter(
        row.get("line_owner_link_status") or "UNKNOWN" for row in owner_rows
    )
    owner_line_link_verified = sum(
        truth(row.get("transaction_line_attribution_verified")) for row in owner_rows
    )

    def true_count(field: str) -> int:
        return sum(truth(row.get(field)) for row in details)

    comparator = form144_details or []
    comparator_summary = {
        "detail_rows": len(comparator),
        "distinct_accessions": len({r.get("accession") for r in comparator if r.get("accession")}),
        "research_observation_eligible_rows": sum(
            truth(r.get("research_observation_eligible")) for r in comparator
        ),
        "source_xml_hash_match_rows": sum(
            str(r.get("source_xml_hash_matches_event") or "").strip().lower() == "true"
            for r in comparator
        ),
        "signal_eligible_rows": sum(truth(r.get("signal_eligible")) for r in comparator),
    }

    return {
        "audit": "PHASE602_FORM4_CONSERVATIVE_RETRIEVAL_CLOCK_AUDIT",
        "disposition": (
            "RETRIEVAL_CLOCK_CANDIDATE_PASS_ATTRIBUTION_GATES_BLOCKED"
            if details and len(eligible) == len(details) and not duplicate_event_accessions
            else "REVIEW_REQUIRED"
        ),
        "form4": {
            "event_rows": len(events),
            "unique_event_accessions": len(event_index),
            "duplicate_event_accessions": duplicate_event_accessions,
            "bounded_event_rows": len(bounded_events),
            "non_bounded_event_rows": len(events) - len(bounded_events),
            "bounded_poll_interval_hours": quantiles(poll_intervals),
            "detail_rows": len(details),
            "detail_accessions": len({r.get("accession") for r in details if r.get("accession")}),
            "detail_parse_status_counts": dict(Counter(r.get("parse_status") or "MISSING" for r in details)),
            "current_research_observation_flag_counts": dict(
                Counter(r.get("research_observation_eligible") or "MISSING" for r in details)
            ),
            "retrieval_clock_candidate_rows": len(eligible),
            "retrieval_clock_candidate_accessions": len(eligible_accessions),
            "eligible_transaction_rows": len(transaction_rows),
            "eligible_transaction_accessions": len(transaction_accessions),
            "transaction_code_counts": dict(sorted(transaction_codes.items())),
            "detail_retrieval_delay_after_first_seen_upper_bound_hours": quantiles(retrieval_delays),
            "candidate_rejection_reason_counts": dict(sorted(reasons.items())),
            "public_availability_certified_rows": true_count("public_availability_certified"),
            "security_identity_verified_rows": true_count("security_identity_verified"),
            "historical_f80_membership_verified_rows": true_count("historical_f80_membership_verified"),
            "owner_attribution_verified_rows": true_count("owner_attribution_verified"),
            "transaction_semantics_verified_rows": true_count("transaction_semantics_verified"),
            "signal_eligible_rows": true_count("signal_eligible"),
        },
        "owner_attribution": {
            "owner_rows": len(owner_rows),
            "owner_accessions": len(owner_accessions),
            "eligible_transaction_accessions_with_owner_sidecar": len(
                transaction_accessions & owner_accessions
            ),
            "transaction_line_attribution_verified_rows": owner_line_link_verified,
            "line_owner_link_status_counts": dict(sorted(owner_link_status.items())),
        },
        "form144_comparator": comparator_summary,
        "policy": {
            "candidate_knowledge_clock_field": "detail_retrieved_at_utc",
            "acceptance_datetime_used_as_knowledge_clock": False,
            "first_seen_receipt_treated_as_exact_public_availability": False,
            "next_use_boundary": "first full XNYS session strictly after detail_retrieved_at_utc",
            "same_day_intraday_use_authorized": False,
            "public_availability_certified": False,
            "source_xml_persisted": False,
            "source_hash_comparable_to_original_feed_event": False,
            "signal_eligibility_changed": False,
            "forward_returns_or_alpha_test_performed": False,
            "bootstrap_loo_or_holdout_used": False,
            "f80_changed": False,
            "production_changed": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", default="research/data/sec_form4_first_seen/events.csv")
    parser.add_argument("--details", default="research/data/sec_form4_first_seen/transaction_details.csv")
    parser.add_argument("--owners", default="research/data/sec_form4_first_seen/reporting_owners.csv")
    parser.add_argument("--form144-details", default="research/data/sec_form144_first_seen/sale_details.csv")
    parser.add_argument("--output", default="phase602_output/summary.json")
    args = parser.parse_args()

    summary = audit_ledgers(
        read_csv(args.events),
        read_csv(args.details),
        read_csv(args.owners),
        read_csv(args.form144_details),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
