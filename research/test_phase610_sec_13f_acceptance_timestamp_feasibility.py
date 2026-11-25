import unittest

from research.phase610_sec_13f_acceptance_timestamp_feasibility import parse_filing_detail_html


class Phase610Tests(unittest.TestCase):
    def test_extracts_accepted_filing_and_period_dates(self):
        html = b"""<html><div class="infoHead">Filing Date</div><div class="info">2026-11-24</div>
        <div class="infoHead">Accepted</div><div class="info">2026-11-24 16:06:20</div>
        <div class="infoHead">Period of Report</div><div class="info">2026-09-30</div></html>"""
        out = parse_filing_detail_html(html)
        self.assertEqual(out["filing_date"], "2026-11-24")
        self.assertEqual(out["accepted_at_et"], "2026-11-24 16:06:20")
        self.assertEqual(out["period_of_report"], "2026-09-30")
        self.assertTrue(out["accepted_date_matches_filing_date"])
        self.assertEqual(out["conservative_knowledge_date_after_filing_date"], "2026-11-25")

    def test_missing_acceptance_timestamp_is_not_imputed(self):
        html = b"""<html><div class="infoHead">Filing Date</div><div class="info">2018-02-14</div></html>"""
        out = parse_filing_detail_html(html)
        self.assertIsNone(out["accepted_at_et"])
        self.assertIsNone(out["accepted_date_matches_filing_date"])
        self.assertIsNone(out["conservative_knowledge_date_after_filing_date"])
        self.assertFalse(out["timestamp_present"])

    def test_same_line_label_and_value_are_supported(self):
        html = b"<html>Accepted: 2018-02-14 13:05:02 Filing Date: 2018-02-14</html>"
        out = parse_filing_detail_html(html)
        self.assertEqual(out["accepted_at_et"], "2018-02-14 13:05:02")
        self.assertEqual(out["filing_date"], "2018-02-14")
        self.assertTrue(out["accepted_date_matches_filing_date"])


if __name__ == "__main__":
    unittest.main()
