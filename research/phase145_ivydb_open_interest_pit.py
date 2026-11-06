#!/usr/bin/env python3
"""Phase 145: point-in-time safeguards for contract-level options open interest.

This helper accepts normalized IvyDB-like rows only after an exact,
date-effective mapping from the morning Open_Interest file to OptionID.
It deliberately treats open interest as contract state, never buyer direction.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any, Iterable, Mapping

REQUIRED = {
    "security_id",
    "option_id",
    "session_date",
    "previous_session_date",
    "open_interest",
    "volume",
    "expiration_date",
    "contract_terms_key",
    "first_received_at",
    "source_file_hash",
    "source_version",
}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _date(value: Any, field: str, *, allow_blank: bool = False) -> date | None:
    raw = _text(value)
    if not raw and allow_blank:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_date:{field}") from exc


def _timestamp(value: Any) -> datetime:
    raw = _text(value)
    if not raw:
        raise ValueError("first_received_at_missing")
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("first_received_at_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("first_received_at_must_be_timezone_aware")
    return parsed


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"invalid_integer:{field}")
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_integer:{field}") from exc
    if str(value).strip() not in {str(number), f"{number}.0"} or number < 0:
        raise ValueError(f"invalid_integer:{field}")
    return number


def build_oi_features(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Build consecutive-session OI state changes using actual first receipt.

    session_date is the trading session whose clearing state the OI represents.
    first_received_at is the actual timestamp the immutable source file arrived,
    not a scheduled vendor SLA. previous_session_date must come from an
    exchange calendar. Contract terms must be unchanged across the pair.
    """
    parsed_rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, date]] = set()

    for raw in rows:
        missing = REQUIRED - set(raw)
        if missing:
            raise ValueError("missing_required_fields:" + ",".join(sorted(missing)))

        security_id = _text(raw.get("security_id"))
        option_id = _text(raw.get("option_id"))
        terms = _text(raw.get("contract_terms_key"))
        source_hash = _text(raw.get("source_file_hash"))
        source_version = _text(raw.get("source_version"))
        if not security_id or not option_id or not terms:
            raise ValueError("contract_identity_or_terms_missing")
        if not source_hash or not source_version:
            raise ValueError("source_provenance_missing")

        session_date = _date(raw.get("session_date"), "session_date")
        previous_session_date = _date(
            raw.get("previous_session_date"), "previous_session_date", allow_blank=True
        )
        expiration_date = _date(raw.get("expiration_date"), "expiration_date")
        received_at = _timestamp(raw.get("first_received_at"))
        if received_at.date() <= session_date:
            raise ValueError("receipt_must_follow_activity_session")

        oi = _nonnegative_int(raw.get("open_interest"), "open_interest")
        volume = _nonnegative_int(raw.get("volume"), "volume")
        key = (security_id, option_id, session_date)
        if key in seen:
            raise ValueError("duplicate_contract_session")
        seen.add(key)

        parsed_rows.append(
            {
                "security_id": security_id,
                "option_id": option_id,
                "session_date": session_date,
                "previous_session_date": previous_session_date,
                "expiration_date": expiration_date,
                "open_interest": oi,
                "volume": volume,
                "contract_terms_key": terms,
                "first_received_at": received_at,
                "source_file_hash": source_hash,
                "source_version": source_version,
            }
        )

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in parsed_rows:
        groups[(row["security_id"], row["option_id"])].append(row)

    output: list[dict[str, Any]] = []
    for (security_id, option_id), group in sorted(groups.items()):
        group.sort(key=lambda row: row["session_date"])
        by_session = {row["session_date"]: row for row in group}

        for row in group:
            prior_date = row["previous_session_date"]
            prior = by_session.get(prior_date) if prior_date is not None else None
            status = "OK"
            delta_oi = None
            prior_oi = None

            if prior_date is None:
                status = "NO_PRIOR_SESSION"
            elif prior is None:
                status = "MISSING_PREVIOUS_SESSION"
            elif any(
                prior_date < candidate["session_date"] < row["session_date"]
                for candidate in group
            ):
                # A supplied prior date is not adjacent if an intervening
                # contract observation exists in the same input panel.
                status = "NON_ADJACENT_PREVIOUS_SESSION"
            elif prior["contract_terms_key"] != row["contract_terms_key"]:
                status = "CONTRACT_TERMS_BREAK"
            elif prior["expiration_date"] != row["expiration_date"]:
                status = "EXPIRATION_DATE_BREAK"
            elif row["expiration_date"] <= row["session_date"]:
                status = "EXPIRY_OR_EXERCISE_AFFECTED"
            elif row["first_received_at"] <= prior["first_received_at"]:
                status = "KNOWLEDGE_TIME_NOT_MONOTONIC"
            else:
                prior_oi = prior["open_interest"]
                delta_oi = row["open_interest"] - prior_oi

            volume = row["volume"]
            delta_to_volume = (
                delta_oi / volume if delta_oi is not None and volume > 0 else None
            )
            volume_to_prior_oi = (
                volume / prior_oi if prior_oi is not None and prior_oi > 0 else None
            )
            delta_fraction = (
                delta_oi / prior_oi if delta_oi is not None and prior_oi > 0 else None
            )

            output.append(
                {
                    "security_id": security_id,
                    "option_id": option_id,
                    "session_date": row["session_date"].isoformat(),
                    "previous_session_date": (
                        prior_date.isoformat() if prior_date is not None else None
                    ),
                    "open_interest": row["open_interest"],
                    "prior_open_interest": prior_oi,
                    "volume": volume,
                    "delta_open_interest": delta_oi,
                    "delta_oi_to_volume": delta_to_volume,
                    "delta_oi_fraction_prior": delta_fraction,
                    "volume_to_prior_oi": volume_to_prior_oi,
                    "status": status,
                    "knowledge_time": row["first_received_at"].isoformat(),
                    "source_file_hash": row["source_file_hash"],
                    "source_version": row["source_version"],
                    "directional_buyer_signal": False,
                }
            )

    return sorted(
        output,
        key=lambda item: (
            item["session_date"], item["security_id"], item["option_id"]
        ),
    )


def features_known_by(
    features: Iterable[Mapping[str, Any]], decision_time: str
) -> list[dict[str, Any]]:
    """Return only features whose actual receipt preceded the decision time."""
    decision = _timestamp(decision_time)
    result = []
    for feature in features:
        known = _timestamp(feature.get("knowledge_time"))
        # No event sequence is stored for equal timestamps. Fail closed:
        # knowledge must strictly precede the decision instant.
        if known < decision and feature.get("status") == "OK":
            result.append(dict(feature))
    return result
