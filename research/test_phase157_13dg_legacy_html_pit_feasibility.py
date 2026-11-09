import os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import phase157_13dg_legacy_html_pit_feasibility as p
class Phase157Tests(unittest.TestCase):
    def test_primary_skips_pdf_duplicate_type(self):
        raw='<DOCUMENT><TYPE>SC 13G/A\n<FILENAME>primary.txt<TEXT><HTML>readable</HTML></TEXT></DOCUMENT><DOCUMENT><TYPE>SC 13G/A\n<FILENAME>x.pdf<TEXT><PDF>encoded</PDF></TEXT></DOCUMENT>'
        self.assertIn("readable",p.primary_document(raw,"13G"))
    def test_parenthetical_issuer(self):
        x,_=p.cover_value(["SCHEDULE 13G","ACME HOLDINGS, INC.","(Name of Issuer)"],r"(?:\(\s*name\s+of\s+issuer\s*\)|name\s+of\s+issuer\s*\))","issuer")
        self.assertEqual(x,"ACME HOLDINGS, INC")
    def test_wrapped_issuer(self):
        x,_=p.cover_value(["Ladder","Capital Corp","(Name of Issuer)"],r"(?:\(\s*name\s+of\s+issuer\s*\)|name\s+of\s+issuer\s*\))","issuer")
        self.assertEqual(x,"Ladder Capital Corp")
    def test_inline_issuer(self):
        x,m=p.cover_value(["Schedule 13G","Name of issuer: MBIA Inc"],r"(?:\(\s*name\s+of\s+issuer\s*\)|name\s+of\s+issuer\s*\))","issuer")
        self.assertEqual((x,m),("MBIA Inc","INLINE_COLON"))
    def test_item_one_not_cover_issuer(self):
        x,_=p.cover_value(["SCHEDULE 13G/A","1(a) Name of Issuer: Acme Holdings, Inc."],r"(?:\(\s*name\s+of\s+issuer\s*\)|name\s+of\s+issuer\s*\))","issuer")
        self.assertIsNone(x)
    def test_class_title(self):
        lines=["ACME HOLDINGS, INC.","(Name of Issuer)","Class A Common Stock, par value $0.01","(Title of Class of Securities)"]
        x,_=p.cover_value(lines,r"(?:\(\s*title\s+of\s+class(?:\s+of\s+securities)?\s*\)|title\s+of\s+class(?:\s+of\s+securities)?\s*\))","class")
        self.assertEqual(x,"Class A Common Stock, par value $0.01")
    def test_event_date(self):
        d,_,s=p.event_date(["January 22, 2016","(Date of Event Which Requires Filing this Statement)"])
        self.assertEqual(d.isoformat(),"2016-01-22");self.assertEqual(s,"LABEL_WINDOW")
    def test_split_event_label(self):
        d,_,_=p.event_date(["October 21, 2022","(Date of Event","which Requires Filing of this Statement)"])
        self.assertEqual(d.isoformat(),"2022-10-21")
    def test_missing_event_not_imputed(self):
        d,raw,s=p.event_date(["SCHEDULE 13D","No event date label"])
        self.assertIsNone(d);self.assertIsNone(raw);self.assertEqual(s,"LABEL_NOT_FOUND")
    def test_first_owner_skips_id_line(self):
        x,_=p.first_owner(["1. NAME OF REPORTING PERSON","I.R.S. Identification Nos. of above persons","The Vanguard Group - 23-1945930"])
        self.assertEqual(x,"The Vanguard Group - 23-1945930")
    def test_zero_shares_value(self):
        x,s=p.numeric_after_label(["7","SOLE VOTING POWER","0 shares","8","SHARED VOTING POWER","123,456 shares"],r"sole\s+voting\s+power")
        self.assertEqual((x,s),("0","FOLLOWING_LINE_VALUE"))
    def test_percent_ignores_row_reference(self):
        x,_=p.numeric_after_label(["13 PERCENT OF CLASS REPRESENTED BY AMOUNT IN ROW (11): 4.31%"],r"percent(?:age)?\s+of\s+class")
        self.assertEqual(x,"4.31%")
    def test_item4_is_13d_only(self):
        lines=["ITEM 4. PURPOSE OF TRANSACTION","The reporting person may consider strategic alternatives.","ITEM 5. INTEREST IN SECURITIES"]
        self.assertTrue(p.item4_purpose(lines,"13D")[0]);self.assertEqual(p.item4_purpose(lines,"13G"),(False,0))
    def test_quarter_end(self):
        self.assertTrue(p.quarter_end(p.date(2024,12,31)));self.assertFalse(p.quarter_end(p.date(2024,12,30)))
    def test_end_to_end_artifacts(self):
        a=os.environ.get("PHASE124_DIR");b=os.environ.get("PHASE127_DIR")
        if not a or not b:self.skipTest("immutable artifacts not supplied")
        with tempfile.TemporaryDirectory() as td:x=p.audit(a,b,td)
        self.assertEqual(x["sources"]["legacy_html_filings"],497)
        self.assertEqual(x["combined"]["event_date_n"],423)
        self.assertEqual(x["combined"]["future_event_dates"],0)
        self.assertEqual(x["combined"]["cusip_checksum_valid_n"],473)
        self.assertTrue(all(v["pass"] for v in x["manual_body_issuer_controls"].values()))
        self.assertFalse(x["decision"]["f80_modified"])
if __name__=="__main__":unittest.main(verbosity=2)
