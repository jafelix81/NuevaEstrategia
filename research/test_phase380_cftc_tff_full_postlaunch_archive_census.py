import unittest
from datetime import date
from research.phase380_cftc_tff_full_postlaunch_archive_census import parse_archive_dates, report_filename, FIRST_TFF_REPORT_DATE

class Phase380Tests(unittest.TestCase):
    def test_first_tff_report_date(self):
        self.assertEqual(FIRST_TFF_REPORT_DATE.isoformat(),"2010-07-20")

    def test_first_report_filename(self):
        self.assertEqual(report_filename("2010-07-20"),"financial_lf072010.htm")

    def test_parse_first_report_page_dates(self):
        html="<pre>Traders in Financial Futures - Futures Only Positions as of July 20, 2010\nUpdated July 23, 2010</pre>"
        report,updated=parse_archive_dates(html)
        self.assertEqual(report.isoformat(),"2010-07-20")
        self.assertEqual(updated.isoformat(),"2010-07-23")

    def test_parse_shutdown_late_archive_update(self):
        html="<pre>Positions as of December 23, 2025\nUpdated December 31, 2025</pre>"
        report,updated=parse_archive_dates(html)
        self.assertEqual((updated-report).days,8)

    def test_filename_deterministic(self):
        self.assertEqual(report_filename("2026-10-27"),"financial_lf102726.htm")

if __name__=="__main__":
    unittest.main()
