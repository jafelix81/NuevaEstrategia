import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.phase295_sec_form4_daily_index_pit_pilot import (
    SAMPLE_ACCESSIONS,
    RetrievalError,
    candidate_index_dates,
    index_url,
    run_audit,
    submission_url,
    _fetch,
)
from research.phase283_sec_daily_index_parser import (
    build_accession_ledger,
    parse_daily_form_index,
)
from research.phase193_nport_raw_filing_retrieval import parse_submission_header

ACCESSION = "0000005513-06-000002"
INDEX = b"""Description: Form 4 filings
CIK|Company Name|Form Type|Date Filed|Filename
--------------------------------------------------------------------------------
5513|Example Company|4|2006-01-03|/Archives/edgar/data/5513/000000551306000002.txt
"""


class Phase295Tests(unittest.TestCase):
    def test_sample_has_three_accessions_per_six_quarters(self):
        self.assertEqual(len(SAMPLE_ACCESSIONS), 18)
        self.assertEqual(len({x["quarter"] for x in SAMPLE_ACCESSIONS}), 6)
        self.assertTrue(all(x["issuer_cik"].isdigit() for x in SAMPLE_ACCESSIONS))

    def test_index_window_is_calendar_date_preserving(self):
        self.assertEqual(
            candidate_index_dates("2026-07-01"),
            ["2026-07-01", "2026-07-02", "2026-07-03", "2026-07-04", "2026-07-05"],
        )

    def test_index_url_uses_quarter_path(self):
        self.assertEqual(
            index_url("2023-03-31"),
            "https://www.sec.gov/Archives/edgar/daily-index/2023/QTR1/form.20230331.idx",
        )
        self.assertEqual(
            index_url("2023-04-03"),
            "https://www.sec.gov/Archives/edgar/daily-index/2023/QTR2/form.20230403.idx",
        )

    def test_submission_url_uses_accession_filer_cik_and_unhyphenated_directory(self):
        self.assertEqual(
            submission_url(ACCESSION, "0000005513"),
            "https://www.sec.gov/Archives/edgar/data/5513/0000005513-06-000002.txt",
        )
        self.assertEqual(
            submission_url("0001180561-06-000004", "0000936528"),
            "https://www.sec.gov/Archives/edgar/data/936528/0001180561-06-000004.txt",
        )

    def test_real_parser_contract_extracts_accession_from_daily_index(self):
        result = parse_daily_form_index(INDEX, "form.20060103.idx")
        self.assertEqual(len(result["records"]), 1)
        row = result["records"][0]
        self.assertEqual(row["accession"], ACCESSION)
        self.assertEqual(row["index_date"], "2006-01-03")
        self.assertEqual(row["index_date_lag_days"], 0)
        ledger = build_accession_ledger(result["records"])
        self.assertEqual(ledger["ledger"][0]["first_daily_index_date"], "2006-01-03")

    def test_parser_does_not_backdate_index_sighting(self):
        result = parse_daily_form_index(INDEX, "form.20060102.idx")
        self.assertEqual(result["records"], [])
        self.assertEqual(result["counts"]["index_date_before_filing_date"], 1)

    def test_sec_header_acceptance_time_reconciles_accession_form_and_date(self):
        header = b"""<SEC-HEADER>
ACCESSION NUMBER: 0000005513-06-000002
CONFORMED SUBMISSION TYPE: 4
FILED AS OF DATE: 20060103
ACCEPTANCE-DATETIME: 20060103123456
</SEC-HEADER>
"""
        result = parse_submission_header(header, ACCESSION, "4")
        self.assertEqual(result["acceptance_datetime_utc"], "2006-01-03T17:34:56+00:00")
        self.assertTrue(result["acceptance_date_matches_filed_date"])

    def test_missing_contact_blocks_without_network(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch(
                "research.phase295_sec_form4_daily_index_pit_pilot._fetch",
                side_effect=AssertionError("network must not be called"),
            ):
                result = run_audit("", Path(temp))
        self.assertEqual(result["status"], "BLOCKED_MISSING_SEC_CONTACT_EMAIL")
        self.assertFalse(result["email_secret_present"])
        self.assertEqual(result["raw_sec_requests"], 0)
        self.assertFalse(result["first_public_timestamp_verified"])
        self.assertTrue(result["f80_frozen"])

    def test_non_sec_url_is_rejected(self):
        with self.assertRaisesRegex(RetrievalError, "non_sec_https_url_rejected"):
            _fetch("https://example.com/index.idx", "test (contact: test@example.com)")


if __name__ == "__main__":
    unittest.main()
