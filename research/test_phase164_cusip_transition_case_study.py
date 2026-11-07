import json
import tempfile
import unittest
from pathlib import Path

from phase164_cusip_transition_case_study import (
    CASE, audit, cusip_on_date, legal_name_on_date, ticker_on_date, write_outputs
)


class Phase164CusipTransitionTests(unittest.TestCase):
    def test_old_and_new_cusips_are_distinct(self):
        self.assertNotEqual(CASE["old_cusip"], CASE["new_cusip"])

    def test_both_cusips_share_current_share_class_figi(self):
        self.assertTrue(CASE["openfigi_current_share_class_figi_equal"])
        self.assertEqual(CASE["share_class_figi"], "BBG001S982M0")

    def test_legal_name_change_precedes_exchange_identifier_change(self):
        self.assertEqual(CASE["legal_name_effective_date"], "2024-06-20")
        self.assertEqual(CASE["tsx_identifier_effective_date"], "2024-06-27")

    def test_legal_name_is_old_before_june_20(self):
        self.assertEqual(legal_name_on_date("2024-06-19"), "Fortuna Silver Mines Inc.")

    def test_legal_name_is_new_from_june_20(self):
        self.assertEqual(legal_name_on_date("2024-06-20"), "Fortuna Mining Corp.")

    def test_old_cusip_remains_through_june_26_on_tsx(self):
        self.assertEqual(cusip_on_date("2024-06-26", "TSX"), "349915108")

    def test_new_cusip_starts_june_27_on_tsx(self):
        self.assertEqual(cusip_on_date("2024-06-27", "TSX"), "349942102")

    def test_nyse_cusip_date_is_not_inferred(self):
        self.assertIsNone(cusip_on_date("2024-06-27", "NYSE"))
        self.assertFalse(CASE["nyse_date_verified"])

    def test_tickers_remain_unchanged(self):
        self.assertEqual(ticker_on_date("TSX"), "FVI")
        self.assertEqual(ticker_on_date("NYSE"), "FSM")

    def test_phase149_mapping_coverage_is_not_complete(self):
        s = audit()
        self.assertEqual(CASE["phase149_input_cusips"], 553)
        self.assertEqual(CASE["phase149_primary_no_match"], 115)
        self.assertEqual(CASE["phase149_fallback_unique_recovered"], 6)

    def test_only_one_cross_cusip_pair_was_found_in_sample(self):
        self.assertEqual(CASE["phase149_cross_cusip_shareclass_pairs"], 1)
        self.assertEqual(CASE["phase149_cross_cusip_pair_count"], 2)

    def test_bridge_is_tsx_only_and_no_backdating(self):
        s = audit()
        self.assertEqual(s["status"], "MANUAL_CORPORATE_ACTION_BRIDGE_VERIFIED_TSX_ONLY")
        self.assertFalse(s["historical_ticker_backdating_allowed"])
        self.assertFalse(s["nyse_cusip_date_inferred"])

    def test_no_returns_holdout_or_production_change(self):
        s = audit()
        self.assertFalse(s["forward_returns_used"])
        self.assertFalse(s["final_holdout_used"])
        self.assertFalse(s["production_changed"])
        self.assertFalse(s["f80_changed"])

    def test_outputs_are_reproducible(self):
        s = audit()
        with tempfile.TemporaryDirectory() as tmp:
            write_outputs(s, Path(tmp))
            saved = json.loads((Path(tmp) / "phase164_cusip_transition_summary.json").read_text())
            self.assertEqual(saved["phase"], 164)
            self.assertTrue((Path(tmp) / "phase164_cusip_transition_bridge.csv").exists())


if __name__ == "__main__":
    unittest.main()
