import unittest
from phase228_13dg_regulatory_regime_split_audit import summarize, CUTOFFS

class Phase228Tests(unittest.TestCase):
    def row(self, lag, weight=1.0, qend=False, amend=False):
        return {
            "event_date": "2024-03-31" if qend else "2024-03-20",
            "filing_minus_event_days": lag,
            "sample_weight": weight,
            "event_date_is_quarter_end": qend,
            "index_form_suffix_is_amendment": amend,
        }

    def test_weighted_quantiles_and_coverage(self):
        s = summarize([self.row(2, 1), self.row(40, 9, True)])
        self.assertEqual(s["parsed_n"], 2)
        self.assertEqual(s["lag_median_calendar_days_weighted"], 40.0)
        self.assertEqual(s["quarter_end_sample_weighted_pct_within_parsed"], 90.0)

    def test_missing_event_is_not_zero_lag(self):
        missing = self.row(0)
        missing["event_date"] = ""
        s = summarize([missing, self.row(4)])
        self.assertEqual(s["parsed_n"], 1)
        self.assertEqual(s["same_day_event_filing_n"], 0)

    def test_empty_group(self):
        s = summarize([])
        self.assertEqual(s["n"], 0)
        self.assertIsNone(s["lag_median_calendar_days_weighted"])

    def test_cutoffs_are_family_specific(self):
        self.assertEqual(CUTOFFS["13D"].isoformat(), "2024-02-05")
        self.assertEqual(CUTOFFS["13G"].isoformat(), "2024-09-30")

if __name__ == "__main__":
    unittest.main(verbosity=2)
