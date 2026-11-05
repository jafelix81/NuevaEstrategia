import unittest
from datetime import date

from research.phase103_sec_midas_security_audit import (
    FEED_BREAK,
    REQUIRED,
    ROUND_LOT_BREAK,
    SAMPLES,
    detect_delimiter,
    normalize_name,
    parse_date,
)


class Phase103MidasTests(unittest.TestCase):
    def test_required_columns_match_sec_page_schema(self):
        self.assertIn("ticker", REQUIRED)
        self.assertIn("date", REQUIRED)
        self.assertIn("hiddenvol('000)", REQUIRED)
        self.assertIn("tradevolforhidden('000)", REQUIRED)
        self.assertIn("tradesforodd lots".replace(" ", ""), REQUIRED)
        self.assertNotIn("trades", REQUIRED)

    def test_header_normalization_preserves_unit_suffix(self):
        self.assertEqual(normalize_name("LitVol('000)"), "litvol('000)")
        self.assertEqual(normalize_name("TradeVolForOddLots('000)"), "tradevolforoddlots('000)")

    def test_delimiter_detection(self):
        self.assertEqual(detect_delimiter("Ticker,Date,Security"), ",")
        self.assertEqual(detect_delimiter("Ticker|Date|Security"), "|")

    def test_date_formats(self):
        self.assertEqual(parse_date("2016-01-04"), date(2016, 1, 4))
        self.assertEqual(parse_date("20160104"), date(2016, 1, 4))
        self.assertIsNone(parse_date("bad-date"))

    def test_methodology_breaks_are_explicit(self):
        self.assertEqual(FEED_BREAK, date(2017, 5, 1))
        self.assertEqual(ROUND_LOT_BREAK, date(2025, 11, 3))

    def test_sample_urls_are_sec_official(self):
        self.assertEqual(len(SAMPLES), 6)
        self.assertTrue(all(x["url"].startswith("https://www.sec.gov/") for x in SAMPLES))
        self.assertEqual({x["key"] for x in SAMPLES}, {"2012q1", "2016q1", "2017q2", "2019q4", "2025q4", "2026q2"})


if __name__ == "__main__":
    unittest.main()
