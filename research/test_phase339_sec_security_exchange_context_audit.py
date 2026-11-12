import unittest
from research.phase339_sec_security_exchange_context_audit import (
    extract_context_rows, build_symbol_exchange_associations,
    build_title_exchange_associations, weighted_rate, find_primary_document_in_payload
)

class Phase339Tests(unittest.TestCase):
    def test_symbol_12b_title_and_exchange_same_context(self):
        facts=[
            {"name":"TradingSymbol","value":" abc ","context_ref":"ctx1","dimensions":[]},
            {"name":"Security12bTitle","value":"Class A common stock","context_ref":"ctx1","dimensions":[]},
            {"name":"SecurityExchangeName","value":" NASDAQ ","context_ref":"ctx1","dimensions":[]},
        ]
        symbols,exchanges,titles=extract_context_rows(facts)
        rows=build_symbol_exchange_associations(symbols,exchanges,titles)
        self.assertEqual(rows[0]["symbol"],"ABC")
        self.assertEqual(rows[0]["association_status"],"SYMBOL_12B_TITLE_AND_EXCHANGE_SAME_CONTEXT")
        self.assertEqual(rows[0]["same_context_exchange_values"],["NASDAQ"])

    def test_security_12b_title_exchange_pair_without_symbol_is_title_level_only(self):
        facts=[
            {"name":"Security12bTitle","value":"Class A common stock","context_ref":"ctx1","dimensions":[]},
            {"name":"SecurityExchangeName","value":"NYSE","context_ref":"ctx1","dimensions":[]},
        ]
        symbols,exchanges,titles=extract_context_rows(facts)
        self.assertEqual(build_symbol_exchange_associations(symbols,exchanges,titles),[])
        pairs=build_title_exchange_associations(titles,exchanges)
        self.assertEqual(len(pairs),1)
        self.assertTrue(pairs[0]["has_required_same_context_exchange"])

    def test_exchange_without_12b_title_is_not_promoted(self):
        facts=[
            {"name":"TradingSymbol","value":"ABC","context_ref":"ctx1","dimensions":[]},
            {"name":"SecurityExchangeName","value":"NYSE","context_ref":"ctx1","dimensions":[]},
        ]
        symbols,exchanges,titles=extract_context_rows(facts)
        rows=build_symbol_exchange_associations(symbols,exchanges,titles)
        self.assertEqual(rows[0]["association_status"],"SYMBOL_EXCHANGE_SAME_CONTEXT_WITHOUT_12B_TITLE")

    def test_document_level_cooccurrence_is_not_direct_binding(self):
        facts=[
            {"name":"TradingSymbol","value":"ABC","context_ref":"symbol_ctx","dimensions":[]},
            {"name":"SecurityExchangeName","value":"NYSE","context_ref":"issuer_ctx","dimensions":[]},
        ]
        symbols,exchanges,titles=extract_context_rows(facts)
        rows=build_symbol_exchange_associations(symbols,exchanges,titles)
        self.assertEqual(rows[0]["association_status"],"DOCUMENT_LEVEL_EXCHANGE_ONLY_NOT_LINKED")

    def test_multi_listing_axis_is_separate_evidence(self):
        facts=[
            {"name":"TradingSymbol","value":"ABC","context_ref":"ctx1","dimensions":[{"dimension":"dei:EntityListingsExchangeAxis","member":"dei:XnysMember"}]},
            {"name":"Security12bTitle","value":"Class A common stock","context_ref":"ctx1","dimensions":[]},
        ]
        symbols,exchanges,titles=extract_context_rows(facts)
        rows=build_symbol_exchange_associations(symbols,exchanges,titles)
        self.assertEqual(rows[0]["association_status"],"MULTI_LISTING_AXIS_ON_SYMBOL_CONTEXT")

    def test_12g_title_is_not_treated_as_12b_exchange_pair(self):
        facts=[
            {"name":"Security12gTitle","value":"OTC security","context_ref":"ctx1","dimensions":[]},
            {"name":"SecurityExchangeName","value":"NYSE","context_ref":"ctx1","dimensions":[]},
        ]
        symbols,exchanges,titles=extract_context_rows(facts)
        pairs=build_title_exchange_associations(titles,exchanges)
        self.assertEqual(pairs,[])

    def test_exchange_fact_dimensions_are_preserved(self):
        facts=[{"name":"SecurityExchangeName","value":"NYSE","context_ref":"ctx1","dimensions":[{"dimension":"dei:EntityListingsExchangeAxis","member":"dei:XnysMember"}]}]
        _,exchanges,_=extract_context_rows(facts)
        self.assertEqual(exchanges[0]["listing_axis_members"],["dei:EntityListingsExchangeAxis=dei:XnysMember"])

    def test_primary_document_lookup_from_recent_submission(self):
        payload={"filings":{"recent":{"form":["10-Q"],"filingDate":["2022-11-03"],"accessionNumber":["0000842183-22-000073"],"primaryDocument":["rpt-20220930.htm"]}}}
        row=find_primary_document_in_payload(payload,"0000842183-22-000073")
        self.assertEqual(row["primaryDocument"],"rpt-20220930.htm")

    def test_missing_primary_document_lookup(self):
        payload={"filings":{"recent":{"form":["10-Q"],"filingDate":["2022-11-03"],"accessionNumber":["0000842183-22-000073"],"primaryDocument":["rpt-20220930.htm"]}}}
        self.assertIsNone(find_primary_document_in_payload(payload,"0000842183-22-000074"))

    def test_weighted_rate_uses_explicit_denominator(self):
        rows=[{"design_weight":10,"ok":True,"eligible":True},{"design_weight":2,"ok":False,"eligible":True},{"design_weight":8,"ok":False,"eligible":False}]
        got=weighted_rate(rows,lambda r:r["ok"],lambda r:r["eligible"])
        self.assertEqual(got["sample_n"],2)
        self.assertEqual(got["weighted_population_units"],12)
        self.assertAlmostEqual(got["weighted_rate_pct"],83.3333,places=3)

if __name__=="__main__": unittest.main()
