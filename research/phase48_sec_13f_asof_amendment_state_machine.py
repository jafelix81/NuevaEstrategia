#!/usr/bin/env python3
"""Phase 48 — conservative SEC Form 13F manager-period amendment state machine.

Pure, deterministic data-layer logic. It does not download SEC data, infer a
security/ticker identity, calculate returns, or emit trading signals.

Availability uses the first supplied regular-session date strictly AFTER
FILING_DATE. This is deliberately conservative because the structured
SUBMISSION table is date-only and does not carry the EDGAR acceptance time.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import date, datetime
from typing import Any

TRUTHY = {"1", "Y", "YES", "TRUE"}
FALSEY = {"0", "N", "NO", "FALSE"}
AMENDMENT_ALIASES = {
    "RESTATEMENT": "RESTATEMENT",
    "NEW HOLDINGS": "NEW_HOLDINGS",
    "NEW HOLDINGS ENTRIES": "NEW_HOLDINGS",
    "NEW_HOLDINGS": "NEW_HOLDINGS",
}
HOLDING_FORMS = {"13F-HR", "13F-HR/A"}
NOTICE_FORMS = {"13F-NT", "13F-NT/A"}


class StateMachineError(ValueError):
    """Raised when the filing chain cannot be reconstructed without guessing."""


def parse_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    raw = str(value or "").strip()
    if not raw:
        raise StateMachineError("missing_date")
    try:
        return date.fromisoformat(raw)
    except ValueError:
        try:
            return datetime.strptime(raw.upper(), "%d-%b-%Y").date()
        except ValueError as exc:
            raise StateMachineError(f"invalid_date:{raw}") from exc


def normalize_cik(value: Any) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if not digits or len(digits) > 10:
        raise StateMachineError("invalid_manager_cik")
    return digits.zfill(10)


def normalize_amendment_type(value: Any) -> str:
    raw = re.sub(r"\s+", " ", str(value or "").strip().upper())
    if raw not in AMENDMENT_ALIASES:
        raise StateMachineError(f"unknown_amendment_type:{raw or '<blank>'}")
    return AMENDMENT_ALIASES[raw]


def _event_kind(event: dict) -> tuple[str, int | None, str | None]:
    form = str(event.get("submission_type") or "").strip().upper()
    if form in NOTICE_FORMS:
        return "NOTICE_ONLY", None, None
    if form not in HOLDING_FORMS:
        raise StateMachineError(f"unsupported_submission_type:{form or '<blank>'}")

    flag = str(event.get("is_amendment") or "").strip().upper()
    if flag and flag not in TRUTHY and flag not in FALSEY:
        raise StateMachineError(f"unknown_is_amendment_flag:{flag}")

    raw_number = str(event.get("amendment_number") or "").strip()
    raw_type = str(event.get("amendment_type") or "").strip()
    form_says_amendment = form.endswith("/A")
    metadata_says_amendment = bool(raw_number or raw_type)
    flag_says_amendment = flag in TRUTHY
    flag_says_original = flag in FALSEY

    if flag_says_original and (form_says_amendment or metadata_says_amendment):
        raise StateMachineError("coverpage_flag_conflicts_with_amendment_metadata")

    is_amendment = form_says_amendment or flag_says_amendment or metadata_says_amendment
    if not is_amendment:
        return "ORIGINAL", 0, None

    if not raw_number or not raw_type:
        raise StateMachineError("amendment_missing_number_or_type")
    try:
        number = int(raw_number)
    except ValueError as exc:
        raise StateMachineError("invalid_amendment_number") from exc
    if number < 1:
        raise StateMachineError("invalid_amendment_number")
    return "AMENDMENT", number, normalize_amendment_type(raw_type)


def _normalize_holding(row: dict) -> tuple[tuple[str, ...], dict]:
    cusip = re.sub(r"\s+", "", str(row.get("cusip") or "").upper())
    if not cusip:
        raise StateMachineError("holding_missing_cusip")
    amount_type = str(row.get("amount_type") or row.get("sshprnamttype") or "").strip().upper()
    key = (
        cusip,
        str(row.get("title_of_class") or "").strip().upper(),
        str(row.get("put_call") or row.get("putcall") or "").strip().upper(),
        str(row.get("investment_discretion") or row.get("investmentdiscretion") or "").strip().upper(),
        str(row.get("other_manager") or row.get("othermanager") or "").strip().upper(),
        amount_type,
    )
    normalized = {
        "cusip": cusip,
        "title_of_class": key[1],
        "put_call": key[2],
        "investment_discretion": key[3],
        "other_manager": key[4],
        "amount_type": key[5],
        "shares": str(row.get("shares") or row.get("sshprnamt") or "").strip(),
        "value": str(row.get("value") or "").strip(),
        "figi": str(row.get("figi") or "").strip().upper(),
        "issuer": str(row.get("issuer") or row.get("nameofissuer") or "").strip(),
    }
    if not normalized["shares"] or not normalized["value"]:
        raise StateMachineError("holding_missing_shares_or_value")
    return key, normalized


def _availability_map(sessions: list[Any]) -> list[date]:
    parsed = sorted({parse_date(value) for value in sessions})
    if not parsed:
        raise StateMachineError("empty_session_calendar")
    return parsed


def first_full_session_after(filing_date: Any, sessions: list[Any]) -> str | None:
    """Return the first supplied regular session strictly after filing_date."""
    filed = parse_date(filing_date)
    calendar = _availability_map(sessions)
    for session in calendar:
        if session > filed:
            return session.isoformat()
    return None


def _prepare_events(
    events: list[dict], sessions: list[Any], as_of: date
) -> tuple[dict, list[dict], list[dict]]:
    """Filter to events knowable as of the requested session BEFORE chain checks.

    This ordering is essential: future amendments/notices must not affect a
    historical state, even by causing a future chain gap or validation error.
    """
    calendar = _availability_map(sessions)
    prepared: dict[tuple[str, str], list[dict]] = defaultdict(list)
    notices: list[dict] = []
    pending_calendar: list[dict] = []
    seen_accessions: set[str] = set()

    for raw in events:
        event = dict(raw)
        filing_date = parse_date(event.get("filing_date"))
        eligible = next((s for s in calendar if s > filing_date), None)

        # A future event is invisible to this as-of query. Do not inspect its
        # amendment type, accession uniqueness, manager, or holdings metadata.
        if eligible is not None and eligible > as_of:
            continue
        if eligible is None:
            if filing_date <= as_of:
                pending_calendar.append({
                    "accession": str(event.get("accession") or "").strip() or None,
                    "filing_date": filing_date.isoformat(),
                    "status": "PENDING_CALENDAR_COVERAGE",
                })
            continue

        accession = str(event.get("accession") or "").strip()
        if not accession:
            raise StateMachineError("missing_accession")
        if accession in seen_accessions:
            raise StateMachineError(f"duplicate_accession:{accession}")
        seen_accessions.add(accession)

        kind, amendment_number, amendment_type = _event_kind(event)
        manager = normalize_cik(event.get("manager_cik"))
        report_period = parse_date(event.get("report_period")).isoformat()
        prepared_event = {
            "accession": accession,
            "manager_cik": manager,
            "report_period": report_period,
            "filing_date": filing_date,
            "available_session": eligible,
            "kind": kind,
            "amendment_number": amendment_number,
            "amendment_type": amendment_type,
            "submission_type": str(event.get("submission_type") or "").strip().upper(),
            "acceptance_datetime": str(event.get("acceptance_datetime") or "").strip() or None,
        }
        if kind == "NOTICE_ONLY":
            notices.append({
                "accession": accession,
                "manager_cik": manager,
                "report_period": report_period,
                "filing_date": filing_date.isoformat(),
                "available_session": eligible.isoformat(),
                "status": "NOTICE_ONLY_NOT_ZERO_HOLDINGS",
            })
        else:
            prepared[(manager, report_period)].append(prepared_event)

    # Only the filings available by as_of participate in amendment-chain
    # validation. Later filings cannot retroactively change a past state.
    for key, group in prepared.items():
        originals = [e for e in group if e["kind"] == "ORIGINAL"]
        if len(originals) != 1:
            raise StateMachineError(
                f"manager_period_requires_exactly_one_original:{key[0]}:{key[1]}:{len(originals)}"
            )
        amendments = [e for e in group if e["kind"] == "AMENDMENT"]
        numbers = sorted(e["amendment_number"] for e in amendments)
        if numbers != list(range(1, len(numbers) + 1)):
            raise StateMachineError(f"amendment_number_gap_or_duplicate:{key[0]}:{key[1]}")
        ordered = sorted(
            group,
            key=lambda e: (
                e["filing_date"],
                0 if e["kind"] == "ORIGINAL" else e["amendment_number"],
                e["accession"],
            ),
        )
        if ordered[0]["kind"] != "ORIGINAL":
            raise StateMachineError(f"amendment_precedes_original:{key[0]}:{key[1]}")
        if any(
            ordered[i]["filing_date"] < ordered[i - 1]["filing_date"]
            for i in range(1, len(ordered))
        ):
            raise StateMachineError(f"filing_date_order_conflict:{key[0]}:{key[1]}")
        prepared[key] = ordered

    return prepared, notices, pending_calendar


def reconstruct_as_of(
    events: list[dict],
    holdings_by_accession: dict[str, list[dict]],
    sessions: list[Any],
    as_of_session: Any,
) -> dict:
    """Reconstruct only manager-period holdings available by as_of_session.

    Future filings are filtered out before amendment validation so they cannot
    leak into or invalidate an earlier state. A RESTATEMENT replaces the full
    state; NEW HOLDINGS ENTRIES appends only previously absent line keys.
    13F-NT notices are returned separately and never become zero portfolios.
    """
    as_of = parse_date(as_of_session)
    calendar = _availability_map(sessions)
    if as_of not in calendar:
        raise StateMachineError("as_of_session_not_in_calendar")

    groups, notices, pending_calendar = _prepare_events(events, calendar, as_of)
    results = []
    applied_total = 0

    for (manager, report_period), group in sorted(groups.items()):
        state: dict[tuple[str, ...], dict] = {}
        applied: list[str] = []
        last_amendment_number = 0

        try:
            for event in group:
                accession = event["accession"]
                rows = holdings_by_accession.get(accession)
                if rows is None or len(rows) == 0:
                    raise StateMachineError(f"missing_holding_rows:{accession}")
                normalized_rows = [_normalize_holding(row) for row in rows]
                keys = [key for key, _ in normalized_rows]
                if len(keys) != len(set(keys)):
                    raise StateMachineError(f"duplicate_line_key_within_accession:{accession}")

                if event["kind"] == "ORIGINAL":
                    if state or applied:
                        raise StateMachineError("multiple_original_states")
                    state = {key: row for key, row in normalized_rows}
                else:
                    expected = last_amendment_number + 1
                    if event["amendment_number"] != expected:
                        raise StateMachineError("amendment_chain_gap_as_of")
                    if event["amendment_type"] == "RESTATEMENT":
                        state = {key: row for key, row in normalized_rows}
                    elif event["amendment_type"] == "NEW_HOLDINGS":
                        overlap = set(state).intersection(keys)
                        if overlap:
                            raise StateMachineError("new_holdings_amendment_overlaps_existing_line")
                        state.update({key: row for key, row in normalized_rows})
                    else:
                        raise StateMachineError("unsupported_amendment_semantics")
                    last_amendment_number = event["amendment_number"]

                applied.append(accession)

            ordered_holdings = [state[key] for key in sorted(state)]
            digest = hashlib.sha256(
                json.dumps(ordered_holdings, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            applied_total += len(applied)
            results.append({
                "manager_cik": manager,
                "report_period": report_period,
                "as_of_session": as_of.isoformat(),
                "status": "PASS",
                "holdings_count": len(ordered_holdings),
                "holdings": ordered_holdings,
                "applied_accessions": applied,
                "last_amendment_number": last_amendment_number,
                "state_sha256": digest,
            })
        except StateMachineError as exc:
            results.append({
                "manager_cik": manager,
                "report_period": report_period,
                "as_of_session": as_of.isoformat(),
                "status": "BLOCKED",
                "reason": str(exc),
                "holdings_count": 0,
                "holdings": [],
                "applied_accessions": applied,
            })

    blocked = any(row["status"] == "BLOCKED" for row in results)
    status = "BLOCKED" if blocked else (
        "PENDING_CALENDAR_COVERAGE" if pending_calendar else "PASS"
    )
    return {
        "status": status,
        "as_of_session": as_of.isoformat(),
        "manager_periods": results,
        "notices": notices,
        "pending_calendar_events": pending_calendar,
        "summary": {
            "manager_period_groups": len(results),
            "pass_groups": sum(row["status"] == "PASS" for row in results),
            "blocked_groups": sum(row["status"] == "BLOCKED" for row in results),
            "notice_only_events": len(notices),
            "pending_calendar_events": len(pending_calendar),
            "applied_accessions": applied_total,
            "signal_eligible": False,
        },
    }
