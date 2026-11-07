from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from research.phase181_ivydb_tradeflow_measurement_protocol import (
    SUMMARY_PATH, load_summary, validate_summary, write_summary
)


class Phase181TradeFlowProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = load_summary()

    def test_phase_and_status(self):
        self.assertEqual(self.summary["phase"], 181)
        self.assertEqual(self.summary["status"], "PREREGISTERED_NOT_DATA_ADMITTED")

    def test_product_launch_does_not_equal_historical_live_availability(self):
        evidence = self.summary["source_evidence"]
        self.assertEqual(evidence["product_launch_date"], "2026-09-30")
        self.assertEqual(evidence["vendor_advertised_history_start"], "2016-01")
        self.assertFalse(evidence["historical_availability"]["contemporaneous_trade_date_delivery_proven"])

    def test_midpoint_assignment_is_not_accuracy(self):
        sample = self.summary["source_evidence"]["methodology_example"]
        self.assertEqual(sample["midpoint_direction_assignment_share"], 0.999)
        self.assertIn("not independently measured directional accuracy", sample["interpretation"])

    def test_institutional_proxy_is_not_owner_identity(self):
        semantics = self.summary["measurement_semantics"]
        self.assertFalse(semantics["beneficial_owner_identity"])
        self.assertFalse(semantics["open_close_status"])
        self.assertTrue(semantics["institutional_1_nested_in_2"])

    def test_retail_proxy_mutual_exclusivity_is_only_vendor_claim(self):
        self.assertTrue(self.summary["measurement_semantics"]["retail_1_2_3_mutually_exclusive_vendor_claim"])

    def test_midpoint_overlap_and_multileg_guards(self):
        semantics = self.summary["measurement_semantics"]
        self.assertTrue(semantics["midpoint_is_subset_of_inside_nbbo"])
        self.assertTrue(semantics["multi_leg_legs_signed_individually"])
        self.assertTrue(semantics["unclassified_volume_retained"])

    def test_literature_keeps_competing_mechanisms(self):
        lit = self.summary["literature_interpretation"]
        self.assertIn("cannot reproduce", lit["pan_poteshman_2006"])
        self.assertIn("hedging/price pressure", lit["bryzgalova_pavlova_sikorskaya_2023"])
        self.assertIn("inventory-risk", lit["option_order_flow_inventory_risk_2015"])

    def test_five_competing_hypotheses_are_preregistered(self):
        ids = {x["id"] for x in self.summary["hypotheses_not_tested"]}
        self.assertEqual(ids, {"H1_information_continuation", "H2_hedging_or_temporary_price_pressure", "H3_participant_proxy_heterogeneity", "H4_flow_x_volatility_surface", "H5_execution_mechanism"})

    def test_controls_cover_return_chasing_and_microstructure(self):
        controls = " ".join(self.summary["controls_required"]).lower()
        for token in ("returns", "iv", "liquidity", "dte", "multi-leg", "event"):
            self.assertIn(token, controls)

    def test_multiple_horizons_without_fixed_holding_period(self):
        horizons = self.summary["horizon_grid"]
        self.assertGreaterEqual(len(horizons), 5)
        self.assertIn("120 trading sessions", horizons)
        self.assertIn("no minimum or maximum", self.summary["validation_protocol"]["holding_period"])

    def test_pit_separates_event_time_and_availability(self):
        pit = self.summary["pit_rules"]
        self.assertTrue(pit["event_time_is_not_availability_time"])
        self.assertIn("Maximum of", pit["first_usable_time"])
        self.assertIn("does not prove", pit["historical_backfill"])

    def test_no_future_greek_or_nominal_interval_assumption(self):
        pit = self.summary["pit_rules"]
        self.assertIn("Never use a later 15:45 Greek", pit["greeks"])
        self.assertIn("actual availability", pit["intraday"])

    def test_all_admission_gates_remain_blocked(self):
        gates = self.summary["admission_gates"]
        self.assertEqual(len(gates), 9)
        self.assertTrue(all(x["status"] == "BLOCKED" for x in gates))

    def test_baseline_costs_bootstrap_loo_and_holdout_discipline(self):
        protocol = self.summary["validation_protocol"]
        self.assertIn("F80_TOP20_PARTIAL50_BASELINE_C20", protocol["baseline"])
        self.assertIn("identical exposure and costs", protocol["baseline"])
        self.assertIn("bootstrap", protocol["robustness"])
        self.assertIn("leave-one-out", protocol["robustness"])
        self.assertIn("untouched", protocol["holdout"])

    def test_no_feature_backtest_or_production_admission(self):
        decision = self.summary["decision"]
        for key in ("feature_admitted", "backtest_authorized", "alpha_admitted", "holdout_used", "vendor_contact", "data_purchase", "production_changed"):
            self.assertFalse(decision[key], key)
        self.assertEqual(decision["frozen_control"], "F80_TOP20_PARTIAL50_BASELINE_C20")

    def test_static_validation_and_deterministic_output(self):
        self.assertEqual(validate_summary(self.summary), [])
        with tempfile.TemporaryDirectory() as temp:
            out = write_summary(Path(temp))
            self.assertEqual(json.loads(out.read_text()), json.loads(SUMMARY_PATH.read_text()))


if __name__ == "__main__":
    unittest.main()
