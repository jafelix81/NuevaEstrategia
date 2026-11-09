import json
import unittest
from pathlib import Path

from phase215_sec_midas_release_pit_audit import evaluate

MANIFEST = json.loads(
    Path(__file__).with_name("phase215_sec_midas_release_pit_audit_manifest.json")
    .read_text(encoding="utf-8")
)


class Phase215Tests(unittest.TestCase):
    def test_quarterly_batch_cadence(self):
        self.assertEqual(
            MANIFEST["release_evidence"]["daily_stock_by_stock_release_cadence"],
            "quarterly",
        )

    def test_public_launch_date_is_not_archive_start(self):
        self.assertEqual(
            MANIFEST["release_evidence"]["public_market_structure_site_launch_date"],
            "2013-10-09",
        )
        self.assertEqual(
            MANIFEST["release_evidence"]["current_archive_inventory"]["first_quarter"],
            "2012Q1",
        )

    def test_q4_2013_mid_february_is_expected_not_confirmed(self):
        evidence = MANIFEST["release_evidence"]["as_of_2014_01_09"]
        self.assertEqual(
            evidence["q4_2013_stock_by_stock_data_expected_update"],
            "mid-February 2014",
        )
        self.assertTrue(evidence["expected_date_is_not_confirmed_actual_release"])

    def test_last_modified_is_not_first_publication(self):
        release = MANIFEST["release_evidence"]
        self.assertFalse(release["last_modified_is_first_publication_timestamp"])
        self.assertFalse(release["per_quarter_first_publication_timestamps_available"])

    def test_daily_pit_is_rejected(self):
        result = evaluate(MANIFEST)
        self.assertFalse(result["strict_daily_pit_admitted"])
        self.assertEqual(
            result["status"],
            "QUARTERLY_BATCH_RELEASE_CONFIRMED_EXACT_VINTAGES_MISSING",
        )

    def test_midas_is_not_off_exchange_or_participant_identity(self):
        result = evaluate(MANIFEST)
        self.assertFalse(result["off_exchange_execution_flow"])
        self.assertFalse(result["participant_identity_available"])
        self.assertFalse(result["hidden_order_equals_dark_pool_flow"])

    def test_no_alpha_or_holdout(self):
        result = evaluate(MANIFEST)
        self.assertFalse(result["alpha_test_authorized"])
        self.assertFalse(result["holdout_used"])
        self.assertTrue(result["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
