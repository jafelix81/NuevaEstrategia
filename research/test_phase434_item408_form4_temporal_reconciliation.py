import unittest

from research.phase434_item408_form4_temporal_reconciliation import (
    analyze_casebook,
    cooling_off_dates,
    load_casebook,
)


class Phase434Item408Form4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.casebook = load_casebook()
        cls.result = analyze_casebook(cls.casebook)
        cls.by_name = {case["insider"]: case for case in cls.result["cases"]}

    def test_gina_cooling_off_dates_follow_cdi_120_29(self):
        dates = cooling_off_dates("2023-07-28", "2023-10-26")
        self.assertEqual(dates["ninety_day_date"], "2023-10-26")
        self.assertEqual(dates["two_business_days_after_filing"], "2023-10-30")
        self.assertEqual(dates["threshold_date"], "2023-10-30")
        self.assertEqual(dates["first_session_after_threshold"], "2023-10-31")

    def test_gina_october_9_s_sales_are_flagged_as_pre_threshold_not_illegal(self):
        case = self.by_name["Gina Mastantuono"]
        first = case["observed_plan_linked_s_sales"][0]
        self.assertEqual(first["transaction_date"], "2023-10-09")
        self.assertEqual(first["shares_total"], 386)
        self.assertTrue(first["before_item408_threshold"])
        self.assertTrue(first["before_form4_footnote_threshold"])
        self.assertEqual(case["legal_conclusion"], "not_assessed")

    def test_non_s_rows_are_not_counted_as_plan_linked_s_supply(self):
        case = self.by_name["Gina Mastantuono"]
        self.assertTrue(all(s["transaction_code"] == "S" for s in case["observed_plan_linked_s_sales"]))
        self.assertEqual(case["observed_plan_linked_s_sales"][0]["row_count"], 2)
        self.assertEqual(case["observed_plan_linked_s_sales"][0]["shares_total"], 386)

    def test_gina_november_sale_is_after_calculated_threshold(self):
        case = self.by_name["Gina Mastantuono"]
        later = next(s for s in case["observed_plan_linked_s_sales"] if s["transaction_date"] == "2023-11-01")
        self.assertEqual(later["shares_total"], 922)
        self.assertFalse(later["before_item408_threshold"])

    def test_item408_was_after_ginas_first_observed_sale(self):
        case = self.by_name["Gina Mastantuono"]
        self.assertEqual(case["item408_filing_lead_days_to_first_observed_sale"], -17)
        self.assertFalse(case["item408_precedes_first_observed_sale"])

    def test_william_first_observed_sale_is_after_both_dates(self):
        case = self.by_name["William R. McDermott"]
        self.assertEqual(case["first_observed_plan_linked_s_sale_date"], "2024-02-20")
        self.assertEqual(case["cooling_off_using_item408_date"]["first_session_after_threshold"], "2023-11-30")
        self.assertFalse(case["has_sale_before_item408_calculated_threshold"])
        self.assertTrue(case["item408_precedes_first_observed_sale"])

    def test_paul_has_ten_day_plan_date_cross_source_mismatch(self):
        case = self.by_name["Paul E. Chamberlain"]
        self.assertEqual(case["plan_date_discrepancy_days_form4_minus_item408"], 10)
        self.assertEqual(
            case["cooling_off_using_item408_date"]["first_session_after_threshold"], "2023-11-20"
        )
        self.assertEqual(
            case["cooling_off_using_form4_footnote_date"]["first_session_after_threshold"], "2023-11-30"
        )
        self.assertEqual(case["first_observed_plan_linked_s_sale_date"], "2023-11-30")
        self.assertFalse(case["has_sale_before_item408_calculated_threshold"])
        self.assertFalse(case["has_sale_before_form4_footnote_calculated_threshold"])

    def test_william_unknown_aggregate_quantity_is_not_fabricated(self):
        case = self.by_name["William R. McDermott"]
        self.assertIsNone(case["observed_plan_linked_s_sales"][0]["shares_total"])

    def test_aff10b5one_is_preserved_as_form_level_metadata(self):
        case = self.by_name["Gina Mastantuono"]
        self.assertTrue(case["observed_plan_linked_s_sales"][0]["form4_aff10b5one"])
        self.assertIsNone(
            next(s for s in case["observed_plan_linked_s_sales"] if s["transaction_date"] == "2023-11-01")[
                "form4_aff10b5one"
            ]
        )

    def test_casebook_summary_counts_are_descriptive_only(self):
        summary = self.result["summary"]
        self.assertEqual(summary["plan_count"], 3)
        self.assertEqual(summary["plans_with_item408_vs_form4_adoption_date_mismatch"], 1)
        self.assertEqual(summary["plans_with_observed_s_sale_before_item408_filing"], 1)
        self.assertEqual(summary["plans_with_observed_s_sale_before_item408_calculated_threshold"], 1)
        self.assertEqual(summary["plans_with_item408_filing_before_first_observed_s_sale"], 2)
        self.assertEqual(summary["alpha_test"], "NOT_RUN")
        self.assertEqual(summary["legal_compliance_assessment"], "NOT_ASSESSED")


if __name__ == "__main__":
    unittest.main()
