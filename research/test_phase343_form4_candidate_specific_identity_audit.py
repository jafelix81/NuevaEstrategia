from __future__ import annotations
import unittest
from research.phase328_sec_collision_prior_filing_xbrl_pilot import select_prior_periodic_filing
from research.phase343_form4_candidate_specific_identity_audit import (
    canonical_sec_date, classify_header_cik, crosswalk, decimal_key, facts_to_contexts, group_event_units,
    strict_date_relation, tx_key_bulk, tx_key_xml, phase342_candidate_tx_key,
)

class Phase343Tests(unittest.TestCase):
    def test_same_context_triple_required(self):
        facts = [
            {"name":"TradingSymbol","value":"ABC","context_ref":"c1","dimensions":[]},
            {"name":"Security12bTitle","value":"Common Stock","context_ref":"c2","dimensions":[]},
            {"name":"SecurityExchangeName","value":"NYSE","context_ref":"c2","dimensions":[]},
        ]
        self.assertEqual(facts_to_contexts(facts), [])

    def test_exact_same_context_triple_is_retained(self):
        facts = [
            {"name":"TradingSymbol","value":"ABC","context_ref":"c1","dimensions":[]},
            {"name":"Security12bTitle","value":"Common Stock","context_ref":"c1","dimensions":[]},
            {"name":"SecurityExchangeName","value":"NYSE","context_ref":"c1","dimensions":[]},
        ]
        contexts = facts_to_contexts(facts)
        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0]["symbol"], "ABC")

    def test_duplicate_fact_values_are_deduplicated_but_conflicts_fail_closed(self):
        facts = [
            {"name":"TradingSymbol","value":"ABC","context_ref":"c1","dimensions":[]},
            {"name":"TradingSymbol","value":"ABC","context_ref":"c1","dimensions":[]},
            {"name":"Security12bTitle","value":"Common Stock","context_ref":"c1","dimensions":[]},
            {"name":"SecurityExchangeName","value":"NYSE","context_ref":"c1","dimensions":[]},
        ]
        self.assertEqual(len(facts_to_contexts(facts)), 1)
        facts.append({"name":"TradingSymbol","value":"XYZ","context_ref":"c1","dimensions":[]})
        self.assertEqual(facts_to_contexts(facts), [])

    def test_class_axis_is_preserved(self):
        dims = [{"dimension":"dei:StatementClassOfStockAxis","member":"dei:ClassAMember"}]
        facts = [
            {"name":"TradingSymbol","value":"ABC","context_ref":"a","dimensions":dims},
            {"name":"Security12bTitle","value":"Class A Common Stock","context_ref":"a","dimensions":dims},
            {"name":"SecurityExchangeName","value":"NASDAQ","context_ref":"a","dimensions":dims},
        ]
        contexts = facts_to_contexts(facts)
        self.assertEqual(contexts[0]["class_axis_members"], ["dei:StatementClassOfStockAxis=dei:ClassAMember"])

    def test_exact_symbol_and_compatible_title_crosswalk(self):
        contexts = [{
            "context_ref":"c1","symbol":"ABC","security_title":"Class A Common Stock",
            "exchange":"NASDAQ","dimensions":[],
            "class_axis_members":["dei:StatementClassOfStockAxis=dei:ClassAMember"],
            "listing_axis_members":[],"instrument_class":"COMMON_STOCK",
            "class_tokens":["A"],"series_tokens":[],
        }]
        result = crosswalk("ABC","Class A Common Stock",contexts)
        self.assertEqual(result["crosswalk_status"],"UNIQUE_COMPATIBLE_SECURITY_CLASS")
        self.assertEqual(result["exchange_values"],["NASDAQ"])

    def test_same_ticker_with_two_class_axes_remains_ambiguous(self):
        contexts = []
        for ref, member in [("a","ClassAMember"),("b","ClassBMember")]:
            contexts.append({
                "context_ref":ref,"symbol":"ABC","security_title":"Common Stock",
                "exchange":"NYSE","dimensions":[],
                "class_axis_members":[f"dei:StatementClassOfStockAxis=dei:{member}"],
                "listing_axis_members":[],"instrument_class":"COMMON_STOCK",
                "class_tokens":[],"series_tokens":[],
            })
        result = crosswalk("ABC","Common Stock",contexts)
        self.assertEqual(result["crosswalk_status"],"AMBIGUOUS_COMPATIBLE_SECURITY_CLASSES")

    def test_strict_date_gates_exclude_same_day_and_lookahead(self):
        self.assertEqual(strict_date_relation("2026-06-30","2026-07-01"),(True,1))
        self.assertEqual(strict_date_relation("2026-07-01","2026-07-01"),(False,0))
        self.assertEqual(strict_date_relation("2026-07-02","2026-07-01"),(False,-1))
        self.assertEqual(strict_date_relation("","2026-07-01"),(False,None))

    def test_form4_header_cik_may_be_issuer_or_reporting_owner(self):
        self.assertEqual(classify_header_cik("0000843006", "843006", ["1062993"]), "ISSUER")
        self.assertEqual(classify_header_cik("0001062993", "843006", ["1062993"]), "REPORTING_OWNER")
        self.assertEqual(classify_header_cik("9999999", "843006", ["1062993"]), "UNMATCHED")
        self.assertEqual(classify_header_cik("", "843006", ["1062993"]), "MISSING")

    def test_sec_bulk_dates_normalize_for_form4_header_and_event_clock(self):
        self.assertEqual(canonical_sec_date("24-SEP-2026"), "2026-09-24")
        self.assertEqual(canonical_sec_date("2026-09-24"), "2026-09-24")
        self.assertEqual(strict_date_relation("2026-09-23", "24-SEP-2026"), (True, 1))
        self.assertEqual(strict_date_relation("2026-09-25", "24-SEP-2026"), (False, -1))

    def test_prior_periodic_selector_uses_normalized_bulk_event_date(self):
        submissions = {"filings": {"recent": {
            "form": ["10-Q", "10-K"],
            "filingDate": ["2026-09-25", "2026-06-30"],
            "accessionNumber": ["later", "prior"],
            "primaryDocument": ["later.htm", "prior.htm"],
            "reportDate": ["2026-09-30", "2026-06-30"],
        }}}
        selected, source = select_prior_periodic_filing(
            submissions, canonical_sec_date("24-SEP-2026")
        )
        self.assertEqual(source, "RECENT")
        self.assertEqual(selected["accessionNumber"], "prior")
        self.assertEqual(selected["filingDate"], "2026-06-30")

    def test_decimal_and_transaction_keys_are_stable(self):
        self.assertEqual(decimal_key("1,000.0000"),"1000")
        self.assertEqual(decimal_key("10.5000"),"10.5")
        bulk = {"security_title":"Common Stock","transaction_date":"24-AUG-2026",
                "transaction_code":"P","transaction_shares":"100.000",
                "transaction_price_per_share":"12.5000"}
        xml = {"security_title":"Common Stock","transaction_date":"2026-08-24",
               "transaction_code":"P","direct_or_indirect":"D","acquired_disposed":"A",
               "shares":"100","price_per_share":"12.5"}
        self.assertEqual(tx_key_bulk(bulk),tx_key_xml(xml))

    def test_bulk_price_precision_matches_original_xml_four_decimal_price(self):
        bulk = {"security_title":"Common Stock","transaction_date":"24-SEP-2026",
                "transaction_code":"P","transaction_shares":"300",
                "transaction_price_per_share":"4.98"}
        xml = {"security_title":"Common Stock","transaction_date":"2026-09-24",
               "transaction_code":"P","direct_or_indirect":"D","acquired_disposed":"A",
               "shares":"300.00","price_per_share":"4.9805"}
        self.assertEqual(tx_key_bulk(bulk), tx_key_xml(xml))

    def test_bulk_price_rounding_does_not_allow_adjacent_cent(self):
        bulk = {"security_title":"Common Stock","transaction_date":"24-SEP-2026",
                "transaction_code":"P","transaction_shares":"300",
                "transaction_price_per_share":"4.98"}
        xml = {"security_title":"Common Stock","transaction_date":"2026-09-24",
               "transaction_code":"P","direct_or_indirect":"D","acquired_disposed":"A",
               "shares":"300.00","price_per_share":"4.9851"}
        self.assertNotEqual(tx_key_bulk(bulk), tx_key_xml(xml))

    def test_phase342_candidate_schema_rebuilds_screened_p_d_a_contract(self):
        # Phase342 candidate_events omits code/ownership/acquired fields only
        # because all three are mandatory in its upstream screen.
        bulk = {"security_title":"Common Stock","transaction_date":"18-SEP-2026",
                "transaction_shares":"10000.0","transaction_price_per_share":"13.4"}
        xml = {"security_title":"Common Stock","transaction_date":"2026-09-18",
               "transaction_code":"P","direct_or_indirect":"D","acquired_disposed":"A",
               "shares":"10000.00","price_per_share":"13.40"}
        self.assertEqual(phase342_candidate_tx_key(bulk), tx_key_xml(xml))

    def test_phase342_candidate_contract_rejects_conflicting_explicit_fields(self):
        bulk = {"security_title":"Common Stock","transaction_date":"18-SEP-2026",
                "transaction_shares":"10000.0","transaction_price_per_share":"13.4",
                "transaction_code":"S"}
        with self.assertRaisesRegex(ValueError, "phase342_candidate_contract_mismatch"):
            phase342_candidate_tx_key(bulk)

    def test_event_unit_requires_every_candidate_row_to_pass(self):
        rows = [
            {"issuer_cik":"1","filing_date":"2026-09-01","accession":"a",
             "event_time_identity":True,"transaction_date_identity":False,
             "form4_symbol_token":"ABC","exchange_values":["NYSE"]},
            {"issuer_cik":"1","filing_date":"2026-09-01","accession":"b",
             "event_time_identity":False,"transaction_date_identity":False,
             "form4_symbol_token":"ABC","exchange_values":[]},
        ]
        events = group_event_units(rows)
        self.assertEqual(len(events),1)
        self.assertFalse(events[0]["event_time_complete"])
        self.assertEqual(events[0]["candidate_accessions"],2)

if __name__ == "__main__":
    unittest.main()
