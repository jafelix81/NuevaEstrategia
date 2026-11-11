"""Phase 262: Databento Security Master temporal and identity eligibility gates.

Documentation-only contract. No Databento API request or credential is used.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
AUTHORIZED_SCOPE = "authorized_internal_research"


def parse_utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}: missing timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field}: invalid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field}: timezone-aware UTC timestamp required")
    if parsed.utcoffset().total_seconds() != 0:
        raise ValueError(f"{field}: timestamp must be UTC")
    return parsed


def assess_pit_record(
    record: dict[str, Any],
    decision_time: str,
    *,
    first_observed_at: str | None,
    raw_sha256: str | None,
    license_scope: str | None,
) -> dict[str, Any]:
    """Fail-closed PIT gate; vendor clocks alone never prove customer availability."""
    decision = parse_utc(decision_time, "decision_time")
    reasons: list[str] = []
    parsed: dict[str, datetime] = {}
    for field in ("ts_effective", "ts_record", "ts_created"):
        try:
            parsed[field] = parse_utc(record.get(field), field)
        except ValueError as exc:
            reasons.append(str(exc))

    if "ts_effective" in parsed and parsed["ts_effective"] > decision:
        reasons.append("NOT_YET_EFFECTIVE_AT_DECISION")
    if "ts_record" in parsed and parsed["ts_record"] > decision:
        reasons.append("RECORD_LAST_CHANGED_AFTER_DECISION")
    if "ts_created" in parsed and parsed["ts_created"] > decision:
        reasons.append("ADDED_TO_DATABASE_AFTER_DECISION")

    observed = None
    if first_observed_at is None:
        reasons.append("FIRST_CUSTOMER_AVAILABILITY_UNPROVEN")
    else:
        try:
            observed = parse_utc(first_observed_at, "first_observed_at")
            if observed > decision:
                reasons.append("FIRST_CAPTURE_AFTER_DECISION")
            if "ts_created" in parsed and observed < parsed["ts_created"]:
                reasons.append("CAPTURE_PRECEDES_DATABASE_INGESTION")
            if "ts_record" in parsed and observed < parsed["ts_record"]:
                reasons.append("CAPTURE_PRECEDES_RECORDED_CHANGE")
        except ValueError as exc:
            reasons.append(str(exc))

    if not isinstance(raw_sha256, str) or not HEX64.fullmatch(raw_sha256):
        reasons.append("IMMUTABLE_RAW_SHA256_REQUIRED")
    if license_scope != AUTHORIZED_SCOPE:
        reasons.append("AUTHORIZED_INTERNAL_RESEARCH_LICENSE_REQUIRED")

    return {
        "strict_pit_eligible": not reasons,
        "decision_time": decision.isoformat(),
        "first_observed_at": observed.isoformat() if observed else None,
        "reasons": reasons,
        "clock_semantics": {
            "ts_effective": "vendor-reported validity start; not customer availability",
            "ts_record": "vendor-reported last-change time; not proven first publication",
            "ts_created": "record added to vendor database; not proven customer API availability",
            "first_observed_at": "our own immutable first successful receipt timestamp",
        },
    }


def identity_key(record: dict[str, Any], level: str) -> str:
    """Require the identifier at the requested entity level; never fall back to ticker."""
    fields = {"listing": "listing_id", "security": "security_id", "issuer": "issuer_id"}
    if level not in fields:
        raise ValueError("level must be listing, security, or issuer; ticker is not an identity level")
    value = record.get(fields[level])
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{fields[level]} required for {level}-level join")
    return value.strip()


def is_us_common_equity(record: dict[str, Any]) -> bool:
    """Conservative candidate filter; does not establish universe completeness."""
    country = record.get("listing_country")
    security_type = record.get("security_type")
    return country == "US" and security_type == "EQS"


def build_audit_result() -> dict[str, Any]:
    return {
        "phase": 262,
        "status": "DATABENTO_SECURITY_MASTER_CONDITIONAL_IDENTITY_SOURCE_PIT_NOT_ADMITTED",
        "source": {
            "provider": "Databento",
            "product": "Security Master",
            "documented_history_start": "2005-01-01",
            "documented_universe": "860,000+ listed and delisted securities",
            "documented_exchange_coverage": "220+ global exchanges",
            "listing_level_records": True,
            "per_date_us_common_equity_coverage_measured": False,
            "frozen_universe_coverage_measured": False,
            "delisted_security_sample_verified": False,
        },
        "clock_adjudication": {
            "ts_effective": "validity start; not customer availability",
            "ts_record": "last changed; not proven first publication",
            "ts_created": "added to vendor database; not proven first customer API availability",
            "strict_pit_rule": "require vendor clocks not after decision AND our own first-observed timestamp not after decision AND immutable raw-byte SHA-256 AND authorized license scope",
            "documented_aapl_example": {
                "ts_effective": "2004-11-19T00:00:00Z",
                "ts_record": "2004-12-06T15:09:30Z",
                "ts_created": "2024-11-11T22:41:24.780487Z",
                "consequence": "historical effective/record dates do not establish availability in 2005",
            },
        },
        "documentation_conflicts": {
            "dataset_spec_update_frequency": "once per week",
            "product_page_update_frequency": "four times daily",
            "cadence_adjudicated": False,
            "action": "do not assume a deterministic historical or prospective update schedule until clarified",
        },
        "identity_rules": {
            "listing_id": "listing-level identity",
            "security_id": "security identity across listings",
            "issuer_id": "issuer identity across securities",
            "ticker_only_join": False,
            "preferred_external_crosswalks": ["ISIN", "US CUSIP", "FIGI"],
            "known_nasdaq_symbol_suffix_issue": "USNYSE class-share suffix normalization can lose delimiters; do not fuzzy-normalize",
            "continuity_caveat": "do not infer continuity across spin-offs or never-relisted delistings",
            "common_equity_filter": "listing_country=US and security_type=EQS; ETFs remain separate",
        },
        "licensing": {
            "account_or_api_key_obtained": False,
            "api_request_made": False,
            "trial_opened": False,
            "purchase_or_contact": False,
            "authorized_internal_research_scope_verified": False,
            "public_redistribution_permitted": False,
        },
        "decision": {
            "identity_reference_candidate": True,
            "strict_pit_admitted": False,
            "universe_admitted": False,
            "adv20_source": False,
            "feature_admitted": False,
            "alpha_test_authorized": False,
            "return_test_run": False,
            "bootstrap_loo_oos_run": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(build_audit_result(), indent=2, sort_keys=True))
