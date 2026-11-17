import unittest

from research.phase460_form4_split_event_guard import classify_split_remarks


class Phase460SplitEventTests(unittest.TestCase):
    def test_reporting_person_limit_split_is_candidate_not_auto_merged(self):
        remarks = (
            "This Form 4 is the first of two Forms 4 filed relating to the same event. "
            "The form has been split because there are more than 10 reporting persons."
        )
        result = classify_split_remarks(remarks)
        self.assertTrue(result["explicit_split_candidate"])
        self.assertEqual(result["split_reason"], "reporting_person_limit")
        self.assertFalse(result["automatic_cross_accession_merge"])

    def test_transaction_row_limit_split_is_candidate_not_auto_merged(self):
        remarks = (
            "This Form 4 is the second of two Forms 4 being filed by the Reporting Person "
            "relating to transactions that occurred on July 6, 2026. Because there are more "
            "than 30 rows associated with the Reporting Person's transactions on that date, "
            "and EDGAR will not allow more than 30 rows on a single Form 4, "
            "the two Forms 4 should be read together as one consolidated filing."
        )
        result = classify_split_remarks(remarks)
        self.assertTrue(result["explicit_split_candidate"])
        self.assertEqual(result["split_reason"], "transaction_row_limit")
        self.assertFalse(result["automatic_cross_accession_merge"])
        self.assertTrue(result["do_not_deduplicate_transaction_rows_without_line_level_evidence"])

    def test_same_date_without_explicit_split_language_is_not_grouped(self):
        result = classify_split_remarks("Transactions occurred on July 6, 2026.")
        self.assertFalse(result["explicit_split_candidate"])
        self.assertFalse(result["automatic_cross_accession_merge"])

    def test_first_of_two_without_same_event_or_consolidated_filing_is_not_grouped(self):
        result = classify_split_remarks("This is the first of two Forms 4 filed today.")
        self.assertFalse(result["explicit_split_candidate"])

    def test_case_and_whitespace_are_normalized(self):
        result = classify_split_remarks(
            " THIS FORM 4 IS THE FIRST OF TWO FORMS 4. RELATING TO THE SAME EVENT. "
            "MORE THAN 10 REPORTING PERSONS "
        )
        self.assertTrue(result["explicit_split_candidate"])
        self.assertEqual(result["split_reason"], "reporting_person_limit")


if __name__ == "__main__":
    unittest.main()
