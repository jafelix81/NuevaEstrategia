import unittest
from research.phase233_cboe_option_sentiment_semantics_audit import (
    SPEC_URL, NOTE2_BLANK_FIELDS, PARTICIPANT_FIELDS, SIZE_FIELDS, DTX_FIELDS,
    MONEYNESS_FIELDS, OI_FIELDS, audit_specification
)

class Phase233Tests(unittest.TestCase):
    def setUp(self):
        self.result = audit_specification()

    def test_canonical_spec_has_80_unique_fields(self):
        self.assertEqual(self.result["documented_field_count"], 80)
        self.assertTrue(self.result["all_schema_checks_pass"])

    def test_footnote_cross_reference_mismatch_is_exactly_three_fields(self):
        self.assertEqual(
            self.result["footnote_cross_reference"]["mismatched_fields"],
            ["net_option_delta", "calls_sold", "puts_sold"]
        )

    def test_note2_blank_field_list_is_present_in_schema(self):
        self.assertEqual(len(NOTE2_BLANK_FIELDS), 11)
        self.assertTrue(self.result["checks"]["note2_blank_fields_exist"])

    def test_participant_categories_have_no_directional_cross_tab(self):
        self.assertEqual(PARTICIPANT_FIELDS, ("cust_volume", "firm_volume", "mkt_mkr_volume"))
        self.assertFalse(self.result["field_dimensionality"]["direction_by_participant_available"])
        self.assertFalse(self.result["field_dimensionality"]["customer_call_put_buy_sell_cross_tab_available"])

    def test_size_buckets_are_not_signed(self):
        self.assertEqual(len(SIZE_FIELDS), 6)
        self.assertFalse(self.result["field_dimensionality"]["direction_by_size_available"])

    def test_dtx_buckets_are_not_signed(self):
        self.assertEqual(len(DTX_FIELDS), 7)
        self.assertFalse(self.result["field_dimensionality"]["direction_by_dtx_available"])

    def test_moneyness_buckets_are_call_put_totals_not_direction(self):
        self.assertEqual(len(MONEYNESS_FIELDS), 6)
        self.assertFalse(self.result["field_dimensionality"]["direction_by_moneyness_available"])
        self.assertTrue(self.result["field_dimensionality"]["non_itm_put_call_volume_computable"])
        self.assertFalse(self.result["field_dimensionality"]["non_itm_put_call_is_directional"])

    def test_open_interest_is_context_only(self):
        self.assertEqual(len(OI_FIELDS), 4)
        self.assertEqual(
            self.result["hypothesis_decisions"][-1]["decision"],
            "PRIOR_NIGHT_STATE_ONLY"
        )

    def test_primary_delta_feature_is_suspended(self):
        self.assertEqual(self.result["primary_feature"]["status"], "SUSPENDED_PENDING_PROVIDER_CLARIFICATION")
        self.assertFalse(self.result["primary_feature"]["units_specified"])
        self.assertFalse(self.result["primary_feature"]["normalization_by_underlying_volume_authorized"])

    def test_delivery_and_revision_gates_block_strict_pit(self):
        self.assertFalse(self.result["availability"]["historical_first_receipt_logs_verified"])
        self.assertFalse(self.result["availability"]["immutable_correction_vintages_verified"])
        self.assertFalse(self.result["availability"]["strict_pit_admission"])

    def test_canonical_public_source_is_pinned(self):
        self.assertEqual(SPEC_URL, "https://datashop.cboe.com/Documents/Cboe_OptionSentiment_Specs.pdf")

    def test_no_alpha_or_production_change(self):
        self.assertFalse(self.result["alpha_test_run"])
        self.assertFalse(self.result["chronological_oos_run"])
        self.assertFalse(self.result["final_holdout_used"])
        self.assertFalse(self.result["production_changed"])
        self.assertFalse(self.result["f80_changed"])

if __name__ == "__main__":
    unittest.main()
