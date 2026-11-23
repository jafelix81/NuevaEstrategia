"""Phase 579: fail-closed FINRA ATS stable-row PIT and identity gate.

This module performs metadata eligibility only. It does not retrieve FINRA data,
resolve real securities, calculate returns, or admit an investment signal.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from math import isfinite
from typing import Any, Iterable, Mapping

ALLOWED_TYPES = {"ATS_W_SMBL", "ATS_W_SMBL_FIRM"}
ALLOWED_PUBLICATION_LAGS = {21, 22}


def _date(value: Any, field: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_missing")
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError as exc:
        raise ValueError(f"{field}_invalid") from exc


def _utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_missing")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def _integer(value: Any, field: str) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}_invalid") from exc
    if not isfinite(number) or not number.is_integer() or number < 0:
        raise ValueError(f"{field}_invalid")
    return int(number)


def _session_calendar(sessions: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output = []
    seen = set()
    for raw in sessions:
        d = _date(raw.get("session_date"), "session_date")
        if d in seen:
            raise ValueError(f"duplicate_session:{d.isoformat()}")
        seen.add(d)
        opened = _utc(raw.get("open_utc"), "session_open_utc")
        output.append({"session_date": d, "open_utc": opened})
    output.sort(key=lambda x: x["session_date"])
    for left, right in zip(output, output[1:]):
        if right["session_date"] <= left["session_date"] or right["open_utc"] <= left["open_utc"]:
            raise ValueError("session_calendar_not_strictly_increasing")
    return output


def _identity_for(
    symbol: str,
    week_start: date,
    entry_open: datetime | None,
    records: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    candidates = []
    matching_symbol = []
    for raw in records:
        alias = str(raw.get("symbol", "")).strip().upper()
        if alias != symbol:
            continue
        matching_symbol.append(raw)
        try:
            effective_from = _date(raw.get("effective_from"), "effective_from")
            effective_to = _date(raw["effective_to"], "effective_to") if raw.get("effective_to") else None
            record_known = _utc(raw.get("record_known_utc"), "record_known_utc")
        except ValueError:
            continue
        if effective_from <= week_start and (effective_to is None or week_start <= effective_to):
            if entry_open is not None and record_known <= entry_open:
                candidates.append(raw)

    if not matching_symbol:
        return {"status": "missing_symbol_mapping"}
    if not candidates:
        if any(raw.get("record_time_semantics_certified") is not True for raw in matching_symbol):
            return {"status": "record_clock_uncertified"}
        return {"status": "no_effective_known_mapping"}
    if any(raw.get("record_time_semantics_certified") is not True for raw in candidates):
        return {"status": "record_clock_uncertified"}
    if len(candidates) != 1:
        return {"status": "ambiguous_mapping"}
    chosen = candidates[0]
    required = ("listing_id", "security_id", "issuer_id")
    if any(not str(chosen.get(key, "")).strip() for key in required):
        return {"status": "incomplete_permanent_identity"}
    return {
        "status": "matched",
        "listing_id": str(chosen["listing_id"]),
        "security_id": str(chosen["security_id"]),
        "issuer_id": str(chosen["issuer_id"]),
    }


def classify_symbol_week(
    rows: Iterable[Mapping[str, Any]],
    sessions: Iterable[Mapping[str, Any]],
    security_master_records: Iterable[Mapping[str, Any]] = (),
    session_calendar_complete: bool = False,
) -> dict[str, Any]:
    """Classify one symbol-week; revised or ambiguous rows fail closed.

    A stable group requires:
      * at least one ATS_W_SMBL aggregate row;
      * every supplied ATS_W_SMBL / ATS_W_SMBL_FIRM row has valid dates;
      * lastUpdateDate == max(initialPublishedDate, lastReportedDate);
      * lastReportedDate <= initialPublishedDate;
      * a 21/22 calendar-day publication lag; and
      * one common initialPublishedDate across the group.

    The first executable session is the first supplied regular session whose
    session_date is strictly later than initialPublishedDate. The publication
    date itself is never used as an entry session.

    The caller must attest that the supplied exchange-session calendar is complete
    through the candidate entry date; otherwise no executable date is admitted.

    Security identity is separate from row PIT. A mapping is accepted only
    when its effective interval covers the report week, its record-known time
    is no later than the next session open, its record-time semantics are
    explicitly certified, and exactly one permanent listing/security/issuer
    tuple matches. This does not certify a vendor's clock by itself; the caller
    must set the certification flag only after written semantic validation.

    Economic eligibility remains false here because historical universe
    membership and complete total-return/delisting coverage are not inputs to
    this metadata-only gate.
    """
    materialized = list(rows)
    if not materialized:
        return {"status": "rejected", "reason": "no_rows", "stable_row_pit_eligible": False}
    calendar = _session_calendar(sessions)
    if not session_calendar_complete:
        return {
            "status": "rejected",
            "reason": "session_calendar_not_certified_complete",
            "stable_row_pit_eligible": False,
            "economic_test_eligible": False,
            "signal_admitted": False,
        }

    symbols = {str(x.get("issueSymbolIdentifier", "")).strip().upper() for x in materialized}
    weeks = set()
    for row in materialized:
        weeks.add(_date(row.get("weekStartDate") or row.get("historicalWeek"), "week_start"))
    if len(symbols) != 1 or "" in symbols:
        return {"status": "rejected", "reason": "symbol_group_mismatch", "stable_row_pit_eligible": False}
    if len(weeks) != 1:
        return {"status": "rejected", "reason": "week_group_mismatch", "stable_row_pit_eligible": False}
    symbol = next(iter(symbols))
    week_start = next(iter(weeks))

    aggregate_rows = []
    firm_rows = []
    publication_dates = set()
    row_lags = []
    row_errors = []
    aggregate_products = []
    firm_mpids = []
    de_minimis = False
    aggregate_shares = aggregate_trades = 0
    firm_shares = firm_trades = 0
    numeric_bridge_valid = True

    for index, row in enumerate(materialized):
        typ = str(row.get("summaryTypeCode", "")).strip().upper()
        if typ not in ALLOWED_TYPES:
            row_errors.append(f"row_{index}:unsupported_summary_type")
            continue
        try:
            pub = _date(row.get("initialPublishedDate"), "initial_published_date")
            reported = _date(row.get("lastReportedDate"), "last_reported_date")
            updated = _date(row.get("lastUpdateDate"), "last_update_date")
            lag = (pub - week_start).days
            if lag not in ALLOWED_PUBLICATION_LAGS:
                row_errors.append(f"row_{index}:publication_lag_outside_21_22")
            if updated != max(pub, reported):
                row_errors.append(f"row_{index}:last_update_semantics_mismatch")
            if reported > pub or updated != pub:
                row_errors.append(f"row_{index}:revised_row_quarantined")
            publication_dates.add(pub)
            row_lags.append(lag)
            shares = _integer(row.get("totalWeeklyShareQuantity"), "shares")
            trades = _integer(row.get("totalWeeklyTradeCount"), "trades")
        except ValueError as exc:
            row_errors.append(f"row_{index}:{exc}")
            continue

        if typ == "ATS_W_SMBL":
            product = str(row.get("productTypeCode", "")).strip().upper()
            if not product:
                row_errors.append(f"row_{index}:aggregate_product_type_missing")
            aggregate_products.append(product)
            aggregate_rows.append(row)
            aggregate_shares += shares
            aggregate_trades += trades
        else:
            firm_rows.append(row)
            firm_shares += shares
            firm_trades += trades
            mpid = str(row.get("atsMpid") or row.get("ATS_MPID") or row.get("marketParticipantId") or "").strip().upper()
            name = str(row.get("marketParticipantName", "")).strip().upper()
            if "DE MINIMIS" in name:
                de_minimis = True
            if not mpid:
                # A De Minimis bucket is deliberately not treated as a participant identity.
                firm_mpids.append("")
            else:
                firm_mpids.append(mpid)

    if not aggregate_rows:
        row_errors.append("aggregate_rows_missing")
    if len(aggregate_products) != len(set(aggregate_products)):
        row_errors.append("duplicate_aggregate_product_type")
    if len(publication_dates) != 1:
        row_errors.append("publication_date_mismatch")
    if not row_errors and not aggregate_rows:
        row_errors.append("aggregate_rows_missing")

    publication_date = next(iter(publication_dates)) if len(publication_dates) == 1 else None
    entry_session = next((s for s in calendar if publication_date is not None and s["session_date"] > publication_date), None)
    if publication_date is not None and entry_session is None:
        row_errors.append("no_future_executable_session")

    stable = not row_errors and publication_date is not None and bool(aggregate_rows)
    identity = _identity_for(symbol, week_start, entry_session["open_utc"] if entry_session else None, security_master_records) if stable else {"status": "not_evaluated"}
    bridge_reconciled = bool(aggregate_rows and firm_rows) and aggregate_shares == firm_shares and aggregate_trades == firm_trades
    unique_mpid = bool(firm_mpids) and all(firm_mpids) and len(firm_mpids) == len(set(firm_mpids))
    concentration_eligible = stable and bridge_reconciled and unique_mpid and not de_minimis
    return {
        "symbol": symbol,
        "week_start_date": week_start.isoformat(),
        "publication_date": publication_date.isoformat() if publication_date else None,
        "publication_lag_days": row_lags[0] if row_lags and len(set(row_lags)) == 1 else None,
        "stable_row_pit_eligible": stable,
        "status": "stable_row_pit_candidate" if stable else "quarantined",
        "rejection_reasons": sorted(set(row_errors)),
        "first_executable_session": entry_session["session_date"].isoformat() if stable and entry_session else None,
        "security_identity": identity,
        "concentration_eligible": concentration_eligible,
        "bridge_reconciled": bridge_reconciled,
        "economic_test_eligible": False,
        "economic_test_blockers": [
            "effective_dated_security_identity_not_certified_for_real_universe",
            "historical_universe_membership_not_supplied",
            "complete_total_return_and_delisting_coverage_not_supplied",
            "no_raw_source_vintage_or_live_first_receipt_attached",
        ],
        "signal_admitted": False,
    }
