from __future__ import annotations

import unittest

from research.phase277_finra_ats_stratified_coverage_audit import (
    WEEKS,
    analyze_partition,
    build_result,
    _prior_context,
)


def row(
    symbol="ABC",
    week="2022-04-04",
    tier="T1",
    summary="ATS_W_SMBL",
    product="CTS",
    published="2022-04-18",
    updated="2022-04-18",
    reported="2022-04-15",
    shares="100",
    trades="10",
):
    return {
        "issueSymbolIdentifier": symbol,
        "issueName": "Example",
        "firmCRDNumber": "",
        "MPID": "",
        "marketParticipantName": "",
        "tierIdentifier": tier,
        "tierDescription": "",
        "summaryStartDate": week,
        "totalWeeklyTradeCount": trades,
        "totalWeeklyShareQuantity": shares,
        "productTypeCode": product,
        "summaryTypeCode": summary,
        "weekStartDate": week,
        "lastUpdateDate": updated,
        "initialPublishedDate": published,
        "lastReportedDate": reported,
    }


def pages(n):
    return [{
        "page": 0,
        "offset": 0,
        "rows": n,
        "record_total": n,
        "week": "2022-04-04",
        "tier": "T1",
        "sha256": "a" * 64,
        "request_id": "req-1",
    }]


class Phase277Tests(unittest.TestCase):
    def test_eight_new_weeks_are_mondays_and_unique(self):
        self.assertEqual(len(WEEKS), 8)
        self.assertEqual(len(set(WEEKS)), 8)
        for value in WEEKS:
            self.assertEqual(__import__("datetime").date.fromisoformat(value).weekday(), 0)

    def test_basic_partition_counts_and_hashes(self):
        result, symbols = analyze_partition([row()], "2022-04-04", "T1", pages(1))
        self.assertEqual(result["rows_total"], 1)
        self.assertEqual(result["api_record_total"], 1)
        self.assertTrue(result["api_record_total_reconciled"])
        self.assertEqual(result["ats_unique_symbol_tokens"], 1)
        self.assertEqual(symbols["ATS_W_SMBL"], {"ABC"})

    def test_missing_symbol_is_not_dropped_or_zero_filled(self):
        result, _ = analyze_partition([row(symbol="")], "2022-04-04", "T1", pages(1))
        self.assertEqual(result["symbol_aggregate_rows"], 1)
        self.assertEqual(result["missing_symbol_bearing_rows"], 1)
        self.assertEqual(result["ats_unique_symbol_tokens"], 0)

    def test_unknown_summary_type_is_reported(self):
        result, _ = analyze_partition(
            [row(summary="NEW_TYPE")], "2022-04-04", "T1", pages(1)
        )
        self.assertEqual(result["unknown_summary_type_rows"], 1)

    def test_wrong_partition_is_reported(self):
        result, _ = analyze_partition(
            [row(week="2022-04-11")], "2022-04-04", "T1", pages(1)
        )
        self.assertGreater(result["partition_validation_problem_count"], 0)

    def test_later_last_update_counts_as_revision(self):
        result, _ = analyze_partition(
            [row(updated="2022-04-20")], "2022-04-04", "T1", pages(1)
        )
        self.assertEqual(result["post_initial_publication_update_rows"], 1)

    def test_missing_update_is_not_assumed_unrevised(self):
        result, _ = analyze_partition(
            [row(updated="")], "2022-04-04", "T1", pages(1)
        )
        self.assertEqual(result["last_update_date_missing_rows"], 1)
        self.assertEqual(result["post_initial_publication_update_rows"], 0)

    def test_early_publication_is_diagnostic(self):
        result, _ = analyze_partition(
            [row(published="2022-04-10")], "2022-04-04", "T1", pages(1)
        )
        self.assertEqual(result["publication_before_tier_minimum_delay_rows"], 1)

    def test_invalid_quantities_are_counted(self):
        result, _ = analyze_partition(
            [row(shares="-1", trades="x")], "2022-04-04", "T1", pages(1)
        )
        self.assertEqual(result["invalid_or_negative_quantity_fields"], 2)

    def test_conflicting_base_duplicate_is_not_deduplicated(self):
        rows = [row(), row(shares="200")]
        result, _ = analyze_partition(rows, "2022-04-04", "T1", pages(2))
        self.assertEqual(result["base_duplicate_key_groups"], 1)
        self.assertEqual(result["conflicting_base_duplicate_groups"], 1)

    def test_exact_duplicate_is_separately_counted(self):
        result, _ = analyze_partition(
            [row(), row()], "2022-04-04", "T1", pages(2)
        )
        self.assertEqual(result["exact_base_duplicate_groups"], 1)
        self.assertEqual(result["conflicting_base_duplicate_groups"], 0)

    def test_last_reported_date_split_is_only_sensitivity(self):
        rows = [row(reported="2022-04-15"), row(reported="2022-04-14", shares="200")]
        result, _ = analyze_partition(rows, "2022-04-04", "T1", pages(2))
        self.assertEqual(result["duplicate_groups_split_by_last_reported_date"], 1)
        self.assertEqual(result["extended_key_duplicate_groups_after_last_reported"], 0)

    def test_ats_otc_token_overlap_is_counted(self):
        rows = [
            row(symbol="ABC", summary="ATS_W_SMBL"),
            row(symbol="ABC", summary="OTC_W_SMBL"),
            row(symbol="XYZ", summary="OTC_W_SMBL"),
        ]
        result, _ = analyze_partition(rows, "2022-04-04", "T1", pages(3))
        self.assertEqual(result["ats_otc_intersection_tokens"], 1)
        self.assertEqual(result["union_unique_symbol_tokens"], 2)

    def test_page_total_mismatch_fails_closed(self):
        bad = pages(1)
        bad[0]["record_total"] = 2
        with self.assertRaisesRegex(ValueError, "RECORD_TOTAL_NOT_RECONCILED"):
            analyze_partition([row()], "2022-04-04", "T1", bad)

    def test_invalid_page_hash_fails_closed(self):
        bad = pages(1)
        bad[0]["sha256"] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "INVALID_PAGE_SHA256"):
            analyze_partition([row()], "2022-04-04", "T1", bad)

    def test_page_offset_gap_fails_closed(self):
        bad = pages(1)
        bad[0]["offset"] = 5
        with self.assertRaisesRegex(ValueError, "NONCONTIGUOUS_PAGE_OFFSET"):
            analyze_partition([row()], "2022-04-04", "T1", bad)

    def test_build_result_requires_exact_partition_grid(self):
        prior = {
            "phase": 264,
            "upstream": {"artifact_zip_sha256": "803c58a5301df8b505b487c5367a449696c6bc467cab39121c50eda762d1f3e9"},
            "sample": {
                "partitions_completed": 10, "partitions_expected": 10,
                "weeks": ["2022-01-03"], "rows_total": 100,
                "symbol_aggregate_rows": 50, "post_initial_publication_update_rows": 1,
            },
            "row_integrity": {"missing_symbol_errors": 0},
            "duplicate_audit": {"conflicting_groups": 0},
        }
        with self.assertRaisesRegex(ValueError, "EXPECTED_16_PARTITIONS"):
            build_result([], prior)

    def test_prior_context_rejects_wrong_hash(self):
        import json
        import tempfile
        from pathlib import Path
        bad = {
            "phase": 264,
            "upstream": {"artifact_zip_sha256": "0" * 64},
            "sample": {"partitions_completed": 10, "partitions_expected": 10},
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prior.json"
            path.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "PHASE264_ARTIFACT_HASH_MISMATCH"):
                _prior_context(path)


if __name__ == "__main__":
    unittest.main()
