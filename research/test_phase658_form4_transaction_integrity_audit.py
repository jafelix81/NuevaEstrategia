import unittest
from research.phase658_form4_transaction_integrity_audit import summarize_rows


def row(**overrides):
    base = {
        "detail_type": "transaction_row",
        "accession": "0000000001-26-000001",
        "form": "4",
        "is_amendment": "False",
        "previous_accession": "",
        "filing_date": "2026-11-25",
        "period_of_report": "2026-11-24",
        "transaction_date": "2026-11-24",
        "transaction_code": "P",
        "issuer_name": "Example Corp",
        "issuer_trading_symbol_normalized": "EXMP",
        "shares_numeric": "100",
        "price_per_share_numeric": "25",
        "aff10b5one_filing_flag": "no",
        "owner_attribution_status": "FILING_GRAIN_ONLY_SINGLE_OWNER",
        "research_observation_eligible": "False",
        "signal_eligible": "False",
        "public_availability_certified": "False",
        "same_day_intraday_use_authorized": "False",
        "security_identity_verified": "False",
        "historical_f80_membership_verified": "False",
        "owner_attribution_verified": "False",
        "transaction_semantics_verified": "False",
        "economic_event_new_trade_authorized": "False",
    }
    base.update(overrides)
    return base


def header(**overrides):
    base = {
        "detail_type": "filing_header",
        "accession": "0000000001-26-000001",
        "form": "4",
        "is_amendment": "False",
        "previous_accession": "",
        "filing_date": "2026-11-25",
        "period_of_report": "2026-11-24",
        "issuer_name": "Example Corp",
        "issuer_trading_symbol_normalized": "EXMP",
    }
    base.update(overrides)
    return base


class Phase658Tests(unittest.TestCase):
    def test_normal_purchase_row_is_retained_without_anomaly(self):
        result = summarize_rows([header(), row()])
        self.assertEqual(result["source"]["transaction_rows"], 1)
        self.assertEqual(result["transaction_codes"]["P"]["rows"], 1)
        self.assertEqual(result["anomalies"]["transaction_date_precedes_period_of_report"], [])
        self.assertEqual(result["anomalies"]["extreme_price_review"], [])
        self.assertEqual(result["anomalies"]["filing_lag_over_30_calendar_days"], [])
        self.assertEqual(result["eligibility_true_row_counts"]["signal_eligible"], 0)

    def test_shmd_like_source_inconsistency_is_flagged_not_deleted(self):
        bad = row(
            accession="0000000001-26-000002",
            issuer_trading_symbol_normalized="SHMD",
            transaction_date="2006-11-25",
            period_of_report="2026-11-24",
            shares_numeric="60000",
            price_per_share_numeric="1731429",
        )
        result = summarize_rows([header(accession="0000000001-26-000002"), bad])
        self.assertEqual(result["source"]["transaction_rows"], 1)
        self.assertEqual(len(result["anomalies"]["transaction_date_precedes_period_of_report"]), 1)
        self.assertEqual(result["anomalies"]["transaction_date_precedes_period_of_report"][0]["days_before_period_of_report"], 7304)
        self.assertEqual(len(result["anomalies"]["extreme_price_review"]), 1)

    def test_stale_disclosure_is_flagged_at_filing_lag_not_retimed(self):
        stale = row(
            transaction_code="A",
            transaction_date="2025-05-09",
            period_of_report="2025-05-09",
            filing_date="2026-11-20",
            price_per_share_numeric="0",
        )
        result = summarize_rows([header(), stale])
        late = result["anomalies"]["filing_lag_over_30_calendar_days"]
        self.assertEqual(len(late), 1)
        self.assertEqual(late[0]["filing_lag_days"], 560)
        self.assertEqual(result["source"]["transaction_rows"], 1)

    def test_amendment_without_original_accession_is_a_lineage_gap(self):
        amended_header = header(
            accession="0000000001-26-000003",
            form="4/A",
            is_amendment="True",
            previous_accession="",
        )
        amended_row = row(
            accession="0000000001-26-000003",
            form="4/A",
            is_amendment="True",
        )
        result = summarize_rows([amended_header, amended_row])
        gaps = result["anomalies"]["amendment_without_stored_previous_accession"]
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["transaction_rows"], 1)

    def test_linked_amendment_is_not_reported_as_missing_lineage(self):
        amended_header = header(
            accession="0000000001-26-000004",
            form="4/A",
            is_amendment="True",
            previous_accession="0000000001-26-000001",
        )
        result = summarize_rows([amended_header])
        self.assertEqual(result["anomalies"]["amendment_without_stored_previous_accession"], [])

    def test_transaction_after_period_of_report_is_not_misclassified(self):
        later_row = row(
            transaction_date="2026-11-23",
            period_of_report="2026-11-20",
        )
        result = summarize_rows([header(), later_row])
        self.assertEqual(result["anomalies"]["transaction_date_precedes_period_of_report"], [])

    def test_manual_adjudications_are_source_linked(self):
        result = summarize_rows([header(), row()])
        self.assertEqual(len(result["manual_source_adjudications"]), 4)
        self.assertTrue(all(item["sec_primary_document_url"].startswith("https://www.sec.gov/") for item in result["manual_source_adjudications"]))


if __name__ == "__main__":
    unittest.main()
