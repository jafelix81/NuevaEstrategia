"""Phase 434: reconcile Item 408 plans with Form 4 plan-linked S-coded rows.

This is a source-semantics and timestamp audit, not a legal opinion or alpha test.
It deliberately preserves form-level AFF10B5ONE separately from row-level plan
footnote linkage and never infers legal compliance from either field.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

CASEBOOK_PATH = Path(__file__).with_name("PHASE434_ITEM408_FORM4_CASES_2026-11-16.json")


def _d(value: str) -> date:
    return date.fromisoformat(value)


def add_weekday_business_days(start: date, count: int) -> date:
    """Add weekdays for this fixed sample; no federal holiday falls in its windows."""
    current = start
    completed = 0
    while completed < count:
        current += timedelta(days=1)
        if current.weekday() < 5:
            completed += 1
    return current


def next_weekday_session(after: date) -> date:
    current = after
    while True:
        current += timedelta(days=1)
        if current.weekday() < 5:
            return current


def cooling_off_dates(adoption_date: str, periodic_filing_date: str) -> dict[str, str]:
    """Date-only application of the 90-day / 2-business-day / 120-day rule.

    The returned first_session_after_threshold is conservative: it is the next
    weekday after the later/capped threshold date. This helper is only used for
    the stated NOW 2023 sample dates and is not a general holiday calendar.
    """
    adopted = _d(adoption_date)
    filed = _d(periodic_filing_date)
    ninety_day_date = adopted + timedelta(days=90)
    two_business_days_after_filing = add_weekday_business_days(filed, 2)
    maximum_date = adopted + timedelta(days=120)
    threshold = min(max(ninety_day_date, two_business_days_after_filing), maximum_date)
    first_session = next_weekday_session(threshold)
    return {
        "ninety_day_date": ninety_day_date.isoformat(),
        "two_business_days_after_filing": two_business_days_after_filing.isoformat(),
        "maximum_date": maximum_date.isoformat(),
        "threshold_date": threshold.isoformat(),
        "first_session_after_threshold": first_session.isoformat(),
    }


def load_casebook() -> dict[str, Any]:
    return json.loads(CASEBOOK_PATH.read_text(encoding="utf-8"))


def analyze_casebook(casebook: dict[str, Any] | None = None) -> dict[str, Any]:
    casebook = casebook or load_casebook()
    item_filing_date = casebook["item408_filing"]["official_filing_date"]
    cases: list[dict[str, Any]] = []

    for plan in casebook["plans"]:
        item_adoption = plan["item408_adoption_date"]
        form4_adoption = plan.get("form4_footnote_adoption_date") or item_adoption
        item_rule = cooling_off_dates(item_adoption, item_filing_date)
        form4_rule = cooling_off_dates(form4_adoption, item_filing_date)
        discrepancy_days = (_d(form4_adoption) - _d(item_adoption)).days

        grouped: dict[tuple[str, str], list[tuple[dict[str, Any], dict[str, Any]]]] = {}
        for record in plan["form4_records"]:
            for transaction in record["transactions"]:
                # Form-level AFF10B5ONE is retained as metadata. A row is linked
                # to a plan here only when its own footnote is explicitly mapped.
                if transaction.get("code") != "S" or not transaction.get("plan_footnote"):
                    continue
                key = (record["accession"], transaction["date"])
                grouped.setdefault(key, []).append((record, transaction))

        sales: list[dict[str, Any]] = []
        for (accession, trade_date), rows in sorted(grouped.items(), key=lambda x: (x[0][1], x[0][0])):
            record = rows[0][0]
            quantities = [tx.get("shares") for _, tx in rows]
            quantity = sum(quantities) if quantities and all(q is not None for q in quantities) else None
            trade = _d(trade_date)
            sales.append({
                "accession": accession,
                "transaction_date": trade_date,
                "transaction_code": "S",
                "row_count": len(rows),
                "shares_total": quantity,
                "price_per_share_values": [tx.get("price") for _, tx in rows],
                "footnote_ids": sorted({tx.get("footnote_id") for _, tx in rows if tx.get("footnote_id")}),
                "form4_aff10b5one": record.get("aff10b5one"),
                "source_url": record.get("source_url"),
                "before_item408_threshold": trade < _d(item_rule["threshold_date"]),
                "before_form4_footnote_threshold": trade < _d(form4_rule["threshold_date"]),
                "before_item408_filing_date": trade < _d(item_filing_date),
                "days_from_item408_filing_to_trade": (trade - _d(item_filing_date)).days,
            })

        first_sale_date = min((s["transaction_date"] for s in sales), default=None)
        cases.append({
            "insider": plan["insider"],
            "insider_cik": plan["insider_cik"],
            "item408_adoption_date": item_adoption,
            "form4_footnote_adoption_date": form4_adoption,
            "plan_date_discrepancy_days_form4_minus_item408": discrepancy_days,
            "item408_expiration_date": plan.get("item408_expiration_date"),
            "item408_plan_description": plan["item408_plan_description"],
            "cooling_off_using_item408_date": item_rule,
            "cooling_off_using_form4_footnote_date": form4_rule,
            "observed_plan_linked_s_sales": sales,
            "first_observed_plan_linked_s_sale_date": first_sale_date,
            "item408_filing_lead_days_to_first_observed_sale": (
                (_d(first_sale_date) - _d(item_filing_date)).days if first_sale_date else None
            ),
            "item408_precedes_first_observed_sale": (
                _d(item_filing_date) < _d(first_sale_date) if first_sale_date else None
            ),
            "has_sale_before_item408_calculated_threshold": any(s["before_item408_threshold"] for s in sales),
            "has_sale_before_form4_footnote_calculated_threshold": any(
                s["before_form4_footnote_threshold"] for s in sales
            ),
            "legal_conclusion": "not_assessed",
        })

    summary = {
        "plan_count": len(cases),
        "plans_with_item408_vs_form4_adoption_date_mismatch": sum(
            c["plan_date_discrepancy_days_form4_minus_item408"] != 0 for c in cases
        ),
        "plans_with_observed_s_sale_before_item408_filing": sum(
            any(s["before_item408_filing_date"] for s in c["observed_plan_linked_s_sales"]) for c in cases
        ),
        "plans_with_observed_s_sale_before_item408_calculated_threshold": sum(
            c["has_sale_before_item408_calculated_threshold"] for c in cases
        ),
        "plans_with_item408_filing_before_first_observed_s_sale": sum(
            c["item408_precedes_first_observed_sale"] is True for c in cases
        ),
        "alpha_test": "NOT_RUN",
        "legal_compliance_assessment": "NOT_ASSESSED",
    }
    return {
        "schema_version": 1,
        "issuer": casebook["issuer"],
        "item408_filing": casebook["item408_filing"],
        "rule_reference": casebook["rule_reference"],
        "summary": summary,
        "cases": cases,
        "interpretation_limits": casebook["interpretation_limits"],
    }


if __name__ == "__main__":
    print(json.dumps(analyze_casebook(), indent=2, sort_keys=True))
