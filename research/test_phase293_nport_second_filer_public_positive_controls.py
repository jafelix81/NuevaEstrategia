import json
import unittest
from pathlib import Path

from research.phase293_nport_second_filer_public_positive_controls import build_audit
from research.phase221_nport_absence_semantics_audit import classify_direct_short_state

FIXTURE = Path(__file__).with_name("phase217_nport_full_submission_text_short_row_pilot.json")


class Phase293NportSecondFilerPositiveControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.audit = build_audit()

    def test_all_23_selected_second_filer_rows_pass_hardened_classifier(self):
        rows = self.fixture["selected_rows"]
        self.assertEqual(len(rows), 23)
        for row in rows:
            with self.subTest(name=row["name"], cusip=row["cusip"]):
                candidate = {
                    "payoff_profile": row["payoff_profile"],
                    "unit": row["units"],
                    "asset_cat": row["asset_category"],
                    "issuer_cat": row["issuer_category"],
                    "investment_country": row["investment_country"],
                    "cusip": row["cusip"],
                    "balance": row["balance"],
                    "currency_value": row["val_usd"],
                    "percentage": row["pct_nav"],
                }
                result = classify_direct_short_state(
                    prior_public_part_c=False,
                    current_period_public=True,
                    current_filing_complete=True,
                    same_series=True,
                    same_security=True,
                    corporate_action_clear=True,
                    current_vintage_as_of_signal=True,
                    part_d_ineligible_due_prior_public=False,
                    current_part_c_rows=[candidate],
                    expected_cusip=row["cusip"],
                    expected_isin=None,
                )
                self.assertEqual(result["status"], "OBSERVED_SHORT_POSITION")

    def test_positive_controls_span_two_distinct_registrants(self):
        filings = self.audit["public_filings"]
        self.assertEqual(self.audit["distinct_registrants"], 2)
        self.assertNotEqual(filings[0]["cik"], filings[1]["cik"])
        self.assertEqual(self.audit["public_positive_controls_passed"], 26)

    def test_second_filer_sample_is_not_misrepresented_as_exhaustive_or_pit(self):
        self.assertFalse(self.audit["second_filer_selected_rows_exhaustive"])
        self.assertFalse(self.audit["first_public_receipt_verified"])
        self.assertFalse(self.audit["series_longitudinal_identity_established"])
        self.assertFalse(self.audit["strict_pit_admitted"])
        self.assertFalse(self.audit["alpha_test_authorized"])
        self.assertFalse(self.audit["holdout_used"])
        self.assertTrue(self.audit["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
