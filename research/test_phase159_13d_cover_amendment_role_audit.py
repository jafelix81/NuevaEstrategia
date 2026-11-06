import os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase159_13d_cover_amendment_role_audit as p
import phase158_13d_item4_segmentation_audit as p158

class Phase159Tests(unittest.TestCase):
    def test_numeric_cover_field(self):
        self.assertEqual(p.parse_cover_amendment_field(["SCHEDULE 13D","(Amendment No. 34 )*"])["number"],34)
    def test_number_without_closing_parenthesis(self):
        self.assertEqual(p.parse_cover_amendment_field(["SCHEDULE 13D","Amendment No. 1* EXCEED WORLD"])["number"],1)
    def test_html_markup(self):
        raw="<DOCUMENT><TYPE>SC 13D\n<TEXT><HTML><P>SCHEDULE 13D</P><P>(Amendment No. <U>4</U>)*</P></HTML></TEXT></DOCUMENT>"
        self.assertEqual(p.parse_cover_amendment_field(p158.text_lines(raw))["number"],4)
    def test_blank_is_not_initial_proof(self):
        self.assertEqual(p.parse_cover_amendment_field(["SCHEDULE 13D","(Amendment No. )*"])["status"],"BLANK_OR_NA")
    def test_underscores_are_not_initial_proof(self):
        self.assertEqual(p.parse_cover_amendment_field(["SCHEDULE 13D","(Amendment No. ________)*"])["status"],"BLANK_OR_NA")
    def test_na_is_not_initial_proof(self):
        self.assertEqual(p.parse_cover_amendment_field(["SCHEDULE 13D","(Amendment No. N/A)*"])["status"],"BLANK_OR_NA")
    def test_missing_is_not_initial_proof(self):
        self.assertEqual(p.parse_cover_amendment_field(["SCHEDULE 13D","Issuer"])["status"],"MISSING")
    def test_first_cover_field_only(self):
        self.assertEqual(p.parse_cover_amendment_field(["SCHEDULE 13D","(Amendment No. )*","Later Amendment No. 7"])["status"],"BLANK_OR_NA")
    def test_other_value_is_quarantined(self):
        self.assertEqual(p.parse_cover_amendment_field(["SCHEDULE 13D","(Amendment No. pending)*"])["status"],"OTHER_UNRESOLVED")
    def test_primary_skips_pdf(self):
        raw="<DOCUMENT><TYPE>SC 13D\n<TEXT><HTML>readable</HTML></TEXT></DOCUMENT><DOCUMENT><TYPE>SC 13D\n<TEXT><PDF>encoded</PDF></TEXT></DOCUMENT>"
        self.assertIn("readable",p158.primary_document(raw))
        self.assertNotIn("encoded",p158.primary_document(raw))
    def test_primary_rejects_13g(self):
        with self.assertRaises(ValueError):
            p158.primary_document("<DOCUMENT><TYPE>SC 13G\n<TEXT>not 13D</TEXT></DOCUMENT>")
    def test_source_constants(self):
        self.assertEqual(p.P124_RUN,42073725379); self.assertEqual(p.P157_RUN,42224436013)
        self.assertEqual(p.P158_RUN,42231437618); self.assertEqual(len(p.P158_CSV_SHA),64)
    def test_end_to_end(self):
        a,b,c=(os.environ.get("PHASE124_DIR"),os.environ.get("PHASE157_DIR"),os.environ.get("PHASE158_DIR"))
        if not all((a,b,c)): self.skipTest("immutable Phase 124/157/158 artifacts not supplied")
        with tempfile.TemporaryDirectory() as td: s=p.audit(a,b,c,Path(td))
        self.assertEqual(s["sources"]["phase124_raw_submissions_verified"],600)
        self.assertEqual(s["population"]["legacy_13d_filings"],180)
        self.assertEqual(s["population"]["index_coded_amendments"],108)
        self.assertEqual(s["role_counts"]["COVER_NUMBERED_AMENDMENT_CANDIDATE"]["filings"],4)
        self.assertEqual(s["role_counts"]["COVER_NUMBERED_AMENDMENT_CANDIDATE"]["item4_extracted"],4)
        self.assertEqual(s["cover_field_status_counts"]["NUMBERED"],4)
        self.assertEqual(s["cover_field_status_counts"]["NOT_APPLICABLE_INDEX_CODED_AMENDMENT"],108)
        self.assertEqual(s["item4_cohort_correction"]["phase158_index_non_amendment_item4_count"],59)
        self.assertEqual(s["item4_cohort_correction"]["remaining_non_amendment_form_unconfirmed_item4"],55)
        self.assertEqual(s["item4_cohort_correction"]["removed_from_initial_candidate_count"],4)
        self.assertEqual([r["cover_amendment_number"] for r in s["cover_numbered_amendment_candidates"]],[34,3,1,4])
        self.assertFalse(s["decision"]["f80_modified"]); self.assertFalse(s["decision"]["final_holdout_used"])

if __name__=="__main__": unittest.main(verbosity=2)
