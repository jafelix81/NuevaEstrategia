import unittest
from research.phase339_sec_security_exchange_context_audit import (
    extract_context_rows, build_symbol_exchange_associations, weighted_rate
)

class Phase339Tests(unittest.TestCase):
    def test_same_context_exchange_is_contextual_not_listing_identity(self):
        facts=[
            {"name":"TradingSymbol","value":" abc ","context_ref":"ctx1","dimensions":[]},
            {"name":"SecurityExchangeName","value":" Nasdaq Global Market ","context_ref":"ctx1","dimensions":[]},
        ]
        symbols,exchanges,_=extract_context_rows(facts)
        rows=build_symbol_exchange_associations(symbols,exchanges)
        self.assertEqual(rows[0]["symbol"],"ABC")
        self.assertEqual(rows[0]["same_context_exchange_values"],["Nasdaq Global Market"])
        self.assertEqual(rows[0]["association_status"],"SAME_CONTEXT_EXCHANGE_NAME_ONLY_NOT_SECURITY_IDENTITY")

    def test_document_level_cooccurrence_is_not_direct_binding(self):
        facts=[
            {"name":"TradingSymbol","value":"ABC","context_ref":"symbol_ctx","dimensions":[]},
            {"name":"SecurityExchangeName","value":"NYSE","context_ref":"issuer_ctx","dimensions":[]},
        ]
        symbols,exchanges,_=extract_context_rows(facts)
        rows=build_symbol_exchange_associations(symbols,exchanges)
        self.assertEqual(rows[0]["same_context_exchange_values"],[])
        self.assertEqual(rows[0]["association_status"],"DOCUMENT_LEVEL_EXCHANGE_ONLY_NOT_LINKED")

    def test_listing_axis_on_symbol_context_is_separate_evidence(self):
        facts=[
            {"name":"TradingSymbol","value":"ABC","context_ref":"ctx1","dimensions":[{"dimension":"dei:EntityListingsExchangeAxis","member":"dei:XnysMember"}]},
            {"name":"SecurityExchangeName","value":"NYSE","context_ref":"ctx1","dimensions":[]},
        ]
        symbols,exchanges,_=extract_context_rows(facts)
        rows=build_symbol_exchange_associations(symbols,exchanges)
        self.assertEqual(rows[0]["association_status"],"DIRECT_LISTING_AXIS_ON_SYMBOL_CONTEXT")
        self.assertEqual(rows[0]["symbol_listing_axis_members"],["dei:EntityListingsExchangeAxis=dei:XnysMember"])

    def test_exchange_fact_dimensions_are_preserved(self):
        facts=[{"name":"SecurityExchangeName","value":"NYSE","context_ref":"ctx1","dimensions":[{"dimension":"dei:EntityListingsExchangeAxis","member":"dei:XnysMember"}]}]
        _,exchanges,_=extract_context_rows(facts)
        self.assertEqual(exchanges[0]["listing_axis_members"],["dei:EntityListingsExchangeAxis=dei:XnysMember"])

    def test_no_context_reference_cannot_match(self):
        symbols=[{"symbol":"ABC","context_ref":"","dimensions":[],"class_axis_members":[],"listing_axis_members":[]}]
        exchanges=[{"exchange_name":"NYSE","context_ref":"","dimensions":[],"class_axis_members":[],"listing_axis_members":[]}]
        rows=build_symbol_exchange_associations(symbols,exchanges)
        self.assertEqual(rows[0]["association_status"],"DOCUMENT_LEVEL_EXCHANGE_ONLY_NOT_LINKED")

    def test_weighted_rate_uses_explicit_denominator(self):
        rows=[{"design_weight":10,"ok":True,"eligible":True},{"design_weight":2,"ok":False,"eligible":True},{"design_weight":8,"ok":False,"eligible":False}]
        got=weighted_rate(rows,lambda r:r["ok"],lambda r:r["eligible"])
        self.assertEqual(got["sample_n"],2)
        self.assertEqual(got["weighted_population_units"],12)
        self.assertAlmostEqual(got["weighted_rate_pct"],83.3333,places=3)

if __name__=="__main__": unittest.main()
