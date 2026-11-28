"""Offline regression tests for the Phase 48 SEC 13F state machine."""
from __future__ import annotations

import unittest

from research.phase48_sec_13f_asof_amendment_state_machine import (
    StateMachineError,
    first_full_session_after,
    reconstruct_as_of,
    select_latest_holdings_period,
)


SESSIONS = ["2026-05-15", "2026-05-18", "2026-05-19", "2026-05-20", "2026-05-21", "2026-05-22", "2026-05-26"]


def event(accession, filing_date, submission_type="13F-HR", number="", amendment_type="", flag="N"):
    return {
        "accession": accession,
        "manager_cik": "123",
        "report_period": "2026-03-31",
        "filing_date": filing_date,
        "submission_type": submission_type,
        "is_amendment": flag,
        "amendment_number": number,
        "amendment_type": amendment_type,
    }


def holding(cusip, shares, value, discretion="SOLE"):
    return {
        "cusip": cusip,
        "title_of_class": "COM",
        "put_call": "",
        "investment_discretion": discretion,
        "other_manager": "",
        "amount_type": "SH",
        "shares": str(shares),
        "value": str(value),
    }


def manager_event(
    accession,
    filing_date,
    manager_cik,
    report_period,
    submission_type="13F-HR",
    number="",
    amendment_type="",
    flag="N",
):
    row = event(accession, filing_date, submission_type, number, amendment_type, flag)
    row["manager_cik"] = manager_cik
    row["report_period"] = report_period
    return row


LATE_FILING_SESSIONS = [
    "2026-08-14",
    "2026-08-17",
    "2026-11-06",
    "2026-11-09",
    "2026-11-27",
    "2026-11-30",
    "2026-12-01",
]


class Phase48Tests(unittest.TestCase):
    def test_first_eligible_session_is_strictly_after_filing_date(self):
        self.assertEqual(first_full_session_after("2026-05-15", SESSIONS), "2026-05-18")
        self.assertEqual(first_full_session_after("2026-05-16", SESSIONS), "2026-05-18")

    def test_new_holdings_then_restatement_reconstruct_as_of_correctly(self):
        events = [
            event("ORIG", "2026-05-15"),
            event("ADD1", "2026-05-20", "13F-HR/A", "1", "NEW HOLDINGS ENTRIES", "Y"),
            event("REST2", "2026-05-22", "13F-HR/A", "2", "RESTATEMENT", "Y"),
        ]
        holdings = {
            "ORIG": [holding("111111111", 100, 1000)],
            "ADD1": [holding("222222222", 200, 2000)],
            "REST2": [holding("111111111", 150, 1800)],
        }

        before_original = reconstruct_as_of(events, holdings, SESSIONS, "2026-05-15")
        self.assertEqual(before_original["manager_periods"], [])
        self.assertEqual(before_original["summary"]["applied_accessions"], 0)

        after_original = reconstruct_as_of(events, holdings, SESSIONS, "2026-05-18")
        self.assertEqual(after_original["manager_periods"][0]["holdings_count"], 1)
        self.assertEqual(after_original["manager_periods"][0]["applied_accessions"], ["ORIG"])

        after_add = reconstruct_as_of(events, holdings, SESSIONS, "2026-05-21")
        add_state = after_add["manager_periods"][0]
        self.assertEqual(add_state["holdings_count"], 2)
        self.assertEqual(add_state["applied_accessions"], ["ORIG", "ADD1"])

        after_restatement = reconstruct_as_of(events, holdings, SESSIONS, "2026-05-26")
        restated = after_restatement["manager_periods"][0]
        self.assertEqual(restated["holdings_count"], 1)
        self.assertEqual(restated["holdings"][0]["cusip"], "111111111")
        self.assertEqual(restated["holdings"][0]["shares"], "150")
        self.assertEqual(restated["applied_accessions"], ["ORIG", "ADD1", "REST2"])
        self.assertFalse(after_restatement["summary"]["signal_eligible"])

    def test_same_day_original_and_numbered_amendment_are_only_known_next_session(self):
        events = [
            event("ORIG", "2026-05-15"),
            event("ADD1", "2026-05-15", "13F-HR", "1", "NEW HOLDINGS", "Y"),
        ]
        holdings = {
            "ORIG": [holding("111111111", 100, 1000)],
            "ADD1": [holding("222222222", 200, 2000)],
        }
        same_day = reconstruct_as_of(events, holdings, SESSIONS, "2026-05-15")
        self.assertEqual(same_day["manager_periods"], [])
        next_session = reconstruct_as_of(events, holdings, SESSIONS, "2026-05-18")
        self.assertEqual(next_session["manager_periods"][0]["holdings_count"], 2)

    def test_13f_nt_is_notice_not_zero_holdings(self):
        notices = [event("NOTICE", "2026-05-15", "13F-NT", flag="")]
        result = reconstruct_as_of(notices, {}, SESSIONS, "2026-05-18")
        self.assertEqual(result["manager_periods"], [])
        self.assertEqual(result["notices"][0]["status"], "NOTICE_ONLY_NOT_ZERO_HOLDINGS")
        self.assertEqual(result["summary"]["notice_only_events"], 1)

    def test_new_holdings_overlap_blocks_instead_of_overwriting(self):
        events = [
            event("ORIG", "2026-05-15"),
            event("ADD1", "2026-05-20", "13F-HR/A", "1", "NEW HOLDINGS", "Y"),
        ]
        holdings = {
            "ORIG": [holding("111111111", 100, 1000)],
            "ADD1": [holding("111111111", 150, 1800)],
        }
        result = reconstruct_as_of(events, holdings, SESSIONS, "2026-05-21")
        group = result["manager_periods"][0]
        self.assertEqual(group["status"], "BLOCKED")
        self.assertEqual(group["reason"], "new_holdings_amendment_overlaps_existing_line")
        self.assertEqual(group["holdings"], [])

    def test_missing_holding_payload_blocks(self):
        events = [event("ORIG", "2026-05-15")]
        result = reconstruct_as_of(events, {}, SESSIONS, "2026-05-18")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["manager_periods"][0]["reason"], "missing_holding_rows:ORIG")

    def test_amendment_without_original_fails_closed(self):
        events = [event("ADD1", "2026-05-20", "13F-HR/A", "1", "RESTATEMENT", "Y")]
        with self.assertRaisesRegex(StateMachineError, "exactly_one_original"):
            reconstruct_as_of(events, {"ADD1": [holding("111111111", 100, 1000)]}, SESSIONS, "2026-05-21")

    def test_amendment_number_gap_fails_closed(self):
        events = [
            event("ORIG", "2026-05-15"),
            event("ADD2", "2026-05-22", "13F-HR/A", "2", "RESTATEMENT", "Y"),
        ]
        with self.assertRaisesRegex(StateMachineError, "amendment_number_gap"):
            reconstruct_as_of(events, {"ORIG": [holding("111111111", 100, 1000)], "ADD2": [holding("222222222", 100, 1000)]}, SESSIONS, "2026-05-26")

    def test_duplicate_line_key_within_accession_blocks(self):
        events = [event("ORIG", "2026-05-15")]
        rows = [holding("111111111", 100, 1000), holding("111111111", 200, 2000)]
        result = reconstruct_as_of(events, {"ORIG": rows}, SESSIONS, "2026-05-18")
        self.assertEqual(result["manager_periods"][0]["status"], "BLOCKED")
        self.assertEqual(result["manager_periods"][0]["reason"], "duplicate_line_key_within_accession:ORIG")

    def test_multiple_originals_fail_closed(self):
        events = [event("ORIG1", "2026-05-15"), event("ORIG2", "2026-05-16")]
        rows = {"ORIG1": [holding("111111111", 100, 1000)], "ORIG2": [holding("222222222", 100, 1000)]}
        with self.assertRaisesRegex(StateMachineError, "exactly_one_original"):
            reconstruct_as_of(events, rows, SESSIONS, "2026-05-19")

    def test_calendar_truncation_is_not_misread_as_not_yet_available(self):
        short_sessions = ["2026-05-15", "2026-05-18"]
        events = [event("ORIG", "2026-05-18")]
        result = reconstruct_as_of(events, {"ORIG": [holding("111111111", 100, 1000)]}, short_sessions, "2026-05-18")
        self.assertEqual(result["status"], "PENDING_CALENDAR_COVERAGE")
        self.assertEqual(result["manager_periods"], [])
        self.assertEqual(result["pending_calendar_events"][0]["status"], "PENDING_CALENDAR_COVERAGE")


    def test_future_amendment_cannot_leak_into_or_block_prior_asof_state(self):
        events = [
            event("ORIG", "2026-05-15"),
            # Future amendment has a number gap and unknown type. Neither may
            # invalidate the original state before this filing is available.
            event("FUTURE2", "2026-05-22", "13F-HR/A", "2", "FUTURE_UNKNOWN", "Y"),
        ]
        holdings = {"ORIG": [holding("111111111", 100, 1000)]}
        result = reconstruct_as_of(events, holdings, SESSIONS, "2026-05-18")
        group = result["manager_periods"][0]
        self.assertEqual(group["status"], "PASS")
        self.assertEqual(group["applied_accessions"], ["ORIG"])
        self.assertEqual(group["holdings_count"], 1)

    def test_future_13f_nt_notice_is_not_visible_before_available_session(self):
        events = [event("NOTICE", "2026-05-20", "13F-NT", flag="")]
        result = reconstruct_as_of(events, {}, SESSIONS, "2026-05-19")
        self.assertEqual(result["notices"], [])
        self.assertEqual(result["summary"]["notice_only_events"], 0)

    def test_unknown_amendment_type_fails_closed(self):
        events = [
            event("ORIG", "2026-05-15"),
            event("ADD1", "2026-05-20", "13F-HR/A", "1", "CORRECTION", "Y"),
        ]
        with self.assertRaisesRegex(StateMachineError, "unknown_amendment_type"):
            reconstruct_as_of(events, {"ORIG": [holding("111111111", 100, 1000)], "ADD1": [holding("222222222", 100, 1000)]}, SESSIONS, "2026-05-21")


    def test_late_originals_for_older_periods_do_not_displace_latest_report_period(self):
        manager = "2037081"
        events = [
            manager_event("IRON-Q3", "2026-11-06", manager, "2026-09-30"),
            manager_event("IRON-Q4-2025", "2026-11-27", manager, "2025-12-31"),
            manager_event("IRON-Q1-2026", "2026-11-27", manager, "2026-03-31"),
            manager_event("IRON-Q2-2026", "2026-11-27", manager, "2026-06-30"),
        ]
        holdings = {
            "IRON-Q3": [holding("111111111", 100, 1000)],
            "IRON-Q4-2025": [holding("222222222", 100, 2000)],
            "IRON-Q1-2026": [holding("333333333", 100, 3000)],
            "IRON-Q2-2026": [holding("444444444", 100, 4000)],
        }

        before_late_filings = reconstruct_as_of(
            events, holdings, LATE_FILING_SESSIONS, "2026-11-27"
        )
        before_selected = select_latest_holdings_period(before_late_filings)
        self.assertEqual(before_selected["managers"][0]["latest_holdings_period"], "2026-09-30")

        after_late_filings = reconstruct_as_of(
            events, holdings, LATE_FILING_SESSIONS, "2026-11-30"
        )
        self.assertEqual(len(after_late_filings["manager_periods"]), 4)
        selected = select_latest_holdings_period(after_late_filings)
        manager_state = selected["managers"][0]
        self.assertEqual(selected["status"], "PASS")
        self.assertEqual(manager_state["latest_holdings_period"], "2026-09-30")
        self.assertEqual(manager_state["applied_accessions"], ["IRON-Q3"])
        self.assertEqual(manager_state["available_report_periods"], [
            "2026-09-30", "2026-06-30", "2026-03-31", "2025-12-31"
        ])
        self.assertFalse(selected["summary"]["signal_eligible"])

    def test_late_restatement_of_older_period_updates_history_not_latest_snapshot(self):
        manager = "1778131"
        events = [
            manager_event("BI-Q2-ORIG", "2026-08-14", manager, "2026-06-30"),
            manager_event("BI-Q3-ORIG", "2026-11-06", manager, "2026-09-30"),
            manager_event(
                "BI-Q2-REST", "2026-11-27", manager, "2026-06-30",
                "13F-HR/A", "1", "RESTATEMENT", "Y",
            ),
        ]
        holdings = {
            "BI-Q2-ORIG": [holding("222222222", 100, 2000)],
            "BI-Q2-REST": [holding("333333333", 150, 3000)],
            "BI-Q3-ORIG": [holding("111111111", 100, 1000)],
        }
        reconstruction = reconstruct_as_of(
            events, holdings, LATE_FILING_SESSIONS, "2026-11-30"
        )
        q2 = next(row for row in reconstruction["manager_periods"] if row["report_period"] == "2026-06-30")
        self.assertEqual(q2["applied_accessions"], ["BI-Q2-ORIG", "BI-Q2-REST"])
        self.assertEqual(q2["holdings"][0]["cusip"], "333333333")

        selected = select_latest_holdings_period(reconstruction)
        manager_state = selected["managers"][0]
        self.assertEqual(manager_state["latest_holdings_period"], "2026-09-30")
        self.assertEqual(manager_state["applied_accessions"], ["BI-Q3-ORIG"])
        self.assertEqual(manager_state["holdings"][0]["cusip"], "111111111")

    def test_blocked_latest_period_never_falls_back_to_older_holdings(self):
        manager = "2037081"
        events = [
            manager_event("Q2-VALID", "2026-08-14", manager, "2026-06-30"),
            manager_event("Q3-BLOCKED", "2026-11-06", manager, "2026-09-30"),
        ]
        reconstruction = reconstruct_as_of(
            events,
            {"Q2-VALID": [holding("222222222", 100, 2000)]},
            LATE_FILING_SESSIONS,
            "2026-11-30",
        )
        selected = select_latest_holdings_period(reconstruction)
        manager_state = selected["managers"][0]
        self.assertEqual(selected["status"], "BLOCKED")
        self.assertEqual(manager_state["status"], "BLOCKED_NO_FALLBACK")
        self.assertEqual(manager_state["latest_holdings_period"], "2026-09-30")
        self.assertEqual(manager_state["holdings"], [])
        self.assertEqual(manager_state["holdings_count"], 0)
        self.assertIn("missing_holding_rows:Q3-BLOCKED", manager_state["reason"])

    def test_newer_13f_nt_notice_warns_without_becoming_zero_portfolio(self):
        manager = "2037081"
        events = [
            manager_event("Q2-VALID", "2026-08-14", manager, "2026-06-30"),
            manager_event(
                "Q3-NOTICE", "2026-11-27", manager, "2026-09-30",
                "13F-NT", flag="",
            ),
        ]
        reconstruction = reconstruct_as_of(
            events,
            {"Q2-VALID": [holding("222222222", 100, 2000)]},
            LATE_FILING_SESSIONS,
            "2026-11-30",
        )
        selected = select_latest_holdings_period(reconstruction)
        manager_state = selected["managers"][0]
        self.assertEqual(selected["status"], "NOTICE_AFTER_LATEST_HOLDINGS")
        self.assertEqual(manager_state["status"], "NOTICE_AFTER_LATEST_HOLDINGS")
        self.assertEqual(manager_state["latest_holdings_period"], "2026-06-30")
        self.assertEqual(manager_state["newer_notice_periods"], ["2026-09-30"])
        self.assertEqual(manager_state["holdings_count"], 1)

    def test_older_blocked_period_is_a_historical_gap_not_a_newer_snapshot(self):
        manager = "2037081"
        events = [
            manager_event("Q2-BLOCKED", "2026-08-14", manager, "2026-06-30"),
            manager_event("Q3-VALID", "2026-11-06", manager, "2026-09-30"),
        ]
        reconstruction = reconstruct_as_of(
            events,
            {"Q3-VALID": [holding("111111111", 100, 1000)]},
            LATE_FILING_SESSIONS,
            "2026-11-30",
        )
        selected = select_latest_holdings_period(reconstruction)
        manager_state = selected["managers"][0]
        self.assertEqual(selected["status"], "HISTORICAL_GAPS")
        self.assertEqual(manager_state["status"], "PASS_WITH_HISTORICAL_GAPS")
        self.assertEqual(manager_state["latest_holdings_period"], "2026-09-30")
        self.assertEqual(manager_state["historical_gap_periods"], ["2026-06-30"])
        self.assertEqual(manager_state["holdings_count"], 1)
        self.assertFalse(manager_state["signal_eligible"])

    def test_notice_without_any_public_holdings_is_not_a_zero_portfolio(self):
        manager = "2037081"
        events = [
            manager_event(
                "ONLY-NOTICE", "2026-11-27", manager, "2026-09-30",
                "13F-NT", flag="",
            )
        ]
        reconstruction = reconstruct_as_of(
            events, {}, LATE_FILING_SESSIONS, "2026-11-30"
        )
        selected = select_latest_holdings_period(reconstruction)
        manager_state = selected["managers"][0]
        self.assertEqual(selected["status"], "NOTICE_ONLY_NO_PUBLIC_HOLDINGS")
        self.assertIsNone(manager_state["latest_holdings_period"])
        self.assertEqual(manager_state["holdings_count"], 0)
        self.assertEqual(manager_state["holdings"], [])

    def test_calendar_gap_blocks_latest_period_selection(self):
        manager = "2037081"
        sessions = ["2026-11-27"]
        events = [
            manager_event("PENDING", "2026-11-27", manager, "2026-09-30")
        ]
        reconstruction = reconstruct_as_of(
            events, {}, sessions, "2026-11-27"
        )
        selected = select_latest_holdings_period(reconstruction)
        self.assertEqual(selected["status"], "PENDING_CALENDAR_COVERAGE")
        self.assertEqual(selected["summary"]["pending_calendar_event_count"], 1)

    def test_duplicate_manager_report_period_input_fails_closed(self):
        duplicate = {
            "as_of_session": "2026-11-30",
            "manager_periods": [
                {"manager_cik": "2037081", "report_period": "2026-09-30",
                 "status": "PASS", "holdings_count": 0, "holdings": []},
                {"manager_cik": "0002037081", "report_period": "2026-09-30",
                 "status": "PASS", "holdings_count": 0, "holdings": []},
            ],
            "notices": [],
            "pending_calendar_events": [],
        }
        with self.assertRaisesRegex(StateMachineError, "duplicate_manager_report_period"):
            select_latest_holdings_period(duplicate)


if __name__ == "__main__":
    unittest.main()
