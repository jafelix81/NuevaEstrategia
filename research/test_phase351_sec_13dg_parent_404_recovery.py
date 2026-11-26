from __future__ import annotations

import unittest

from research.phase351_sec_13dg_parent_404_recovery import (
    build_recovery_target,
    evaluate_parent_response,
)
from research.phase350_sec_13dg_parent_retrieval import build_archive_url


class Phase351TargetTests(unittest.TestCase):
    def prior(self):
        return [{
            "child_accession": "0000886982-25-001416",
            "parent_accession": "0000769993-25-000432",
            "parent_archive_path_cik_candidate": "723612",
            "http_status": "404",
            "retrieval_status": "NOT_FOUND",
        }]

    def manifest(self):
        return [{
            "child_accession": "0000886982-25-001416",
            "explicit_parent_accession": "0000769993-25-000432",
            "subject_issuer_cik": "723612",
            "parent_archive_path_cik": "769993",
            "form_family": "13G",
            "child_acceptance_utc": "2025-11-10T17:16:36+00:00",
        }]

    def test_single_404_selects_manifest_accession_prefix_candidate(self):
        target = build_recovery_target(self.prior(), self.manifest())
        self.assertEqual(target["alternate_archive_path_cik_candidate"], "0000769993")
        self.assertEqual(target["subject_issuer_cik"], "0000723612")
        self.assertEqual(target["alternate_path_role"], "UNVERIFIED_MANIFEST_CANDIDATE_FROM_ACCESSION_PREFIX")

    def test_alternate_url_uses_only_candidate_as_locator(self):
        target = build_recovery_target(self.prior(), self.manifest())
        url = build_archive_url(target["parent_accession"], target["alternate_archive_path_cik_candidate"])
        self.assertIn("/data/769993/", url)
        self.assertIn("/000076999325000432/", url)

    def test_no_404_target_is_rejected(self):
        rows = [{**self.prior()[0], "http_status": "200", "retrieval_status": "HTTP_200"}]
        with self.assertRaisesRegex(ValueError, "expected_exactly_one"):
            build_recovery_target(rows, self.manifest())

    def test_multiple_404_targets_are_rejected(self):
        rows = self.prior() + [{**self.prior()[0], "child_accession": "0000000001-25-000001"}]
        with self.assertRaisesRegex(ValueError, "expected_exactly_one"):
            build_recovery_target(rows, self.manifest())

    def test_manifest_child_join_must_be_unique(self):
        rows = self.manifest() + self.manifest()
        with self.assertRaisesRegex(ValueError, "not_unique"):
            build_recovery_target(self.prior(), rows)

    def test_candidate_must_match_accession_prefix(self):
        rows = [{**self.manifest()[0], "parent_archive_path_cik": "723612"}]
        with self.assertRaisesRegex(ValueError, "not_accession_prefix"):
            build_recovery_target(self.prior(), rows)

    def test_candidate_must_differ_from_failed_subject_path(self):
        prior = [{**self.prior()[0], "parent_archive_path_cik_candidate": "723612"}]
        with self.assertRaisesRegex(ValueError, "not_distinct"):
            build_recovery_target(prior, self.manifest())


class Phase351HeaderValidationTests(unittest.TestCase):
    def header(self, acceptance="20250812120000", form="SC 13G/A", subject="0000723612",
               accession="0000769993-25-000432"):
        return f"""<SEC-HEADER>
ACCESSION NUMBER: {accession}
CONFORMED SUBMISSION TYPE: {form}
FILED AS OF DATE: 20250812
<ACCEPTANCE-DATETIME>{acceptance}
SUBJECT COMPANY:
  COMPANY DATA:
    CENTRAL INDEX KEY: {subject}
FILED BY:
  COMPANY DATA:
    CENTRAL INDEX KEY: 0000769993
</SEC-HEADER>""".encode()

    def target(self):
        return {
            "parent_accession": "0000769993-25-000432",
            "subject_issuer_cik": "0000723612",
            "form_family": "13G",
            "child_acceptance_utc": "2025-11-10T17:16:36+00:00",
        }

    def test_correct_subject_family_and_earlier_acceptance_pass(self):
        result = evaluate_parent_response(self.header(), self.target())
        self.assertEqual(result["reference_validation_status"], "VALID_EXPLICIT_REFERENCE")
        self.assertTrue(result["accession_match"])
        self.assertTrue(result["subject_cik_match"])
        self.assertTrue(result["form_family_match"])
        self.assertTrue(result["acceptance_strictly_earlier"])

    def test_wrong_subject_is_quarantined(self):
        result = evaluate_parent_response(self.header(subject="0000000009"), self.target())
        self.assertIn("parent_subject_cik_mismatch", result["validation_reasons"])

    def test_wrong_family_is_quarantined(self):
        result = evaluate_parent_response(self.header(form="SC 13D/A"), self.target())
        self.assertIn("parent_form_family_mismatch", result["validation_reasons"])

    def test_parent_not_strictly_earlier_is_quarantined(self):
        result = evaluate_parent_response(self.header(acceptance="20251110171636"), self.target())
        self.assertIn("parent_acceptance_not_strictly_earlier", result["validation_reasons"])


if __name__ == "__main__":
    unittest.main()
