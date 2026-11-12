import unittest

from phase302_form4a_daily_index_pac_clock_audit import (
    build_accession_clock,
    index_window_dates,
    pair_clock,
    previous_business_day,
)
from phase283_sec_daily_index_parser import parse_daily_form_index


ACCESSION = "0000000123-23-000001"
ISSUER = "0000000123"
INDEX_ROW = (
    b"Description: Form 4 filings\n"
    b"CIK|Company Name|Form Type|Date Filed|Filename\n"
    b"--------------------------------------------------------------------------------\n"
    b"123|Example Company|4|2023-05-01|/Archives/edgar/data/123/000000012323000001.txt\n"
)


class Phase302Tests(unittest.TestCase):
    def test_previous_business_day_skips_weekend_and_juneteenth(self):
        self.assertEqual(previous_business_day(__import__("datetime").date(2023, 6, 20)).isoformat(), "2023-06-16")

    def test_index_window_includes_negative_control_and_skips_federal_holiday(self):
        self.assertEqual(
            index_window_dates("2023-06-30"),
            ["2023-06-29", "2023-06-30", "2023-07-03", "2023-07-05", "2023-07-06"],
        )

    def test_index_window_is_deterministic_for_weekend_filing_date(self):
        self.assertEqual(
            index_window_dates("2023-07-01"),
            ["2023-06-30", "2023-07-01", "2023-07-03", "2023-07-05", "2023-07-06"],
        )

    def test_daily_index_pre_filing_row_is_quarantined_not_backdated(self):
        parsed = parse_daily_form_index(INDEX_ROW, "form.20230428.idx")
        self.assertEqual(parsed["records"], [])
        self.assertEqual(parsed["counts"]["index_date_before_filing_date"], 1)
        self.assertEqual(parsed["quarantine"][0]["reason"], "index_date_precedes_filing_date")

    def test_daily_index_later_sighting_retains_positive_lag(self):
        parsed = parse_daily_form_index(INDEX_ROW, "form.20230502.idx")
        self.assertEqual(len(parsed["records"]), 1)
        self.assertEqual(parsed["records"][0]["index_date_lag_days"], 1)

    def test_complete_window_identity_match_is_window_verified(self):
        parsed = parse_daily_form_index(INDEX_ROW, "form.20230501.idx")
        expected = {
            "accession": ACCESSION,
            "document_type": "4",
            "filing_date": "2023-05-01",
            "issuer_cik": ISSUER,
            "index_window_dates": ["2023-04-28", "2023-05-01", "2023-05-02"],
        }
        result = build_accession_clock(expected, parsed["records"], [], True)
        self.assertEqual(result["index_status"], "INDEX_IDENTITY_MATCH_WINDOW_COMPLETE")
        self.assertTrue(result["daily_index_identity_match"])
        self.assertTrue(result["first_index_date_is_window_verified"])
        self.assertEqual(result["first_observed_index_lag_days"], 0)

    def test_incomplete_window_does_not_promote_observed_date_to_verified(self):
        parsed = parse_daily_form_index(INDEX_ROW, "form.20230501.idx")
        expected = {
            "accession": ACCESSION,
            "document_type": "4",
            "filing_date": "2023-05-01",
            "issuer_cik": ISSUER,
            "index_window_dates": ["2023-04-28", "2023-05-01", "2023-05-02"],
        }
        result = build_accession_clock(expected, parsed["records"], [], False)
        self.assertEqual(result["index_status"], "INDEX_IDENTITY_MATCH_WINDOW_INCOMPLETE")
        self.assertFalse(result["first_index_date_is_window_verified"])

    def test_same_daily_index_date_does_not_claim_intraday_pac_order(self):
        parent = {
            "header_reconciled": True,
            "index_window_complete": True,
            "first_observed_index_date_within_window": "2023-05-01",
            "acceptance_datetime_et": "2023-05-01T16:10:00-04:00",
        }
        child = {
            "header_reconciled": True,
            "index_window_complete": True,
            "first_observed_index_date_within_window": "2023-05-01",
            "acceptance_datetime_et": "2023-05-01T17:10:00-04:00",
        }
        self.assertEqual(
            pair_clock(parent, child)["status"],
            "SAME_INDEX_DATE_INTRADAY_ORDER_UNRESOLVED",
        )

    def test_later_child_index_date_is_ordered_after_parent_at_daily_grain(self):
        parent = {
            "header_reconciled": True,
            "index_window_complete": True,
            "first_observed_index_date_within_window": "2023-05-01",
            "acceptance_datetime_et": "2023-05-01T16:10:00-04:00",
        }
        child = {
            "header_reconciled": True,
            "index_window_complete": True,
            "first_observed_index_date_within_window": "2023-05-02",
            "acceptance_datetime_et": "2023-05-02T09:10:00-04:00",
        }
        self.assertEqual(pair_clock(parent, child)["status"], "PARENT_INDEX_DATE_PRECEDES_AMENDMENT")

    def test_child_index_before_parent_is_quarantined(self):
        parent = {
            "header_reconciled": True,
            "index_window_complete": True,
            "first_observed_index_date_within_window": "2023-05-02",
            "acceptance_datetime_et": "2023-05-01T16:10:00-04:00",
        }
        child = {
            "header_reconciled": True,
            "index_window_complete": True,
            "first_observed_index_date_within_window": "2023-05-01",
            "acceptance_datetime_et": "2023-05-02T09:10:00-04:00",
        }
        self.assertEqual(pair_clock(parent, child)["status"], "AMENDMENT_INDEX_PRECEDES_CANDIDATE_PARENT")

    def test_acceptance_order_conflict_is_not_overridden_by_index_dates(self):
        parent = {
            "header_reconciled": True,
            "index_window_complete": True,
            "first_observed_index_date_within_window": "2023-05-01",
            "acceptance_datetime_et": "2023-05-02T09:10:00-04:00",
        }
        child = {
            "header_reconciled": True,
            "index_window_complete": True,
            "first_observed_index_date_within_window": "2023-05-03",
            "acceptance_datetime_et": "2023-05-01T16:10:00-04:00",
        }
        self.assertEqual(pair_clock(parent, child)["status"], "ACCEPTANCE_ORDER_CONFLICT")

    def test_incomplete_index_window_blocks_pair_clock(self):
        parent = {
            "header_reconciled": True,
            "index_window_complete": False,
            "first_observed_index_date_within_window": "2023-05-01",
            "acceptance_datetime_et": "2023-05-01T16:10:00-04:00",
        }
        child = {
            "header_reconciled": True,
            "index_window_complete": True,
            "first_observed_index_date_within_window": "2023-05-02",
            "acceptance_datetime_et": "2023-05-02T09:10:00-04:00",
        }
        self.assertEqual(pair_clock(parent, child)["status"], "INDEX_WINDOW_INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
