import unittest
from decimal import Decimal

from research.phase109_finra_ats_full_reconciliation import (
    SYMBOL_BEARING,
    cohort_reconcile,
    expanded_candidate_key,
    parse_decimal,
    parse_page_metadata,
    parse_response,
)


def row(summary, symbol="LND", last_date="2025-01-08", qty="100", trades="10"):
    return {
        "issueSymbolIdentifier": symbol,
        "weekStartDate": "2025-01-06",
        "tierIdentifier": "T2",
        "summaryTypeCode": summary,
        "productTypeCode": "CTS" if summary.endswith("_SMBL") else "",
        "MPID": "ABCD" if summary.endswith("_SMBL_FIRM") else "",
        "firmCRDNumber": "",
        "lastReportedDate": last_date,
        "totalWeeklyShareQuantity": qty,
        "totalWeeklyTradeCount": trades,
    }


class Phase109Tests(unittest.TestCase):
    def test_parse_response_accepts_list_and_nested_data(self):
        self.assertEqual(parse_response([{"x": 1}]), [{"x": 1}])
        self.assertEqual(parse_response({"data": {"data": [{"x": 2}]}}), [{"x": 2}])

    def test_parse_response_rejects_error_object(self):
        with self.assertRaises(ValueError):
            parse_response({"statusCode": 400, "message": "bad request"})

    def test_page_metadata_uses_body_length_when_optional_header_missing(self):
        self.assertEqual(
            parse_page_metadata(
                {"Record-Total": "9", "Record-Offset": "0"},
                [{"x": 1}, {"x": 2}], 0,
            ),
            (9, 2, "body_length"),
        )

    def test_page_metadata_rejects_wrong_offset_and_count(self):
        headers = {
            "Record-Total": "9",
            "Total-Records-On-Page": "2",
            "Record-Offset": "5",
        }
        self.assertEqual(
            parse_page_metadata(headers, [{"x": 1}, {"x": 2}], 5),
            (9, 2, "header"),
        )
        with self.assertRaises(RuntimeError):
            parse_page_metadata({**headers, "Record-Offset": "0"}, [{"x": 1}, {"x": 2}], 5)
        with self.assertRaises(RuntimeError):
            parse_page_metadata({**headers, "Total-Records-On-Page": "1"}, [{"x": 1}, {"x": 2}], 5)

    def test_decimal_parser_is_exact_and_rejects_nonfinite(self):
        self.assertEqual(parse_decimal("1,234"), Decimal("1234"))
        self.assertIsNone(parse_decimal("NaN"))
        self.assertIsNone(parse_decimal(""))

    def test_symbol_bearing_types_are_explicit(self):
        self.assertIn("ATS_W_SMBL", SYMBOL_BEARING)
        self.assertIn("OTC_W_SMBL_FIRM", SYMBOL_BEARING)

    def test_candidate_key_includes_participant_and_report_date(self):
        a = row("ATS_W_SMBL_FIRM", last_date="2025-01-08")
        b = {**a, "lastReportedDate": "2025-01-10"}
        c = {**a, "MPID": "WXYZ"}
        self.assertNotEqual(expanded_candidate_key(a), expanded_candidate_key(b))
        self.assertNotEqual(expanded_candidate_key(a), expanded_candidate_key(c))

    def test_lnd_incremental_reporting_cohorts_reconcile(self):
        rows = [
            row("ATS_W_SMBL", last_date="2025-01-08", qty="5226", trades="144"),
            row("ATS_W_SMBL", last_date="2025-01-10", qty="6224", trades="37"),
            row("ATS_W_SMBL_FIRM", last_date="2025-01-07", qty="400", trades="7"),
            row("ATS_W_SMBL_FIRM", last_date="2025-01-08", qty="4826", trades="137"),
            row("ATS_W_SMBL_FIRM", last_date="2025-01-10", qty="6224", trades="37"),
        ]
        summary, details, symbols = cohort_reconcile(rows, "2025-01-06", "T2")
        ats = summary["families"]["ATS"]
        self.assertEqual(ats["symbol_keys"], 1)
        self.assertEqual(ats["cohort_count"], 2)
        self.assertEqual(ats["cohort_matches"], 2)
        self.assertEqual(ats["fully_reconciled_keys"], 1)
        self.assertEqual(symbols[0]["aggregate_quantity_total"], "11450")
        self.assertEqual(symbols[0]["firm_quantity_total"], "11450")
        self.assertTrue(symbols[0]["fully_reconciled"])
        self.assertTrue(all(x["cohort_match"] for x in details))

    def test_trailing_firm_update_is_not_silently_absorbed(self):
        rows = [
            row("ATS_W_SMBL", last_date="2025-01-08", qty="100", trades="10"),
            row("ATS_W_SMBL_FIRM", last_date="2025-01-08", qty="100", trades="10"),
            row("ATS_W_SMBL_FIRM", last_date="2025-01-10", qty="25", trades="2"),
        ]
        summary, details, symbols = cohort_reconcile(rows, "2025-01-06", "T2")
        self.assertEqual(symbols[0]["trailing_unmatched_firm_rows"], 1)
        self.assertFalse(symbols[0]["fully_reconciled"])
        self.assertEqual(summary["families"]["ATS"]["keys_with_trailing_firm_rows"], 1)

    def test_quantity_mismatch_fails_cohort(self):
        rows = [
            row("OTC_W_SMBL", last_date="2025-01-08", qty="101", trades="10"),
            row("OTC_W_SMBL_FIRM", last_date="2025-01-08", qty="100", trades="10"),
        ]
        summary, details, symbols = cohort_reconcile(rows, "2025-01-06", "T2")
        self.assertFalse(details[0]["quantity_match"])
        self.assertFalse(symbols[0]["fully_reconciled"])
        self.assertEqual(summary["families"]["OTC"]["cohort_matches"], 0)

    def test_negative_quantity_cannot_pass_reconciliation(self):
        rows = [
            row("ATS_W_SMBL", last_date="2025-01-08", qty="-100", trades="10"),
            row("ATS_W_SMBL_FIRM", last_date="2025-01-08", qty="-100", trades="10"),
        ]
        summary, details, symbols = cohort_reconcile(rows, "2025-01-06", "T2")
        self.assertFalse(details[0]["cohort_match"])
        self.assertFalse(symbols[0]["fully_reconciled"])

    def test_missing_symbol_is_counted_separately(self):
        rows = [
            row("OTC_W_SMBL", symbol="", last_date="2025-01-08", qty="50", trades="5"),
        ]
        summary, details, symbols = cohort_reconcile(rows, "2025-01-06", "T2")
        self.assertEqual(summary["missing_symbol_rows"], 1)
        self.assertEqual(summary["families"]["OTC"]["symbol_keys"], 0)


if __name__ == "__main__":
    unittest.main()
