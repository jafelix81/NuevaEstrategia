import unittest

from research.phase475_delisted_price_source_feasibility import load_summary, validate


class Phase475Tests(unittest.TestCase):
    def setUp(self):
        self.summary = load_summary()

    def test_provider_set_is_complete(self):
        self.assertEqual(validate(self.summary), [])

    def test_massive_is_conditional_not_admitted(self):
        massive = next(p for p in self.summary["providers"] if p["name"] == "Massive")
        self.assertEqual(massive["rank"], 1)
        self.assertEqual(massive["disposition"], "conditional_primary_price_panel_candidate")
        self.assertFalse(massive["sample_verified"])

    def test_massive_developer_plan_misses_exact_start(self):
        massive = next(p for p in self.summary["providers"] if p["name"] == "Massive")
        self.assertFalse(massive["developer_plan_10y_exact_window_pass"])
        self.assertEqual(self.summary["phase20c"]["exact_window_start"], "2016-10-24")

    def test_massive_bars_are_not_dividend_adjusted(self):
        massive = next(p for p in self.summary["providers"] if p["name"] == "Massive")
        self.assertTrue(massive["raw_bars_available"])
        self.assertFalse(massive["dividend_adjusted_bars"])

    def test_sharadar_record_known_clock_is_unknown(self):
        sharadar = next(p for p in self.summary["providers"] if p["name"] == "Sharadar SEP")
        self.assertIn("not established", sharadar["record_known_vintages"])

    def test_eodhd_is_secondary_only(self):
        eodhd = next(p for p in self.summary["providers"] if p["name"] == "EOD Historical Data")
        self.assertFalse(eodhd["delisted_completeness_guaranteed"])
        self.assertFalse(eodhd["historical_versioning"])
        self.assertEqual(eodhd["disposition"], "secondary_cross_check_only")

    def test_crsp_terminal_return_fields_are_preserved(self):
        crsp = next(p for p in self.summary["providers"] if p["name"] == "CRSP US Stock Database")
        self.assertTrue({"DLRET", "DLRETX", "DLPRC", "DLPDT", "DLAMT"}.issubset(set(crsp["delisting_fields"])))

    def test_norgate_not_selected_for_terminal_repair(self):
        norgate = next(p for p in self.summary["providers"] if p["name"] == "Norgate")
        self.assertFalse(norgate["delisting_return_or_terminal_recovery_field"])
        self.assertEqual(norgate["license"], "personal non-commercial only")

    def test_seven_inactive_symbols_remain_in_universe(self):
        self.assertEqual(
            set(self.summary["phase20c"]["inactive_missing"]),
            {"AVB", "EA", "EQR", "LPRO", "ROKU", "WBD", "WBS"},
        )
        self.assertEqual(self.summary["phase20c"]["universe_count"], 335)

    def test_no_price_or_alpha_test_is_claimed(self):
        admission = self.summary["admission"]
        for key in admission:
            self.assertFalse(admission[key], key)


if __name__ == "__main__":
    unittest.main()
