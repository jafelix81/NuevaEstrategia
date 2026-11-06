#!/usr/bin/env python3
"""Receipt-aware immutable IvyDB OI correction vintages."""
from __future__ import annotations
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Iterable, Mapping

REQUIRED = {
    "security_id", "option_id", "session_date", "previous_session_date",
    "open_interest", "volume", "expiration_date", "contract_terms_key",
    "first_received_at", "source_file_hash", "source_version",
    "version_id", "version_kind", "supersedes_version_id", "operation",
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

def _timestamp(value: Any, field: str = "first_received_at") -> datetime:
    raw = _text(value)
    if not raw:
        raise ValueError(f"{field}_missing")
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field}_must_be_timezone_aware")
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

def _parse_version(raw: Mapping[str, Any]) -> dict[str, Any]:
    missing = REQUIRED - set(raw)
    if missing:
        raise ValueError("missing_required_fields:" + ",".join(sorted(missing)))
    security_id, option_id = _text(raw.get("security_id")), _text(raw.get("option_id"))
    terms = _text(raw.get("contract_terms_key"))
    source_hash, source_version = _text(raw.get("source_file_hash")), _text(raw.get("source_version"))
    version_id = _text(raw.get("version_id"))
    kind, operation = _text(raw.get("version_kind")).lower(), _text(raw.get("operation")).lower()
    supersedes = _text(raw.get("supersedes_version_id"))
    if not security_id or not option_id or not terms:
        raise ValueError("contract_identity_or_terms_missing")
    if not source_hash or not source_version or not version_id:
        raise ValueError("source_or_version_provenance_missing")
    if kind not in {"initial", "correction"}:
        raise ValueError("invalid_version_kind")
    if operation not in {"upsert", "delete"}:
        raise ValueError("invalid_operation")
    if kind == "initial" and supersedes:
        raise ValueError("initial_version_cannot_supersede")
    if kind == "correction" and not supersedes:
        raise ValueError("correction_missing_supersedes")
    if kind == "initial" and operation == "delete":
        raise ValueError("initial_version_cannot_be_delete")
    session_date = _date(raw.get("session_date"), "session_date")
    previous_session_date = _date(raw.get("previous_session_date"), "previous_session_date", allow_blank=True)
    expiration_date = _date(raw.get("expiration_date"), "expiration_date")
    received_at = _timestamp(raw.get("first_received_at"))
    if received_at.date() <= session_date:
        raise ValueError("receipt_must_follow_activity_session")
    if operation == "upsert":
        oi = _nonnegative_int(raw.get("open_interest"), "open_interest")
        volume = _nonnegative_int(raw.get("volume"), "volume")
    else:
        oi = volume = None
    return {
        "security_id": security_id, "option_id": option_id,
        "session_date": session_date, "previous_session_date": previous_session_date,
        "expiration_date": expiration_date, "open_interest": oi, "volume": volume,
        "contract_terms_key": terms, "first_received_at": received_at,
        "source_file_hash": source_hash, "source_version": source_version,
        "version_id": version_id, "version_kind": kind,
        "supersedes_version_id": supersedes or None, "operation": operation,
    }

def _validate_ledger(rows: Iterable[Mapping[str, Any]]):
    groups: dict[tuple[str, str, date], list[dict[str, Any]]] = defaultdict(list)
    seen_ids: set[str] = set()
    for raw in rows:
        row = _parse_version(raw)
        if row["version_id"] in seen_ids:
            raise ValueError("duplicate_version_id")
        seen_ids.add(row["version_id"])
        groups[(row["security_id"], row["option_id"], row["session_date"])].append(row)
    session_dates: dict[tuple[str, str], set[date]] = defaultdict(set)
    for (security_id, option_id, session_date), chain in groups.items():
        session_dates[(security_id, option_id)].add(session_date)
        chain.sort(key=lambda item: item["first_received_at"])
        if chain[0]["version_kind"] != "initial":
            raise ValueError("vintage_chain_missing_initial")
        if sum(x["version_kind"] == "initial" for x in chain) != 1:
            raise ValueError("multiple_initial_versions")
        seen_hashes: set[str] = set()
        previous = None
        previous_time = None
        for item in chain:
            if item["source_file_hash"] in seen_hashes:
                raise ValueError("duplicate_source_hash_in_chain")
            seen_hashes.add(item["source_file_hash"])
            received = item["first_received_at"]
            if previous_time is not None and received <= previous_time:
                raise ValueError("ambiguous_or_nonmonotonic_vintage_time")
            if previous is None:
                if item["version_kind"] != "initial" or item["supersedes_version_id"]:
                    raise ValueError("invalid_initial_vintage")
            else:
                if item["version_kind"] != "correction":
                    raise ValueError("noninitial_vintage_must_be_correction")
                if item["supersedes_version_id"] != previous["version_id"]:
                    raise ValueError("correction_chain_mismatch")
            previous, previous_time = item, received
    return groups, session_dates

def select_vintages_asof(rows: Iterable[Mapping[str, Any]], decision_time: str) -> list[dict[str, Any]]:
    """Select latest immutable row version with receipt strictly before decision."""
    decision = _timestamp(decision_time, "decision_time")
    groups, _ = _validate_ledger(rows)
    selected = []
    for _, chain in sorted(groups.items(), key=lambda item: item[0]):
        known = [item for item in chain if item["first_received_at"] < decision]
        if not known:
            continue
        chosen = dict(known[-1])
        chosen["knowledge_time"] = chosen["first_received_at"].isoformat()
        chosen["correction_count"] = sum(x["version_kind"] == "correction" for x in known)
        chosen["vintage_count_known"] = len(known)
        chosen["asof_decision_time"] = decision.isoformat()
        chosen["status"] = "WITHDRAWN" if chosen["operation"] == "delete" else "OK"
        selected.append(chosen)
    return sorted(selected, key=lambda x: (x["session_date"], x["security_id"], x["option_id"]))

def build_oi_features_asof(rows: Iterable[Mapping[str, Any]], decision_time: str) -> list[dict[str, Any]]:
    """Build OI deltas from current/prior vintages known at one decision instant."""
    ledger = list(rows)
    decision = _timestamp(decision_time, "decision_time")
    groups, all_session_dates = _validate_ledger(ledger)
    selected = select_vintages_asof(ledger, decision.isoformat())
    by_key = {(x["security_id"], x["option_id"], x["session_date"]): x for x in selected}
    output = []
    for current in selected:
        security_id, option_id = current["security_id"], current["option_id"]
        session_date, prior_date = current["session_date"], current["previous_session_date"]
        status, prior, delta_oi, prior_oi = "OK", None, None, None
        if current["operation"] == "delete":
            status = "CURRENT_VINTAGE_WITHDRAWN"
        elif prior_date is None:
            status = "NO_PRIOR_SESSION"
        else:
            prior_key = (security_id, option_id, prior_date)
            prior = by_key.get(prior_key)
            if prior is None:
                status = "PRIOR_NOT_YET_KNOWN" if prior_key in groups else "MISSING_PREVIOUS_SESSION"
            elif prior["operation"] == "delete":
                status = "PRIOR_VINTAGE_WITHDRAWN"
            elif any(prior_date < d < session_date for d in all_session_dates[(security_id, option_id)]):
                status = "NON_ADJACENT_PREVIOUS_SESSION"
            elif current["expiration_date"] <= session_date:
                status = "EXPIRY_OR_EXERCISE_AFFECTED"
            elif prior["expiration_date"] != current["expiration_date"]:
                status = "EXPIRATION_DATE_BREAK"
            elif prior["contract_terms_key"] != current["contract_terms_key"]:
                status = "CONTRACT_TERMS_BREAK"
            elif prior["source_version"] != current["source_version"]:
                status = "SOURCE_VERSION_BREAK"
            else:
                prior_oi = prior["open_interest"]
                delta_oi = current["open_interest"] - prior_oi
        used_receipts = [current["first_received_at"]]
        if prior is not None:
            used_receipts.append(prior["first_received_at"])
        knowledge_time = max(used_receipts)
        if not knowledge_time < decision:
            raise AssertionError("asof_knowledge_time_not_strictly_before_decision")
        volume = current["volume"]
        output.append({
            "security_id": security_id, "option_id": option_id,
            "session_date": session_date.isoformat(),
            "previous_session_date": prior_date.isoformat() if prior_date else None,
            "open_interest": current["open_interest"], "prior_open_interest": prior_oi,
            "volume": volume, "delta_open_interest": delta_oi,
            "delta_oi_fraction_prior": delta_oi / prior_oi if delta_oi is not None and prior_oi > 0 else None,
            "delta_oi_to_volume": delta_oi / volume if delta_oi is not None and volume > 0 else None,
            "volume_to_prior_oi": volume / prior_oi if prior_oi is not None and prior_oi > 0 else None,
            "status": status, "knowledge_time": knowledge_time.isoformat(),
            "decision_time": decision.isoformat(),
            "current_version_id": current["version_id"],
            "prior_version_id": prior["version_id"] if prior else None,
            "current_source_file_hash": current["source_file_hash"],
            "prior_source_file_hash": prior["source_file_hash"] if prior else None,
            "current_source_version": current["source_version"],
            "prior_source_version": prior["source_version"] if prior else None,
            "current_correction_count": current["correction_count"],
            "prior_correction_count": prior["correction_count"] if prior else None,
            "directional_buyer_signal": False,
        })
    return sorted(output, key=lambda x: (x["session_date"], x["security_id"], x["option_id"]))
