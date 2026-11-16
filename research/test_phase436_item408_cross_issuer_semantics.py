"""Phase 436 regression tests for Item 408 cross-issuer normalization."""
from __future__ import annotations

import copy
import unittest

from research.phase436_item408_cross_issuer_semantics import audit_casebook, load_casebook


class Phase436Item408SemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.casebook = load_casebook()
        cls.result = audit_casebook(cls.casebook)

    def test_six_issuer_purposive_sample(self):
        self.assertEqual(self.result["issuer_count"], 6)
        self.assertEqual(self.result["filing_count"], 6)

    def test_action_counts_keep_termination_separate(self):
        self.assertEqual(self.result["plan_action_count"], 12)
        self.assertEqual(self.result["action_counts"], {"adopt": 11, "terminate": 1})
        self.assertEqual(self.result["termination_plan_ids"], ["CARG_QUINN_2023"])

    def test_juniper_direction_remains_unknown(self):
        self.assertEqual(self.result["unknown_direction_plan_ids"], ["JNPR_KM_2024"])
        self.assertEqual(self.result["direction_counts"]["unknown"], 1)

    def test_celanese_purchase_is_not_sale_supply(self):
        self.assertEqual(self.result["purchase_plan_ids"], ["CE_RICHARDSON_2023"])
        self.assertEqual(self.result["direction_counts"]["buy"], 1)

    def test_general_mills_option_exercise_and_sale_is_separate(self):
        self.assertEqual(self.result["exercise_and_sell_plan_ids"], ["GIS_HARMENING_2024"])
        self.assertEqual(self.result["direction_counts"]["exercise_and_sell"], 1)

    def test_gross_award_and_conditional_share_amounts_are_flagged(self):
        self.assertGreaterEqual(
            self.result["share_amount_records_not_comparable_to_plain_ceiling"], 6
        )

    def test_dollar_termination_is_not_converted_to_shares(self):
        self.assertEqual(self.result["amount_unit_counts"], {"USD": 1, "shares": 11})

    def test_explicit_future_windows_are_preserved(self):
        self.assertEqual(self.result["actions_with_explicit_scheduled_start_date"], 3)

    def test_amounts_are_never_aggregated_across_plans(self):
        self.assertFalse(self.result["amounts_aggregated_across_plans"])

    def test_direction_is_never_inferred_from_amount_alone(self):
        self.assertFalse(self.result["direction_inferred_from_amount_only"])

    def test_first_eligible_session_is_after_filing_date(self):
        for issuer in self.casebook["issuers"]:
            self.assertGreater(issuer["first_eligible_session"], issuer["filed_date"])

    def test_acceptance_timestamps_are_timezone_aware(self):
        for issuer in self.casebook["issuers"]:
            self.assertRegex(issuer["accepted_eastern"], r"[+-]\\d{2}:\\d{2}$")

    def test_unknown_direction_is_not_silently_promoted_to_sell(self):
        mutated = copy.deepcopy(self.casebook)
        mutated["issuers"][0]["plans"][0]["direction"] = "sell"
        result = audit_casebook(mutated)
        self.assertEqual(result["direction_counts"]["sell"], 10)
        self.assertNotIn("JNPR_KM_2024", result["unknown_direction_plan_ids"])

    def test_missing_termination_date_fails_closed(self):
        mutated = copy.deepcopy(self.casebook)
        del mutated["issuers"][2]["plans"][3]["termination_date"]
        with self.assertRaises(ValueError):
            audit_casebook(mutated)

    def test_duplicate_plan_ids_fail_closed(self):
        mutated = copy.deepcopy(self.casebook)
        mutated["issuers"][1]["plans"][0]["plan_id"] = "JNPR_KM_2024"
        with self.assertRaises(ValueError):
            audit_casebook(mutated)

    def test_no_alpha_or_signal_admission(self):
        self.assertEqual(self.result["alpha_test"], "NOT_RUN")
        self.assertEqual(self.result["signal_admission"], "NOT_ADMITTED")
        self.assertFalse(self.result["frozen_baseline_changed"])


if __name__ == "__main__":
    unittest.main()
