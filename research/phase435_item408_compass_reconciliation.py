"""Phase 435: Item 408 plan-cap vs subsequent Form 4 / Form 144 reconciliation.

One-issuer descriptive audit only. No return or alpha inference.
"""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

CASEBOOK_PATH = Path(__file__).with_name("PHASE435_ITEM408_COMPASS_CASEBOOK_2026-11-16.json")


def _date(value: str) -> date:
    return date.fromisoformat(value)


def _pct(numerator: int, denominator: int) -> str:
    return str((Decimal(numerator) * Decimal("100") / Decimal(denominator)).quantize(Decimal("0.0001")))


def load_casebook() -> dict[str, Any]:
    return json.loads(CASEBOOK_PATH.read_text(encoding="utf-8"))


def analyze_casebook(casebook: dict[str, Any] | None = None) -> dict[str, Any]:
    casebook = casebook or load_casebook()
    plan = casebook["plan"]
    filing = casebook["item408_filing"]
    share_count = casebook["issuer_share_count"]
    sales = casebook["form144_reconciliation"]["sales"]

    direct = [row for row in sales if row["seller"] == "Robert Reffkin"]
    trust = [row for row in sales if row["seller"] == "2021 Reffkin Remainder Interest Trust"]
    total_shares = sum(int(row["shares"]) for row in sales)
    direct_shares = sum(int(row["shares"]) for row in direct)
    trust_shares = sum(int(row["shares"]) for row in trust)
    gross_proceeds = sum(int(row["gross_proceeds_usd"]) for row in sales)

    first_sale = min(row["date"] for row in sales)
    last_sale = max(row["date"] for row in sales)
    filed = filing["filed_date"]
    adopted = plan["adoption_date"]

    form4_rows = [
        transaction
        for record in casebook["form4_corroboration"]
        for transaction in record["transactions"]
    ]
    form4_shares = sum(int(row["shares"]) for row in form4_rows if row["code"] == "S")
    form4_filing_after_transaction = all(
        _date(record["filing_date"]) > max(_date(row["date"]) for row in record["transactions"])
        for record in casebook["form4_corroboration"]
    )

    sessions = casebook["post_filing_trading_sessions_through_first_sale"]
    first_sale_rank = sessions.index(first_sale) + 1 if first_sale in sessions else None
    intervening_sessions = [session for session in sessions if session < first_sale]

    cap = int(plan["maximum_shares"])
    outstanding = int(share_count["shares_outstanding"])
    return {
        "issuer": casebook["issuer"],
        "item408_filing_date": filed,
        "conservative_first_eligible_session": filing["conservative_first_eligible_session"],
        "plan_adoption_date": adopted,
        "adoption_to_public_filing_calendar_days": (_date(filed) - _date(adopted)).days,
        "first_reported_sale_date": first_sale,
        "last_reported_sale_date": last_sale,
        "public_filing_to_first_sale_calendar_days": (_date(first_sale) - _date(filed)).days,
        "full_intervening_trading_sessions": intervening_sessions,
        "first_sale_post_filing_session_rank": first_sale_rank,
        "form144_rows": len(sales),
        "direct_reffkin_shares": direct_shares,
        "trust_shares": trust_shares,
        "total_form144_reported_shares": total_shares,
        "form144_reported_gross_proceeds_usd": gross_proceeds,
        "plan_maximum_shares": cap,
        "observed_sales_as_pct_of_plan_maximum": _pct(total_shares, cap),
        "plan_maximum_as_pct_of_shares_outstanding": _pct(cap, outstanding),
        "observed_sales_as_pct_of_shares_outstanding": _pct(total_shares, outstanding),
        "unobserved_difference_vs_plan_ceiling_shares": cap - total_shares,
        "unobserved_difference_is_active_balance": False,
        "selected_form4_crosscheck_rows": len(form4_rows),
        "selected_form4_crosscheck_shares": form4_shares,
        "selected_form4_crosscheck_as_pct_of_form144_total": _pct(form4_shares, total_shares),
        "form4_filings_postdate_their_reported_transactions": form4_filing_after_transaction,
        "form4_crosschecks_are_added_to_form144_total": False,
        "alpha_test": "NOT_RUN",
        "signal_admission": "NOT_ADMITTED",
        "population_coverage": "NOT_ESTABLISHED",
    }


if __name__ == "__main__":
    print(json.dumps(analyze_casebook(), indent=2, sort_keys=True))
