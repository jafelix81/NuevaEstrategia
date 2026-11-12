import unittest
from research.phase341_form4_issuer_symbol_class_crosswalk_audit import parse_symbol, cls, match_title, raw_meta
class Phase341Tests(unittest.TestCase):
 def test_known_exchange_prefix(self): self.assertEqual(parse_symbol("NYSE: SCS"),("SCS","SINGLE_TOKEN","NYSE"))
 def test_unknown_prefix_rejected(self): self.assertEqual(parse_symbol("HMNY:US")[1],"UNKNOWN_EXCHANGE_PREFIX")
 def test_balanced_wrappers(self):
  self.assertEqual(parse_symbol('"OMEX"')[0],"OMEX");self.assertEqual(parse_symbol("(SIRI)")[0],"SIRI");self.assertEqual(parse_symbol("[PEFF]")[0],"PEFF")
 def test_multi_symbols_rejected(self):
  self.assertEqual(parse_symbol("UHAL,UHALB")[1],"MULTI_OR_MALFORMED");self.assertEqual(parse_symbol("CRDA CRDB")[1],"MULTI_OR_MALFORMED")
 def test_malformed_not_repaired(self): self.assertEqual(parse_symbol("ADAP]")[1],"MALFORMED")
 def test_placeholders(self): self.assertEqual(parse_symbol("N/A")[1],"PLACEHOLDER");self.assertEqual(parse_symbol("NONE")[1],"PLACEHOLDER")
 def test_common_and_ordinary_separate(self):
  self.assertEqual(cls("Common Stock")[0],"COMMON_STOCK");self.assertEqual(cls("Ordinary Shares")[0],"ORDINARY_SHARES");self.assertFalse(match_title("Common Stock","Ordinary Shares")[0])
 def test_beneficial_interest_separate(self):
  self.assertFalse(match_title("Common Stock","Common Shares of Beneficial Interest")[0]);self.assertTrue(match_title("Common Shares of Beneficial Interest","Common Shares of Beneficial Interest ($0.01 par value)")[0])
 def test_class_tokens(self):
  self.assertTrue(match_title("Class A Common Stock","Class A Common Stock, par value $0.01")[0]);self.assertFalse(match_title("Class A Common Stock","Common Stock")[0]);self.assertFalse(match_title("Class A Common Stock","Class B Common Stock")[0])
 def test_preferred_series(self):
  self.assertTrue(match_title("Series E Preferred Stock","Series E Preferred Stock, $0.001 par value")[0]);self.assertFalse(match_title("Series E Preferred Stock","Series D Preferred Stock")[0])
 def test_debt_exact_only(self): self.assertFalse(match_title("Senior Notes due 2028","Senior Notes due 2030")[0])
 def test_raw_xml_ownership_metadata(self):
  raw=b'''<XML><ownershipDocument><issuer><issuerCik>0000000001</issuerCik><issuerTradingSymbol>NYSE: ABC</issuerTradingSymbol></issuer><reportingOwner><reportingOwnerId><rptOwnerName>TEST</rptOwnerName></reportingOwnerId><reportingOwnerRelationship><isDirector>1</isDirector><isOfficer>0</isOfficer></reportingOwnerRelationship></reportingOwner><aff10b5One>0</aff10b5One><nonDerivativeTable><nonDerivativeTransaction><securityTitle><value>Common Stock</value></securityTitle><transactionDate><value>2023-05-23</value></transactionDate><transactionCoding><transactionCode>P</transactionCode></transactionCoding><ownershipNature><directOrIndirectOwnership><value>I</value></directOrIndirectOwnership><natureOfOwnership><value>By 401(k) Plan</value></natureOfOwnership></ownershipNature></nonDerivativeTransaction></nonDerivativeTable></ownershipDocument></XML>'''
  m=raw_meta(raw);self.assertEqual(m["cik"],"1");self.assertEqual(m["symbol"],"NYSE: ABC");self.assertEqual(m["aff"],"0");self.assertEqual(m["rows"][("NON_DERIVATIVE",1)]["nature"],"By 401(k) Plan")
if __name__=="__main__":unittest.main()
