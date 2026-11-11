"""Fail-closed tests for Phase 285 Nasdaq alternative-data metadata admission."""
from __future__ import annotations

import unittest

from research.phase285_nasdaq_alternative_data_admission_audit import (
    build_result,
    validate_result,
)


class Phase285NasdaqAlternativeDataTests(unittest.TestCase):
    def setUp(self):
        self.result = build_result()
        validate_result(self.result)

    def test_fis_table_history_starts_are_not_conflated(self):
        history = self.result["fis_astec_sld"]["history_start_by_table"]
        self.assertEqual(history["FIS/R1"], "2012-01-02")
        self.assertEqual(history["FIS/POS"], "2013-07-01")
        self.assertEqual(history["FIS/U1"], "2013-07-01")
        self.assertEqual(history["FIS/U2"], "2014-01-01")

    def test_fis_coverage_is_mixed_asset_not_equity_only(self):
        coverage = self.result["fis_astec_sld"]["coverage"]
        self.assertEqual(coverage["advertised_securities"], "45000+")
        self.assertEqual(coverage["asset_scope"], ["equities", "fixed_income"])
        self.assertFalse(coverage["equity_only_count_known"])

    def test_fis_retail_rate_means_prime_broker_client_segment(self):
        semantics = self.result["fis_astec_sld"]["semantics"]
        self.assertIn("prime broker", semantics["retail_loan_rate_definition"])
        self.assertTrue(semantics["retail_loan_rate_is_not_retail_investor_rate"])
        self.assertFalse(semantics["borrower_or_fund_identity_available"])

    def test_fis_loan_is_not_assumed_to_be_a_short_sale(self):
        self.assertFalse(self.result["fis_astec_sld"]["semantics"]["loan_is_proof_of_short_sale"])

    def test_u1_is_not_reconstructed_from_pos_and_u2(self):
        self.assertFalse(
            self.result["fis_astec_sld"]["semantics"][
                "reconstruct_u1_from_pos_units_divided_by_u2_available_units"
            ]
        )

    def test_r1_and_pos_are_not_added_or_reconciled_as_same_contract_scope(self):
        semantics = self.result["fis_astec_sld"]["semantics"]
        self.assertTrue(semantics["r1_excludes_term_trades"])
        self.assertTrue(semantics["r1_new_units_are_subset_of_r1_units"])

    def test_fis_pit_and_alpha_remain_closed(self):
        fis = self.result["fis_astec_sld"]
        self.assertFalse(fis["pit_admitted"])
        self.assertFalse(fis["alpha_admitted"])
        self.assertFalse(fis["delivery"]["actual_first_receipt_captured"])
        self.assertFalse(fis["delivery"]["immutable_historical_vintages_established"])

    def test_uref_intraday_tables_cover_2016_to_current_split(self):
        uref = self.result["nasdaq_urefint"]
        self.assertEqual(uref["history_start"], "2016-01-04")
        self.assertEqual(uref["tables"]["current"]["code"], "UREF/FFI")
        self.assertEqual(len(uref["tables"]["historical"]), 9)

    def test_uref_timestamp_and_health_fields_have_era_boundaries(self):
        fields = self.result["nasdaq_urefint"]["fields"]
        self.assertEqual(fields["update_time_populated_from"], "2022-06-01")
        self.assertEqual(fields["is_healthy_populated_from"], "2021-08-02")
        self.assertTrue(fields["known_incomplete_dates_before_2021"])

    def test_uref_generation_time_is_not_first_receipt(self):
        fields = self.result["nasdaq_urefint"]["fields"]
        self.assertIn("not documented first receipt", fields["update_time_semantics"])
        self.assertFalse(self.result["nasdaq_urefint"]["delivery"]["actual_first_receipt_captured"])

    def test_uref_daily_and_intraday_15m_are_distinct_products(self):
        daily = self.result["nasdaq_uref_daily_separate_product"]
        self.assertFalse(daily["same_as_urefint_15_minute_product"])
        self.assertEqual(daily["tables"]["daily"], "UREF/DF")
        self.assertEqual(daily["tables"]["intraday_30_minute"], "UREF/IF")

    def test_price_filter_and_identity_gates_are_explicit(self):
        uref = self.result["nasdaq_urefint"]
        self.assertTrue(uref["coverage"]["price_below_usd_1_excluded"])
        self.assertTrue(uref["coverage"]["point_in_time_ticker_symbology_claimed"])
        self.assertFalse(uref["identity"]["permanent_security_identifier_in_documented_schema"])

    def test_all_research_and_production_admission_gates_remain_closed(self):
        validate_result(self.result)
        self.assertFalse(self.result["controls"]["alpha_admission"])
        self.assertTrue(self.result["controls"]["f80_frozen"])
        self.assertFalse(self.result["controls"]["production_changed"])


if __name__ == "__main__":
    unittest.main()
