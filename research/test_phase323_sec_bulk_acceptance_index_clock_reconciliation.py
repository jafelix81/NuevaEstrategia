import unittest

from research.phase323_sec_bulk_acceptance_index_clock_reconciliation import (
    business_day_lag, candidate_dates_from_acceptance, raw_line_matches,
    reconcile_case, validate_result,
)


def base_case():
    return {
        "accession": "0001140361-06-002128",
        "quarter": "2006Q1",
        "form_type": "4",
        "issuer_cik": "93859",
        "issuer_name": "STEAK & SHAKE CO",
        "ticker_as_filed": "SNS",
        "bulk_filing_date": "2006-02-10",
        "header_filed_date": "2006-02-10",
        "master_filed_dates": ["2006-02-10"],
        "acceptance_datetime_et": "20060213132936",
        "expected_entity_ciks": ["93859", "1309311"],
        "daily_index_hit_count": 2,
        "daily_index_dates": ["2006-02-13"],
        "daily_index_filed_dates": ["2006-02-13"],
        "daily_index_forms": ["4"],
        "daily_index_ciks": ["93859", "1309311"],
    }


class Phase323TwoClockTests(unittest.TestCase):
    def test_weekend_acceptance_lag_is_one_edgar_business_day(self):
        self.assertEqual(business_day_lag("2006-02-10", "2006-02-13"), 1)

    def test_acceptance_window_skips_weekend_and_holiday(self):
        self.assertEqual(
            candidate_dates_from_acceptance("2023-07-03", 2),
            ["2023-07-03", "2023-07-05"],
        )

    def test_filed_acceptance_index_two_clock_split_is_corrobated(self):
        result = reconcile_case(base_case(), [], [])
        self.assertEqual(result["classification"], "FILED_DATE_ACCEPTANCE_INDEX_TWO_CLOCKS_CORROBORATED")
        self.assertEqual(result["availability_anchor_date"], "2006-02-13")
        self.assertEqual(result["acceptance_lag_business_days"], 1)
        self.assertFalse(result["strict_pit_admitted"])

    def test_long_acceptance_lag_remains_quarantined(self):
        case = base_case()
        case.update({
            "issuer_cik": "775662",
            "bulk_filing_date": "2006-02-15",
            "header_filed_date": "2006-02-15",
            "master_filed_dates": ["2006-02-15"],
            "acceptance_datetime_et": "20081002131457",
            "daily_index_dates": ["2008-10-02"],
            "daily_index_filed_dates": ["2008-10-02"],
            "daily_index_ciks": ["775662", "1102914"],
            "expected_entity_ciks": ["775662", "1102914"],
        })
        result = reconcile_case(case, [], [])
        self.assertEqual(result["classification"], "LONG_ACCEPTANCE_LAG_INDEX_FOUND_QUARANTINED")
        self.assertEqual(result["availability_anchor_date"], "")

    def test_missing_daily_index_is_not_admitted(self):
        case = base_case()
        case.update({
            "daily_index_hit_count": 0, "daily_index_dates": [],
            "daily_index_filed_dates": [], "daily_index_forms": [],
            "daily_index_ciks": [],
        })
        result = reconcile_case(case, [], [])
        self.assertEqual(result["classification"], "HEADER_MASTER_CONFIRMED_DAILY_INDEX_ABSENT_QUARANTINED")
        self.assertEqual(result["availability_anchor_date"], "")

    def test_raw_line_without_parser_row_is_quarantined(self):
        case = base_case()
        case.update({
            "daily_index_hit_count": 0, "daily_index_dates": [],
            "daily_index_filed_dates": [], "daily_index_forms": [],
            "daily_index_ciks": [],
        })
        result = reconcile_case(case, [], [{"index_date": "2006-02-13", "line_number": 12, "line_sha256": "abc"}])
        self.assertEqual(result["classification"], "RAW_INDEX_LINE_PRESENT_PARSER_MISS_QUARANTINED")

    def test_index_acceptance_date_divergence_is_quarantined(self):
        case = base_case()
        case.update({
            "daily_index_dates": ["2006-02-14"],
            "daily_index_filed_dates": ["2006-02-14"],
        })
        result = reconcile_case(case, [], [])
        self.assertEqual(result["classification"], "INDEX_ACCEPTANCE_DATE_DIVERGENCE_QUARANTINED")

    def test_owner_coverage_gap_is_quarantined(self):
        case = base_case()
        case.update({"daily_index_ciks": ["93859"]})
        result = reconcile_case(case, [], [])
        self.assertEqual(result["classification"], "DAILY_INDEX_ENTITY_COVERAGE_INCOMPLETE_QUARANTINED")

    def test_raw_line_scan_returns_hash_not_source_text(self):
        raw = b"00000093859|STEAK & SHAKE CO|4|2006-02-13|edgar/data/93859/000114036106002128.txt\n"
        matches = raw_line_matches(raw, "0001140361-06-002128")
        self.assertEqual(len(matches), 1)
        self.assertIn("line_sha256", matches[0])
        self.assertNotIn("text", matches[0])

    def test_validator_keeps_research_controls_closed(self):
        result = {
            "phase": 323,
            "summary": {
                "total_exceptions": 24, "two_clock_cases_corroborated": 21,
                "long_acceptance_lag_quarantined": 2, "other_quarantined": 1,
            },
            "controls": {
                "f80_frozen": True,
                "strict_pit_admitted": False, "alpha_test_authorized": False,
                "return_test_run": False, "bootstrap_loo_run": False,
                "chronological_oos_run": False, "holdout_used": False,
                "production_changed": False, "universe_changed": False,
                "capital_changed": False, "parameters_changed": False,
                "raw_sec_bytes_uploaded": False, "vendor_contacted": False,
                "data_purchased": False, "email_sent": False,
            },
            "retrieval": {"raw_sec_bytes_uploaded": False},
        }
        validate_result(result)
        result["controls"]["strict_pit_admitted"] = True
        with self.assertRaises(ValueError):
            validate_result(result)


if __name__ == "__main__":
    unittest.main()
