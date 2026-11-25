import unittest
from datetime import datetime, timezone

import exchange_calendars as xcals
import pandas as pd

from research.phase612_xnys_session_knowledge_clock import (
    audit_calendar,
    resolve_daily_knowledge_clock,
)

CAL = xcals.get_calendar("XNYS", start="2001-01-01", end="2027-12-31")


class Phase612Tests(unittest.TestCase):
    def test_calendar_coverage_and_official_2026_cross_checks(self):
        result = audit_calendar(CAL)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["session_count"], 3496)
        self.assertEqual(result["early_close_count_1300_et"], 29)
        self.assertTrue(all(result["checks"].values()))

    def test_regular_session_open_and_close(self):
        out = resolve_daily_knowledge_clock(
            "2026-08-26T08:00:00-04:00",
            "2026-08-26",
            "2026-08-26T12:00:00Z",
            CAL,
        )
        self.assertEqual(out["first_event_only_open_session"], "2026-08-26")
        self.assertEqual(out["first_completed_daily_bar_session"], "2026-08-26")
        self.assertEqual(out["first_completed_daily_bar_close_at_utc"], "2026-08-26T20:00:00+00:00")
        self.assertEqual(out["daily_bar_signal_earliest_next_open_session"], "2026-08-27")

    def test_intraday_knowledge_uses_current_session_bar_but_not_past_open(self):
        out = resolve_daily_knowledge_clock(
            "2026-08-26T11:11:54-04:00",
            "2026-08-26",
            "2026-08-26T15:30:00Z",
            CAL,
        )
        self.assertEqual(out["first_event_only_open_session"], "2026-08-27")
        self.assertEqual(out["first_completed_daily_bar_session"], "2026-08-26")
        self.assertEqual(out["daily_bar_signal_earliest_next_open_session"], "2026-08-27")

    def test_first_seen_earlier_than_acceptance_uses_acceptance(self):
        out = resolve_daily_knowledge_clock(
            "2026-08-26T11:11:54-04:00",
            "2026-08-26",
            "2026-08-26T14:00:00Z",
            CAL,
        )
        self.assertEqual(out["effective_knowledge_at_utc"], "2026-08-26T15:11:54+00:00")

    def test_first_seen_later_than_acceptance_controls_knowledge_time(self):
        out = resolve_daily_knowledge_clock(
            "2026-08-26T11:11:54-04:00",
            "2026-08-26",
            "2026-08-26T20:30:00Z",
            CAL,
        )
        self.assertEqual(out["effective_knowledge_at_utc"], "2026-08-26T20:30:00+00:00")
        self.assertEqual(out["first_completed_daily_bar_session"], "2026-08-27")

    def test_exact_close_is_not_treated_as_pre_close(self):
        out = resolve_daily_knowledge_clock(
            "2026-08-26T16:00:00-04:00",
            "2026-08-26",
            "2026-08-26T20:00:00Z",
            CAL,
        )
        self.assertEqual(out["first_completed_daily_bar_session"], "2026-08-27")

    def test_after_close_knowledge_moves_decision_bar_to_next_session(self):
        out = resolve_daily_knowledge_clock(
            "2026-08-26T16:00:01-04:00",
            "2026-08-26",
            "2026-08-26T20:00:01Z",
            CAL,
        )
        self.assertEqual(out["first_completed_daily_bar_session"], "2026-08-27")
        self.assertEqual(out["daily_bar_signal_earliest_next_open_session"], "2026-08-28")

    def test_early_close_uses_actual_1300_et_close(self):
        out = resolve_daily_knowledge_clock(
            "2026-11-27T12:00:00-05:00",
            "2026-11-27",
            "2026-11-27T17:00:00Z",
            CAL,
        )
        self.assertEqual(out["first_completed_daily_bar_session"], "2026-11-27")
        self.assertEqual(out["first_completed_daily_bar_close_at_utc"], "2026-11-27T18:00:00+00:00")
        self.assertEqual(out["daily_bar_signal_earliest_next_open_session"], "2026-11-30")

    def test_exact_early_close_is_not_treated_as_pre_close(self):
        out = resolve_daily_knowledge_clock(
            "2026-11-27T13:00:00-05:00",
            "2026-11-27",
            "2026-11-27T18:00:00Z",
            CAL,
        )
        self.assertEqual(out["first_completed_daily_bar_session"], "2026-11-30")

    def test_exchange_holiday_uses_next_session(self):
        out = resolve_daily_knowledge_clock(
            "2026-07-03T10:00:00-04:00",
            "2026-07-03",
            "2026-07-03T14:00:00Z",
            CAL,
        )
        self.assertEqual(out["first_completed_daily_bar_session"], "2026-07-06")

    def test_weekend_first_seen_uses_next_session_without_backdating_filing_date(self):
        out = resolve_daily_knowledge_clock(
            "2026-08-28T12:00:00-04:00",
            "2026-08-28",
            "2026-08-29T16:00:00Z",
            CAL,
        )
        self.assertEqual(out["first_completed_daily_bar_session"], "2026-08-31")

    def test_after_1730_first_seen_before_legal_filing_floor_is_not_backdated(self):
        out = resolve_daily_knowledge_clock(
            "2026-08-26T18:42:02-04:00",
            "2026-08-27",
            "2026-08-26T23:45:00Z",
            CAL,
        )
        self.assertEqual(out["availability_mode"], "OBSERVED_FIRST_SEEN_BEFORE_LEGAL_FILING_FLOOR")
        self.assertEqual(out["legal_filing_date_floor_utc"], "2026-08-27T10:00:00+00:00")
        self.assertEqual(out["effective_knowledge_at_utc"], "2026-08-27T10:00:00+00:00")
        self.assertEqual(out["first_completed_daily_bar_session"], "2026-08-27")
        self.assertEqual(out["daily_bar_signal_earliest_next_open_session"], "2026-08-28")

    def test_after_1730_first_seen_after_legal_filing_floor_is_preserved(self):
        out = resolve_daily_knowledge_clock(
            "2026-08-26T18:42:02-04:00",
            "2026-08-27",
            "2026-08-27T14:00:00Z",
            CAL,
        )
        self.assertEqual(out["availability_mode"], "OBSERVED_FIRST_SEEN_MAX_ACCEPTED_AND_LEGAL_FLOOR")
        self.assertEqual(out["effective_knowledge_at_utc"], "2026-08-27T14:00:00+00:00")

    def test_after_1730_same_day_first_seen_is_quarantined(self):
        with self.assertRaisesRegex(ValueError, "after_hours_13f_first_seen_before_next_business_day"):
            resolve_daily_knowledge_clock(
                "2026-08-26T18:42:02-04:00",
                "2026-08-27",
                "2026-08-26T23:45:00Z",
                CAL,
            )

    def test_exact_1730_does_not_trigger_after_hours_quarantine(self):
        out = resolve_daily_knowledge_clock(
            "2026-08-26T17:30:00-04:00",
            "2026-08-26",
            "2026-08-26T21:31:00Z",
            CAL,
        )
        self.assertEqual(out["effective_knowledge_at_utc"], "2026-08-26T21:31:00+00:00")

    def test_missing_collector_uses_end_of_legal_filing_date(self):
        out = resolve_daily_knowledge_clock(
            "2026-08-26T11:11:54-04:00",
            "2026-08-26",
            None,
            CAL,
        )
        self.assertEqual(out["availability_mode"], "FILING_DATE_END_OF_DAY_FALLBACK")
        self.assertEqual(out["effective_knowledge_at_utc"], "2026-08-27T03:59:59+00:00")
        self.assertEqual(out["first_completed_daily_bar_session"], "2026-08-27")
        self.assertEqual(out["daily_bar_signal_earliest_next_open_session"], "2026-08-28")

    def test_after_1730_legal_filing_date_fallback_does_not_backdate(self):
        out = resolve_daily_knowledge_clock(
            "2026-08-26T18:42:02-04:00",
            "2026-08-27",
            None,
            CAL,
        )
        self.assertEqual(out["effective_knowledge_at_utc"], "2026-08-28T03:59:59+00:00")
        self.assertEqual(out["first_completed_daily_bar_session"], "2026-08-28")

    def test_dst_conversion_uses_exchange_timezone_not_fixed_offset(self):
        winter = resolve_daily_knowledge_clock(
            "2026-02-27T08:00:00-05:00",
            "2026-02-27",
            "2026-02-27T13:00:00Z",
            CAL,
        )
        summer = resolve_daily_knowledge_clock(
            "2026-03-09T08:00:00-04:00",
            "2026-03-09",
            "2026-03-09T12:00:00Z",
            CAL,
        )
        self.assertEqual(winter["first_completed_daily_bar_close_at_utc"], "2026-02-27T21:00:00+00:00")
        self.assertEqual(summer["first_completed_daily_bar_close_at_utc"], "2026-03-09T20:00:00+00:00")

    def test_naive_timestamps_are_rejected(self):
        with self.assertRaises(ValueError):
            resolve_daily_knowledge_clock(
                datetime(2026, 8, 26, 11, 11, 54),
                "2026-08-26",
                None,
                CAL,
            )

    def test_filing_date_rejects_datetime_objects(self):
        with self.assertRaises(TypeError):
            resolve_daily_knowledge_clock(
                "2026-08-26T11:11:54-04:00",
                datetime(2026, 8, 26, tzinfo=timezone.utc),
                None,
                CAL,
            )


if __name__ == "__main__":
    unittest.main()
