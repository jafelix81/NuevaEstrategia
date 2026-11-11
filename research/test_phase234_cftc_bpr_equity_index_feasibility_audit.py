import unittest

from research.phase234_cftc_bpr_equity_index_feasibility_audit import (
    BankRow, aggregate_contract, build_audit, parse_bank_row
)

class Phase234Tests(unittest.TestCase):
    def test_us_row_parses(self):
        row = parse_bank_row(
            "CME E-MINI S&P 500 | U.S. | 7 | 39,925 | 2.0 | 71,568 | 3.6 | 1,986,532",
            "US",
        )
        self.assertEqual(row.bank_count, 7)
        self.assertEqual(row.long_positions, 39925)
        self.assertEqual(row.short_positions, 71568)
        self.assertEqual(row.open_interest, 1986532)

    def test_non_us_row_parses_without_oi(self):
        row = parse_bank_row(
            "NON U.S. | 19 | 15,383 | 0.8 | 273,885 | 13.8 |",
            "NON_US",
        )
        self.assertEqual(row.bank_count, 19)
        self.assertEqual(row.open_interest, None)

    def test_suppressed_bank_count_is_unknown_not_zero(self):
        row = parse_bank_row(
            "CME E-MINI S&P 400 STOCK INDEX | U.S. | | 2,213 | 4.5 | 0 | 0.0 | 48,725",
            "US",
        )
        self.assertIsNone(row.bank_count)

    def test_zero_position_is_preserved_as_zero(self):
        row = parse_bank_row(
            "CBT DJIA x $5 | U.S. | 4 | 0 | 0.0 | 1,865 | 2.1 | 87,410",
            "US",
        )
        self.assertEqual(row.long_positions, 0)

    def test_category_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_bank_row("NON U.S. | 19 | 1 | 1.0 | 2 | 2.0 |", "US")

    def test_aggregate_reconciles_and_computes_net(self):
        us = parse_bank_row(
            "CME E-MINI S&P 500 | U.S. | 7 | 39,925 | 2.0 | 71,568 | 3.6 | 1,986,532",
            "US",
        )
        non = parse_bank_row(
            "NON U.S. | 19 | 15,383 | 0.8 | 273,885 | 13.8 |",
            "NON_US",
        )
        out = aggregate_contract(us, non, {"bank_count": 26, "long_positions": 55308, "short_positions": 345453})
        self.assertEqual(out["net_long_minus_short"], -290145)
        self.assertAlmostEqual(out["net_to_open_interest"], -290145 / 1986532)

    def test_aggregate_mismatch_fails_closed(self):
        us = parse_bank_row("CME NASDAQ MINI | U.S. | 6 | 19,891 | 6.8 | 5,310 | 1.8 | 292,587", "US")
        non = parse_bank_row("NON U.S. | 15 | 6,753 | 2.3 | 18,858 | 6.4 |", "NON_US")
        with self.assertRaises(ValueError):
            aggregate_contract(us, non, {"bank_count": 21, "long_positions": 1, "short_positions": 24168})

    def test_oi_must_be_positive(self):
        us = BankRow("US", 5, 10, 1.0, 5, 0.5, 0)
        non = BankRow("NON_US", 5, 1, 0.1, 1, 0.1, None)
        with self.assertRaises(ValueError):
            aggregate_contract(us, non, {"bank_count": 10, "long_positions": 11, "short_positions": 6})

    def test_absent_market_is_not_zero(self):
        audit = build_audit()
        self.assertNotIn("CME VIX FUTURES", audit["sample_contracts"])
        self.assertTrue(audit["semantics"]["missing_market_is_unknown_not_zero"])

    def test_archive_limit_blocks_historical_alpha_admission(self):
        audit = build_audit()
        self.assertEqual(audit["archive_retention_months"], 25)
        self.assertFalse(audit["archive_long_history_gate"])
        self.assertFalse(audit["alpha_admission"])

    def test_first_receipt_missing_blocks_pit(self):
        audit = build_audit()
        self.assertIsNone(audit["first_receipt_timestamp"])
        self.assertFalse(audit["historical_pit_admission"])

    def test_stock_level_coverage_not_claimed(self):
        audit = build_audit()
        self.assertFalse(audit["stock_level_universe_coverage"])
        self.assertTrue(audit["market_regime_candidate_only"])

    def test_options_not_delta_adjusted(self):
        audit = build_audit()
        self.assertTrue(audit["semantics"]["options_report_is_separate_and_gross_not_delta_adjusted"])

if __name__ == "__main__":
    unittest.main()
