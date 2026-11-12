import unittest

from research.phase322_sec_bulk_index_exception_adjudication import (
    accession_year, candidate_business_dates, classify_case, parse_master_index,
    validate_result,
)


def base_case():
    return {
        "accession": "0000001750-23-000002",
        "quarter": "2023Q1",
        "form_type": "4",
        "filing_date": "2023-03-20",
        "issuer_cik": "1750",
        "issuer_name": "AAR CORP",
        "ticker_as_filed": "AIR",
        "reporting_owner_count": "1",
        "reporting_owner_ciks": ["200"],
    }


def base_header(filed_date="2023-03-20", acceptance="20230320150000"):
    return {
        "accession": "0000001750-23-000002",
        "form_type": "4",
        "cik": "200",
        "filed_date": filed_date,
        "acceptance_datetime_et": acceptance,
    }


def base_master(filed_date="2023-03-20"):
    return [{
        "accession": "0000001750-23-000002",
        "form_type": "4",
        "filed_date": filed_date,
    }]


def base_index(index_date="2023-03-20", ciks=("1750", "200")):
    return [{
        "accession": "0000001750-23-000002",
        "form_type": "4",
        "filing_date": index_date,
        "index_date": index_date,
        "cik": cik,
    } for cik in ciks]


class Phase322ExceptionAdjudicationTests(unittest.TestCase):
    def test_accession_year_uses_accession_not_bulk_date(self):
        self.assertEqual(accession_year("0000775662-08-000044"), 2008)

    def test_candidate_dates_skips_federal_holiday(self):
        self.assertEqual(
            candidate_business_dates("2023-07-03", 2),
            ["2023-07-03", "2023-07-05"],
        )

    def test_master_index_parser_normalizes_accession(self):
        raw = (
            b"Description: Master Index\nCIK|Company Name|Form Type|Date Filed|Filename\n"
            b"0000001750|AAR CORP|4|2023-03-20|edgar/data/1750/000000175023000002.txt\n"
            b"0000001750|AAR CORP|10-K|2023-03-20|edgar/data/1750/000000175023000003.txt\n"
        )
        rows, data_lines = parse_master_index(raw, 2023, 1)
        self.assertEqual(data_lines, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["accession"], "0000001750-23-000002")
        self.assertEqual(rows[0]["filed_date"], "2023-03-20")

    def test_bulk_date_confirmed_only_with_header_master_and_index(self):
        result = classify_case(base_case(), base_header(), base_master(), base_index())
        self.assertEqual(result["classification"], "BULK_DATE_CONFIRMED")
        self.assertFalse(result["strict_pit_admitted"])

    def test_after_cutoff_next_business_day_is_consistent_not_proof(self):
        header = base_header("2023-03-21", "20230320180000")
        result = classify_case(
            base_case(), header, base_master("2023-03-21"), base_index("2023-03-21")
        )
        self.assertEqual(result["classification"], "LATE_ACCEPTANCE_NEXT_EDGAR_DAY_CORROBORATED")
        self.assertTrue(result["late_acceptance_shift_consistent"])
        self.assertFalse(result["strict_pit_admitted"])

    def test_before_cutoff_date_shift_is_quarantined(self):
        header = base_header("2023-03-21", "20230320150000")
        result = classify_case(
            base_case(), header, base_master("2023-03-21"), base_index("2023-03-21")
        )
        self.assertEqual(result["classification"], "BULK_DATE_DIFFERS_FROM_OFFICIAL_FILED_DATE_QUARANTINED")
        self.assertFalse(result["late_acceptance_shift_consistent"])

    def test_missing_owner_entity_is_quarantined(self):
        result = classify_case(
            base_case(), base_header(), base_master(), base_index(ciks=("1750",))
        )
        self.assertEqual(result["classification"], "DAILY_INDEX_ENTITY_COVERAGE_INCOMPLETE_QUARANTINED")
        self.assertEqual(result["missing_expected_ciks"], ["200"])

    def test_multiple_index_dates_are_quarantined(self):
        hits = base_index() + base_index("2023-03-21")
        result = classify_case(base_case(), base_header(), base_master(), hits)
        self.assertEqual(result["classification"], "MULTIPLE_DAILY_INDEX_DATES_QUARANTINED")

    def test_header_and_master_without_daily_index_remain_quarantined(self):
        result = classify_case(base_case(), base_header(), base_master(), [])
        self.assertEqual(result["classification"], "HEADER_MASTER_FOUND_DAILY_INDEX_MISSING_QUARANTINED")

    def test_validator_requires_all_research_controls_closed(self):
        result = {
            "phase": 322,
            "exception_summary": {"total": 24, "fully_corroborated": 20, "quarantined_or_unresolved": 4},
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
        result["controls"]["holdout_used"] = True
        with self.assertRaises(ValueError):
            validate_result(result)


if __name__ == "__main__":
    unittest.main()
