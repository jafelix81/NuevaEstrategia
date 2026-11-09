import unittest

from research.phase105_sec_ftd_identity import build_mapping_diagnostics


class Phase105FtdIdentityTests(unittest.TestCase):
    def test_detects_same_day_many_to_many_mapping(self):
        rows = [
            {"settlement_date": "2026-01-02", "cusip": "111111111", "symbol": "AAA", "description": "A"},
            {"settlement_date": "2026-01-02", "cusip": "111111111", "symbol": "AAB", "description": "A"},
            {"settlement_date": "2026-01-02", "cusip": "222222222", "symbol": "BBB", "description": "B"},
            {"settlement_date": "2026-01-02", "cusip": "333333333", "symbol": "BBB", "description": "C"},
        ]
        summary, ambiguous = build_mapping_diagnostics(rows)
        self.assertEqual(summary["same_day_cusip_multiple_symbol_keys"], 1)
        self.assertEqual(summary["same_day_symbol_multiple_cusip_keys"], 1)
        self.assertEqual(len(ambiguous), 2)

    def test_cross_date_ticker_change_is_not_same_day_ambiguity(self):
        rows = [
            {"settlement_date": "2026-01-02", "cusip": "111111111", "symbol": "AAA", "description": "A"},
            {"settlement_date": "2026-01-05", "cusip": "111111111", "symbol": "AAB", "description": "A"},
        ]
        summary, _ = build_mapping_diagnostics(rows)
        self.assertEqual(summary["same_day_cusip_multiple_symbol_keys"], 0)
        self.assertEqual(summary["cusips_with_multiple_symbols_across_sample"], 1)

    def test_duplicate_key_and_blank_fields_are_visible(self):
        rows = [
            {"settlement_date": "2026-01-02", "cusip": "111111111", "symbol": "AAA", "description": "A"},
            {"settlement_date": "2026-01-02", "cusip": "111111111", "symbol": "AAA", "description": "A"},
            {"settlement_date": "2026-01-02", "cusip": "222222222", "symbol": "", "description": "B"},
        ]
        summary, _ = build_mapping_diagnostics(rows)
        self.assertEqual(summary["duplicate_date_cusip_symbol_keys"], 1)
        self.assertEqual(summary["duplicate_rows_beyond_first"], 1)
        self.assertEqual(summary["blank_symbol_rows"], 1)


if __name__ == "__main__":
    unittest.main()
