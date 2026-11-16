"""Phase 436: fail-closed normalization of heterogeneous SEC Item 408 plan disclosures.

The casebook is a purposive six-issuer schema/semantics stress sample. This
module counts actions and classifies direction/basis; it deliberately never
sums heterogeneous amounts or infers trading alpha.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

CASEBOOK_PATH = Path(__file__).with_name(
    "PHASE436_ITEM408_CROSS_ISSUER_SEMANTICS_CASEBOOK_2026-11-16.json"
)
ACTIONS = {"adopt", "modify", "terminate"}
DIRECTIONS = {"buy", "sell", "exercise_and_sell", "unknown"}
UNITS = {"shares", "USD"}


def _iso_date(value: str) -> date:
    return date.fromisoformat(value)


def _validate_amount(value: str, unit: str) -> None:
    if unit not in UNITS:
        raise ValueError(f"unsupported amount unit: {unit}")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {value!r}") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"amount must be finite and non-negative: {value!r}")


def load_casebook() -> dict[str, Any]:
    return json.loads(CASEBOOK_PATH.read_text(encoding="utf-8"))


def audit_casebook(casebook: dict[str, Any] | None = None) -> dict[str, Any]:
    casebook = casebook or load_casebook()
    issuers = casebook["issuers"]
    action_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
    seen_plan_ids: set[str] = set()

    for issuer in issuers:
        if len(issuer["cik"]) != 10 or not issuer["cik"].isdigit():
            raise ValueError(f"issuer CIK must be 10 digits: {issuer['cik']}")
        if not issuer["ticker"] or not issuer["accession"]:
            raise ValueError("ticker and accession are required")

        filed = _iso_date(issuer["filed_date"])
        accepted = datetime.fromisoformat(issuer["accepted_eastern"])
        if accepted.date() != filed:
            raise ValueError("acceptance date must match the SEC filing date")
        if accepted.utcoffset() is None:
            raise ValueError("acceptance timestamp must be timezone-aware")
        first_eligible = _iso_date(issuer["first_eligible_session"])
        if first_eligible <= filed:
            raise ValueError("first eligible session must be after filing date")

        for plan in issuer["plans"]:
            if plan["plan_id"] in seen_plan_ids:
                raise ValueError(f"duplicate plan/action id: {plan['plan_id']}")
            seen_plan_ids.add(plan["plan_id"])
            if plan["action"] not in ACTIONS:
                raise ValueError(f"unknown lifecycle action: {plan['action']}")
            if plan["direction"] not in DIRECTIONS:
                raise ValueError(f"unknown direction class: {plan['direction']}")
            _validate_amount(plan["amount_value"], plan["amount_unit"])
            if plan["action"] == "terminate" and not plan.get("termination_date"):
                raise ValueError("termination action requires termination_date")
            if plan["action"] != "terminate" and plan.get("termination_date"):
                raise ValueError("termination_date must not be attached to a non-termination action")
            if plan.get("adoption_date") and _iso_date(plan["adoption_date"]) > filed:
                raise ValueError("adoption date cannot be after the disclosure filing date")
            if plan.get("scheduled_start_date") and _iso_date(plan["scheduled_start_date"]) < filed:
                # A disclosed plan window may begin before the public filing;
                # preserve it, but never make it the public signal date.
                pass
            action_rows.append((issuer, plan))

    action_counts = Counter(plan["action"] for _, plan in action_rows)
    direction_counts = Counter(plan["direction"] for _, plan in action_rows)
    unit_counts = Counter(plan["amount_unit"] for _, plan in action_rows)
    nonstandard_basis_count = sum(
        plan["amount_basis"] != "stated_share_ceiling"
        for _, plan in action_rows if plan["amount_unit"] == "shares"
    )
    explicit_window_count = sum(
        bool(plan.get("scheduled_start_date"))
        for _, plan in action_rows
    )

    return {
        "issuer_count": len(issuers),
        "filing_count": len({issuer["accession"] for issuer in issuers}),
        "plan_action_count": len(action_rows),
        "action_counts": dict(sorted(action_counts.items())),
        "direction_counts": dict(sorted(direction_counts.items())),
        "amount_unit_counts": dict(sorted(unit_counts.items())),
        "share_amount_records_not_comparable_to_plain_ceiling": nonstandard_basis_count,
        "actions_with_explicit_scheduled_start_date": explicit_window_count,
        "unknown_direction_plan_ids": [
            plan["plan_id"] for _, plan in action_rows if plan["direction"] == "unknown"
        ],
        "purchase_plan_ids": [
            plan["plan_id"] for _, plan in action_rows if plan["direction"] == "buy"
        ],
        "exercise_and_sell_plan_ids": [
            plan["plan_id"] for _, plan in action_rows if plan["direction"] == "exercise_and_sell"
        ],
        "termination_plan_ids": [
            plan["plan_id"] for _, plan in action_rows if plan["action"] == "terminate"
        ],
        "amounts_aggregated_across_plans": False,
        "direction_inferred_from_amount_only": False,
        "first_eligible_session_policy": "next regular session after filing date",
        "first_public_receipt_certified": False,
        "alpha_test": "NOT_RUN",
        "signal_admission": "NOT_ADMITTED",
        "population_coverage": "NOT_ESTABLISHED",
        "frozen_baseline_changed": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit_casebook(), indent=2, sort_keys=True))
