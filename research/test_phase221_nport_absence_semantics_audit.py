import json
import unittest
from research.phase221_nport_absence_semantics_audit import (
    EVIDENCE, build_audit, classify_direct_short_state
)


def base_inputs(**overrides):
    data = {
        "prior_public_part_c": True,
        "current_period_public": True,
        "current_filing_complete": True,
        "same_series": True,
        "same_security": True,
        "corporate_action_clear": True,
        "current_vintage_as_of_signal": True,
        "part_d_ineligible_due_prior_public": True,
        "current_part_c_rows": [],
        "expected_cusip": "000000000",
        "expected_isin": "US0000000000"
    }
    data.update(overrides)
    return data


def valid_row(**overrides):
    row = {
        "payoff_profile": "Short", "unit": "NS", "asset_cat": "EC",
        "issuer_cat": "CORP", "investment_country": "US",
        "cusip": "000000000", "isin": "US0000000000",
        "balance": -40, "currency_value": -4000, "percentage": -0.4,
        "title": "Common Stock"
    }
    row.update(overrides)
    return row


class Phase221NportAbsenceSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.audit = build_audit(cls.evidence)

    def test_prior_public_part_c_absence_is_only_conditional_zero(self):
        got = classify_direct_short_state(**base_inputs())
        self.assertEqual(got["status"], "CONDITIONAL_ZERO_BY_PART_D_EXCLUSION")
        self.assertEqual(got["short_shares"], 0.0)

    def test_never_public_security_absence_remains_unknown(self):
        got = classify_direct_short_state(**base_inputs(
            prior_public_part_c=False,
            part_d_ineligible_due_prior_public=False
        ))
        self.assertEqual(got["status"], "UNKNOWN")

    def test_part_d_not_excluded_remains_unknown(self):
        got = classify_direct_short_state(**base_inputs(
            part_d_ineligible_due_prior_public=False
        ))
        self.assertEqual(got["status"], "UNKNOWN")

    def test_first_or_second_fiscal_quarter_month_is_not_public(self):
        got = classify_direct_short_state(**base_inputs(current_period_public=False))
        self.assertEqual(got["status"], "UNKNOWN")

    def test_incomplete_filing_is_unknown(self):
        got = classify_direct_short_state(**base_inputs(current_filing_complete=False))
        self.assertEqual(got["status"], "UNKNOWN")

    def test_series_mismatch_is_unknown(self):
        got = classify_direct_short_state(**base_inputs(same_series=False))
        self.assertEqual(got["status"], "UNKNOWN")

    def test_security_mismatch_is_unknown(self):
        got = classify_direct_short_state(**base_inputs(same_security=False))
        self.assertEqual(got["status"], "UNKNOWN")

    def test_unresolved_corporate_action_is_unknown(self):
        got = classify_direct_short_state(**base_inputs(corporate_action_clear=False))
        self.assertEqual(got["status"], "UNKNOWN")

    def test_later_amendment_cannot_be_backdated(self):
        got = classify_direct_short_state(**base_inputs(current_vintage_as_of_signal=False))
        self.assertEqual(got["status"], "UNKNOWN")

    def test_two_short_rows_are_aggregated(self):
        rows = [valid_row(balance=-40, currency_value=-4000, percentage=-0.4),
                valid_row(balance=-60, currency_value=-6000, percentage=-0.6)]
        got = classify_direct_short_state(**base_inputs(current_part_c_rows=rows))
        self.assertEqual(got["status"], "OBSERVED_SHORT_POSITION")
        self.assertEqual(got["short_shares"], 100.0)

    def test_long_only_part_c_rows_are_zero_direct_short(self):
        rows = [valid_row(payoff_profile="Long", balance=75,
                          currency_value=7500, percentage=0.75)]
        got = classify_direct_short_state(**base_inputs(current_part_c_rows=rows))
        self.assertEqual(got["status"], "OBSERVED_ZERO_DIRECT_SHORT_IN_PART_C")
        self.assertEqual(got["short_shares"], 0.0)

    def test_malformed_short_row_fails_closed(self):
        rows = [valid_row(unit="USD")]
        got = classify_direct_short_state(**base_inputs(current_part_c_rows=rows))
        self.assertEqual(got["status"], "UNKNOWN")

    def test_none_is_not_an_empty_complete_parse(self):
        got = classify_direct_short_state(**base_inputs(current_part_c_rows=None))
        self.assertEqual(got["status"], "UNKNOWN")

    def test_audit_preserves_no_alpha_and_frozen_controls(self):
        self.assertEqual(self.audit["synthetic_cases_validated"], 13)
        self.assertTrue(self.audit["exact_cusip_or_isin_required"])
        self.assertTrue(self.audit["us_common_equity_required"])
        self.assertTrue(self.audit["balance_value_percentage_sign_concordance_required"])
        self.assertFalse(self.audit["alpha_test_authorized"])
        self.assertFalse(self.audit["holdout_used"])
        self.assertTrue(self.audit["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
