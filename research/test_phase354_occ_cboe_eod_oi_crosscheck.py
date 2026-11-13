import io
import unittest
import zipfile

from research.phase354_occ_cboe_eod_oi_crosscheck import (
    choose_alignment,
    compare_field,
    extract_csv_members,
    normalize_option_symbol,
    parse_cboe_eod_sample,
    parse_date,
    parse_integer,
    parse_occ_report,
)


class Phase354OICrosscheckTests(unittest.TestCase):
    def test_osi_normalization_removes_padding_spaces_only(self):
        self.assertEqual(
            normalize_option_symbol(" AAPL  250328C00100000 "),
            "AAPL250328C00100000",
        )

    def test_osi_normalization_rejects_blank(self):
        self.assertIsNone(normalize_option_symbol("   "))

    def test_integer_parser_accepts_grouped_and_decimal_integer(self):
        self.assertEqual(parse_integer("12,345"), 12345)
        self.assertEqual(parse_integer("12345.0"), 12345)

    def test_integer_parser_rejects_fraction_and_non_numeric(self):
        self.assertIsNone(parse_integer("12.5"))
        self.assertIsNone(parse_integer("N/A"))

    def test_date_parser_handles_iso_and_us_date(self):
        self.assertEqual(parse_date("2025-03-28"), "2025-03-28")
        self.assertEqual(parse_date("03/28/2025"), "2025-03-28")
        self.assertIsNone(parse_date("03/04/05"))

    def test_occ_parser_reads_preamble_and_exact_symbol_oi(self):
        payload = (
            b"Daily Open Interest Report\n"
            b"Option Symbol,Underlying Symbol,Open Interest\n"
            b"AAPL  250328C00100000,AAPL,12345\n"
        )
        parsed = parse_occ_report(payload, "2025-03-28")
        self.assertEqual(parsed["row_count"], 1)
        self.assertEqual(parsed["unique_symbol_count"], 1)
        self.assertEqual(
            parsed["index"]["AAPL250328C00100000"],
            [12345],
        )

    def test_occ_parser_preserves_duplicate_keys_as_ambiguous(self):
        payload = (
            b"Option Symbol,Open Interest\n"
            b"AAPL  250328C00100000,100\n"
            b"AAPL250328C00100000,100\n"
        )
        parsed = parse_occ_report(payload, "2025-03-28")
        self.assertEqual(parsed["duplicate_symbol_count"], 1)
        result = compare_field(
            [{"option_symbol": "AAPL250328C00100000", "open_interest": 100}],
            "open_interest",
            parsed["index"],
        )
        self.assertEqual(result["ambiguous_occ_rows"], 1)
        self.assertEqual(result["matched_unique_occ_rows"], 0)

    def test_compare_field_reports_exact_and_mismatched_values(self):
        rows = [
            {"option_symbol": "AAPL250328C00100000", "open_interest": 100},
            {"option_symbol": "AAPL250328P00100000", "open_interest": 125},
        ]
        index = {
            "AAPL250328C00100000": [100],
            "AAPL250328P00100000": [120],
        }
        result = compare_field(rows, "open_interest", index)
        self.assertEqual(result["valid_cboe_rows"], 2)
        self.assertEqual(result["matched_unique_occ_rows"], 2)
        self.assertEqual(result["exact_matches"], 1)
        self.assertEqual(result["mismatches"], 1)
        self.assertEqual(result["median_absolute_difference"], 2.5)

    def test_compare_field_does_not_turn_missing_occ_into_zero(self):
        rows = [
            {"option_symbol": "AAPL250328C00100000", "open_interest": 0},
            {"option_symbol": "MSFT250328C00100000", "open_interest": 10},
            {"option_symbol": None, "open_interest": 20},
            {"option_symbol": "NVDA250328C00100000", "open_interest": None},
        ]
        result = compare_field(
            rows,
            "open_interest",
            {"AAPL250328C00100000": [0]},
        )
        self.assertEqual(result["exact_matches"], 1)
        self.assertEqual(result["missing_occ_rows"], 1)
        self.assertEqual(result["invalid_cboe_rows"], 2)

    def test_alignment_requires_large_coverage_and_unique_margin(self):
        comparisons = [
            {
                "field": "open_interest", "report_date": "2025-03-27",
                "matched_unique_occ_rows": 2000, "coverage_rate": 0.90,
                "exact_match_rate": 0.995,
            },
            {
                "field": "open_interest", "report_date": "2025-03-28",
                "matched_unique_occ_rows": 2000, "coverage_rate": 0.90,
                "exact_match_rate": 0.980,
            },
        ]
        result = choose_alignment(comparisons, "open_interest")
        self.assertEqual(result["status"], "UNIQUE_STRONG_MATCH")
        self.assertEqual(result["best_report_date"], "2025-03-27")

    def test_alignment_remains_unresolved_when_dates_tie(self):
        comparisons = [
            {
                "field": "previous_open_interest", "report_date": "2025-03-26",
                "matched_unique_occ_rows": 2000, "coverage_rate": 0.90,
                "exact_match_rate": 1.0,
            },
            {
                "field": "previous_open_interest", "report_date": "2025-03-27",
                "matched_unique_occ_rows": 2000, "coverage_rate": 0.90,
                "exact_match_rate": 1.0,
            },
        ]
        result = choose_alignment(comparisons, "previous_open_interest")
        self.assertEqual(result["status"], "UNRESOLVED_OR_AMBIGUOUS")

    def test_nested_zip_csv_extraction(self):
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "sample_eod.csv",
                "quote_date,underlying_symbol,option_symbol,open_interest,previous_open_interest\n"
                "2025-03-28,AAPL,AAPL  250328C00100000,100,90\n",
            )
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("nested.zip", inner.getvalue())
        members = extract_csv_members(outer.getvalue())
        self.assertEqual(len(members), 1)
        self.assertIn("sample_eod.csv", members[0][0])

    def test_cboe_sample_parser_selects_one_eod_member(self):
        sample = io.BytesIO()
        with zipfile.ZipFile(sample, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "EOD_Sample.csv",
                "quote_date,underlying_symbol,option_symbol,open_interest,previous_open_interest\n"
                "03/28/2025,AAPL,AAPL  250328C00100000,100,90\n"
                "03/28/2025,MSFT,MSFT  250328C00100000,200,180\n",
            )
            archive.writestr(
                "intraday_sample.csv",
                "trading_dt,underlying_symbol,option_symbol\n"
                "2025-03-28,AAPL,AAPL  250328C00100000\n",
            )
        parsed = parse_cboe_eod_sample(sample.getvalue())
        self.assertEqual(parsed["quote_dates"], ["2025-03-28"])
        self.assertEqual(parsed["row_count"], 2)
        self.assertEqual(parsed["underlying_count"], 2)
        self.assertEqual(parsed["rows"][0]["open_interest"], 100)

    def test_cboe_parser_rejects_multiple_eod_members_not_pool_them(self):
        sample = io.BytesIO()
        with zipfile.ZipFile(sample, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in ("one_eod.csv", "two_eod.csv"):
                archive.writestr(
                    name,
                    "quote_date,underlying_symbol,option_symbol,open_interest,previous_open_interest\n"
                    "2025-03-28,AAPL,AAPL  250328C00100000,100,90\n",
                )
        with self.assertRaises(ValueError):
            parse_cboe_eod_sample(sample.getvalue())


if __name__ == "__main__":
    unittest.main()
