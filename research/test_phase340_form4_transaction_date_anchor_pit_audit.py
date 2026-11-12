import unittest
from research.phase340_form4_transaction_date_anchor_pit_audit import (
    anchor_relation,norm_title,exact_title_matches,build_title_map
)

class Phase340Tests(unittest.TestCase):
    def test_anchor_must_strictly_precede_transaction(self):
        self.assertEqual(anchor_relation("2022-01-01","2022-01-02"),"ANCHOR_STRICTLY_PRE_TRANSACTION")
    def test_same_day_anchor_is_not_prior(self):
        self.assertEqual(anchor_relation("2022-01-02","2022-01-02"),"ANCHOR_SAME_DATE_NOT_STRICTLY_PRIOR")
    def test_anchor_after_transaction_is_lookahead(self):
        self.assertEqual(anchor_relation("2022-01-03","2022-01-02"),"ANCHOR_AFTER_TRANSACTION_LOOKAHEAD")
    def test_missing_date_is_quarantined(self):
        self.assertEqual(anchor_relation("2022-01-01",""),"MISSING_DATE")
    def test_title_normalization_preserves_class_tokens(self):
        self.assertEqual(norm_title("Class A Common Stock, par value $0.01"),"CLASS A COMMON STOCK PAR VALUE 0 01")
        self.assertNotEqual(norm_title("Class A Common Stock"),norm_title("Class B Common Stock"))
    def test_exact_title_match_requires_unique_symbol(self):
        mapping={("123","COMMON STOCK"):["ABC"]}
        self.assertEqual(exact_title_matches("123","Common Stock",mapping),["ABC"])
        self.assertEqual(exact_title_matches("123","Common Shares",mapping),[])
    def test_title_map_keeps_ambiguous_symbols(self):
        p={"symbol_exchange_contexts":[
            {"issuer_cik":"123","symbol":"ABC","same_context_security_12b_titles":["Common Stock"]},
            {"issuer_cik":"123","symbol":"ABC.A","same_context_security_12b_titles":["Common Stock"]}]}
        m=build_title_map(p)
        self.assertEqual(exact_title_matches("123","Common Stock",m),["ABC","ABC.A"])
    def test_title_map_separates_issuers(self):
        p={"symbol_exchange_contexts":[
            {"issuer_cik":"123","symbol":"ABC","same_context_security_12b_titles":["Common Stock"]},
            {"issuer_cik":"456","symbol":"XYZ","same_context_security_12b_titles":["Common Stock"]}]}
        m=build_title_map(p)
        self.assertEqual(exact_title_matches("123","Common Stock",m),["ABC"])
        self.assertEqual(exact_title_matches("456","Common Stock",m),["XYZ"])

if __name__=="__main__":unittest.main()
