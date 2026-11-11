from __future__ import annotations

import unittest

from research.phase278_finra_ats_duplicate_grain_followup import (
    WEEK,
    TIER,
    build_result,
    inspect_duplicate_groups,
)


def row(
    symbol="LND",
    summary="ATS_W_SMBL",
    product="CTS",
    week=WEEK,
    tier=TIER,
    shares="100",
    trades="10",
    reported="2025-07-10",
    published="2025-08-04",
    updated="2025-08-04",
):
    return {
        "issueSymbolIdentifier": symbol,
        "weekStartDate": week,
        "tierIdentifier": tier,
        "summaryTypeCode": summary,
        "productTypeCode": product,
        "totalWeeklyShareQuantity": shares,
        "totalWeeklyTradeCount": trades,
        "initialPublishedDate": published,
        "lastUpdateDate": updated,
        "lastReportedDate": reported,
    }


def pages(n):
    return [{
        "page": 0,
        "offset": 0,
        "rows": n,
        "record_total": n,
        "week": WEEK,
        "tier": TIER,
        "sha256": "a" * 64,
        "request_id": "req-1",
    }]


class Phase278Tests(unittest.TestCase):
    def test_conflict_split_by_last_reported_is_diagnostic_only(self):
        result = inspect_duplicate_groups([
            row(shares="100", reported="2025-07-08"),
            row(shares="200", reported="2025-07-10"),
        ])
        self.assertEqual(result["candidate_key_group_count"], 1)
        self.assertEqual(result["conflicting_groups"], 1)
        self.assertEqual(result["groups_split_by_last_reported_date"], 1)
        self.assertEqual(result["groups_still_duplicate_after_last_reported_date"], 0)
        self.assertIn("lastReportedDate", result["groups"][0]["differing_fields"])

    def test_exact_duplicate_is_not_conflict(self):
        result = inspect_duplicate_groups([row(), row()])
        self.assertEqual(result["exact_duplicate_groups"], 1)
        self.assertEqual(result["conflicting_groups"], 0)
        self.assertEqual(result["groups_still_duplicate_after_last_reported_date"], 1)

    def test_conflict_same_last_reported_remains_after_extended_key(self):
        result = inspect_duplicate_groups([row(shares="100"), row(shares="200")])
        self.assertEqual(result["conflicting_groups"], 1)
        self.assertEqual(result["groups_split_by_last_reported_date"], 0)
        self.assertEqual(result["groups_still_duplicate_after_last_reported_date"], 1)

    def test_different_summary_types_are_separate_keys(self):
        result = inspect_duplicate_groups([
            row(summary="ATS_W_SMBL"),
            row(summary="OTC_W_SMBL"),
        ])
        self.assertEqual(result["candidate_key_group_count"], 0)

    def test_non_symbol_firm_rows_are_not_in_candidate_key_scope(self):
        result = inspect_duplicate_groups([
            row(summary="ATS_W_SMBL_FIRM"),
            row(summary="ATS_W_SMBL_FIRM"),
        ])
        self.assertEqual(result["candidate_key_group_count"], 0)

    def test_row_digest_changes_when_payload_changes(self):
        result = inspect_duplicate_groups([
            row(shares="100", reported="2025-07-08"),
            row(shares="200", reported="2025-07-10"),
        ])
        self.assertEqual(len(set(result["groups"][0]["row_sha256"])), 2)

    def test_build_result_enforces_full_partition_and_controls(self):
        result = build_result([row()], pages(1))
        self.assertTrue(result["retrieval"]["api_record_total_reconciled"])
        self.assertFalse(result["pit"]["strict_pit_admitted"])
        self.assertFalse(result["economic_interpretation"]["alpha_test_authorized"])
        self.assertTrue(result["controls"]["f80_frozen"])
        self.assertFalse(result["controls"]["full_partition_rows_persisted"])

    def test_page_hash_invalid_fails_closed(self):
        bad = pages(1)
        bad[0]["sha256"] = "bad"
        with self.assertRaisesRegex(ValueError, "INVALID_PAGE_SHA256"):
            build_result([row()], bad)

    def test_noncontiguous_offset_fails_closed(self):
        bad = pages(1)
        bad[0]["offset"] = 5
        with self.assertRaisesRegex(ValueError, "NONCONTIGUOUS_PAGE_OFFSET"):
            build_result([row()], bad)

    def test_record_total_mismatch_fails_closed(self):
        bad = pages(1)
        bad[0]["record_total"] = 2
        with self.assertRaisesRegex(ValueError, "RECORD_TOTAL_NOT_RECONCILED"):
            build_result([row()], bad)

    def test_partition_mismatch_fails_closed(self):
        bad = pages(1)
        bad[0]["tier"] = "T1"
        with self.assertRaisesRegex(ValueError, "PAGE_PARTITION_MISMATCH"):
            build_result([row()], bad)

    def test_missing_symbol_row_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "PARTITION_ROW_VALIDATION_FAILED"):
            build_result([row(symbol="")], pages(1))

    def test_unknown_summary_type_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "PARTITION_ROW_VALIDATION_FAILED"):
            build_result([row(summary="UNKNOWN")], pages(1))


if __name__ == "__main__":
    unittest.main()
