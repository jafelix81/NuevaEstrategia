from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from research.phase180_ivydb_tradeflow_documentation_feasibility import (
    SUMMARY_PATH,
    load_summary,
    validate_summary,
    write_summary,
)


class Phase180TradeFlowDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = load_summary()

    def test_phase_number(self):
        self.assertEqual(self.summary["phase"], 180)

    def test_conditional_not_admitted_status(self):
        self.assertEqual(self.summary["status"], "CONDITIONAL_CANDIDATE_NOT_FEATURE_ADMITTED")

    def test_launch_date_and_advertised_history(self):
        product = self.summary["product"]
        self.assertEqual(product["launch_date"], "2026-09-30")
        self.assertEqual(product["advertised_history_start"], "2016-01")

    def test_all_exchange_scope_is_explicitly_a_vendor_claim(self):
        product = self.summary["product"]
        self.assertIn("all U.S. options exchanges", product["advertised_coverage"])
        self.assertTrue(product["vendor_data_claims_not_independently_verified"])

    def test_intervals(self):
        self.assertEqual(set(self.summary["product"]["intervals"]), {"5-minute", "30-minute", "end-of-day"})

    def test_four_relational_tables(self):
        self.assertEqual(set(self.summary["product"]["tables"]), {"Signed_Volume", "Trade_Conditions", "Market_Structure", "Signed_Exchange"})

    def test_classifier_is_sequential_and_keeps_unclassified(self):
        classifier = self.summary["classifier"]
        self.assertEqual(len(classifier["stages"]), 5)
        self.assertTrue(classifier["unresolved_volume_retained"])

    def test_vendor_accuracy_example_is_one_day_only(self):
        sample = self.summary["classifier"]["direction_assignment_accuracy_claim"]
        self.assertEqual(sample["sample"], "SPY options, 2026-06-17 FOMC session only")
        self.assertFalse(sample["representative_historical_accuracy"])

    def test_retail_buckets_are_mutually_exclusive(self):
        self.assertTrue(self.summary["participant_proxies"]["retail_1_2_3_mutually_exclusive"])

    def test_institutional_one_is_nested_in_two(self):
        proxies = self.summary["participant_proxies"]
        self.assertTrue(proxies["institutional_1_is_subset_of_institutional_2"])
        self.assertFalse(proxies["institutional_1_and_2_additive"])

    def test_institutional_label_is_only_aggressive_proxy(self):
        proxies = self.summary["participant_proxies"]
        self.assertTrue(proxies["institutional_2_is_aggressive_liquidity_demand_proxy"])
        self.assertFalse(proxies["institutional_proxy_is_total_institutional_participation"])
        self.assertFalse(proxies["beneficial_owner_or_account_identity_available"])

    def test_midpoint_is_subset_of_inside_nbbo(self):
        self.assertTrue(self.summary["microstructure_semantics"]["midpoint_is_subset_of_inside_NBBO"])
        self.assertIn("do not add midpoint separately", self.summary["microstructure_semantics"]["total_volume_reconciliation"])

    def test_multi_leg_legs_are_signed_individually(self):
        micro = self.summary["microstructure_semantics"]
        self.assertTrue(micro["multi_leg_legs_signed_individually"])
        self.assertTrue(micro["multi_leg_requires_separate_filter_or_sensitivity"])

    def test_open_close_is_not_provided(self):
        self.assertFalse(self.summary["microstructure_semantics"]["open_close_position_status_provided"])

    def test_lot_size_history_conflict_is_not_silently_backdated(self):
        history = self.summary["historical_field_coverage"]
        self.assertEqual(history["legacy_signed_volume_lot_size_fields_start"], "2021")
        self.assertEqual(history["tradeflow_lot_size_and_participant_proxy_backfill_start"], "UNRESOLVED")

    def test_first_receipt_and_revisions_remain_blocked(self):
        gates = {x["gate"]: x["status"] for x in self.summary["data_gates"]}
        self.assertTrue(gates["First-publication and first-receipt timestamps/latency"].startswith("BLOCKED"))
        self.assertTrue(gates["Late trades, cancellations, corrections and revision vintages"].startswith("BLOCKED"))

    def test_inactive_delisted_coverage_remains_blocked(self):
        gates = {x["gate"]: x["status"] for x in self.summary["data_gates"]}
        self.assertTrue(gates["Per-year, per-underlying, per-contract and inactive/delisted coverage"].startswith("BLOCKED"))

    def test_sample_and_licensing_remain_blocked(self):
        gates = {x["gate"]: x["status"] for x in self.summary["data_gates"]}
        self.assertTrue(gates["Raw sample and full data dictionary"].startswith("BLOCKED"))
        self.assertTrue(gates["Price, internal-use license and derived-data rights"].startswith("BLOCKED"))

    def test_ivydb_intraday_is_only_a_coarse_greek_complement(self):
        intraday = self.summary["complementary_data"]["ivydb_us_intraday"]
        self.assertEqual(intraday["advertised_history_start"], "2018-01")
        self.assertEqual(intraday["snapshots_et"], ["10:00", "14:00", "15:45"])
        self.assertFalse(intraday["first_receipt_pit_verified"])

    def test_cboe_open_close_is_complementary_not_equivalent(self):
        cboe = self.summary["complementary_data"]["cboe_open_close"]
        self.assertIn("capacity and open/close", cboe["distinction"])
        self.assertIn("aggressor-side", cboe["distinction"])

    def test_no_backtest_purchase_contact_or_alpha_admission(self):
        decision = self.summary["decision"]
        for key in ("feature_admitted", "alpha_admitted", "backtest_authorized", "holdout_used", "data_purchase", "vendor_contact", "raw_data_request", "production_changed"):
            self.assertFalse(decision[key], key)
        self.assertEqual(decision["frozen_control"], "F80_TOP20_PARTIAL50_BASELINE_C20")

    def test_static_validation_passes(self):
        self.assertEqual(validate_summary(self.summary), [])

    def test_output_is_deterministic_and_matches_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            out = write_summary(Path(temp))
            self.assertEqual(json.loads(out.read_text()), json.loads(SUMMARY_PATH.read_text()))


if __name__ == "__main__":
    unittest.main()
