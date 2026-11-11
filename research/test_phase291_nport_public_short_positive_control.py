import json
import math
import unittest
from pathlib import Path

from research.phase221_nport_absence_semantics_audit import classify_direct_short_state

FIXTURE = Path(__file__).with_name("phase291_nport_public_short_positive_control.json")


def base_inputs(rows):
    return {
        "prior_public_part_c": False,
        "current_period_public": True,
        "current_filing_complete": True,
        "same_series": True,
        "same_security": True,
        "corporate_action_clear": True,
        "current_vintage_as_of_signal": True,
        "part_d_ineligible_due_prior_public": False,
        "current_part_c_rows": rows,
    }


class Phase291NportPublicShortPositiveControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_three_actual_public_short_common_equity_rows(self):
        self.assertEqual(len(self.fixture["positions"]), 3)
        for position in self.fixture["positions"]:
            with self.subTest(ticker=position["ticker"]):
                self.assertNotIn("common stock", position["issuer_title"].lower())
                self.assertLess(position["balance_shares"], 0)
                self.assertLess(position["currency_value_usd"], 0)
                self.assertLess(position["percentage_nav"], 0)
                row = {
                    "payoff_profile": position["payoff_profile"],
                    "unit": position["unit_code"],
                    "asset_cat": position["asset_cat_code"],
                    "issuer_cat": position["issuer_cat_code"],
                    "title": position["issuer_title"],
                    "balance": position["balance_shares"],
                }
                got = classify_direct_short_state(**base_inputs([row]))
                self.assertEqual(got["status"], "OBSERVED_SHORT_POSITION")
                self.assertEqual(got["short_shares"], abs(position["balance_shares"]))

    def test_non_finite_balance_fails_closed(self):
        row = {
            "payoff_profile": "Short",
            "unit": "NS",
            "asset_cat": "EC",
            "issuer_cat": "CORP",
            "title": "Example Inc",
            "balance": math.nan,
        }
        got = classify_direct_short_state(**base_inputs([row]))
        self.assertEqual(got["status"], "UNKNOWN")
        self.assertEqual(got["reason"], "non_finite_balance")

    def test_non_common_equity_asset_category_fails_closed(self):
        row = {
            "payoff_profile": "Short",
            "unit": "NS",
            "asset_cat": "EP",
            "issuer_cat": "CORP",
            "title": "Example Preferred",
            "balance": -100,
        }
        got = classify_direct_short_state(**base_inputs([row]))
        self.assertEqual(got["status"], "UNKNOWN")
        self.assertEqual(got["reason"], "row_not_verified_as_direct_common_equity")


if __name__ == "__main__":
    unittest.main()
