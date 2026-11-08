import json
import unittest

from research.phase218_nport_publication_vintage_and_lending_audit import (
    EVIDENCE_PATH,
    build_audit,
)


class Phase218NportPublicationVintageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        cls.result = build_audit(cls.evidence)

    def test_official_sec_archive_has_28_quarters_through_2026_q3(self):
        sec = self.evidence["official_sec_archive"]
        self.assertEqual(sec["quarter_count"], 28)
        self.assertEqual(sec["history_end"], "2026-09-30")
        self.assertEqual(sec["latest_archive"], "2026 Q3")

    def test_data_gov_catalog_is_one_quarter_behind(self):
        self.assertEqual(self.evidence["data_gov_catalog_comparison"]["resource_count"], 27)
        self.assertTrue(self.result["data_gov_one_quarter_stale"])

    def test_filing_sample_is_explicitly_nonrepresentative(self):
        self.assertIn("not random or representative", self.evidence["filing_lag_sample"]["design"])
        self.assertEqual(self.result["filing_count"], 19)

    def test_filing_lag_summary_reproduces(self):
        self.assertEqual(
            self.result["report_to_filing_calendar_days"],
            {"min": 49, "median": 58, "max": 60},
        )

    def test_all_sample_accessions_are_unique_and_nport_p(self):
        self.assertTrue(self.result["all_accessions_unique"])
        self.assertTrue(self.result["all_forms_nport_p"])

    def test_acceptance_dates_match_filing_dates(self):
        self.assertTrue(self.result["all_acceptance_dates_match_filing_dates"])

    def test_amendments_are_preserved_as_filed(self):
        semantics = self.evidence["readme_semantics"]
        self.assertEqual(semantics["as_filed_data"], "yes")
        self.assertEqual(semantics["amendments_included"], "yes")
        self.assertEqual(semantics["submission_primary_key"], "ACCESSION_NUMBER")

    def test_lending_is_a_separate_holding_level_construct(self):
        semantics = self.evidence["readme_semantics"]
        self.assertEqual(semantics["securities_lending_key"], ["HOLDING_ID"])
        self.assertEqual(semantics["securities_lending_fields"], ["IS_LOAN_BY_FUND", "LOAN_VALUE"])

    def test_borrower_aggregate_is_not_security_level(self):
        semantics = self.evidence["readme_semantics"]
        self.assertIn("aggregate value of all securities", semantics["borrower_aggregate_value_scope"])
        self.assertIn("not documented", semantics["security_level_borrower_to_holding_link"])

    def test_no_raw_integrity_or_first_receipt_claim(self):
        self.assertFalse(self.result["raw_submission_sha256_verified"])
        self.assertFalse(self.result["raw_primary_xml_sha256_verified"])
        self.assertFalse(self.result["first_public_receipt_verified"])

    def test_no_alpha_or_holdout_use_and_f80_frozen(self):
        self.assertFalse(self.result["alpha_test_authorized"])
        self.assertFalse(self.result["holdout_used"])
        self.assertTrue(self.result["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
