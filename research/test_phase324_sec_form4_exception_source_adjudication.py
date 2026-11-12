import unittest

from research.phase324_sec_form4_exception_source_adjudication import (
    classify_index_evidence,
    extract_xml_identity,
    transaction_code_buckets,
    validate_result,
)


class Phase324ExceptionSourceTests(unittest.TestCase):
    def test_multi_index_date_conflict_stays_quarantined(self):
        header = {
            "filed_date": "2006-02-15",
            "acceptance_date": "2008-10-02",
        }
        rows = [
            {"index_date": "2008-10-02", "filing_date": "2006-02-15", "form_type": "4", "cik": "775662"},
            {"index_date": "2008-10-06", "filing_date": "2008-10-02", "form_type": "4", "cik": "775662"},
        ]
        result = classify_index_evidence(rows, header, "2006-02-15")
        self.assertEqual(result["classification"], "MULTI_INDEX_DATE_OR_FILED_DATE_CONFLICT_QUARANTINED")
        self.assertFalse(result["strict_pit_admitted"])

    def test_long_acceptance_lag_stays_quarantined_even_if_index_matches(self):
        header = {
            "filed_date": "2006-02-14",
            "acceptance_date": "2006-10-13",
        }
        rows = [
            {"index_date": "2006-10-13", "filing_date": "2006-10-13", "form_type": "4", "cik": "1298341"},
        ]
        result = classify_index_evidence(rows, header, "2006-02-14")
        self.assertEqual(result["classification"], "LONG_ACCEPTANCE_LAG_INDEX_FOUND_QUARANTINED")
        self.assertEqual(result["acceptance_lag_business_days"], 168)

    def test_missing_index_after_recheck_is_quarantined(self):
        header = {"filed_date": "2026-09-16", "acceptance_date": "2026-09-16"}
        result = classify_index_evidence([], header, "2026-09-16")
        self.assertEqual(
            result["classification"],
            "ORIGINAL_HEADER_CONFIRMED_DAILY_INDEX_ABSENT_IN_RECHECK_WINDOW_QUARANTINED",
        )


    def test_incomplete_index_search_is_not_misclassified_as_absence(self):
        header = {"filed_date": "2026-09-16", "acceptance_date": "2026-09-16"}
        result = classify_index_evidence([], header, "2026-09-16", search_incomplete=True)
        self.assertEqual(result["classification"], "INDEX_SEARCH_INCOMPLETE_QUARANTINED")

    def test_same_day_acceptance_index_is_date_level_only(self):
        header = {"filed_date": "2026-09-16", "acceptance_date": "2026-09-16"}
        rows = [
            {"index_date": "2026-09-16", "filing_date": "2026-09-16", "form_type": "4", "cik": "1651308"},
        ]
        result = classify_index_evidence(rows, header, "2026-09-16")
        self.assertEqual(
            result["classification"],
            "ACCEPTANCE_DATE_AND_DAILY_INDEX_CORROBORATED_DATE_LEVEL_ONLY",
        )
        self.assertFalse(result["strict_pit_admitted"])

    def test_xml_identity_extracts_issuer_and_multiple_reporting_owners(self):
        raw = b"""
        <issuerCik>0001651308</issuerCik>
        <rptOwnerCik>0001263508</rptOwnerCik>
        <rptOwnerCik>0001087939</rptOwnerCik>
        """
        result = extract_xml_identity(raw)
        self.assertEqual(result["issuer_ciks"], ["1651308"])
        self.assertEqual(result["reporting_owner_ciks"], ["1087939", "1263508"])

    def test_m_code_is_not_treated_as_open_market_purchase(self):
        raw = b"""
        <transactionCode>M</transactionCode>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
        """
        result = extract_xml_identity(raw)
        buckets = transaction_code_buckets(result["transaction_codes"])
        self.assertIn("EXERCISE_OR_CONVERSION_NOT_OPEN_MARKET", buckets)
        self.assertNotIn("OPEN_MARKET_PURCHASE", buckets)


    def test_p_code_does_not_overstate_public_market_execution(self):
        raw = b"<transactionCode>P</transactionCode>"
        result = extract_xml_identity(raw)
        buckets = transaction_code_buckets(result["transaction_codes"])
        self.assertIn("OPEN_MARKET_OR_PRIVATE_PURCHASE", buckets)
        self.assertNotIn("OPEN_MARKET_PURCHASE", buckets)

    def test_validator_keeps_strategy_controls_closed(self):
        result = {
            "phase": 324,
            "summary": {"target_exceptions": 3, "original_filings_retrieved": 3},
            "cases": [{}, {}, {}],
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
            "retrieval": {"raw_sec_bytes_uploaded": False, "http_request_errors": 0, "parser_errors": 0},
        }
        validate_result(result)
        result["controls"]["holdout_used"] = True
        with self.assertRaises(ValueError):
            validate_result(result)


if __name__ == "__main__":
    unittest.main()
