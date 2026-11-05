import unittest
from datetime import date

from research.phase102_sec_ftd_multiperiod_audit import (
    BREAK,
    EXPECTED_HEADER,
    normalize_row,
    parse_page_links,
    parse_text_member,
)


class Phase102FtdTests(unittest.TestCase):
    def test_page_links_extract_exact_zip_names(self):
        html = '<a href="/files/data/other/fails-deliver-data/cnsfails2008q3.zip">Q3</a>'
        links = parse_page_links(html)
        self.assertIn("cnsfails2008q3.zip", links)

    def test_normalize_pipe_row_with_extra_delimiter_in_description(self):
        row = ["20260915", "123456789", "ABC", "10000", "Issuer|Class A", "12.5"]
        self.assertEqual(normalize_row(row), ["20260915", "123456789", "ABC", "10000", "Issuer|Class A", "12.5"])

    def test_normalize_five_fields_adds_missing_price(self):
        self.assertEqual(normalize_row(["20260915", "123456789", "ABC", "10000", "Issuer"]), 
                         ["20260915", "123456789", "ABC", "10000", "Issuer", "."])

    def test_parser_validates_header_and_rows(self):
        body = "|".join(EXPECTED_HEADER) + "\n"
        body += "20260915|123456789|ABC|10000|Issuer|12.50\n"
        result = parse_text_member(body.encode("latin-1"), "sample.txt")
        self.assertEqual(result["valid_records"], 1)
        self.assertEqual(result["records"][0]["settlement_date"], "2026-09-15")
        self.assertEqual(result["bad_fields"], {})

    def test_parser_reconciles_trailer(self):
        body = "|".join(EXPECTED_HEADER) + "\n"
        body += "20260915|123456789|ABC|10000|Issuer|12.50\n"
        body += "Trailer record count 1\n"
        body += "Trailer total quantity of shares 10000\n"
        result = parse_text_member(body.encode("latin-1"), "sample.txt")
        self.assertTrue(result["trailer_count_match"])
        self.assertTrue(result["trailer_quantity_match"])

    def test_threshold_boundary_is_september_16_2008(self):
        self.assertEqual(BREAK, date(2008, 9, 16))
        self.assertLess(date(2008, 9, 15), BREAK)
        self.assertGreaterEqual(date(2008, 9, 16), BREAK)


if __name__ == "__main__":
    unittest.main()
