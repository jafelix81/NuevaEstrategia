import io
import unittest
import zipfile

from research.phase61_orats_near_eod_sample_audit import (
    compute_coverage,
    extract_csvs,
    field_stats,
    find_field,
    parse_csv,
)


class OratsNearEodSampleTests(unittest.TestCase):
    def test_parse_csv_and_resolve_fields(self):
        raw = (
            b"ticker,tradeDate,expirDate,strike,cVolu,pVolu,cOi,pOi,delta\n"
            b"AAPL,2024-01-03,2024-02-16,180,100,80,500,400,0.55\n"
            b"XYZ,2024-01-03,2024-02-16,10,0,20,0,100,-0.20\n"
        )
        headers, rows = parse_csv(raw)
        self.assertEqual(len(rows), 2)
        self.assertEqual(find_field(headers, ("tradeDate", "trade_date")), "tradeDate")
        self.assertEqual(find_field(headers, ("expirDate", "expiration")), "expirDate")

    def test_field_stats_keep_zero_distinct_from_missing(self):
        rows = [{"oi": "0"}, {"oi": "10"}, {"oi": ""}]
        stats = field_stats(rows, "oi")
        self.assertEqual(stats["nonnull_rate"], 2 / 3)
        self.assertEqual(stats["positive_rate_of_numeric"], 0.5)
        self.assertEqual(stats["zero_rate_of_numeric"], 0.5)

    def test_nested_zip_csv_extraction(self):
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("sample.csv", "ticker,strike\nAAPL,100\n")
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("nested.zip", inner.getvalue())
        found = extract_csvs(outer.getvalue())
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0][0].endswith("nested.zip!sample.csv"))

    def test_universe_coverage(self):
        result = compute_coverage({"AAPL", "MSFT", "XYZ"}, {"AAPL", "XYZ", "SPY"})
        self.assertEqual(result["observed_universe_tickers"], 2)
        self.assertAlmostEqual(result["coverage_rate"], 2 / 3)
        self.assertEqual(result["missing_tickers"], ["MSFT"])


if __name__ == "__main__":
    unittest.main()
