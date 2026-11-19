from __future__ import annotations

import unittest

from research.phase498_sec_form4_poll_cadence_interval_audit import build_summary, quantile


def event(run_id, status, lower="", upper="", research="False", signal="False"):
    return {
        "first_seen_poll_run_id": run_id,
        "first_seen_interval_status": status,
        "first_seen_interval_lower_bound_utc": lower,
        "first_seen_interval_upper_bound_utc": upper,
        "research_observation_eligible": research,
        "signal_eligible": signal,
    }


def feed(run_id, received):
    return {"poll_run_id": run_id, "response_received_at_utc": received}


class Phase498Tests(unittest.TestCase):
    def setUp(self):
        self.events = [
            event("baseline", "INITIAL_BASELINE_NO_LOWER_BOUND"),
            event("r2", "BOUNDED_METADATA_ONLY", "2026-11-18T19:00:00Z", "2026-11-19T01:00:00Z"),
            event("r3", "BOUNDED_METADATA_ONLY", "2026-11-19T01:00:00Z", "2026-11-19T09:00:00Z"),
        ]
        self.feeds = [
            feed("baseline", "2026-11-18T19:00:00Z"),
            feed("r2", "2026-11-19T01:00:00Z"),
            feed("r3", "2026-11-19T09:00:00Z"),
        ]
        self.state = {"last_poll_run_id": "r3", "last_poll_ended_utc": "2026-11-19T09:00:00Z"}
        self.workflow = 'schedule:\n  - cron: "17 * * * 1-5"\n'

    def test_baseline_is_excluded_from_interval_distribution(self):
        result = build_summary(self.events, self.feeds, self.state, self.workflow)
        self.assertEqual(result["event_ledger"]["total_rows"], 3)
        self.assertEqual(result["event_ledger"]["initial_baseline_without_lower_bound_rows"], 1)
        self.assertEqual(result["event_ledger"]["bounded_metadata_only_rows"], 2)
        self.assertEqual(result["event_ledger"]["interval_width_hours"]["min"], 6.0)

    def test_poll_gap_uses_prior_end_to_next_start(self):
        result = build_summary(self.events, self.feeds, self.state, self.workflow)
        self.assertEqual(result["collector"]["observed_poll_gap_hours"], [6.0, 8.0])

    def test_negative_interval_is_rejected(self):
        bad = [self.events[0], event("r2", "BOUNDED_METADATA_ONLY", "2026-11-19T02:00:00Z", "2026-11-19T01:00:00Z")]
        with self.assertRaisesRegex(ValueError, "negative_first_seen_interval"):
            build_summary(bad, self.feeds, self.state, self.workflow)

    def test_signal_eligibility_is_fail_closed(self):
        bad = [self.events[0], event("r2", "BOUNDED_METADATA_ONLY", "2026-11-18T19:00:00Z", "2026-11-19T01:00:00Z", signal="True")]
        with self.assertRaisesRegex(ValueError, "signal_eligibility_must_remain_false"):
            build_summary(bad, self.feeds, self.state, self.workflow)

    def test_research_eligibility_is_fail_closed(self):
        bad = [event("r2", "BOUNDED_METADATA_ONLY", "2026-11-18T19:00:00Z", "2026-11-19T01:00:00Z", research="True")]
        with self.assertRaisesRegex(ValueError, "research_observation_eligibility_must_remain_false"):
            build_summary(bad, self.feeds, self.state, self.workflow)

    def test_unknown_interval_status_is_rejected(self):
        bad = [event("r2", "EXACT_PUBLICATION")]
        with self.assertRaisesRegex(ValueError, "unexpected_interval_status"):
            build_summary(bad, self.feeds, self.state, self.workflow)

    def test_quantile_interpolates(self):
        self.assertEqual(quantile([1.0, 3.0], 0.5), 2.0)

    def test_schedule_is_recorded(self):
        result = build_summary(self.events, self.feeds, self.state, self.workflow)
        self.assertEqual(result["collector"]["declared_schedule_cron_utc"], "17 * * * 1-5")
        self.assertFalse(result["decision"]["nominal_hourly_cadence_demonstrated"])

    def test_missing_timezone_is_rejected(self):
        bad = [self.events[0], event("r2", "BOUNDED_METADATA_ONLY", "2026-11-18T19:00:00", "2026-11-19T01:00:00Z")]
        with self.assertRaisesRegex(ValueError, "timestamp_must_be_timezone_aware"):
            build_summary(bad, self.feeds, self.state, self.workflow)


if __name__ == "__main__":
    unittest.main()
