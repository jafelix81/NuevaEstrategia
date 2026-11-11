import unittest

from research.phase279_sec_insider_bulk_history_gate import (
    EXPECTED_QUARTERS, TABLE_KEYS, build_result, main, quarter_labels, validate_result,
)


class Phase279Tests(unittest.TestCase):
    def test_quarter_range_has_83_archives(self):
        self.assertEqual(len(quarter_labels()), 83)
        self.assertEqual(len(quarter_labels()), EXPECTED_QUARTERS)

    def test_quarter_range_endpoints(self):
        labels = quarter_labels()
        self.assertEqual(labels[0], "2006Q1")
        self.assertEqual(labels[-1], "2026Q3")

    def test_quarter_range_has_no_gaps(self):
        labels = quarter_labels()
        self.assertEqual(labels[3], "2006Q4")
        self.assertEqual(labels[4], "2007Q1")
        self.assertEqual(labels[-2:], ["2026Q2", "2026Q3"])

    def test_invalid_quarter_rejected(self):
        with self.assertRaises(ValueError):
            quarter_labels(start_quarter=0)
        with self.assertRaises(ValueError):
            quarter_labels(end_quarter=5)

    def test_reversed_range_rejected(self):
        with self.assertRaises(ValueError):
            quarter_labels(2026, 3, 2006, 1)

    def test_eight_documented_tables(self):
        result = build_result()
        self.assertEqual(set(result["documented_tables"]), set(TABLE_KEYS))
        self.assertEqual(result["documented_tables"], TABLE_KEYS)

    def test_submission_uses_accession_primary_key(self):
        result = build_result()
        self.assertEqual(result["documented_tables"]["SUBMISSION"], ["ACCESSION_NUMBER"])

    def test_flattened_transactions_do_not_identify_reporting_owner(self):
        result = build_result()
        self.assertFalse(result["schema_contract"]["transaction_table_has_reporting_owner_cik"])
        self.assertTrue(result["pit_and_identity"]["multi_owner_transaction_join_requires_raw_xml_or_exclusion"])

    def test_flattened_submission_has_no_acceptance_datetime(self):
        result = build_result()
        self.assertFalse(result["schema_contract"]["submission_has_acceptance_datetime"])
        self.assertTrue(result["pit_and_identity"]["acceptance_time_requires_accession_join"])

    def test_aff10b5one_missing_is_not_false(self):
        result = build_result()
        field = result["schema_contract"]["aff10b5one"]
        self.assertFalse(field["present_in_documented_readme"])
        self.assertFalse(field["missing_means_false"])
        self.assertTrue(field["submission_level_not_transaction_level"])
        self.assertTrue(result["pit_and_identity"]["aff10b5one_must_not_be_broadcast_as_line_level_plan_label"])

    def test_archive_volume_is_documented_not_downloaded(self):
        result = build_result()
        source = result["source"]
        self.assertEqual(source["sec_listed_zip_size_mb_sum"], 887.43)
        self.assertEqual(source["sec_listed_zip_size_mb_min"], 7.59)
        self.assertEqual(source["sec_listed_zip_size_mb_max"], 16.51)
        self.assertFalse(source["archive_bytes_downloaded"])

    def test_p_code_does_not_prove_open_market(self):
        result = build_result()
        self.assertFalse(result["pit_and_identity"]["transaction_code_p_alone_proves_open_market"])
        self.assertTrue(result["pit_and_identity"]["explicit_footnote_review_required"])

    def test_amendments_remain_vintages(self):
        result = build_result()
        self.assertTrue(result["source"]["includes_amendments"])
        self.assertTrue(result["pit_and_identity"]["amendments_must_remain_separate_vintages"])
        self.assertFalse(result["pit_and_identity"]["form4a_is_new_transaction_signal"])

    def test_no_pit_or_alpha_admission(self):
        result = main()
        self.assertFalse(result["gates"]["strict_pit_admitted"])
        self.assertFalse(result["gates"]["alpha_test_authorized"])
        self.assertTrue(result["gates"]["f80_frozen"])

    def test_documentation_only_no_network_or_archive_access(self):
        result = build_result()
        self.assertEqual(result["controls"]["raw_sec_requests"], 0)
        self.assertEqual(result["controls"]["raw_archives_downloaded"], 0)
        self.assertFalse(result["source"]["archive_bytes_downloaded"])

    def test_validator_rejects_false_pit_admission(self):
        result = build_result()
        result["gates"]["strict_pit_admitted"] = True
        with self.assertRaises(ValueError):
            validate_result(result)


if __name__ == "__main__":
    unittest.main()
