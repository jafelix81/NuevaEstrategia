from __future__ import annotations
import unittest
from research.phase525_form144_form4_crosswalk import build_crosswalk

def fixtures(owner_count="1", owner_status="SINGLE_REPORTING_OWNER_FILING_GRAIN_ONLY", owner_cik="0000000002", owner_name="Doe Jane"):
    f144 = [
        {"parse_status":"parsed","detail_section":"securities_information","accession":"144-A","issuer_cik":"0000000001","issuer_name":"Example Inc","filer_cik":"0000000002","seller_name":"JANE DOE","approx_sale_date_iso":"2026-11-19","proposed_units_numeric":"100","security_class":"Common","aggregate_market_value_numeric":"500","submission_acceptance_utc":"2026-11-19T20:00:00Z","first_seen_interval_upper_bound_utc":"2026-11-19T22:00:00Z"},
        {"parse_status":"parsed","detail_section":"securities_sold_in_past_3_months","accession":"144-A","issuer_cik":"0000000001","issuer_name":"Example Inc","filer_cik":"0000000002","seller_name":"JANE DOE","prior_sale_seller":"JANE DOE","prior_sale_date_iso":"2026-11-18","prior_sale_amount_numeric":"50","prior_sale_gross_proceeds_numeric":"200","security_class":"Common","submission_acceptance_utc":"2026-11-19T20:00:00Z","first_seen_interval_upper_bound_utc":"2026-11-19T22:00:00Z"},
    ]
    f4 = [
        {"detail_type":"transaction_row","parse_status":"parsed","accession":"4-A","issuer_cik":"0000000001","issuer_name":"Example Inc","transaction_date":"2026-11-19","transaction_code":"S","acquired_disposed_code":"D","shares_numeric":"100","price_per_share_numeric":"5","security_title":"Common Stock","acceptance_datetime_utc":"2026-11-20T01:00:00Z","first_seen_interval_upper_bound_utc":"2026-11-20T02:00:00Z"},
        {"detail_type":"transaction_row","parse_status":"parsed","accession":"4-A","issuer_cik":"0000000001","issuer_name":"Example Inc","transaction_date":"2026-11-18","transaction_code":"S","acquired_disposed_code":"D","shares_numeric":"50","price_per_share_numeric":"4","security_title":"Common Stock","acceptance_datetime_utc":"2026-11-20T01:00:00Z","first_seen_interval_upper_bound_utc":"2026-11-20T02:00:00Z"},
    ]
    owners = [{"accession":"4-A","reporting_owner_count":owner_count,"owner_cik":owner_cik,"owner_name":owner_name,"line_owner_link_status":owner_status,"parse_status":"parsed","remarks_flags_json":'{"exercise_price_payment_mention":true,"tax_planning_mention":true}'}]
    return f144, f4, owners

class Phase525CrosswalkTests(unittest.TestCase):
    def test_exact_proposed_and_prior_sales_match_by_issuer_owner_date_quantity(self):
        f144, f4, owners = fixtures()
        rows, summary = build_crosswalk(f144, f4, owners)
        self.assertEqual(len(rows), 2)
        self.assertEqual(summary["matched_proposed_sales"], 1)
        self.assertEqual(summary["matched_prior_sales"], 1)
        proposed = next(x for x in rows if x["form144_event_role"] == "PROPOSED_SALE")
        self.assertEqual(proposed["availability_relation"], "FORM144_ACCEPTED_BEFORE_FORM4_ACCEPTANCE_EXECUTION_TIME_UNKNOWN")
        self.assertEqual(proposed["economic_context_class"], "EXERCISE_OR_TAX_CONTEXT_MENTIONED")
        self.assertFalse(proposed["signal_eligible"])

    def test_multi_owner_filing_is_quarantined(self):
        f144, f4, owners = fixtures("2", "MULTI_OWNER_FILING_GRAIN_ONLY_NO_LINE_LINK")
        rows, summary = build_crosswalk(f144, f4, owners)
        self.assertEqual(rows, [])
        self.assertEqual(summary["multi_owner_accessions_quarantined"], 1)

    def test_wrong_owner_cik_does_not_match(self):
        f144, f4, owners = fixtures(owner_cik="0000000003")
        rows, _ = build_crosswalk(f144, f4, owners)
        self.assertEqual(rows, [])

    def test_wrong_owner_name_does_not_match(self):
        f144, f4, owners = fixtures(owner_name="Someone Else")
        rows, _ = build_crosswalk(f144, f4, owners)
        self.assertEqual(rows, [])

    def test_ambiguous_transaction_candidates_are_quarantined(self):
        f144, f4, owners = fixtures()
        f4.append(dict(f4[0]))
        rows, summary = build_crosswalk(f144, f4, owners)
        self.assertEqual(summary["ambiguous_form144_events_quarantined"], 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["form144_event_role"], "PRIOR_SALE_HISTORY")

    def test_one_form4_transaction_cannot_be_reused_for_two_form144_rows(self):
        f144, f4, owners = fixtures()
        f144.append(dict(f144[0], accession="144-B"))
        rows, summary = build_crosswalk(f144, f4, owners)
        self.assertEqual(summary["ambiguous_transaction_reuse_quarantined"], 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["form144_event_role"], "PRIOR_SALE_HISTORY")

    def test_no_owner_sidecar_cannot_create_a_match(self):
        f144, f4, _ = fixtures()
        rows, summary = build_crosswalk(f144, f4, [])
        self.assertEqual(rows, [])
        self.assertEqual(summary["signal_eligible_matches"], 0)

if __name__ == "__main__":
    unittest.main()
