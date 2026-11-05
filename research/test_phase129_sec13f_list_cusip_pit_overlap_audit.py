import unittest
from datetime import date
from research.phase129_sec13f_list_cusip_pit_overlap_audit import (
    parse_cusip_line, parse_run_metadata, quarter_iter, select_latest
)

class Phase129Tests(unittest.TestCase):
    def test_parse_spaced_cusip_with_option_marker(self):
        self.assertEqual(parse_cusip_line("B38564 10 8 *  CMB.TECH NV  SHS"), "B38564108")

    def test_parse_spaced_alphanumeric_cusip(self):
        self.assertEqual(parse_cusip_line("C00948 20 5  AGRIFORCE GROWERS INC"), "C00948205")

    def test_parse_compact_cusip(self):
        self.assertEqual(parse_cusip_line("037833100  APPLE INC COM"), "037833100")

    def test_ignore_header_and_page_lines(self):
        self.assertIsNone(parse_cusip_line("CUSIP NO.  ISSUER NAME"))
        self.assertIsNone(parse_cusip_line("Run Date: 10/1/2025"))
        self.assertIsNone(parse_cusip_line("Page 1 of 4"))

    def test_parse_run_metadata(self):
        d, t, q = parse_run_metadata("Run Date: 10/1/2025\nRun Time: 10:03\nYear: 2025 Qtr: 3")
        self.assertEqual(d, date(2025, 10, 1))
        self.assertEqual(t, "10:03")
        self.assertEqual(q, "2025Q3")

    def test_quarter_iterator(self):
        values = list(quarter_iter(2015, 3, 2016, 1))
        self.assertEqual(values, [(2015, 3), (2015, 4), (2016, 1)])

    def test_latest_prior_snapshot(self):
        snaps = [
            {"quarter": "2025Q2", "available": "2025-07-07"},
            {"quarter": "2025Q3", "available": "2025-10-07"},
        ]
        got = select_latest(snaps, date(2025, 10, 6), "available")
        self.assertEqual(got["quarter"], "2025Q2")

if __name__ == "__main__":
    unittest.main()
