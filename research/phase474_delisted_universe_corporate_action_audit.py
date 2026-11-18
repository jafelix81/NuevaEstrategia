"""Phase 474: validate corporate-action metadata for seven inactive Phase 20C symbols.

No market prices are downloaded or retained. The module only validates the
evidence ledger and provides a transparent per-old-share consideration formula.
"""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

LEDGER_PATH = Path(__file__).with_name("phase474_delisted_universe_corporate_action_ledger.json")
EXPECTED_TICKERS = {"AVB", "EA", "EQR", "LPRO", "ROKU", "WBD", "WBS"}


def load_ledger() -> dict[str, Any]:
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def validate_ledger(ledger: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = ledger.get("actions", [])
    tickers = [row.get("ticker") for row in rows]
    if len(rows) != 7 or set(tickers) != EXPECTED_TICKERS or len(tickers) != len(set(tickers)):
        errors.append("corporate_action_ticker_set_mismatch")
    for row in rows:
        ticker = row.get("ticker", "<missing>")
        if row.get("status") not in {
            "merged_into_successor",
            "acquired_private_delisted",
            "issuer_name_and_ticker_change",
            "acquired_by_fox_delisted",
            "acquired_by_skydance_delisted",
            "acquired_by_santander_delisted",
        }:
            errors.append(f"{ticker}:invalid_status")
        if not row.get("closing_date"):
            errors.append(f"{ticker}:missing_closing_date")
        if not row.get("source_urls"):
            errors.append(f"{ticker}:missing_primary_source")
        c = row.get("consideration", {})
        if c.get("cash_per_old_share") is None or c.get("successor_shares_per_old_share") is None:
            errors.append(f"{ticker}:incomplete_consideration")
        if row.get("signal_eligible") is not False:
            errors.append(f"{ticker}:must_remain_signal_ineligible")
        if row.get("price_reconstruction") != "required":
            errors.append(f"{ticker}:price_reconstruction_gate_missing")
    adjudication = ledger.get("adjudication", {})
    for key in ("universe_may_be_reduced", "historical_delisted_rows_may_be_dropped",
                "fallback_price_series_admitted", "terminal_returns_reconstructed",
                "alpha_test_authorized", "oos_authorized", "f80_changed", "production_changed"):
        if adjudication.get(key) is not False:
            errors.append(f"adjudication:{key}_must_be_false")
    return errors


def terminal_consideration_per_old_share(row: dict[str, Any], successor_price: str | None = None) -> Decimal | None:
    """Return contractual cash plus successor shares valued at supplied price.

    For stock consideration, successor_price is mandatory. This does not include
    fractional-share cash-in-lieu, dividends, withholding, or execution costs.
    It is a transparent building block, not a total-return label.
    """
    c = row["consideration"]
    cash = Decimal(str(c["cash_per_old_share"]))
    shares = Decimal(str(c["successor_shares_per_old_share"]))
    if shares == 0:
        return cash
    if successor_price is None:
        return None
    return cash + shares * Decimal(str(successor_price))


def main() -> int:
    ledger = load_ledger()
    errors = validate_ledger(ledger)
    print(f"PHASE474_ACTIONS={len(ledger.get('actions', []))}")
    print(f"PHASE474_VALIDATION={'PASS' if not errors else 'FAIL'}")
    for error in errors:
        print("ERROR=" + error)
    print("RAW_PRICES_RETAINED=False")
    print("TERMINAL_RETURNS_RECONSTRUCTED=False")
    print("ALPHA_TEST_AUTHORIZED=False")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
