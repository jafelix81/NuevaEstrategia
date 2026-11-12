from __future__ import annotations

import unittest

from research.phase321_sec_bulk_daily_index_full_census import (
    EXPECTED_TOTAL_ACCESSIONS,
    evaluate_index_rows,
    owner_count_bin,
    select_header_samples,
    validate_result,
)


class Phase321FullCensusTests(unittest.TestCase):
    def test_owner_count_bins(self):
        self.assertEqual(owner_count_bin(0), "0")
        self.assertEqual(owner_count_bin(1), "1")
        self.assertEqual(owner_count_bin(2), "2")
        self.assertEqual(owner_count_bin(3), "3-5")
        self.assertEqual(owner_count_bin(5), "3-5")
        self.assertEqual(owner_count_bin(6), "6+")
        self.assertEqual(owner_count_bin(10), "6+")

    def test_stratified_header_sample_is_deterministic_and_complete(self):
        rows = []
        for quarter in ("2006Q1", "2012Q1"):
            for form in ("4", "4/A"):
                for owner_count in (1, 2, 3, 6):
                    for j in range(3):
                        rows.append({
                            "quarter": quarter, "form_type": form,
                            "accession": f"{len(rows)+1:010d}-26-{j+1:06d}",
                            "reporting_owner_count": owner_count,
                        })
        a, missing_a = select_header_samples(rows, ("2006Q1", "2012Q1"), set())
        b, missing_b = select_header_samples(rows, ("2006Q1", "2012Q1"), set())
        self.assertEqual([r["accession"] for r in a], [r["accession"] for r in b])
        self.assertEqual(missing_a, missing_b)
        self.assertEqual(len(a), 16)
        self.assertEqual(missing_a, [])
        self.assertEqual(
            {(r["quarter"], r["form_type"], r["owner_count_bin"]) for r in a},
            {
                (q, f, b)
                for q in ("2006Q1", "2012Q1")
                for f in ("4", "4/A")
                for b in ("1", "2", "3-5", "6+")
            },
        )

    def test_index_rows_reconcile_issuer_and_every_reporting_owner(self):
        sample = {
            "issuer_cik": "0000000100", "form_type": "4/A",
            "filing_date": "2026-09-01",
            "reporting_owner_ciks": ["0000000200", "0000000300"],
        }
        rows = [
            {"form_type": "4/A", "filing_date": "2026-09-01", "cik": "100"},
            {"form_type": "4/A", "filing_date": "2026-09-01", "cik": "200"},
            {"form_type": "4/A", "filing_date": "2026-09-01", "cik": "300"},
        ]
        result = evaluate_index_rows(rows, sample, "2026-09-01")
        self.assertTrue(result["accession_found"])
        self.assertTrue(result["index_form_match"])
        self.assertTrue(result["index_filing_date_match"])
        self.assertTrue(result["issuer_entity_row_present"])
        self.assertTrue(result["reporting_owner_ciks_present"])
        self.assertEqual(result["expected_entity_cik_count"], 3)
        self.assertEqual(result["index_entity_count"], 3)
        self.assertTrue(result["index_entity_count_matches_expected"])

    def test_missing_owner_is_explicit(self):
        sample = {
            "issuer_cik": "100", "form_type": "4",
            "filing_date": "2026-09-01", "reporting_owner_ciks": ["200", "300"],
        }
        rows = [
            {"form_type": "4", "filing_date": "2026-09-01", "cik": "100"},
            {"form_type": "4", "filing_date": "2026-09-01", "cik": "200"},
        ]
        result = evaluate_index_rows(rows, sample, "2026-09-01")
        self.assertFalse(result["reporting_owner_ciks_present"])
        self.assertEqual(result["missing_reporting_owner_ciks"], ["300"])

    def test_unexpected_index_entity_is_not_silently_ignored(self):
        sample = {
            "issuer_cik": "100", "form_type": "4",
            "filing_date": "2026-09-01", "reporting_owner_ciks": ["200"],
        }
        rows = [
            {"form_type": "4", "filing_date": "2026-09-01", "cik": "100"},
            {"form_type": "4", "filing_date": "2026-09-01", "cik": "200"},
            {"form_type": "4", "filing_date": "2026-09-01", "cik": "999"},
        ]
        result = evaluate_index_rows(rows, sample, "2026-09-01")
        self.assertEqual(result["unexpected_index_entity_ciks"], ["999"])
        self.assertFalse(result["index_entity_count_matches_expected"])

    def test_result_validator_preserves_all_controls(self):
        result = {
            "phase": 321,
            "source_archives": {"archives_verified": 6},
            "bulk_census": {
                "total_accessions": EXPECTED_TOTAL_ACCESSIONS,
                "unique_filing_dates": 377,
            },
            "controls": {
                "f80_frozen": True, "strict_pit_admitted": False,
                "alpha_test_authorized": False, "return_test_run": False,
                "bootstrap_loo_run": False, "chronological_oos_run": False,
                "holdout_used": False, "production_changed": False,
                "universe_changed": False, "capital_changed": False,
                "parameters_changed": False, "raw_sec_bytes_uploaded": False,
                "vendor_contacted": False, "data_purchased": False,
                "email_sent": False,
            },
        }
        validate_result(result)
        result["controls"]["holdout_used"] = True
        with self.assertRaises(ValueError):
            validate_result(result)


if __name__ == "__main__":
    unittest.main()
