import unittest
from datetime import date
from research.phase383_cftc_russell_eminifutures_pit_panel_audit import parse_archive_dates, filename, SERIES_START

class Phase383Tests(unittest.TestCase):
    def test_series_start_is_post_2017_contract_era(self):
        self.assertEqual(SERIES_START.isoformat(),"2017-08-15")

    def test_filename(self):
        self.assertEqual(filename(date(2018,9,25)),"financial_lf092518.htm")

    def test_parse_valid_archive_dates(self):
        report,updated=parse_archive_dates("<pre>Positions as of October 27, 2026\nUpdated October 30, 2026</pre>")
        self.assertEqual(report.isoformat(),"2026-10-27")
        self.assertEqual(updated.isoformat(),"2026-10-30")

    def test_parse_stale_updated_date_for_exclusion(self):
        report,updated=parse_archive_dates("<pre>Positions as of May 10, 2011\nUpdated May 13, 2010</pre>")
        self.assertLess(updated,report)

    def test_missing_updated_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_archive_dates("<pre>Positions as of May 10, 2011</pre>")

if __name__=="__main__":
    unittest.main()
