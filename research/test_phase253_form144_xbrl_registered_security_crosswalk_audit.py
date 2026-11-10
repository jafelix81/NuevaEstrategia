import unittest
from research.phase253_form144_xbrl_registered_security_crosswalk_audit import (
    norm, validate_context, resolve_form144_class, select_prior_vintage,
    companyfacts_can_supply_context,
)

def ctx(i="c1",facts=None,dims=None):
    return {"context_id":i,"facts":facts or {
        "dei:Security12bTitle":["Class A common stock"],
        "dei:SecurityExchangeName":["NYSE"],"dei:TradingSymbol":["ABC"]},"dimensions":dims or []}

class Phase253Tests(unittest.TestCase):
    def test_undimensioned(self):
        self.assertEqual(validate_context(ctx())["class_scope"],"UNDIMENSIONED_REGISTERED_SECURITY")
    def test_class_axis(self):
        r=validate_context(ctx(dims=[{"axis":"us-gaap:StatementClassOfStockAxis","member":"us-gaap:CommonClassAMember"}]))
        self.assertEqual(r["class_member"],"us-gaap:CommonClassAMember")
    def test_listing_axis_not_class(self):
        r=validate_context(ctx(dims=[{"axis":"dei:EntityListingsExchangeAxis","member":"exch:XNYS"}]))
        self.assertIsNone(r["class_member"]); self.assertEqual(r["listing_member"],"exch:XNYS")
    def test_adr_exception(self):
        r=validate_context(ctx(facts={"dei:Security12bTitle":["ADS"],"dei:TradingSymbol":["XYZ"]},
            dims=[{"axis":"us-gaap:StatementClassOfStockAxis","member":"dei:AdrMember"}]))
        self.assertEqual(r["exchange_status"],"ADR_EXCEPTION")
    def test_12b_exchange_required_same_context(self):
        r=validate_context(ctx(facts={"dei:Security12bTitle":["Class A"],"dei:TradingSymbol":["ABC"]}))
        self.assertEqual(r["status"],"MISSING_12B_EXCHANGE_IN_SAME_CONTEXT")
    def test_12g_no_exchange_required(self):
        r=validate_context(ctx(facts={"dei:Security12gTitle":["Common"],"dei:TradingSymbol":["ABC"]}))
        self.assertEqual(r["status"],"VALID_NORMALIZED_CONTEXT")
    def test_symbol_and_no_symbol_conflict(self):
        f={"dei:Security12bTitle":["A"],"dei:SecurityExchangeName":["NYSE"],"dei:TradingSymbol":["A"],"dei:NoTradingSymbolFlag":["true"]}
        self.assertEqual(validate_context(ctx(facts=f))["status"],"TRADING_SYMBOL_NO_SYMBOL_FLAG_CONFLICT")
    def test_explicit_no_symbol(self):
        f={"dei:Security12bTitle":["A"],"dei:SecurityExchangeName":["NYSE"],"dei:NoTradingSymbolFlag":["true"]}
        self.assertEqual(validate_context(ctx(facts=f))["symbol_status"],"EXPLICIT_NO_TRADING_SYMBOL")
    def test_missing_symbol_is_unknown(self):
        f={"dei:Security12bTitle":["A"],"dei:SecurityExchangeName":["NYSE"]}
        self.assertEqual(validate_context(ctx(facts=f))["symbol_status"],"TRADING_SYMBOL_UNKNOWN")
    def test_missing_title_is_not_no_symbol(self):
        self.assertEqual(validate_context(ctx(facts={"dei:TradingSymbol":["A"]}))["status"],"NO_REGISTERED_SECURITY_TITLE_FACTS")
    def test_multiple_class_members_rejected(self):
        d=[{"axis":"us-gaap:StatementClassOfStockAxis","member":"A"},{"axis":"us-gaap:ClassesOfShareCapitalAxis","member":"B"}]
        self.assertEqual(validate_context(ctx(dims=d))["status"],"MULTIPLE_CLASS_AXIS_MEMBERS_IN_ONE_CONTEXT")
    def test_exact_title_join(self):
        r=resolve_form144_class(" CLASS A common stock ",[validate_context(ctx())])
        self.assertEqual(r["symbols"],["ABC"])
    def test_no_fuzzy_title_join(self):
        r=resolve_form144_class("Class A",[validate_context(ctx())])
        self.assertEqual(r["status"],"NO_EXACT_CLASS_TITLE_MATCH")
    def test_multiple_listings_same_class(self):
        d1=[{"axis":"us-gaap:StatementClassOfStockAxis","member":"A"},{"axis":"dei:EntityListingsExchangeAxis","member":"exch:XNYS"}]
        d2=[{"axis":"us-gaap:StatementClassOfStockAxis","member":"A"},{"axis":"dei:EntityListingsExchangeAxis","member":"exch:XCHI"}]
        r=resolve_form144_class("Class A common stock",[validate_context(ctx("1",dims=d1)),validate_context(ctx("2",dims=d2))])
        self.assertEqual(r["status"],"MULTIPLE_LISTINGS_SAME_CLASS")
    def test_conflicting_symbols_ambiguous(self):
        c1=validate_context(ctx()); c2=validate_context(ctx("2",{"dei:Security12bTitle":["Class A common stock"],"dei:SecurityExchangeName":["NASDAQ"],"dei:TradingSymbol":["XYZ"]}))
        self.assertEqual(resolve_form144_class("Class A common stock",[c1,c2])["status"],"AMBIGUOUS_CLASS_OR_SYMBOL")
    def test_same_day_and_future_excluded(self):
        fs=[{"accession":"A","form":"10-K","filing_date":"2025-01-09"},{"accession":"B","form":"10-Q","filing_date":"2025-01-10"},{"accession":"C","form":"10-K/A","filing_date":"2025-01-11"}]
        self.assertEqual(select_prior_vintage(fs,"2025-01-10")["accession"],"A")
    def test_later_amendment_not_backdated(self):
        fs=[{"accession":"O","form":"10-K","filing_date":"2025-01-01"},{"accession":"A","form":"10-K/A","filing_date":"2025-01-15"}]
        self.assertEqual(select_prior_vintage(fs,"2025-01-10")["accession"],"O")
    def test_same_day_tie_unknown_without_acceptance(self):
        fs=[{"accession":"A","form":"10-Q","filing_date":"2025-01-08"},{"accession":"B","form":"8-K","filing_date":"2025-01-08"}]
        self.assertEqual(select_prior_vintage(fs,"2025-01-10")["status"],"SAME_DAY_VINTAGE_TIE_UNKNOWN")
    def test_acceptance_time_resolves_tie(self):
        fs=[{"accession":"A","form":"10-Q","filing_date":"2025-01-08","acceptance_datetime":"2025-01-08T10:00:00-05:00"},{"accession":"B","form":"8-K","filing_date":"2025-01-08","acceptance_datetime":"2025-01-08T15:00:00-05:00"}]
        self.assertEqual(select_prior_vintage(fs,"2025-01-10")["accession"],"B")
    def test_no_prior_vintage_unknown(self):
        self.assertEqual(select_prior_vintage([{"accession":"A","filing_date":"2025-01-10"}],"2025-01-10")["status"],"NO_STRICTLY_PRIOR_VINTAGE")
    def test_companyfacts_excludes_dimensioned(self):
        self.assertFalse(companyfacts_can_supply_context(ctx(dims=[{"axis":"a","member":"b"}])))
    def test_companyfacts_allows_entity_wide(self):
        self.assertTrue(companyfacts_can_supply_context(ctx()))
    def test_normalization_preserves_class(self):
        self.assertEqual(norm(" Class A  Common Stock "),"class a common stock")
        self.assertNotEqual(norm("Class A"),norm("Class B"))

if __name__=="__main__": unittest.main()
