import unittest
from datetime import date

from research.phase377_cftc_tff_full_coverage_audit import (
    _weekly_coverage, build_summary, parse_report_date, resolve_position_fields,
)

FIELDS = [
    "id", "report_date_as_yyyy_mm_dd", "cftc_contract_market_code",
    "market_and_exchange_names", "contract_market_name", "cftc_market_code",
    "open_interest_all",
    "dealer_positions_long_all", "dealer_positions_short_all", "dealer_positions_spread_all",
    "asset_mgr_positions_long_all", "asset_mgr_positions_short_all", "asset_mgr_positions_spread_all",
    "lev_money_positions_long_all", "lev_money_positions_short_all", "lev_money_positions_spread_all",
    "other_rept_positions_long_all", "other_rept_positions_short_all", "other_rept_positions_spread_all",
    "nonrept_positions_long_all", "nonrept_positions_short_all",
]


def make_row(report_date="2026-11-03", code="13874A", name="E-MINI S&P 500 - CME", row_id="1"):
    row = {
        "id": row_id,
        "report_date_as_yyyy_mm_dd": report_date + "T00:00:00.000",
        "cftc_contract_market_code": code,
        "market_and_exchange_names": name,
        "contract_market_name": name,
        "cftc_market_code": "CME",
        "open_interest_all": "1000",
    }
    for field in FIELDS:
        if "positions" in field:
            row[field] = "10"
    return row


class Phase377Tests(unittest.TestCase):
    def test_parse_iso_timestamp_to_date(self):
        self.assertEqual(parse_report_date("2026-11-03T00:00:00.000"), date(2026, 11, 3))

    def test_weekly_coverage_does_not_forward_fill_missing_week(self):
        result = _weekly_coverage([date(2026, 10, 20), date(2026, 11, 3)])
        self.assertEqual(result["expected_weekly_anchors"], 3)
        self.assertEqual(result["missing_week_count"], 1)
        self.assertEqual(result["coverage_pct"], 66.666667)

    def test_position_field_resolver(self):
        result = resolve_position_fields(FIELDS)
        self.assertEqual(result["dealer"]["long"], "dealer_positions_long_all")
        self.assertEqual(result["leveraged_money"]["short"], "lev_money_positions_short_all")
        self.assertIsNone(result["non_reportables"]["spread"])

    def test_candidate_code_coverage_and_names(self):
        rows = [make_row("2026-10-20"), make_row("2026-10-27"), make_row("2026-11-03")]
        result = build_summary(
            rows, FIELDS, metadata={"name": "TFF Futures Only"},
            count_before=3, count_after=3,
            metadata_updated_before=123, metadata_updated_after=123,
        )
        candidate = result["candidate_contracts"]["13874A"]
        self.assertEqual(candidate["row_count"], 3)
        self.assertEqual(candidate["weekly_coverage"]["coverage_pct"], 100.0)
        self.assertEqual(candidate["first_report_date"], "2026-10-20")
        self.assertTrue(result["snapshot_stable_during_retrieval"])

    def test_duplicate_report_date_code_is_flagged(self):
        rows = [make_row(row_id="1"), make_row(row_id="2")]
        result = build_summary(
            rows, FIELDS, count_before=2, count_after=2,
            metadata_updated_before=123, metadata_updated_after=123,
        )
        self.assertEqual(
            result["candidate_contracts"]["13874A"]["duplicate_report_date_code_groups"], 1
        )
        self.assertEqual(result["candidate_natural_key_duplicate_groups_all_dataset"], 1)

    def test_consolidated_sp500_is_separate_non_additive_series(self):
        rows = [
            make_row(code="13874A", name="E-MINI S&P 500 - CME"),
            make_row(code="13874+", name="S&P 500 Consolidated - CME", row_id="2"),
        ]
        result = build_summary(
            rows, FIELDS, count_before=2, count_after=2,
            metadata_updated_before=123, metadata_updated_after=123,
        )
        consolidated = [
            x for x in result["related_equity_index_series"] if x["code"] == "13874+"
        ]
        self.assertEqual(len(consolidated), 1)
        self.assertTrue(consolidated[0]["non_additive_comparison_warning"])

    def test_missing_positions_remain_missing_not_zero(self):
        row = make_row()
        row["lev_money_positions_long_all"] = None
        result = build_summary(
            [row], FIELDS, count_before=1, count_after=1,
            metadata_updated_before=123, metadata_updated_after=123,
        )
        missing = result["candidate_contracts"]["13874A"]["position_field_missing_cells"]
        self.assertEqual(missing["lev_money_positions_long_all"], 1)

    def test_unstable_metadata_timestamp_fails_snapshot_gate(self):
        result = build_summary(
            [make_row()], FIELDS, count_before=1, count_after=1,
            metadata_updated_before=123, metadata_updated_after=124,
        )
        self.assertFalse(result["snapshot_stable_during_retrieval"])
        self.assertEqual(result["research_disposition"], "CFTC_TFF_COVERAGE_AUDIT_INCOMPLETE")

    def test_count_mismatch_fails_disposition(self):
        result = build_summary(
            [make_row()], FIELDS, count_before=2, count_after=2,
            metadata_updated_before=123, metadata_updated_after=123,
        )
        self.assertEqual(result["retrieved_row_count"], 1)
        self.assertFalse(result["row_count_reconciled"])

    def test_related_index_names_are_discovered_without_universe_assumption(self):
        rows = [
            make_row(code="13874A", name="E-MINI S&P 500 - CME"),
            make_row(code="209742", name="NASDAQ-100 STOCK INDEX (MINI) - CME", row_id="2"),
            make_row(code="239742", name="RUSSELL 2000 STOCK INDEX (MINI) - CME", row_id="3"),
            make_row(code="124603", name="DOW JONES INDUSTRIAL AVG - x $5 - CBT", row_id="4"),
        ]
        result = build_summary(
            rows, FIELDS, count_before=4, count_after=4,
            metadata_updated_before=123, metadata_updated_after=123,
        )
        codes = {x["code"] for x in result["related_equity_index_series"]}
        self.assertEqual(codes, {"13874A", "209742", "239742", "124603"})

    def test_no_raw_rows_or_identifiers_are_retained(self):
        result = build_summary(
            [make_row()], FIELDS, count_before=1, count_after=1,
            metadata_updated_before=123, metadata_updated_after=123,
        )
        self.assertFalse(result["raw_rows_retained"])
        self.assertFalse(result["raw_ids_retained"])
        self.assertNotIn("rows", result)

    def test_cftc_position_date_is_tuesday_diagnostic(self):
        result = _weekly_coverage([date(2026, 11, 3), date(2026, 11, 10)])
        self.assertEqual(result["non_tuesday_count"], 0)

    def test_all_candidate_codes_must_be_present_and_unique(self):
        rows = [
            make_row(code="13874A", row_id="1"),
            make_row(code="209742", row_id="2"),
            make_row(code="239742", row_id="3"),
            make_row(code="124603", row_id="4"),
        ]
        result = build_summary(
            rows, FIELDS, count_before=4, count_after=4,
            metadata_updated_before=123, metadata_updated_after=123,
        )
        self.assertTrue(result["candidate_codes_present_gate"])
        self.assertTrue(result["candidate_report_date_code_unique_gate"])

    def test_missing_candidate_contract_is_not_silently_accepted(self):
        result = build_summary(
            [make_row(code="13874A")], FIELDS, count_before=1, count_after=1,
            metadata_updated_before=123, metadata_updated_after=123,
        )
        self.assertFalse(result["candidate_codes_present_gate"])


if __name__ == "__main__":
    unittest.main()
