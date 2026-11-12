import unittest
from research.phase319_sec_daily_index_live_pilot import (
    SAMPLE_DATES, normalize_accession, parse_filing_header, quarter_path, select_sample_records,
    verify_header_against_index,
)


class Phase319Tests(unittest.TestCase):
    def test_seven_dates_cover_2006_to_2026(self):
        self.assertEqual(len(SAMPLE_DATES), 7)
        self.assertEqual(SAMPLE_DATES[0], "2006-01-03")
        self.assertEqual(SAMPLE_DATES[-1], "2026-11-10")

    def test_quarter_path_mapping(self):
        self.assertEqual(
            quarter_path("2006-01-03")[2],
            "edgar/daily-index/2006/QTR1/form.20060103.idx",
        )
        self.assertEqual(
            quarter_path("2023-04-03")[2],
            "edgar/daily-index/2023/QTR2/form.20230403.idx",
        )
        self.assertEqual(
            quarter_path("2026-11-10")[2],
            "edgar/daily-index/2026/QTR4/form.20261110.idx",
        )

    def test_accession_normalization(self):
        self.assertEqual(normalize_accession("0001193125-26-000001"), "0001193125-26-000001")
        self.assertEqual(normalize_accession("000119312526000001"), "0001193125-26-000001")
        self.assertEqual(normalize_accession("bad"), "")

    def test_parses_label_style_original_header(self):
        raw = b"""ACCESSION NUMBER: 0001193125-26-000001
CONFORMED SUBMISSION TYPE: 4/A
CENTRAL INDEX KEY: 0000320193
FILED AS OF DATE: 20260102
<ACCEPTANCE-DATETIME>20260102123456</ACCEPTANCE-DATETIME>
"""
        parsed = parse_filing_header(raw)
        self.assertEqual(parsed["accession"], "0001193125-26-000001")
        self.assertEqual(parsed["form_type"], "4/A")
        self.assertEqual(parsed["cik"], "320193")
        self.assertEqual(parsed["filed_date"], "2026-01-02")
        self.assertEqual(parsed["acceptance_datetime_et"], "20260102123456")

    def test_missing_acceptance_is_not_silently_filled(self):
        raw = b"""ACCESSION NUMBER: 0001193125-26-000001
CONFORMED SUBMISSION TYPE: 4
CENTRAL INDEX KEY: 0000320193
FILED AS OF DATE: 20260102
"""
        parsed = parse_filing_header(raw)
        self.assertEqual(parsed["acceptance_datetime_et"], "")

    def test_deterministic_sample_one_per_form(self):
        rows = [
            {"form_type": "4", "accession": "0000000001-26-000001"},
            {"form_type": "4", "accession": "0000000002-26-000002"},
            {"form_type": "4/A", "accession": "0000000003-26-000003"},
        ]
        a = select_sample_records(rows, "2026-01-02")
        b = select_sample_records(rows, "2026-01-02")
        self.assertEqual(a, b)
        self.assertEqual({x["form_type"] for x in a}, {"4", "4/A"})
        self.assertEqual(len(a), 2)

    def test_header_reconciliation_is_explicit(self):
        row = {"accession": "0001193125-26-000001", "form_type": "4",
               "cik": "320193", "filing_date": "2026-01-02"}
        header = {"accession": "0001193125-26-000001", "form_type": "4",
                  "cik": "320193", "filed_date": "2026-01-02",
                  "acceptance_datetime_et": "20260102123456"}
        self.assertTrue(all(verify_header_against_index(row, header).values()))


if __name__ == "__main__":
    unittest.main()
