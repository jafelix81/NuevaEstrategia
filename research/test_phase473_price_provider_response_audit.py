import unittest

from research.phase473_price_provider_response_audit import (
    CONTROLS,
    MISSING,
    build_summary,
    classify_provider,
    valid_close_dates,
    normalize_nasdaq_date,
)


def records(provider, control_rows, missing_rows):
    out = []
    for ticker, rows in zip(CONTROLS, control_rows):
        out.append({"ticker": ticker, "provider": provider, "rows": rows, "status": "ok" if rows else "empty"})
    for ticker, rows in zip(MISSING, missing_rows):
        out.append({"ticker": ticker, "provider": provider, "rows": rows, "status": "ok" if rows else "empty"})
    return out


class Phase473Tests(unittest.TestCase):
    def test_controls_empty_means_provider_method_unvalidated(self):
        result = classify_provider(records("nasdaq", [0, 0, 0, 0], [0] * 7), "nasdaq")
        self.assertFalse(result["method_validated_by_controls"])
        self.assertEqual(result["disposition"], "PROVIDER_METHOD_UNVALIDATED_CONTROLS_INSUFFICIENT")

    def test_controls_pass_but_missing_empty_is_not_global_no_history_claim(self):
        result = classify_provider(records("yahoo", [100, 101, 102, 103], [0] * 7), "yahoo")
        self.assertTrue(result["method_validated_by_controls"])
        self.assertEqual(result["disposition"], "VALID_CONTROLS_BUT_MISSING_SYMBOL_RESPONSES_EMPTY")
        self.assertNotIn("NO_HISTORY", result["disposition"])

    def test_partial_missing_symbol_coverage_is_reported(self):
        result = classify_provider(records("stooq", [100, 100, 100, 0], [0, 25, 0, 0, 0, 0, 0]), "stooq")
        self.assertTrue(result["method_validated_by_controls"])
        self.assertEqual(result["missing_symbol_nonempty_count"], 1)
        self.assertEqual(result["disposition"], "VALID_CONTROLS_AND_SOME_MISSING_SYMBOL_HISTORY")

    def test_failed_provider_rows_do_not_become_zero_history_evidence(self):
        sample = [
            {"ticker": "AAPL", "provider": "stooq", "rows": 0, "status": "request_or_parse_error", "http_status": None},
            {"ticker": "AVB", "provider": "stooq", "rows": 0, "status": "request_or_parse_error", "http_status": None},
        ]
        result = classify_provider(sample, "stooq")
        self.assertEqual(result["control_nonempty_count"], 0)
        self.assertFalse(result["method_validated_by_controls"])

    def test_yahoo_timestamp_without_close_is_not_a_price_observation(self):
        dates = valid_close_dates([1792800000, 1792886400], [None, 0])
        self.assertEqual(dates, [])

    def test_yahoo_counts_only_positive_finite_close_dates(self):
        dates = valid_close_dates([1792800000, 1792886400, 1792972800], [10.0, None, float("nan")])
        self.assertEqual(len(dates), 1)

    def test_nasdaq_dates_are_normalized_chronologically(self):
        self.assertEqual(normalize_nasdaq_date("10/24/2016"), "2016-10-24")
        self.assertEqual(normalize_nasdaq_date("2026-10-23"), "2026-10-23")
        self.assertEqual(normalize_nasdaq_date("not-a-date"), None)

    def test_summary_is_metadata_only_and_fallback_remains_false(self):
        rows = records("yahoo", [10, 10, 10, 10], [0] * 7)
        summary = build_summary(rows)
        self.assertFalse(summary["raw_price_data_retained"])
        self.assertFalse(summary["raw_provider_response_bodies_retained"])
        self.assertFalse(summary["fallback_accepted"])
        forbidden = {"open", "high", "low", "close", "adjclose", "price", "volume", "bid", "ask"}
        self.assertTrue(forbidden.isdisjoint(set(summary.keys())))


if __name__ == "__main__":
    unittest.main()
