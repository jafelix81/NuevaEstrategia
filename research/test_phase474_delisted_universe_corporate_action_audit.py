import unittest
from decimal import Decimal

from research.phase474_delisted_universe_corporate_action_audit import (
    EXPECTED_TICKERS,
    load_ledger,
    terminal_consideration_per_old_share,
    validate_ledger,
)


class Phase474CorporateActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = load_ledger()
        cls.rows = {row["ticker"]: row for row in cls.ledger["actions"]}

    def test_exact_seven_missing_tickers_are_adjudicated(self):
        self.assertEqual(set(self.rows), EXPECTED_TICKERS)
        self.assertEqual(len(self.rows), 7)

    def test_ledger_passes_fail_closed_validation(self):
        self.assertEqual(validate_ledger(self.ledger), [])

    def test_cash_only_terminal_consideration(self):
        self.assertEqual(terminal_consideration_per_old_share(self.rows["EA"]), Decimal("210"))
        self.assertEqual(terminal_consideration_per_old_share(self.rows["LPRO"]), Decimal("3.15"))
        self.assertEqual(terminal_consideration_per_old_share(self.rows["WBD"]), Decimal("31.01666668"))

    def test_stock_consideration_requires_successor_price(self):
        for ticker in ("AVB", "EQR", "ROKU", "WBS"):
            self.assertIsNone(terminal_consideration_per_old_share(self.rows[ticker]))

    def test_avb_exchange_ratio(self):
        value = terminal_consideration_per_old_share(self.rows["AVB"], "100")
        self.assertEqual(value, Decimal("279.3"))

    def test_roku_uses_closing_adjusted_terms_not_earlier_announcement(self):
        c = self.rows["ROKU"]["consideration"]
        self.assertEqual(c["successor_shares_per_old_share"], 0.9799)
        self.assertEqual(c["cash_per_old_share"], 95.30)
        self.assertIn("after adjustment", c["adjustment_note"])

    def test_webster_mixed_consideration(self):
        value = terminal_consideration_per_old_share(self.rows["WBS"], "100")
        self.assertEqual(value, Decimal("254.23"))

    def test_no_historical_prices_or_signals_are_admitted(self):
        self.assertFalse(self.ledger["adjudication"]["fallback_price_series_admitted"])
        self.assertFalse(self.ledger["adjudication"]["terminal_returns_reconstructed"])
        self.assertFalse(self.ledger["adjudication"]["alpha_test_authorized"])
        self.assertFalse(self.ledger["adjudication"]["oos_authorized"])


if __name__ == "__main__":
    unittest.main()
