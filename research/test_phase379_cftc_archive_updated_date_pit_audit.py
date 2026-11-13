import unittest
from datetime import date
from research.phase379_cftc_archive_updated_date_pit_audit import parse_archive_dates, report_filename

class Phase379Tests(unittest.TestCase):
    def test_parse_report_and_updated_dates(self):
        html="""<html><pre>Traders in Financial Futures - Futures Only Positions as of October 27, 2026
        ...
        Updated October 30, 2026</pre></html>"""
        report,updated=parse_archive_dates(html)
        self.assertEqual(report.isoformat(),"2026-10-27")
        self.assertEqual(updated.isoformat(),"2026-10-30")

    def test_reject_missing_updated_date(self):
        with self.assertRaises(ValueError):
            parse_archive_dates("<pre>Positions as of October 27, 2026</pre>")

    def test_filename_is_deterministic(self):
        self.assertEqual(report_filename("2017-10-03"),"financial_lf100317.htm")
        self.assertEqual(report_filename("2026-10-27"),"financial_lf102726.htm")

    def test_archive_updated_date_is_not_first_publication_claim(self):
        html="<pre>Positions as of November 10, 2025\nUpdated December 10, 2025</pre>"
        report,updated=parse_archive_dates(html)
        self.assertGreater(updated,report)

if __name__=="__main__":
    unittest.main()
