import unittest
from datetime import date, timedelta
from research.phase381_finra_price_provider_fallback_audit import (
    epoch, summarize_series, compare_returns, public_record,
)

class Phase381Tests(unittest.TestCase):
    def test_fixed_window_epoch(self):
        self.assertEqual(epoch("2016-10-24"),1477267200)

    def test_series_summary_uses_valid_rows(self):
        result=summarize_series("AAPL","test",["2024-01-02","2024-01-03"],[100,101],"ok")
        self.assertEqual(result["rows"],2)
        self.assertEqual(result["first_date"],"2024-01-02")
        self.assertEqual(result["last_date"],"2024-01-03")

    def test_cross_provider_return_comparison(self):
        start=date(2024,1,2)
        dates=[(start+timedelta(days=i)).isoformat() for i in range(31)]
        a={d:100.0+i for i,d in enumerate(dates)}
        b={d:2.0*(100.0+i) for i,d in enumerate(dates)}
        result=compare_returns(a,b)
        self.assertEqual(result["common_dates"],31)
        self.assertEqual(result["return_pairs"],30)
        self.assertAlmostEqual(result["median_abs_return_diff"],0.0,places=12)

    def test_provider_comparison_requires_overlap(self):
        result=compare_returns({"2024-01-02":1.0},{"2024-01-02":1.0})
        self.assertEqual(result["return_pairs"],0)
        self.assertIsNone(result["return_corr"])

    def test_public_record_does_not_retain_prices(self):
        result=summarize_series("AAPL","test",["2024-01-02"],[100],"ok")
        public=public_record(result)
        self.assertNotIn("_series",public)
        self.assertNotIn("_adj_series",public)

if __name__=="__main__":
    unittest.main()
