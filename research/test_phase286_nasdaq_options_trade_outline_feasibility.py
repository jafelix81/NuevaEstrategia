"""Fail-closed tests for Phase 286 Nasdaq NOTO/NOP feasibility."""
from __future__ import annotations

import unittest

from research.phase286_nasdaq_options_trade_outline_feasibility import (
    build_result,
    validate_result,
)


class Phase286NasdaqOptionsTests(unittest.TestCase):
    def setUp(self):
        self.result = build_result()
        validate_result(self.result)

    def test_noto_history_and_eod_timing(self):
        noto = self.result["noto"]
        self.assertEqual(noto["history_start"], "2011-11")
        self.assertTrue(noto["eod"]["availability"].startswith("next business day"))
        self.assertTrue(noto["eod"]["includes_total_industry_volume"])

    def test_noto_intraday_snapshots_are_cumulative(self):
        intraday = self.result["noto"]["intraday"]
        self.assertEqual(intraday["frequency"], "10-minute")
        self.assertTrue(intraday["snapshots_are_cumulative"])
        self.assertEqual(intraday["current_table_resets_utc"], "01:40")

    def test_professional_is_order_frequency_category_not_institution(self):
        noto = self.result["noto"]
        self.assertIn("390 listed-options orders", noto["professional_definition"])
        self.assertFalse(noto["professional_is_institutional_identity"])
        self.assertFalse(noto["named_beneficial_owner_available"])

    def test_open_close_is_position_semantics_not_aggressor_side(self):
        sem = self.result["noto"]["opening_closing_semantics"]
        self.assertIn("long option position", sem["opening_buy"])
        self.assertIn("short option position", sem["opening_write"])
        self.assertFalse(sem["is_aggressor_side"])

    def test_noto_is_venue_specific(self):
        self.assertEqual(self.result["noto"]["venue"], "NOM")
        self.assertIn("no other-exchange", self.result["noto"]["market_scope"])

    def test_other_nasdaq_venues_are_not_assumed_harmonized(self):
        family = self.result["nasdaq_options_trade_outline_family"]
        self.assertEqual(len(family["advertised_venues"]), 6)
        self.assertFalse(family["all_venues_have_identical_schema_and_history"])
        self.assertFalse(family["combined_panel_admitted"])

    def test_pricing_conflict_fails_closed(self):
        fees = self.result["noto"]["fees_usd"]
        self.assertEqual(fees["eod_monthly"], 575)
        self.assertEqual(fees["intraday_monthly"], 2000)
        self.assertFalse(fees["ad_hoc_historical_price_conflict"]["resolved"])

    def test_external_derived_data_license_is_separate(self):
        fees = self.result["noto"]["fees_usd"]
        self.assertEqual(fees["external_derived_data_monthly"], 4000)

    def test_nop_is_derived_and_not_independent_confirmation(self):
        nop = self.result["nasdaq_options_pulse"]
        self.assertEqual(nop["history_start"], "2019-01")
        self.assertEqual(nop["frequency"], "10-minute")
        self.assertTrue(nop["schema_is_derived_sentiment_score"])
        self.assertFalse(nop["independent_of_noto"])

    def test_no_pit_or_alpha_admission(self):
        validate_result(self.result)
        self.assertFalse(self.result["noto"]["pit_admitted"])
        self.assertFalse(self.result["noto"]["alpha_admitted"])
        self.assertFalse(self.result["nasdaq_options_pulse"]["pit_admitted"])
        self.assertFalse(self.result["controls"]["alpha_admission"])
        self.assertTrue(self.result["controls"]["f80_frozen"])

    def test_no_purchase_contact_trial_or_data_download(self):
        c = self.result["controls"]
        self.assertFalse(c["raw_data_downloaded"])
        self.assertFalse(c["vendor_contacted"])
        self.assertFalse(c["trial_started"])
        self.assertFalse(c["license_or_terms_accepted"])

    def test_option_identity_gate_is_explicit(self):
        identity = self.result["noto"]["contract_identity"]
        self.assertIn("option_symbol", identity["series_fields"])
        self.assertFalse(identity["effective_dated_option_master_verified"])


if __name__ == "__main__":
    unittest.main()
