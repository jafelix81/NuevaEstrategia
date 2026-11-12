"""Synthetic fail-closed tests for Phase 283 SEC daily-index parsing."""
from __future__ import annotations

import unittest

from research.phase283_sec_daily_index_parser import (
    build_accession_ledger,
    build_contract_result,
    next_full_xnys_session_close,
    parse_daily_form_index,
    validate_contract_result,
)

INDEX_HEADER = (
    "Description: Daily Index of EDGAR Disseminated Filings\n"
    "CIK|Company Name|Form Type|Date Filed|Filename\n"
    "--------------------------------------------------------------------------------\n"
)
FORM4 = "320193|APPLE INC|4|2026-01-02|edgar/data/320193/000032019326000001.txt"
FORM4A = "320193|APPLE INC|4/A|2026-01-02|edgar/data/320193/000032019326000002.txt"
FIXED_INDEX_HEADER = (
    "Description: Daily Index of EDGAR Dissemination Feed by Form Type\\n"
    "Last Data Received:    Jan  2, 2026\\n"
    "Form Type   Company Name                                                  CIK\\n"
    "      Date Filed  File Name\\n"
    "---------------------------------------------------------------------------------------------------------------------------------------------\\n"
)
FIXED_FORM4 = (
    "4          Example Company                                     320193     20260102    "
    "edgar/data/320193/0000789000-26-000001.txt"
)


class Phase283DailyIndexTests(unittest.TestCase):
    def parse(self, rows: str, filename: str = "form.20260102.idx"):
        return parse_daily_form_index((INDEX_HEADER + rows + "\n").encode(), filename)

    def test_parses_form4_and_form4a_as_distinct_accessions(self):
        result = self.parse(FORM4 + "\n" + FORM4A)
        self.assertEqual([r["form_type"] for r in result["records"]], ["4", "4/A"])
        self.assertEqual(len({r["accession"] for r in result["records"]}), 2)

    def test_non_form4_rows_are_ignored(self):
        row = "320193|APPLE INC|10-K|2026-01-02|edgar/data/320193/000032019326000003.txt"
        result = self.parse(row)
        self.assertEqual(result["records"], [])
        self.assertEqual(result["counts"]["non_form4_rows_ignored"], 1)

    def test_cik_path_mismatch_is_quarantined(self):
        row = "320193|APPLE INC|4|2026-01-02|edgar/data/789/000032019326000001.txt"
        result = self.parse(row)
        self.assertEqual(result["records"], [])
        self.assertEqual(result["quarantine"][0]["reason"], "row_cik_path_cik_mismatch")

    def test_accession_prefix_may_differ_from_issuer_cik(self):
        row = "320193|APPLE INC|4|2026-01-02|edgar/data/320193/000078900026000001.txt"
        result = self.parse(row)
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["accession"], "0000789000-26-000001")
        self.assertEqual(result["records"][0]["cik"], "320193")

    def test_parses_actual_sec_legacy_fixed_width_index_with_dashed_accession(self):
        raw = (FIXED_INDEX_HEADER + FIXED_FORM4 + "\\n").encode("latin-1")
        result = parse_daily_form_index(raw, "form.20260102.idx")
        self.assertEqual(result["format"], "legacy_fixed_width")
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["accession"], "0000789000-26-000001")
        self.assertEqual(result["records"][0]["cik"], "320193")
        self.assertEqual(result["records"][0]["filing_date"], "2026-01-02")

    def test_fixed_width_index_accepts_latin1_company_names(self):
        row = FIXED_FORM4.replace("Example Company", "Café Holdings")
        raw = (FIXED_INDEX_HEADER + row + "\\n").encode("latin-1")
        result = parse_daily_form_index(raw, "form.20260102.idx")
        self.assertEqual(result["records"][0]["company_name"], "Café Holdings")

    def test_fixed_width_date_before_index_is_quarantined(self):
        raw = (FIXED_INDEX_HEADER + FIXED_FORM4 + "\\n").encode("latin-1")
        result = parse_daily_form_index(raw, "form.20260101.idx")
        self.assertEqual(result["records"], [])
        self.assertEqual(result["counts"]["index_date_before_filing_date"], 1)

    def test_index_date_before_filing_date_is_quarantined(self):
        row = "320193|APPLE INC|4|2026-01-05|edgar/data/320193/000032019326000001.txt"
        result = self.parse(row)
        self.assertEqual(result["records"], [])
        self.assertEqual(result["quarantine"][0]["reason"], "index_date_precedes_filing_date")

    def test_later_index_date_is_retained_as_lagged_observation(self):
        result = self.parse(FORM4, "form.20260105.idx")
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["index_date_lag_days"], 3)
        self.assertEqual(result["counts"]["index_date_after_filing_date"], 1)

    def test_unrecognized_accession_path_is_quarantined(self):
        row = "320193|APPLE INC|4|2026-01-02|edgar/data/320193/not-an-accession.txt"
        result = self.parse(row)
        self.assertEqual(result["records"], [])
        self.assertEqual(result["quarantine"][0]["reason"], "unrecognized_accession_path")

    def test_malformed_rows_are_quarantined_without_raw_text(self):
        result = self.parse("this is not a pipe-delimited row")
        self.assertEqual(result["counts"]["malformed_rows"], 1)
        self.assertNotIn("this is not", str(result["quarantine"]))

    def test_exact_duplicate_in_one_index_is_counted_and_collapsed(self):
        result = self.parse(FORM4 + "\n" + FORM4)
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["counts"]["exact_duplicate_rows"], 1)
        self.assertEqual(result["records"][0]["same_file_exact_duplicate_rows"], 1)

    def test_conflicting_duplicate_accession_is_excluded(self):
        conflict = (
            "320193|APPLE INC CLASS A|4|2026-01-02|"
            "edgar/data/320193/000032019326000001.txt"
        )
        result = self.parse(FORM4 + "\n" + conflict)
        self.assertEqual(result["records"], [])
        self.assertEqual(result["counts"]["conflicting_duplicate_accessions"], 1)

    def test_reporting_owner_cik_does_not_override_issuer_path_cik(self):
        owner_row = (
            "1184085|BEST ROBERT O|4|2026-01-02|"
            "edgar/data/320193/000032019326000001.txt"
        )
        result = self.parse(FORM4 + "\\n" + owner_row)
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["counts"]["issuer_cik_path_mismatches"], 1)
        self.assertEqual(
            result["quarantine"][0]["reason"],
            "row_cik_path_cik_mismatch",
        )
        self.assertEqual(result["counts"]["multi_entity_accessions"], 0)

    def test_ledger_keeps_all_sightings_and_uses_earliest_index_date(self):
        first = self.parse(FORM4, "form.20260102.idx")["records"][0]
        later = self.parse(FORM4, "form.20260105.idx")["records"][0]
        ledger = build_accession_ledger([later, first])
        self.assertEqual(len(ledger["ledger"]), 1)
        self.assertEqual(ledger["ledger"][0]["first_daily_index_date"], "2026-01-02")
        self.assertEqual(ledger["ledger"][0]["first_index_lag_days"], 0)
        self.assertEqual(ledger["ledger"][0]["max_index_lag_days"], 3)
        self.assertEqual(
            ledger["ledger"][0]["all_daily_index_dates"], ["2026-01-02", "2026-01-05"]
        )
        self.assertEqual(ledger["ledger"][0]["index_sightings"], 2)

    def test_later_only_sighting_is_not_backdated_to_filing_date(self):
        later = self.parse(FORM4, "form.20260105.idx")["records"][0]
        ledger = build_accession_ledger([later])
        self.assertEqual(ledger["ledger"][0]["first_daily_index_date"], "2026-01-05")
        self.assertEqual(ledger["ledger"][0]["first_index_lag_days"], 3)

    def test_cross_index_identity_conflict_is_quarantined(self):
        first = self.parse(FORM4)["records"][0]
        changed = dict(first, form_type="4/A")
        ledger = build_accession_ledger([first, changed])
        self.assertEqual(ledger["ledger"], [])
        self.assertEqual(ledger["quarantine"][0]["reason"], "cross_index_form_or_filing_date_conflict")

    def test_next_full_session_close_skips_early_close(self):
        sessions = [
            {"session_date": "2026-11-13", "open_utc": "2026-11-13T14:30:00+00:00",
             "close_utc": "2026-11-13T18:00:00+00:00"},
            {"session_date": "2026-11-16", "open_utc": "2026-11-16T14:30:00+00:00",
             "close_utc": "2026-11-16T21:00:00+00:00"},
        ]
        self.assertEqual(
            next_full_xnys_session_close("2026-11-12", sessions),
            "2026-11-16T21:00:00+00:00",
        )

    def test_session_timestamps_must_be_timezone_aware(self):
        sessions = [{
            "session_date": "2026-11-16", "open_utc": "2026-11-16T09:30:00",
            "close_utc": "2026-11-16T16:00:00",
        }]
        with self.assertRaises(ValueError):
            next_full_xnys_session_close("2026-11-12", sessions)

    def test_missing_future_full_session_fails_closed(self):
        sessions = [{
            "session_date": "2026-11-13", "open_utc": "2026-11-13T14:30:00+00:00",
            "close_utc": "2026-11-13T18:00:00+00:00",
        }]
        with self.assertRaises(LookupError):
            next_full_xnys_session_close("2026-11-12", sessions)

    def test_contract_cannot_admit_pit_or_alpha(self):
        result = build_contract_result()
        validate_contract_result(result)
        self.assertFalse(result["gates"]["strict_pit_admitted"])
        self.assertFalse(result["gates"]["alpha_test_authorized"])
        self.assertTrue(result["gates"]["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
