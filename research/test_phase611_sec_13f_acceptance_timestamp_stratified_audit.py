import unittest
from unittest.mock import patch

from research.phase611_sec_13f_acceptance_timestamp_stratified_audit import (
    parse_filing_detail_html,
    select_stratified_samples,
    build_index_url,
    normalize_dataset_date,
    audit_sample,
)


class Phase611Tests(unittest.TestCase):
    def test_parses_identity_and_accepted_timestamp_with_dst_conversion(self):
        html = b"""<html>
        <div>Form 13F-HR/A - Quarterly report filed by institutional managers</div>
        <div>SEC Accession No. 0001951757-26-001605</div>
        <div class="infoHead">Filing Date</div><div class="info">2026-08-26</div>
        <div class="infoHead">Accepted</div><div class="info">2026-08-26 11:11:54</div>
        <div class="infoHead">Period of Report</div><div class="info">2025-09-30</div>
        <div>Dakota Wealth Management (Filer) CIK: 0001631353</div>
        </html>"""
        out = parse_filing_detail_html(html)
        self.assertEqual(out["accession_from_page"], "0001951757-26-001605")
        self.assertEqual(out["filer_cik_from_page"], "0001631353")
        self.assertEqual(out["form_type"], "13F-HR/A")
        self.assertEqual(out["accepted_at_et"], "2026-08-26 11:11:54")
        self.assertEqual(out["accepted_at_utc"], "2026-08-26T15:11:54+00:00")
        self.assertTrue(out["accepted_date_matches_filing_date"])
        self.assertEqual(out["period_of_report"], "2025-09-30")
        self.assertEqual(out["accepted_clock_bucket"], "REGULAR_SESSION_CLOCK_WEEKDAY")
        self.assertFalse(out["accepted_on_weekend"])

    def test_dataset_dates_are_normalized_from_sec_tsv_format(self):
        self.assertEqual(normalize_dataset_date("07-FEB-2018"), "2018-02-07")
        self.assertEqual(normalize_dataset_date("31-DEC-2017"), "2017-12-31")
        self.assertEqual(normalize_dataset_date("2026-08-26"), "2026-08-26")
        self.assertIsNone(normalize_dataset_date("not-a-date"))

    def test_after_close_and_weekend_are_distinguished(self):
        after_close = parse_filing_detail_html(
            b"<html>Accepted: 2026-08-26 16:00:00 Filing Date: 2026-08-26</html>"
        )
        weekend = parse_filing_detail_html(
            b"<html>Accepted: 2026-08-29 10:00:00 Filing Date: 2026-08-29</html>"
        )
        self.assertEqual(after_close["accepted_clock_bucket"], "AFTER_CLOSE_WEEKDAY")
        self.assertEqual(weekend["accepted_clock_bucket"], "WEEKEND")
        self.assertTrue(weekend["accepted_on_weekend"])

    def test_after_1730_acceptance_rolls_to_next_sec_business_day(self):
        out = parse_filing_detail_html(
            b"<html>Accepted: 2026-08-10 18:42:02 Filing Date: 2026-08-11</html>"
        )
        self.assertTrue(out["accepted_after_1730_et"])
        self.assertFalse(out["accepted_date_matches_filing_date"])
        self.assertEqual(
            out["filing_date_clock_reconciliation"],
            "AFTER_1730_NEXT_SEC_BUSINESS_DAY",
        )

    def test_friday_after_1730_rolls_to_monday(self):
        out = parse_filing_detail_html(
            b"<html>Accepted: 2026-07-17 20:00:00 Filing Date: 2026-07-20</html>"
        )
        self.assertEqual(
            out["filing_date_clock_reconciliation"],
            "AFTER_1730_NEXT_SEC_BUSINESS_DAY",
        )

    def test_federal_holiday_rollover_is_respected(self):
        out = parse_filing_detail_html(
            b"<html>Accepted: 2026-12-24 20:00:00 Filing Date: 2026-12-28</html>"
        )
        self.assertEqual(
            out["filing_date_clock_reconciliation"],
            "AFTER_1730_NEXT_SEC_BUSINESS_DAY",
        )

    def test_before_cutoff_cannot_roll_to_next_filing_date(self):
        out = parse_filing_detail_html(
            b"<html>Accepted: 2026-08-26 17:00:00 Filing Date: 2026-08-27</html>"
        )
        self.assertEqual(out["filing_date_clock_reconciliation"], "MISMATCH")

    def test_weekend_acceptance_is_not_valid(self):
        out = parse_filing_detail_html(
            b"<html>Accepted: 2026-08-29 10:00:00 Filing Date: 2026-08-31</html>"
        )
        self.assertEqual(
            out["filing_date_clock_reconciliation"],
            "INVALID_NON_BUSINESS_DAY_ACCEPTANCE",
        )

    def test_missing_acceptance_is_not_imputed(self):
        out = parse_filing_detail_html(
            b"<html>SEC Accession No. 0000000001-26-000001 Filing Date: 2026-08-26</html>"
        )
        self.assertIsNone(out["accepted_at_et"])
        self.assertIsNone(out["accepted_at_utc"])
        self.assertIsNone(out["accepted_date_matches_filing_date"])
        self.assertIsNone(out["accepted_clock_bucket"])

    def test_stratified_selection_is_deterministic_and_spans_form_types(self):
        filers = {}
        for i, date in enumerate(
            ["2018-01-05", "2018-01-15", "2018-02-05", "2018-03-20"],
            start=1,
        ):
            accession = f"0000000001-18-{i:06d}"
            filers[accession] = {
                "cik": f"{i:010d}",
                "submission_type": "13F-HR",
                "report_type": "13F HOLDINGS",
                "filing_date": date,
                "report_period": "2017-12-31",
            }
        filers["0000000002-18-000001"] = {
            "cik": "0000000002",
            "submission_type": "13F-NT",
            "report_type": "13F NOTICE",
            "filing_date": "2018-02-15",
            "report_period": "2017-12-31",
        }
        a = select_stratified_samples("2018_q1", filers, per_stratum=4)
        b = select_stratified_samples("2018_q1", filers, per_stratum=4)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 5)
        self.assertEqual({x["submission_type"] for x in a}, {"13F-HR", "13F-NT"})
        self.assertEqual(len({x["accession"] for x in a}), len(a))

    def test_archive_path_uses_filer_cik_not_accession_prefix(self):
        sample = {
            "filer_cik_from_dataset": "0001631353",
            "accession": "0001951757-26-001605",
        }
        url = build_index_url(sample)
        self.assertIn("/data/1631353/000195175726001605/", url)
        self.assertNotIn("/data/1951757/", url)


    def test_filer_cik_is_verified_from_canonical_archive_path(self):
        sample = {
            "dataset": "2026_jun_jul_aug",
            "accession": "0001951757-26-001605",
            "filer_cik_from_dataset": "0001631353",
            "submission_type": "13F-HR/A",
            "report_type": "13F HOLDINGS",
            "filing_date_from_dataset": "2026-08-26",
            "period_of_report_from_dataset": "2025-09-30",
        }
        html = b"""<html>
        Form 13F-HR/A - Quarterly report
        SEC Accession No. 0001951757-26-001605
        Filing Date 2026-08-26
        Accepted 2026-08-26 11:11:54
        Period of Report 2025-09-30
        </html>"""
        url = build_index_url(sample)
        with patch(
            "research.phase611_sec_13f_acceptance_timestamp_stratified_audit.fetch_page",
            return_value=(html, url, 200),
        ):
            out = audit_sample(sample, "test-agent")
        self.assertTrue(out["checks"]["filer_cik_path_matches"])
        self.assertTrue(out["checks"]["accession_matches"])
        self.assertEqual(out["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
