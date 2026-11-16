import unittest

from research.phase435_item408_compass_reconciliation import analyze_casebook, load_casebook


class Phase435CompassReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.casebook = load_casebook()
        cls.result = analyze_casebook(cls.casebook)

    def test_form144_sales_sum_to_three_point_five_million(self):
        self.assertEqual(self.result["direct_reffkin_shares"], 3000000)
        self.assertEqual(self.result["trust_shares"], 500000)
        self.assertEqual(self.result["total_form144_reported_shares"], 3500000)

    def test_form144_gross_proceeds_reconcile(self):
        self.assertEqual(self.result["form144_reported_gross_proceeds_usd"], 17131613)

    def test_plan_cap_is_not_treated_as_expected_sales(self):
        self.assertEqual(self.result["plan_maximum_shares"], 10500000)
        self.assertEqual(self.result["observed_sales_as_pct_of_plan_maximum"], "33.3333")

    def test_plan_cap_and_observed_sales_are_scaled_to_outstanding(self):
        self.assertEqual(self.result["plan_maximum_as_pct_of_shares_outstanding"], "2.0784")
        self.assertEqual(self.result["observed_sales_as_pct_of_shares_outstanding"], "0.6928")

    def test_adoption_date_is_not_public_signal_date(self):
        self.assertEqual(self.result["adoption_to_public_filing_calendar_days"], 84)
        self.assertEqual(self.result["item408_filing_date"], "2024-08-02")

    def test_first_sale_follows_public_filing_by_ten_calendar_days(self):
        self.assertEqual(self.result["first_reported_sale_date"], "2024-08-12")
        self.assertEqual(self.result["public_filing_to_first_sale_calendar_days"], 10)

    def test_five_full_sessions_intervened_before_first_sale(self):
        self.assertEqual(
            self.result["full_intervening_trading_sessions"],
            ["2024-08-05", "2024-08-06", "2024-08-07", "2024-08-08", "2024-08-09"],
        )
        self.assertEqual(self.result["first_sale_post_filing_session_rank"], 6)

    def test_selected_form4_rows_are_crosschecks_not_additional_sales(self):
        self.assertEqual(self.result["selected_form4_crosscheck_shares"], 2370000)
        self.assertEqual(self.result["selected_form4_crosscheck_as_pct_of_form144_total"], "67.7143")
        self.assertFalse(self.result["form4_crosschecks_are_added_to_form144_total"])

    def test_form4_reports_postdate_the_transactions(self):
        self.assertTrue(self.result["form4_filings_postdate_their_reported_transactions"])

    def test_unobserved_cap_difference_is_not_called_active(self):
        self.assertEqual(self.result["unobserved_difference_vs_plan_ceiling_shares"], 7000000)
        self.assertFalse(self.result["unobserved_difference_is_active_balance"])

    def test_no_alpha_or_signal_admission(self):
        self.assertEqual(self.result["alpha_test"], "NOT_RUN")
        self.assertEqual(self.result["signal_admission"], "NOT_ADMITTED")
        self.assertEqual(self.result["population_coverage"], "NOT_ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
