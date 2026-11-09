import hashlib
import json
import unittest
from pathlib import Path

from phase230_cboe_quotes_locale_reclassification import audit

SUMMARY_PATH = Path(__file__).with_name("phase175_cboe_option_quotes_date_locale_audit_result_2026-11-09.json")
EXPECTED_SUMMARY_SHA256 = "c69f4aa08b220d00a11903339d57c60a0deb6c84492286487d0fff74440f831d"


class Phase230Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = SUMMARY_PATH.read_bytes()
        cls.sha = hashlib.sha256(source).hexdigest()
        cls.result = audit(json.loads(source), cls.sha)

    def test_summary_hash_pinned(self):
        self.assertEqual(self.sha, EXPECTED_SUMMARY_SHA256)

    def test_original_iso_only_failure_total(self):
        self.assertEqual(self.result["counts"]["phase174_iso_only_invalid_contract_row_instances"], 94607)

    def test_unique_expiration_interpretations(self):
        self.assertEqual(self.result["counts"]["expiration_unique_interpretation_row_instances_all_members"], 112313)

    def test_ambiguous_expirations_quarantined(self):
        self.assertEqual(self.result["counts"]["expiration_ambiguous_row_instances_all_members"], 3304)

    def test_failed_rows_split_exactly(self):
        self.assertEqual(self.result["counts"]["originally_failed_rows_with_unique_expiration_interpretation"], 91303)
        self.assertEqual(self.result["counts"]["originally_failed_rows_still_ambiguous"], 3304)

    def test_all_quote_timestamps_have_unique_candidate(self):
        self.assertEqual(self.result["counts"]["quote_datetime_unique_interpretation_row_instances"], 115617)
        self.assertEqual(self.result["counts"]["quote_datetime_ambiguous_row_instances"], 0)

    def test_counts_are_row_instances_not_contracts(self):
        self.assertTrue(self.result["interpretation"]["112313_counts_row_instances_across_five_members_not_unique_contracts"])

    def test_no_sample_or_pit_admission(self):
        self.assertFalse(self.result["admission"]["sample_schema_admitted"])
        self.assertFalse(self.result["admission"]["strict_pit_admitted"])
        self.assertFalse(self.result["admission"]["alpha_admitted"])

    def test_no_holdout_or_production_change(self):
        self.assertFalse(self.result["admission"]["final_holdout_used"])
        self.assertFalse(self.result["admission"]["production_changed"])
        self.assertEqual(self.result["admission"]["f80_status"], "FROZEN")

    def test_archive_hash_pinned(self):
        self.assertEqual(self.result["source"]["archive_sha256"], "7645a6cc94f1a984e98264a4b494f748e373c30ecde85de25ceadb83a5c56782")


if __name__ == "__main__":
    unittest.main()
