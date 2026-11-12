from __future__ import annotations

import unittest
from datetime import date

from research.phase283_sec_daily_index_parser import parse_daily_form_index
from research.phase318_nport_next_business_day_clock import next_edgar_business_day
from research.phase319_sec_daily_index_live_pilot import parse_filing_header
from research.phase320_sec_bulk_daily_index_join import (
    header_identity_flags,
    index_row_summary,
    index_url,
    normalize_accession,
    normalize_bulk_date,
    normalize_cik,
    select_form_samples,
    submission_url,
    validate_result,
)


class Phase320BulkDailyIndexJoinTests(unittest.TestCase):
    def test_bulk_date_normalization_is_locale_independent(self):
        self.assertEqual(normalize_bulk_date("31-MAR-2006"), "2006-03-31")
        self.assertEqual(normalize_bulk_date("2026-11-10"), "2026-11-10")

    def test_identifier_normalization(self):
        self.assertEqual(normalize_cik("0000001234"), "1234")
        self.assertEqual(normalize_accession("0000001234-26-000001"), "0000001234-26-000001")

    def test_deterministic_stratified_sample_excludes_prior_accessions(self):
        rows_by_date = {}
        for day in range(1, 25):
            filing_date = f"2026-09-{day:02d}"
            rows_by_date[filing_date] = [
                {"accession": f"0000000001-26-{day:06d}", "filing_date": filing_date},
                {"accession": f"0000000002-26-{day:06d}", "filing_date": filing_date},
            ]
        excluded = {"0000000001-26-000001"}
        first = select_form_samples(rows_by_date, "2026Q3", "4", 8, excluded)
        second = select_form_samples(rows_by_date, "2026Q3", "4", 8, excluded)
        self.assertEqual([r["accession"] for r in first], [r["accession"] for r in second])
        self.assertEqual(len(first), 8)
        self.assertNotIn("0000000001-26-000001", {r["accession"] for r in first})
        self.assertEqual(len({r["filing_date"] for r in first}), 8)

    def test_next_edgar_business_day_observes_veterans_day(self):
        self.assertEqual(next_edgar_business_day(date(2026, 11, 10)), date(2026, 11, 12))

    def test_index_row_summary_preserves_multiple_entity_ciks(self):
        sample = {
            "accession": "0000000001-26-000001",
            "form_type": "4",
            "filing_date": "2026-09-01",
            "issuer_cik": "0000000001",
        }
        rows = [
            {"accession": sample["accession"], "form_type": "4", "filing_date": "2026-09-01",
             "cik": "2", "filename": "edgar/data/2/0000000001-26-000001.txt"},
            {"accession": sample["accession"], "form_type": "4", "filing_date": "2026-09-01",
             "cik": "1", "filename": "edgar/data/1/0000000001-26-000001.txt"},
        ]
        result = index_row_summary(rows, sample, "2026-09-01")
        self.assertTrue(result["accession_found"])
        self.assertTrue(result["index_form_match"])
        self.assertTrue(result["index_filing_date_match"])
        self.assertTrue(result["issuer_entity_row_present"])
        self.assertEqual(result["index_entity_count"], 2)

    def test_header_identity_flags_require_all_core_fields(self):
        sample = {
            "accession": "0000000001-26-000001",
            "form_type": "4/A",
            "issuer_cik": "0000000001",
            "filing_date": "2026-09-01",
        }
        header = {
            "accession": sample["accession"],
            "form_type": "4/A",
            "cik": "1",
            "filed_date": "2026-09-01",
            "acceptance_datetime_et": "20260901173000",
        }
        flags = header_identity_flags(header, sample)
        self.assertTrue(all(flags.values()))
        header["cik"] = "2"
        self.assertFalse(header_identity_flags(header, sample)["issuer_cik_match"])

    def test_sec_urls_are_scoped_to_official_host(self):
        self.assertEqual(
            index_url("2026-09-01"),
            "https://www.sec.gov/Archives/edgar/daily-index/2026/QTR3/form.20260901.idx",
        )
        self.assertEqual(
            submission_url("0000000001-26-000001", "0000000001"),
            "https://www.sec.gov/Archives/edgar/data/1/0000000001-26-000001.txt",
        )

    def test_original_header_parser_reconciles_sgml_fields(self):
        raw = b"""<SEC-HEADER>
ACCESSION NUMBER: 0000000001-26-000001
CONFORMED SUBMISSION TYPE: 4/A
CENTRAL INDEX KEY: 0000000001
FILED AS OF DATE: 20260901
<ACCEPTANCE-DATETIME>20260901173000
</SEC-HEADER>"""
        header = parse_filing_header(raw)
        sample = {
            "accession": "0000000001-26-000001",
            "form_type": "4/A",
            "issuer_cik": "1",
            "filing_date": "2026-09-01",
        }
        self.assertTrue(all(header_identity_flags(header, sample)[key]
                            for key in ("accession_match", "form_match", "issuer_cik_match", "filed_date_match")))

    def test_result_validator_keeps_all_research_controls_closed(self):
        result = {
            "phase": 320,
            "source_archives": {"archives_verified": 6},
            "sample": {"sampled_accessions": 72},
            "controls": {
                "f80_frozen": True,
                "strict_pit_admitted": False,
                "alpha_test_authorized": False,
                "return_test_run": False,
                "bootstrap_loo_run": False,
                "chronological_oos_run": False,
                "holdout_used": False,
                "production_changed": False,
                "universe_changed": False,
                "capital_changed": False,
                "parameters_changed": False,
                "raw_sec_bytes_uploaded": False,
                "vendor_contacted": False,
                "data_purchased": False,
                "email_sent": False,
            },
        }
        validate_result(result)
        result["controls"]["holdout_used"] = True
        with self.assertRaises(ValueError):
            validate_result(result)


if __name__ == "__main__":
    unittest.main()
