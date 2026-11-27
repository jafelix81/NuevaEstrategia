"""Offline regression tests for Phase 47 SEC 13F PIT and amendment audit."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from research.phase47_sec_13f_pit_accession_join_audit import (
    build_amendment_map,
    build_submission_map,
    distribution,
)
from research.sec_user_agent import resolve_sec_user_agent


class Phase47Tests(unittest.TestCase):
    def setUp(self):
        self.submission_header = [
            "ACCESSION_NUMBER", "FILING_DATE", "SUBMISSIONTYPE", "CIK", "PERIODOFREPORT"
        ]
        self.coverpage_header = [
            "ACCESSION_NUMBER", "ISAMENDMENT", "AMENDMENTNO", "AMENDMENTTYPE"
        ]
        self.submission_rows = [
            ["A1", "15-MAY-2026", "13F-HR", "100", "31-MAR-2026"],
            ["A2", "20-MAY-2026", "13F-HR/A", "100", "31-MAR-2026"],
            ["A3", "22-MAY-2026", "13F-HR/A", "100", "31-MAR-2026"],
            ["A4", "15-MAY-2026", "13F-NT", "200", "31-MAR-2026"],
        ]

    def test_amendments_join_from_coverpage_and_lags_are_per_submission(self):
        submissions, meta, schema_ok = build_submission_map(
            self.submission_header, self.submission_rows
        )
        self.assertTrue(schema_ok)
        self.assertEqual(meta["stats"]["filing_lag_days"]["n_submissions"], 4)
        cover_rows = [
            ["A1", "0", "", ""],
            ["A2", "1", "1", "RESTATEMENT"],
            ["A3", "1", "2", "NEW HOLDINGS ENTRIES"],
            ["A4", "1", "1", "RESTATEMENT"],
        ]
        cover, amendment_meta, amendment_ok = build_amendment_map(
            self.coverpage_header, cover_rows, submissions
        )
        stats = amendment_meta["stats"]
        self.assertTrue(amendment_ok)
        self.assertEqual(len(cover), 4)
        self.assertEqual(stats["amendment_rows"], 3)
        self.assertEqual(stats["amendment_type_counts"], {
            "NEW HOLDINGS ENTRIES": 1,
            "RESTATEMENT": 2,
        })
        self.assertEqual(stats["form_type_amendment_discordance_rows"], 1)
        self.assertEqual(stats["amendment_flag_mismatch_rows"], 0)
        self.assertEqual(meta["stats"]["manager_period_groups_with_multiple_submissions"], 1)

    def test_missing_amendment_number_or_type_fails_closed(self):
        submissions, _, schema_ok = build_submission_map(
            self.submission_header, [self.submission_rows[1]]
        )
        self.assertTrue(schema_ok)
        _, meta, amendment_ok = build_amendment_map(
            self.coverpage_header,
            [["A2", "1", "", ""]],
            submissions,
        )
        self.assertFalse(amendment_ok)
        self.assertEqual(meta["stats"]["amendment_missing_number_rows"], 1)
        self.assertEqual(meta["stats"]["amendment_missing_type_rows"], 1)

    def test_missing_coverpage_accession_fails_closed(self):
        submissions, _, _ = build_submission_map(self.submission_header, self.submission_rows)
        _, meta, amendment_ok = build_amendment_map(
            self.coverpage_header,
            [["A1", "0", "", ""]],
            submissions,
        )
        self.assertFalse(amendment_ok)
        self.assertEqual(meta["stats"]["missing_coverpage_accessions"], 3)

    def test_blank_is_amendment_flag_is_allowed_when_nullable(self):
        submissions, _, _ = build_submission_map(self.submission_header, self.submission_rows)
        cover_rows = [
            ["A1", "", "", ""],
            ["A2", "1", "1", "RESTATEMENT"],
            ["A3", "1", "2", "NEW HOLDINGS ENTRIES"],
            ["A4", "", "", ""],
        ]
        _, meta, amendment_ok = build_amendment_map(
            self.coverpage_header, cover_rows, submissions
        )
        self.assertTrue(amendment_ok)
        self.assertEqual(meta["stats"]["amendment_flag_missing_amendment_rows"], 0)
        self.assertEqual(meta["stats"]["amendment_flag_missing_non_amendment_rows"], 2)

    def test_filing_lag_distribution_counts_submission_events(self):
        stats = distribution([45, 45, 50, 52])
        self.assertEqual(stats["n_submissions"], 4)
        self.assertEqual(stats["median"], 45)
        self.assertEqual(stats["p75"], 50)

    def test_repository_secret_is_preferred(self):
        with patch.dict(os.environ, {"SEC_USER_AGENT": "unit-test-contact@example.net"}):
            value, source = resolve_sec_user_agent()
        self.assertEqual(value, "unit-test-contact@example.net")
        self.assertEqual(source, "repository_secret")

    def test_project_contact_fallback_is_available(self):
        with patch.dict(os.environ, {}, clear=True):
            value, source = resolve_sec_user_agent()
        self.assertIn("@", value)
        self.assertNotIn("example.com", value.lower())
        self.assertEqual(source, "shared_project_contact_fallback")


if __name__ == "__main__":
    unittest.main()
