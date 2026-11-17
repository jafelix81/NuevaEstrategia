import unittest
from research.phase455_form4_universe_overlap_audit import classify_symbol, summarize

class Phase455Tests(unittest.TestCase):
    def test_only_exact_single_symbol_match_is_accepted(self):
        u={"AAPL","MSFT"}
        self.assertEqual(classify_symbol("aapl",u),("AAPL","exact_335_match"))
        self.assertEqual(classify_symbol("NASDAQ:AAPL",u)[1],"ambiguous_format")
        self.assertEqual(classify_symbol("AAPL, MSFT",u)[1],"ambiguous_format")
        self.assertEqual(classify_symbol("OTHER",u)[1],"outside_snapshot")

    def test_sentinels_are_unknown(self):
        for s in ("","NONE","N/A","NA","NULL","-","[NONE]"):
            self.assertEqual(classify_symbol(s,{"AAPL"})[1],"unknown")

    def test_duplicate_transaction_rows_do_not_inflate_accessions_or_events(self):
        rows=[{"period":"2026Q3","accession":"A1","issuer_cik":"1","filing_date":"2026-08-01","issuer_symbol_as_filed":"AAPL"}]*2
        r=summarize(rows,{"AAPL"})
        self.assertEqual(r["overall"]["candidate_rows"],2)
        self.assertEqual(r["overall"]["accessions"],1)
        self.assertEqual(r["overall"]["issuer_filing_events"],1)
        self.assertEqual(r["overall"]["exact_match_issuer_filing_events"],1)

    def test_multi_symbol_accession_is_not_exact(self):
        rows=[
          {"period":"2026Q3","accession":"A1","issuer_cik":"1","filing_date":"2026-08-01","issuer_symbol_as_filed":"AAPL"},
          {"period":"2026Q3","accession":"A1","issuer_cik":"1","filing_date":"2026-08-01","issuer_symbol_as_filed":"MSFT"}]
        r=summarize(rows,{"AAPL","MSFT"})
        self.assertEqual(r["overall"]["exact_match_rows"],2)
        self.assertEqual(r["overall"]["exact_match_accessions"],0)
        self.assertEqual(r["overall"]["exact_match_issuer_filing_events"],0)

    def test_cik_ticker_changes_are_not_normalized(self):
        rows=[
          {"period":"2025Q3","accession":"A1","issuer_cik":"1","filing_date":"2025-08-01","issuer_symbol_as_filed":"AULT"},
          {"period":"2026Q3","accession":"A2","issuer_cik":"1","filing_date":"2026-08-01","issuer_symbol_as_filed":"GPUS"}]
        r=summarize(rows,{"AULT","GPUS"})
        self.assertEqual(r["identity_diagnostics"]["issuer_ciks_with_multiple_as_filed_symbols_across_sample"],1)
        self.assertEqual(r["overall"]["exact_match_issuer_ciks"],0)

    def test_missing_identity_fails_closed(self):
        rows=[{"period":"2026Q3","accession":"A1","issuer_cik":"1","filing_date":"","issuer_symbol_as_filed":"AAPL"}]
        with self.assertRaisesRegex(ValueError,"missing required identity field"):
            summarize(rows,{"AAPL"})

if __name__=="__main__": unittest.main()
