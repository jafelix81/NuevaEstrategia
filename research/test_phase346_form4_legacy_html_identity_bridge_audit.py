from __future__ import annotations
import unittest
from research.phase346_form4_legacy_html_identity_bridge_audit import (
    class_exchange_rows, classify, exchange_prose, family, parse_doc, section_text,
    temporal, ticker_mentions,
)

class Phase346Tests(unittest.TestCase):
    def test_same_row_class_exchange_extracted(self):
        p=parse_doc(b"<table><tr><td>Title of Each Class</td><td>Name of Each Exchange on Which Registered</td></tr><tr><td>Common Stock, $0.01 Par Value</td><td>New York Stock Exchange</td></tr></table>")
        self.assertEqual(len(p["class_exchange_rows"]),1)
        self.assertEqual(p["class_exchange_rows"][0]["class_family"],"COMMON_STOCK")
        self.assertEqual(p["class_exchange_rows"][0]["exchange"],"New York Stock Exchange")

    def test_class_and_exchange_separate_rows_not_joined(self):
        self.assertEqual(class_exchange_rows([[["Title of each class"],["Common Stock"],["Name of each exchange on which registered"],["NASDAQ"]]]),[])

    def test_none_row_is_not_exchange_listing(self):
        p=parse_doc(b"<table><tr><td>Title of each class</td><td>Name of exchange on which registered</td></tr><tr><td>None</td><td></td></tr></table>")
        self.assertEqual(p["class_exchange_rows"][0]["class_family"],"")
        self.assertEqual(p["class_exchange_rows"][0]["exchange"],"")

    def test_explicit_issuer_ticker_suffixes(self):
        s="Our common stock began trading under the new ticker symbol of AVN.R. Our common shares trade under the symbol BMHC."
        self.assertEqual({x["symbol"] for x in ticker_mentions(s)},{"AVN.R","BMHC"})

    def test_unrelated_ticker_not_issuer_specific(self):
        self.assertEqual(ticker_mentions("A director also serves at another company (NYSE:LGF)."),[])

    def test_section12g_class_is_not_exchange(self):
        s="Securities registered pursuant to Section 12(b) of the Act: None Securities registered pursuant to Section 12(g) of the Act: Common Stock (Title of Class) Indicate by check mark"
        v=section_text(s,"g")
        self.assertIn("Common Stock",v)
        self.assertEqual(family(v),"COMMON_STOCK")

    def test_class_and_series_qualifiers_preserved(self):
        self.assertNotEqual(family("Common Stock"),family("Class A Common Stock"))
        self.assertNotEqual(family("Common Stock"),family("Series A Common Stock"))

    def test_temporal_gate_is_strict(self):
        base={"anchor_accession":"0000000001-12-000001","anchor_filing_date":"2012-03-10"}
        self.assertEqual(temporal({**base,"transaction_date":"2012-03-11"}),("PRETRANSACTION_FRESH_ANCHOR",True))
        self.assertEqual(temporal({**base,"transaction_date":"2012-03-10"}),("ANCHOR_SAME_DAY_AS_TRANSACTION",False))
        self.assertEqual(temporal({**base,"transaction_date":"2012-03-09"}),("ANCHOR_AFTER_TRANSACTION",False))
        self.assertEqual(temporal({**base,"anchor_filing_date":"2011-01-01","transaction_date":"2012-03-10"}),("ANCHOR_STALE_OVER_365D",False))

    def test_ticker_mismatch_not_promoted(self):
        g={"symbols":{"AVN"},"titles":{"Class A Common Stock"}}
        p={"ticker_mentions":[{"symbol":"AVN.R","snippet":"Our common stock uses ticker symbol AVN.R"}],
           "class_exchange_rows":[],"section12b_text":"","section12g_text":"","exchange_prose":[]}
        self.assertEqual(classify(g,p)["evidence_grade"],"ISSUER_TICKER_MISMATCH")

    def test_same_row_class_exchange_plus_ticker_corrobates(self):
        g={"symbols":{"CLSN"},"titles":{"Celsion Corporation Common Stock"}}
        p={"ticker_mentions":[{"symbol":"CLSN","snippet":"Our Common Stock trades under symbol CLSN"}],
           "class_exchange_rows":[{"title":"COMMON STOCK, PAR VALUE $.01 PER SHARE","exchange":"NASDAQ CAPITAL MARKET","class_family":"COMMON_STOCK"}],
           "section12b_text":"","section12g_text":"None","exchange_prose":[]}
        r=classify(g,p)
        self.assertEqual(r["evidence_grade"],"TICKER_CLASS_AND_EXCHANGE_CORROBORATED")
        self.assertEqual(r["class_exchange_table_status"],"UNIQUE_CLASS_FAMILY_EXCHANGE_ROW")

    def test_hypothetical_exchange_not_current_evidence(self):
        s="If our common stock were delisted, trading could move to the OTC Bulletin Board. Our common stock is currently listed on the NASDAQ Capital Market."
        terms={x["exchange_term"] for x in exchange_prose(s)}
        self.assertIn("NASDAQ Capital Market",terms)
        self.assertNotIn("OTC Bulletin Board",terms)

if __name__=="__main__": unittest.main()
