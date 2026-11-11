import unittest
from datetime import date, timedelta

from research.phase255_adv20_source_feasibility import (
    daily_dollar_volume,
    compute_adv20,
    proposed_notional_to_adv20_days,
)


SESSIONS = [
    "2025-03-03", "2025-03-04", "2025-03-05", "2025-03-06", "2025-03-07",
    "2025-03-10", "2025-03-11", "2025-03-12", "2025-03-13", "2025-03-14",
    "2025-03-17", "2025-03-18", "2025-03-19", "2025-03-20", "2025-03-21",
    "2025-03-24", "2025-03-25", "2025-03-26", "2025-03-27", "2025-03-28",
]
EVENT_DATE = "2025-03-31"


def bars(basis="raw"):
    return [
        {
            "date": day,
            "vwap": str(10 + i),
            "volume": "1000",
            "price_basis": basis,
            "volume_basis": basis,
            "status": "VALID",
        }
        for i, day in enumerate(SESSIONS)
    ]


class Phase255Tests(unittest.TestCase):
    def test_raw_vwap_volume_notional(self):
        result = daily_dollar_volume("12.5", "400", "raw", "raw")
        self.assertEqual(result["status"], "VALID")
        self.assertEqual(result["dollar_volume_usd"], "5000.0")

    def test_split_adjusted_pair_is_valid(self):
        result = daily_dollar_volume("12.5", "400", "split_adjusted", "split_adjusted")
        self.assertEqual(result["status"], "VALID")

    def test_raw_and_split_adjusted_basis_cannot_be_mixed(self):
        result = daily_dollar_volume("12.5", "400", "raw", "split_adjusted")
        self.assertEqual(result["status"], "ADJUSTMENT_BASIS_MISMATCH")

    def test_fractional_volume_is_not_truncated(self):
        result = daily_dollar_volume("10", "0.25", "raw", "raw")
        self.assertEqual(result["status"], "VALID")
        self.assertEqual(result["dollar_volume_usd"], "2.50")

    def test_split_adjustment_preserves_dollar_turnover(self):
        raw = daily_dollar_volume("100", "1000", "raw", "raw")
        adjusted = daily_dollar_volume("10", "10000", "split_adjusted", "split_adjusted")
        self.assertEqual(raw["dollar_volume_usd"], adjusted["dollar_volume_usd"])

    def test_dividend_adjusted_basis_is_not_admitted(self):
        result = daily_dollar_volume("12.5", "400", "dividend_adjusted", "dividend_adjusted")
        self.assertEqual(result["status"], "UNSUPPORTED_ADJUSTMENT_BASIS")

    def test_exact_twenty_session_adv20(self):
        result = compute_adv20(bars(), SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "VALID_ADV20")
        self.assertEqual(result["session_count"], 20)
        self.assertEqual(result["adv20_usd"], "19500")

    def test_nineteen_bars_are_missing_not_zero_filled(self):
        result = compute_adv20(bars()[:-1], SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "MISSING_OR_EXTRA_SESSION")

    def test_twenty_one_bars_are_rejected(self):
        extra = bars() + [{
            "date": "2025-02-28", "vwap": "10", "volume": "1000",
            "price_basis": "raw", "volume_basis": "raw",
        }]
        result = compute_adv20(extra, SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "MISSING_OR_EXTRA_SESSION")

    def test_duplicate_bar_session_rejected(self):
        sample = bars()
        sample[-1] = dict(sample[0])
        result = compute_adv20(sample, SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "DUPLICATE_SESSION")

    def test_same_day_bar_rejected(self):
        sample = bars()
        sample[-1]["date"] = EVENT_DATE
        result = compute_adv20(sample, SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "LOOKAHEAD_SESSION_REJECTED")

    def test_future_bar_rejected(self):
        sample = bars()
        sample[-1]["date"] = "2025-04-01"
        result = compute_adv20(sample, SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "LOOKAHEAD_SESSION_REJECTED")

    def test_expected_session_on_event_date_rejected(self):
        expected = list(SESSIONS)
        expected[-1] = EVENT_DATE
        result = compute_adv20(bars(), expected, EVENT_DATE)
        self.assertEqual(result["status"], "LOOKAHEAD_EXPECTED_SESSION_REJECTED")

    def test_expected_session_duplicates_rejected(self):
        expected = list(SESSIONS)
        expected[-1] = expected[-2]
        result = compute_adv20(bars(), expected, EVENT_DATE)
        self.assertEqual(result["status"], "DUPLICATE_EXPECTED_SESSION")

    def test_expected_sessions_must_be_sorted(self):
        expected = list(SESSIONS)
        expected[0], expected[1] = expected[1], expected[0]
        result = compute_adv20(bars(), expected, EVENT_DATE)
        self.assertEqual(result["status"], "UNSORTED_EXPECTED_SESSIONS")

    def test_missing_vwap_rejected(self):
        sample = bars()
        sample[0]["vwap"] = None
        result = compute_adv20(sample, SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "MISSING_OR_INVALID_VWAP_VOLUME")

    def test_missing_volume_rejected(self):
        sample = bars()
        sample[0]["volume"] = None
        result = compute_adv20(sample, SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "MISSING_OR_INVALID_VWAP_VOLUME")

    def test_zero_volume_rejected(self):
        sample = bars()
        sample[0]["volume"] = "0"
        result = compute_adv20(sample, SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "NONPOSITIVE_VWAP_OR_VOLUME")

    def test_zero_vwap_rejected(self):
        sample = bars()
        sample[0]["vwap"] = "0"
        result = compute_adv20(sample, SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "NONPOSITIVE_VWAP_OR_VOLUME")

    def test_negative_volume_rejected(self):
        sample = bars()
        sample[0]["volume"] = "-1"
        result = compute_adv20(sample, SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "NONPOSITIVE_VWAP_OR_VOLUME")

    def test_mixed_basis_across_sessions_rejected(self):
        sample = bars()
        sample[-1]["price_basis"] = "split_adjusted"
        sample[-1]["volume_basis"] = "split_adjusted"
        result = compute_adv20(sample, SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "MIXED_SESSION_ADJUSTMENT_BASIS")

    def test_invalid_bar_status_rejected(self):
        sample = bars()
        sample[4]["status"] = "MISSING"
        result = compute_adv20(sample, SESSIONS, EVENT_DATE)
        self.assertEqual(result["status"], "INVALID_OR_MISSING_BAR")

    def test_proposed_notional_adv20_ratio(self):
        adv = compute_adv20(bars(), SESSIONS, EVENT_DATE)
        result = proposed_notional_to_adv20_days("39000", adv)
        self.assertEqual(result["status"], "VALID_PROPOSED_NOTIONAL_ADV20_DAYS")
        self.assertEqual(result["days"], "2")

    def test_nonpositive_proposed_notional_rejected(self):
        adv = compute_adv20(bars(), SESSIONS, EVENT_DATE)
        result = proposed_notional_to_adv20_days("0", adv)
        self.assertEqual(result["status"], "NONPOSITIVE_OR_INVALID_NOTIONAL")

    def test_invalid_event_date_rejected(self):
        result = compute_adv20(bars(), SESSIONS, "not-a-date")
        self.assertEqual(result["status"], "INVALID_EVENT_FILING_DATE")

    def test_expected_session_count_must_be_twenty(self):
        result = compute_adv20(bars(), SESSIONS[:-1], EVENT_DATE)
        self.assertEqual(result["status"], "INVALID_EXPECTED_SESSION_COUNT")


if __name__ == "__main__":
    unittest.main()
