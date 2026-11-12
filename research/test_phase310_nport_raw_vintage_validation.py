import unittest

from research.phase310_nport_raw_vintage_validation import build_validation


def _summary(row):
    return {
        "status": "RAW_SAMPLE_RETRIEVED_ACCEPTANCE_RECONCILED",
        "accession_results": [row],
    }


def _evidence(cusips=None):
    return {
        "accessions": [{
            "accession": "0001145549-25-033457",
            "cik": "1467631",
            "filing_year": 2025,
            "expected_cusips": cusips if cusips is not None else ["31428X106"],
        }]
    }


def _row(sign=True, truncated=False, series=True):
    return {
        "accession": "0001145549-25-033457",
        "status": "RAW_RETRIEVED",
        "index_sha256": "a" * 64,
        "submission_sha256": "b" * 64,
        "primary_xml_sha256": "c" * 64,
        "index_bytes": 100,
        "submission_bytes": 200,
        "primary_xml_bytes": 300,
        "raw_files_staged_for_artifact": True,
        "submission_header": {
            "header_accession_reconciled": "true",
            "header_form_reconciled": "true",
            "acceptance_datetime_utc": "2025-05-28T20:04:35+00:00",
            "acceptance_date_matches_filed_date": True,
        },
        "index_listing": {"primary_document_last_modified": "2025-05-28 16:04:35"},
        "xml_audit": {
            "series_ids": ["S000000001"] if series else [],
            "distinct_series_id_count": 1 if series else 0,
            "holding_nodes": 100,
            "counts": {"short_ec_corp_us_rows": 1},
            "direct_short_rows_sample": [{
                "cusip": "31428X106",
                "units": "NS",
                "balance": "-100",
                "val_usd": "-1000",
                "pct_net_assets": "-0.1",
                "sign_concordant": sign,
            }],
            "direct_short_rows_sample_truncated": truncated,
        },
    }


class Phase310NportRawVintageTests(unittest.TestCase):
    def test_raw_hashes_headers_series_and_sign_control_pass(self):
        result = build_validation(_summary(_row()), _evidence())
        self.assertEqual(result["status"], "RAW_BYTES_HASHED_ACCEPTANCE_RECONCILED")
        self.assertEqual(result["expected_public_positive_control_sign_gate"], "PASS")
        self.assertEqual(result["accessions"][0]["conservative_next_full_xnys_session"], "2025-05-29")
        self.assertTrue(result["controls"]["f80_frozen"])
        self.assertFalse(result["controls"]["strict_pit_admitted"])

    def test_expected_cusip_with_sign_conflict_fails_separate_gate(self):
        result = build_validation(_summary(_row(sign=False)), _evidence())
        self.assertEqual(result["status"], "RAW_BYTES_HASHED_ACCEPTANCE_RECONCILED")
        self.assertEqual(result["expected_public_positive_control_sign_gate"], "FAIL")
        self.assertEqual(result["accessions"][0]["expected_cusips_missing_sign_concordant"], ["31428X106"])

    def test_truncated_row_sample_leaves_sign_gate_unknown(self):
        result = build_validation(_summary(_row(truncated=True)), _evidence())
        self.assertEqual(result["expected_public_positive_control_sign_gate"], "UNKNOWN")

    def test_missing_series_fails_raw_reconciliation_gate(self):
        result = build_validation(_summary(_row(series=False)), _evidence())
        self.assertEqual(result["status"], "PARTIAL_RAW_RETRIEVAL_OR_RECONCILIATION")
        self.assertEqual(result["series_identity_presence_gate"], "FAIL")

    def test_missing_accession_is_not_treated_as_zero_or_complete(self):
        result = build_validation({"accession_results": []}, _evidence())
        self.assertEqual(result["status"], "PARTIAL_RAW_RETRIEVAL_OR_RECONCILIATION")
        self.assertEqual(result["accession_identity_set_gate"], "FAIL")
        self.assertEqual(result["expected_public_positive_control_sign_gate"], "UNKNOWN")

    def test_duplicate_accession_results_fail_closed(self):
        row = _row()
        with self.assertRaisesRegex(ValueError, "missing_or_duplicate_accession_result"):
            build_validation({"accession_results": [row, row]}, _evidence())

    def test_first_public_receipt_never_inferred_from_acceptance_or_index(self):
        result = build_validation(_summary(_row()), _evidence())
        self.assertFalse(result["controls"]["first_public_receipt_verified"])
        self.assertFalse(result["controls"]["acceptance_is_first_public_time"])
        self.assertFalse(result["controls"]["report_date_used_as_knowledge_date"])


if __name__ == "__main__":
    unittest.main()
