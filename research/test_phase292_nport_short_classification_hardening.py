import unittest

from research.phase221_nport_absence_semantics_audit import classify_direct_short_state


def row(**overrides):
    value = {
        "payoff_profile": "Short", "unit": "NS", "asset_cat": "EC",
        "issuer_cat": "CORP", "investment_country": "US",
        "cusip": "15677J108", "isin": "US15677J1088",
        "balance": -100, "currency_value": -1000, "percentage": -0.25
    }
    value.update(overrides)
    return value


def inputs(rows, **overrides):
    value = {
        "prior_public_part_c": False,
        "current_period_public": True,
        "current_filing_complete": True,
        "same_series": True,
        "same_security": True,
        "corporate_action_clear": True,
        "current_vintage_as_of_signal": True,
        "part_d_ineligible_due_prior_public": False,
        "current_part_c_rows": rows,
        "expected_cusip": "15677J108",
        "expected_isin": "US15677J1088"
    }
    value.update(overrides)
    return value


class Phase292NportShortClassificationHardeningTests(unittest.TestCase):
    def test_non_us_common_equity_is_not_admitted(self):
        got = classify_direct_short_state(**inputs([row(investment_country="CA")]))
        self.assertEqual(got["status"], "UNKNOWN")
        self.assertEqual(got["reason"], "row_not_verified_as_us_common_equity")

    def test_positive_currency_value_conflicts_with_short_balance(self):
        got = classify_direct_short_state(**inputs([row(currency_value=1000)]))
        self.assertEqual(got["status"], "UNKNOWN")
        self.assertEqual(got["reason"], "short_signs_not_concordant")

    def test_positive_percentage_conflicts_with_short_balance(self):
        got = classify_direct_short_state(**inputs([row(percentage=0.25)]))
        self.assertEqual(got["status"], "UNKNOWN")
        self.assertEqual(got["reason"], "short_signs_not_concordant")

    def test_wrong_cusip_is_not_accepted_even_when_ticker_is_unavailable(self):
        got = classify_direct_short_state(**inputs([row(cusip="189054109")]))
        self.assertEqual(got["status"], "UNKNOWN")
        self.assertEqual(got["reason"], "row_security_identifier_mismatch")

    def test_wrong_isin_is_not_accepted(self):
        got = classify_direct_short_state(**inputs([row(isin="US1890541097")]))
        self.assertEqual(got["status"], "UNKNOWN")
        self.assertEqual(got["reason"], "row_security_identifier_mismatch")

    def test_missing_row_identifiers_are_unknown(self):
        got = classify_direct_short_state(**inputs([row(cusip=None, isin=None)]))
        self.assertEqual(got["status"], "UNKNOWN")
        self.assertEqual(got["reason"], "row_security_identifier_missing")

    def test_missing_expected_identifier_blocks_classification(self):
        got = classify_direct_short_state(**inputs([row()], expected_cusip=None, expected_isin=None))
        self.assertEqual(got["status"], "UNKNOWN")
        self.assertEqual(got["reason"], "expected_exact_security_identifier_missing")

    def test_missing_country_is_not_assumed_us(self):
        got = classify_direct_short_state(**inputs([row(investment_country=None)]))
        self.assertEqual(got["status"], "UNKNOWN")
        self.assertEqual(got["reason"], "row_not_verified_as_us_common_equity")

    def test_empty_part_c_requires_exact_identity_before_zero_inference(self):
        got = classify_direct_short_state(**inputs([], expected_cusip=None, expected_isin=None,
                                                   prior_public_part_c=True,
                                                   part_d_ineligible_due_prior_public=True))
        self.assertEqual(got["status"], "UNKNOWN")
        self.assertEqual(got["reason"], "expected_exact_security_identifier_missing")


if __name__ == "__main__":
    unittest.main()
