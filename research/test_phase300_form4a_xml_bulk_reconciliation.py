import unittest

from phase300_form4a_xml_bulk_reconciliation import (
    ND_FULL, ND_CORE, DV_FULL, DV_CORE, normalized, multiset_match, diff_rows,
)
from phase299_form4a_edgar_validation import ND_COARSE, DV_COARSE


class Phase300Tests(unittest.TestCase):
    def test_date_normalization_matches_bulk_and_xml_formats(self):
        self.assertEqual(normalized("TRANS_DATE", "15-MAY-2026"), "2026-05-15")
        self.assertEqual(normalized("TRANS_DATE", "2026-05-15"), "2026-05-15")

    def test_numeric_normalization_matches_bulk_two_decimal_precision(self):
        self.assertEqual(normalized("TRANS_PRICEPERSHARE", "81.5165"), "81.52")
        self.assertEqual(normalized("CONV_EXERCISE_PRICE", "3.605"), "3.61")
        self.assertEqual(normalized("TRANS_SHARES", "100.0"), "100.00")

    def test_footnote_and_timeliness_fields_are_excluded_only_from_core_signature(self):
        bulk = [{
            "SECURITY_TITLE": "Common Stock", "TRANS_DATE": "15-MAY-2026",
            "TRANS_FORM_TYPE": "4", "TRANS_CODE": "P", "EQUITY_SWAP_INVOLVED": "0",
            "TRANS_SHARES": "100", "TRANS_PRICEPERSHARE": "10",
            "TRANS_ACQUIRED_DISP_CD": "A", "SHRS_OWND_FOLWNG_TRANS": "1100",
            "DIRECT_INDIRECT_OWNERSHIP": "D", "NATURE_OF_OWNERSHIP": "SEE NOTE 4",
            "TRANS_TIMELINESS": "",
        }]
        xml = [{
            "SECURITY_TITLE": "Common Stock", "TRANS_DATE": "2026-05-15",
            "TRANS_FORM_TYPE": "4", "TRANS_CODE": "P", "EQUITY_SWAP_INVOLVED": "0",
            "TRANS_SHARES": "100", "TRANS_PRICEPERSHARE": "10.00",
            "TRANS_ACQUIRED_DISP_CD": "A", "SHRS_OWND_FOLWNG_TRANS": "1100.00",
            "DIRECT_INDIRECT_OWNERSHIP": "D", "NATURE_OF_OWNERSHIP": "",
            "TRANS_TIMELINESS": "",
        }]
        self.assertFalse(multiset_match(bulk, xml, ND_FULL))
        self.assertTrue(multiset_match(bulk, xml, ND_CORE))

    def test_core_signature_does_not_ignore_transaction_amount_mismatch(self):
        bulk = [{
            "SECURITY_TITLE": "Common Stock", "TRANS_DATE": "15-MAY-2026",
            "TRANS_FORM_TYPE": "4", "TRANS_CODE": "P", "TRANS_SHARES": "100",
            "TRANS_PRICEPERSHARE": "10", "TRANS_ACQUIRED_DISP_CD": "A",
        }]
        xml = [{
            "SECURITY_TITLE": "Common Stock", "TRANS_DATE": "2026-05-15",
            "TRANS_FORM_TYPE": "4", "TRANS_CODE": "P", "TRANS_SHARES": "101",
            "TRANS_PRICEPERSHARE": "10", "TRANS_ACQUIRED_DISP_CD": "A",
        }]
        self.assertFalse(multiset_match(bulk, xml, ND_CORE))

    def test_derivative_core_keeps_amount_and_underlying_fields(self):
        bulk = [{
            "SECURITY_TITLE": "Warrants", "TRANS_DATE": "27-JAN-2012",
            "TRANS_FORM_TYPE": "4", "TRANS_CODE": "P", "TRANS_SHARES": "",
            "TRANS_TOTAL_VALUE": "", "TRANS_PRICEPERSHARE": "0",
            "TRANS_ACQUIRED_DISP_CD": "A", "EXCERCISE_DATE": "27-JAN-2012",
            "EXPIRATION_DATE": "27-JAN-2017", "CONV_EXERCISE_PRICE": "0.10",
            "UNDLYNG_SEC_TITLE": "Common Stock", "UNDLYNG_SEC_SHARES": "400000",
            "SHRS_OWND_FOLWNG_TRANS": "", "DIRECT_INDIRECT_OWNERSHIP": "I",
            "NATURE_OF_OWNERSHIP": "By fund", "TRANS_TIMELINESS": "",
        }]
        xml = [{
            "SECURITY_TITLE": "Warrants", "TRANS_DATE": "2012-01-27",
            "TRANS_FORM_TYPE": "4", "TRANS_CODE": "P", "TRANS_SHARES": "400000",
            "TRANS_TOTAL_VALUE": "", "TRANS_PRICEPERSHARE": "0",
            "TRANS_ACQUIRED_DISP_CD": "A", "EXCERCISE_DATE": "2012-01-27",
            "EXPIRATION_DATE": "2017-01-27", "CONV_EXERCISE_PRICE": "0.10",
            "UNDLYNG_SEC_TITLE": "Common Stock", "UNDLYNG_SEC_SHARES": "400000",
            "SHRS_OWND_FOLWNG_TRANS": "400000", "DIRECT_INDIRECT_OWNERSHIP": "I",
            "NATURE_OF_OWNERSHIP": "By fund", "TRANS_TIMELINESS": "",
        }]
        self.assertFalse(multiset_match(bulk, xml, DV_CORE))

    def test_line_diff_uses_normalized_date_and_price_precision(self):
        parent = [{
            "SECURITY_TITLE": "Common Stock", "TRANS_DATE": "15-MAY-2026",
            "TRANS_FORM_TYPE": "4", "TRANS_CODE": "P", "TRANS_SHARES": "100",
            "TRANS_PRICEPERSHARE": "10.00",
        }]
        child = [{
            "SECURITY_TITLE": "Common Stock", "TRANS_DATE": "2026-05-15",
            "TRANS_FORM_TYPE": "4", "TRANS_CODE": "P", "TRANS_SHARES": "100.00",
            "TRANS_PRICEPERSHARE": "10",
        }]
        result = diff_rows(parent, child, ND_CORE, ND_COARSE)
        self.assertEqual(result["exact_repeated"], 1)
        self.assertEqual(result["same_coarse_unmatched"], 0)
        self.assertEqual(result["distinct_coarse_added"], 0)


if __name__ == "__main__":
    unittest.main()
