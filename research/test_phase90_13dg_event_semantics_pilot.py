import unittest

from research.phase90_13dg_event_semantics_pilot import (
    classify_predecessor, event_lag_days, previous_accession_field_status,
)


class Phase90EventSemanticsTests(unittest.TestCase):
    def test_event_lag_is_filing_date_minus_reported_event_date(self):
        self.assertEqual(event_lag_days("2025-01-01", "2025-01-10"), 9)
        self.assertEqual(event_lag_days("01/01/2025", "2025-01-10"), 9)
        self.assertEqual(event_lag_days("2025-01-11", "2025-01-10"), -1)
        self.assertIsNone(event_lag_days("", "2025-01-10"))

    def test_previous_accession_field_absent_empty_and_populated_are_distinct(self):
        self.assertEqual(previous_accession_field_status("<headerData></headerData>"), "field_absent")
        self.assertEqual(previous_accession_field_status("<previousAccessionNumber/>"), "field_empty")
        self.assertEqual(
            previous_accession_field_status("<previousAccessionNumber>0000000001-24-000001</previousAccessionNumber>"),
            "field_nonempty",
        )

    def test_predecessor_must_match_subject_family_and_be_earlier(self):
        prior = {
            "0000000001-24-000001": {
                "subject_cik": "0000000001",
                "form_family": "13D",
                "filing_date": "2024-01-01",
            }
        }
        current = {
            "subject_cik": "0000000001",
            "form_family": "13D",
            "filing_date": "2024-02-01",
            "is_amendment": True,
        }
        self.assertEqual(
            classify_predecessor(current, "0000000001-24-000001", prior),
            "predecessor_in_sample_consistent",
        )
        self.assertEqual(
            classify_predecessor(current, "0000000002-24-000001", prior),
            "predecessor_outside_sample",
        )

    def test_predecessor_subject_and_family_mismatches_are_flagged(self):
        prior = {
            "0000000001-24-000001": {
                "subject_cik": "0000000002",
                "form_family": "13G",
                "filing_date": "2024-01-01",
            }
        }
        current = {
            "subject_cik": "0000000001",
            "form_family": "13D",
            "filing_date": "2024-02-01",
            "is_amendment": True,
        }
        self.assertEqual(
            classify_predecessor(current, "0000000001-24-000001", prior),
            "predecessor_subject_mismatch",
        )

    def test_amendment_without_predecessor_is_not_silently_treated_as_original(self):
        current = {
            "subject_cik": "0000000001",
            "form_family": "13D",
            "filing_date": "2024-02-01",
            "is_amendment": True,
        }
        self.assertEqual(
            classify_predecessor(current, "", {}),
            "amendment_missing_predecessor",
        )


if __name__ == "__main__":
    unittest.main()
