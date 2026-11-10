from __future__ import annotations

import os
import unittest
from pathlib import Path

from research.phase272_form4_candidate_unit_price_basis_audit import analyze_artifact

SOURCE = Path(os.environ.get("PHASE272_SOURCE_ARTIFACT", Path(__file__).resolve().parent.parent / "phase39_form345_source.zip"))


class Phase272Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = analyze_artifact(SOURCE)

    def test_source_hashes_and_phase(self):
        self.assertEqual(self.result["phase"], 272)
        self.assertEqual(self.result["source_artifact"]["outer_sha256"], "203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66")

    def test_phase271_candidate_counts_preserved(self):
        self.assertEqual(self.result["periods"]["2012Q1"]["candidate_transaction_rows"], 102)
        self.assertEqual(self.result["periods"]["2026Q3"]["candidate_transaction_rows"], 85)

    def test_2012_zero_price_is_unknown_not_zero_notional(self):
        p = self.result["periods"]["2012Q1"]
        self.assertEqual(p["reported_price_field_status_counts"]["reported_zero_price_unquantifiable"], 48)
        self.assertEqual(p["reported_value_proxy"]["eligible_rows"], 53)

    def test_2012_onteco_concentration(self):
        e = self.result["periods"]["2012Q1"]["descriptive_examples"]["2012_onteco"]
        self.assertEqual((e["rows"], e["accessions"], e["owners"]), (48, 11, 1))
        self.assertEqual(e["zero_reported_price_rows"], 47)
        self.assertEqual(e["share_basis_restatement_rows"], 31)

    def test_2012_share_basis_restatement_summary(self):
        p = self.result["periods"]["2012Q1"]
        self.assertEqual(p["share_basis_restatement_rows"], 31)
        self.assertEqual(p["share_basis_restatement_accessions"], 8)
        self.assertEqual(p["share_basis_restatement_issuers"], 1)

    def test_2012_role_split(self):
        roles = self.result["periods"]["2012Q1"]["owner_role_row_counts"]
        self.assertEqual(roles["ten_percent_owner_only"], 48)
        self.assertEqual(roles["director_or_officer"], 52)
        self.assertEqual(roles["other_or_mixed"], 2)

    def test_2012_issuer_concentration(self):
        s = self.result["periods"]["2012Q1"]["row_unit_concentration"]["issuer"]
        self.assertAlmostEqual(s["top1_share"], 48/102, places=6)
        self.assertAlmostEqual(s["top2_share"], 65/102, places=6)
        self.assertEqual(s["effective_groups"], 3.789)

    def test_2012_multirow_accession_clustering(self):
        s = self.result["periods"]["2012Q1"]["accession_row_clustering"]
        self.assertEqual(s["accessions_with_multiple_transaction_rows"], 19)
        self.assertEqual(s["rows_in_multirow_accessions"], 74)

    def test_2026_no_zero_or_negative_price(self):
        p = self.result["periods"]["2026Q3"]
        self.assertEqual(p["reported_price_field_status_counts"]["positive_price_proxy_only"], 85)
        self.assertNotIn("reported_zero_price_unquantifiable", p["reported_price_field_status_counts"])

    def test_2026_role_split_and_entity_name_flag(self):
        p = self.result["periods"]["2026Q3"]
        self.assertEqual(p["owner_role_row_counts"]["director_or_officer"], 72)
        self.assertEqual(p["owner_role_row_counts"]["ten_percent_owner_only"], 12)
        self.assertEqual(p["owner_name_legal_entity_flag_rows"], 12)
        self.assertEqual(p["owner_name_legal_entity_flag_unique_owners"], 1)

    def test_2026_income_opportunity_is_one_accession_not_twelve_events(self):
        e = self.result["periods"]["2026Q3"]["descriptive_examples"]["2026_income_opportunity_realty"]
        self.assertEqual((e["rows"], e["accessions"], e["owners"]), (12, 1, 1))
        self.assertEqual(e["transaction_date_min"], "2026-06-04")
        self.assertEqual(e["transaction_date_max"], "2026-06-23")
        self.assertEqual(e["filing_dates"], ["06-JUL-2026"])

    def test_2026_ault_is_one_owner_across_two_issuers(self):
        e = self.result["periods"]["2026Q3"]["descriptive_examples"]["2026_ault_cross_issuer"]
        self.assertEqual((e["rows"], e["accessions"], e["issuers"], e["owners"]), (15, 10, 2, 1))

    def test_2026_issuer_concentration(self):
        s = self.result["periods"]["2026Q3"]["row_unit_concentration"]["issuer"]
        self.assertAlmostEqual(s["top1_share"], 12/85, places=6)
        self.assertAlmostEqual(s["top2_share"], 22/85, places=6)

    def test_2026_small_reported_value_proxy_counts(self):
        t = self.result["periods"]["2026Q3"]["reported_value_proxy"]["threshold_counts"]
        self.assertEqual(t["under_10000"], 28)
        self.assertEqual(t["under_100000"], 66)
        self.assertEqual(t["under_1000000"], 84)

    def test_rows_are_clustered_and_not_independent(self):
        for period in ("2012Q1", "2026Q3"):
            p = self.result["periods"][period]
            self.assertGreater(p["unique_accessions"], 0)
            self.assertGreater(p["unique_issuer_owner_groups"], 0)
            self.assertLess(p["unique_accessions"], p["candidate_transaction_rows"])

    def test_no_pit_alpha_or_holdout_admission(self):
        a = self.result["admission"]
        self.assertFalse(a["strict_pit"])
        self.assertFalse(a["alpha"])
        self.assertFalse(a["return_test"])
        self.assertFalse(a["holdout_used"])
        self.assertTrue(a["f80_frozen"])
        self.assertFalse(a["production_changed"])

    def test_reported_value_proxy_is_explicitly_not_executable_notional(self):
        for period in ("2012Q1", "2026Q3"):
            warning = self.result["periods"][period]["reported_value_proxy"]["warning"]
            self.assertIn("not ADV-scaled", warning)
            self.assertIn("market impact", warning)


if __name__ == "__main__":
    unittest.main()