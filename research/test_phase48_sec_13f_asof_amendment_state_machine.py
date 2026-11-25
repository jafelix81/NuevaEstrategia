"""Offline regression tests for the Phase 48 SEC 13F state machine."""
from __future__ import annotations

import unittest

from research.phase48_sec_13f_asof_amendment_state_machine import (
    StateMachineError,
    first_full_session_after,
    reconstruct_as_of,
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


if __name__ == "__main__":
    unittest.main()
