import unittest

from research.phase108_finra_ats_anomaly_resolution import (
    SYMBOL_BEARING,
    coarse_key,
    expanded_candidate_key,
    parse_response,
    parse_page_metadata,
    partition_issues,
    grouped_collisions,
)


class Phase108Tests(unittest.TestCase):
    def test_parse_response_list_and_nested(self):
        self.assertEqual(parse_response([{"a": 1}]), [{"a": 1}])
        self.assertEqual(parse_response({"data": {"data": [{"a": 2}]}}), [{"a": 2}])

    def test_parse_response_rejects_error_object(self):
        with self.assertRaises(ValueError):
            parse_response({"statusCode": 400, "message": "bad request"})

    def test_page_metadata_uses_body_length_without_optional_header(self):
        headers = {"Record-Total": "9", "Record-Offset": "0", "Record-Limit": "5000"}
        self.assertEqual(
            parse_page_metadata(headers, [{"x": 1}, {"x": 2}], "2025-01-06", "T2", 0),
            (9, 2, "body_length"),
        )

    def test_page_metadata_validates_header_count_and_offset(self):
        headers = {
            "Record-Total": "9",
            "Total-Records-On-Page": "2",
            "Record-Offset": "5",
        }
        self.assertEqual(
            parse_page_metadata(headers, [{"x": 1}, {"x": 2}], "2025-01-06", "T2", 5),
            (9, 2, "header"),
        )
        with self.assertRaises(RuntimeError):
            parse_page_metadata(
                {**headers, "Total-Records-On-Page": "1"},
                [{"x": 1}, {"x": 2}], "2025-01-06", "T2", 5,
            )
        with self.assertRaises(RuntimeError):
            parse_page_metadata(
                {**headers, "Record-Offset": "0"},
                [{"x": 1}, {"x": 2}], "2025-01-06", "T2", 5,
            )

    def test_missing_symbol_is_separate_from_week_tier_mismatch(self):
        rows = [
            {"weekStartDate": "2022-01-03", "tierIdentifier": "T2",
             "summaryTypeCode": "OTC_W_SMBL", "issueSymbolIdentifier": None},
            {"weekStartDate": "2022-01-03", "tierIdentifier": "T2",
             "summaryTypeCode": "OTC_W_FIRM", "issueSymbolIdentifier": None},
            {"weekStartDate": "2022-01-10", "tierIdentifier": "T2",
             "summaryTypeCode": "ATS_W_SMBL", "issueSymbolIdentifier": "ABC"},
        ]
        mismatches, missing = partition_issues(rows, "2022-01-03", "T2")
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(len(missing), 1)
        self.assertIn("OTC_W_SMBL", SYMBOL_BEARING)

    def test_last_reported_date_and_participant_are_in_expanded_candidate_key(self):
        base = {
            "issueSymbolIdentifier": "LND",
            "weekStartDate": "2025-01-06",
            "tierIdentifier": "T2",
            "summaryTypeCode": "ATS_W_SMBL",
            "productTypeCode": "CTS",
            "lastReportedDate": "2025-01-08",
            "MPID": "",
            "firmCRDNumber": "",
        }
        later = {**base, "lastReportedDate": "2025-01-10"}
        other_firm = {**base, "MPID": "ABCD"}
        self.assertEqual(coarse_key(base), coarse_key(later))
        self.assertNotEqual(expanded_candidate_key(base), expanded_candidate_key(later))
        self.assertNotEqual(expanded_candidate_key(base), expanded_candidate_key(other_firm))

    def test_coarse_collision_can_resolve_into_distinct_candidate_rows(self):
        a = {
            "issueSymbolIdentifier": "LND", "weekStartDate": "2025-01-06",
            "tierIdentifier": "T2", "summaryTypeCode": "ATS_W_SMBL",
            "productTypeCode": "CTS", "MPID": "", "firmCRDNumber": "",
            "lastReportedDate": "2025-01-08",
        }
        b = {**a, "lastReportedDate": "2025-01-10"}
        self.assertEqual(len(grouped_collisions([a, b], coarse_key)), 1)
        self.assertEqual(len(grouped_collisions([a, b], expanded_candidate_key)), 0)


if __name__ == "__main__":
    unittest.main()
