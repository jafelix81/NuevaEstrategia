import unittest
from datetime import date

import exchange_calendars as xc

from research.phase274_form4_conservative_date_only_pit_clusters import (
    build_cluster_records,
    first_xnys_session_after,
)


class Phase274Form4DateOnlyPITTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calendar = xc.get_calendar("XNYS")

    def test_filing_date_session_uses_strictly_next_session(self):
        result = first_xnys_session_after(date(2026, 9, 14), self.calendar)
        self.assertEqual(result["session"], "2026-09-15")
        self.assertIn("T16:00:00-04:00", result["close_et"])

    def test_friday_before_mlk_day_skips_holiday(self):
        result = first_xnys_session_after(date(2012, 1, 13), self.calendar)
        self.assertEqual(result["session"], "2012-01-17")
        self.assertIn("T16:00:00-05:00", result["close_et"])

    def test_weekend_filing_date_uses_next_open_session(self):
        result = first_xnys_session_after(date(2026, 7, 4), self.calendar)
        self.assertEqual(result["session"], "2026-07-06")

    def test_early_close_is_respected(self):
        result = first_xnys_session_after(date(2026, 11, 25), self.calendar)
        self.assertEqual(result["session"], "2026-11-27")
        self.assertIn("T13:00:00-05:00", result["close_et"])

    def test_same_issuer_filing_date_and_trade_date_forms_cluster(self):
        rows = [
            {"accession":"a1","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-10","owner_cik":"11","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
            {"accession":"a2","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-10","owner_cik":"12","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
        ]
        result = build_cluster_records(rows, "2026Q3", self.calendar)
        self.assertEqual(result["same_issuer_filing_date_transaction_date_multi_owner_clusters"], 1)
        self.assertEqual(result["cluster_accession_memberships"], 2)
        self.assertEqual(result["cluster_reporting_owner_memberships"], 2)
        self.assertEqual(result["clusters"][0]["first_tradable_xnys_session"], "2026-09-15")

    def test_duplicate_transaction_rows_do_not_inflate_accession_or_owner_counts(self):
        rows = [
            {"accession":"a1","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-10","owner_cik":"11","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
            {"accession":"a1","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-10","owner_cik":"11","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
            {"accession":"a2","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-10","owner_cik":"12","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
        ]
        result = build_cluster_records(rows, "2026Q3", self.calendar)
        cluster = result["clusters"][0]
        self.assertEqual(cluster["accession_count"], 2)
        self.assertEqual(cluster["reporting_owner_cik_count"], 2)
        self.assertEqual(cluster["candidate_transaction_rows"], 3)

    def test_same_owner_across_two_accessions_is_not_multi_owner(self):
        rows = [
            {"accession":"a1","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-10","owner_cik":"11","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
            {"accession":"a2","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-10","owner_cik":"11","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
        ]
        result = build_cluster_records(rows, "2026Q3", self.calendar)
        self.assertEqual(result["same_issuer_filing_date_transaction_date_multi_owner_clusters"], 0)

    def test_different_transaction_dates_are_separate_clusters(self):
        rows = [
            {"accession":"a1","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-10","owner_cik":"11","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
            {"accession":"a2","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-11","owner_cik":"12","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
        ]
        result = build_cluster_records(rows, "2026Q3", self.calendar)
        self.assertEqual(result["broad_issuer_filing_date_multi_owner_groups"], 1)
        self.assertEqual(result["same_issuer_filing_date_transaction_date_multi_owner_clusters"], 0)

    def test_negative_filing_lag_is_quarantined(self):
        rows = [
            {"accession":"a1","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-15","owner_cik":"11","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
        ]
        result = build_cluster_records(rows, "2026Q3", self.calendar)
        self.assertEqual(result["negative_filing_lag_rows_quarantined"], 1)
        self.assertEqual(result["same_issuer_filing_date_transaction_date_multi_owner_clusters"], 0)

    def test_reused_accessions_across_trade_dates_are_counted_once_as_unique(self):
        rows = [
            {"accession":"a1","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-10","owner_cik":"11","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
            {"accession":"a2","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-10","owner_cik":"12","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
            {"accession":"a1","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-11","owner_cik":"11","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
            {"accession":"a2","issuer_cik":"1","ticker":"ABC","filing_date":"14-SEP-2026","transaction_date_iso":"2026-09-11","owner_cik":"12","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
        ]
        result = build_cluster_records(rows, "2026Q3", self.calendar)
        self.assertEqual(result["same_issuer_filing_date_transaction_date_multi_owner_clusters"], 2)
        self.assertEqual(result["cluster_accession_memberships"], 4)
        self.assertEqual(result["unique_accessions_in_clusters"], 2)
        self.assertEqual(result["cluster_reporting_owner_memberships"], 4)
        self.assertEqual(result["unique_reporting_owners_in_clusters"], 2)

    def test_unknown_plan_status_stays_unknown_for_2012(self):
        rows = [
            {"accession":"a1","issuer_cik":"1","ticker":"ABC","filing_date":"26-JAN-2012","transaction_date_iso":"2012-01-26","owner_cik":"11","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
            {"accession":"a2","issuer_cik":"1","ticker":"ABC","filing_date":"26-JAN-2012","transaction_date_iso":"2012-01-26","owner_cik":"12","owner_role_class":"director_or_officer","owner_name_legal_entity_flag":False},
        ]
        result = build_cluster_records(rows, "2012Q1", self.calendar)
        self.assertEqual(result["clusters"][0]["plan_status"], "AFF10B5ONE_NOT_AVAILABLE_OR_NOT_REQUIRED_UNKNOWN")


if __name__ == "__main__":
    unittest.main()
