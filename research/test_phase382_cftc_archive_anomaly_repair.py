import unittest
from datetime import date
from research.phase382_cftc_archive_anomaly_repair import candidate_dates, filename, parse_dates

class Phase382Tests(unittest.TestCase):
    def test_neighbor_search_includes_target_and_adjacent_weeks(self):
        ds=candidate_dates("2018-09-25")
        self.assertIn(date(2018,9,25),ds)
        self.assertIn(date(2018,9,18),ds)
        self.assertIn(date(2018,10,2),ds)
        self.assertEqual(len(ds),5)

    def test_filename(self):
        self.assertEqual(filename(date(2018,9,25)),"financial_lf092518.htm")

    def test_parse_dates(self):
        report,updated=parse_dates("<pre>Positions as of May 10, 2011\nUpdated May 13, 2010</pre>")
        self.assertEqual(report.isoformat(),"2011-05-10")
        self.assertEqual(updated.isoformat(),"2010-05-13")

    def test_missing_updated_field_is_preserved_as_missing(self):
        report,updated=parse_dates("<pre>Positions as of May 10, 2011</pre>")
        self.assertEqual(report.isoformat(),"2011-05-10")
        self.assertIsNone(updated)

if __name__=="__main__":
    unittest.main()
