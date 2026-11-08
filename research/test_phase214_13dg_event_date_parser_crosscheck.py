import os, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase214_13dg_event_date_parser_crosscheck as phase214

try:
    import bs4
    import lxml.etree
    HAS_BS4=True
except ImportError:
    HAS_BS4=False

class Phase214Tests(unittest.TestCase):
    @unittest.skipUnless(HAS_BS4,"beautifulsoup4/lxml required")
    def test_date_before_label(self):
        v,m,_=phase214.extract_event_bs4("<p>December 31, 2022</p><p>Date of Event Which Requires Filing of this Statement</p>")
        self.assertEqual(v.isoformat(),"2022-12-31"); self.assertEqual(m,"HTML_LABEL_NEAREST_DATE")
    @unittest.skipUnless(HAS_BS4,"beautifulsoup4/lxml required")
    def test_date_after_label(self):
        v,m,_=phase214.extract_event_bs4("<p>Date of Event Which Requires Filing of this Statement</p><p>November 30, 2017</p>")
        self.assertEqual(v.isoformat(),"2017-11-30"); self.assertEqual(m,"HTML_LABEL_NEAREST_DATE")
    @unittest.skipUnless(HAS_BS4,"beautifulsoup4/lxml required")
    def test_same_node(self):
        v,m,_=phase214.extract_event_bs4("June 30, 2023 (Date of Event Which Requires Filing of this Statement)")
        self.assertEqual(v.isoformat(),"2023-06-30"); self.assertEqual(m,"HTML_LABEL_NEAREST_DATE")
    @unittest.skipUnless(HAS_BS4,"beautifulsoup4/lxml required")
    def test_no_label_not_imputed(self):
        v,m,_=phase214.extract_event_bs4("CUSIP 123456789 December 31, 2022")
        self.assertIsNone(v); self.assertEqual(m,"NO_LABEL")
    @unittest.skipUnless(HAS_BS4,"beautifulsoup4/lxml required")
    def test_label_without_date(self):
        v,m,_=phase214.extract_event_bs4("(Date of Event Which Requires Filing of this Statement) N/A")
        self.assertIsNone(v); self.assertEqual(m,"LABEL_NO_DATE")
    @unittest.skipUnless(HAS_BS4,"beautifulsoup4/lxml required")
    def test_nearest_date_wins(self):
        body="<p>Power of Attorney dated October 12, 2009</p><p>June 30, 2023</p><p>Date of Event Which Requires Filing of this Statement</p>"
        v,m,d=phase214.extract_event_bs4(body)
        self.assertEqual(v.isoformat(),"2023-06-30"); self.assertEqual(m,"HTML_LABEL_NEAREST_DATE")
        self.assertLessEqual(d["distance_chars"],2)
    def test_13d_xml(self):
        v,m=phase214.extract_event("<edgarSubmission><dateOfEvent>03/14/2025</dateOfEvent></edgarSubmission>")
        self.assertEqual(v.isoformat(),"2025-03-14"); self.assertEqual(m,"XML_dateOfEvent")
    def test_13g_xml(self):
        v,m=phase214.extract_event("<edgarSubmission><eventDateRequiresFilingThisStatement>09/30/2024</eventDateRequiresFilingThisStatement></edgarSubmission>")
        self.assertEqual(v.isoformat(),"2024-09-30"); self.assertEqual(m,"XML_eventDateRequiresFilingThisStatement")
    @unittest.skipUnless(HAS_BS4,"beautifulsoup4/lxml required")
    def test_full_artifact_when_supplied(self):
        input_dir=os.environ.get("PHASE124_INPUT_DIR")
        if not input_dir: self.skipTest("PHASE124_INPUT_DIR not set")
        zip_path=os.environ.get("PHASE124_ZIP_PATH")
        r=phase214.audit(Path(input_dir),Path(zip_path) if zip_path else None)
        self.assertEqual(r["legacy_html_cross_parser"]["same_date_and_status_outcomes"],497)
        self.assertEqual(r["legacy_html_cross_parser"]["conflicts"],0)
        self.assertEqual(r["combined_event_date_recovery"]["parsed_event_dates"],553)

if __name__=="__main__":
    unittest.main(verbosity=2)
