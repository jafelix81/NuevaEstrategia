import unittest
from research.phase453_form4_bulk_symbol_crosswalk_audit import class_tokens, sentinel, summarize_period

def sub(acc,cik,symbol,form="4"):
    return {"ACCESSION_NUMBER":acc,"ISSUERCIK":cik,"ISSUERTRADINGSYMBOL":symbol,"DOCUMENT_TYPE":form}
def tx(acc,title): return {"ACCESSION_NUMBER":acc,"SECURITY_TITLE":title}

class Phase453Tests(unittest.TestCase):
    def test_sentinels_remain_unknown(self):
        for x in ("","NONE","N/A","NA","[NONE]"): self.assertTrue(sentinel(x))
        self.assertFalse(sentinel("NYSE:SSD"))
    def test_class_tokens_require_common_stock_or_share(self):
        self.assertEqual(class_tokens(["Class A Common Stock","Class B Common Stock"]),{("CLASS","A"),("CLASS","B")})
        self.assertEqual(class_tokens(["Class A Stock Option"]),set())
    def test_single_issuer_symbol_does_not_resolve_multiple_classes(self):
        r=summarize_period("T",[sub("A1","100","LEN")],[tx("A1","Class A Common Stock"),tx("A1","Class B Common Stock")])
        d=r["security_title_diagnostics"]
        self.assertEqual(d["accessions_with_multiple_common_class_or_series_tokens"],1)
        self.assertEqual(d["multi_class_accessions_with_single_issuer_symbol_string"],1)
        self.assertFalse(r["interpretation"]["symbol_field_alone_resolves_class_specific_security_identity"])
    def test_comma_symbol_is_preserved_as_one_raw_issuer_field(self):
        r=summarize_period("T",[sub("A1","100","LEN, LEN.B")],[tx("A1","Class A Common Stock"),tx("A1","Class B Common Stock")])
        self.assertEqual(r["issuer_symbol_raw_field"]["comma_delimited_filings"],1)
        self.assertEqual(r["security_title_diagnostics"]["multi_class_accessions_with_comma_delimited_issuer_symbol_string"],1)
    def test_symbol_collisions_and_multiple_symbols_are_diagnostics(self):
        s=[sub("A1","100","AAA"),sub("A2","100","BBB"),sub("B1","200","AAA")]
        r=summarize_period("T",s,[tx("A1","Common Stock"),tx("A2","Common Stock"),tx("B1","Common Stock")])
        d=r["issuer_symbol_raw_field"]
        self.assertEqual(d["issuers_with_multiple_distinct_non_sentinel_symbol_values_in_quarter"],1)
        self.assertEqual(d["exact_raw_symbol_values_linked_to_multiple_issuer_ciks"],1)
    def test_non_form4_submissions_are_excluded(self):
        s=[sub("A1","100","AAA","4"),sub("B1","200","BBB","5")]
        r=summarize_period("T",s,[tx("A1","Common Stock"),tx("B1","Common Stock")])
        self.assertEqual(r["form4_and_4a_submissions"],1)
        self.assertEqual(r["nonderivative_form4_rows"],1)
    def test_unknown_symbol_is_not_treated_as_zero_or_valid(self):
        r=summarize_period("T",[sub("A1","100","NONE")],[tx("A1","Common Stock")])
        self.assertEqual(r["issuer_symbol_raw_field"]["sentinel_filings"],1)
        self.assertEqual(r["nonderivative_rows_with_sentinel_issuer_symbol"],1)

if __name__=="__main__": unittest.main()
