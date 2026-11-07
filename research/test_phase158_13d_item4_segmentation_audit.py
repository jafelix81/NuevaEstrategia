import os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase158_13d_item4_segmentation_audit as p

class Phase158Tests(unittest.TestCase):
    def test_primary_prefers_readable_sc13d_and_skips_pdf(self):
        raw = ("<DOCUMENT><TYPE>SC 13D\n<TEXT><HTML>readable</HTML></TEXT></DOCUMENT>"
               "<DOCUMENT><TYPE>SC 13D\n<TEXT><PDF>encoded</PDF></TEXT></DOCUMENT>")
        self.assertIn("readable", p.primary_document(raw))
        self.assertNotIn("encoded", p.primary_document(raw))

    def test_primary_rejects_13g_only(self):
        with self.assertRaises(ValueError):
            p.primary_document("<DOCUMENT><TYPE>SC 13G\n<TEXT>not 13D</TEXT></DOCUMENT>")

    def test_split_item4_heading(self):
        lines = ["SCHEDULE 13D", "Item 4.", "Purpose of Transaction", "New proposal", "Item 5.", "Interest in Securities"]
        self.assertEqual(p.find_item4_start(lines), 1)
        self.assertEqual(p.next_item_boundary(lines, 1), (4, "ITEM5"))

    def test_searches_beyond_1000_lines(self):
        lines = ["page"] * 1316 + ["Item 4.", "Purpose of Transaction", "No material change.", "Item 5."]
        self.assertEqual(p.find_item4_start(lines), 1316)

    def test_standalone_item6_boundary(self):
        lines = ["Item 4.", "Purpose of Transaction", "New agreement", "Item 6.", "Contracts"]
        self.assertEqual(p.next_item_boundary(lines, 0), (3, "ITEM6"))

    def test_standalone_item7_boundary(self):
        lines = ["Item 4.", "Purpose of Transaction", "Letter", "Item 7.", "Exhibits"]
        self.assertEqual(p.next_item_boundary(lines, 0), (3, "ITEM7"))

    def test_inline_item7_boundary(self):
        lines = ["Item 4.", "Purpose of Transaction", "Text", "Item 7. Material to Be Filed as Exhibits"]
        self.assertEqual(p.next_item_boundary(lines, 0), (3, "ITEM7"))

    def test_does_not_stop_on_narrative_item_reference(self):
        lines = ["Item 4.", "Purpose of Transaction", "See Item 7 below for details.", "Further text", "Item 5."]
        self.assertEqual(p.next_item_boundary(lines, 0), (4, "ITEM5"))

    def test_no_boundary_is_quarantined(self):
        lines = ["Item 4.", "Purpose of Transaction", "No next item heading", "more text"]
        self.assertEqual(p.next_item_boundary(lines, 0), (None, None))

    def test_page_noise_removed(self):
        cleaned = p.clean_section(["Purpose of Transaction", "No material change.", "CUSIP No. Y8162K121", "SCHEDULE 13D", "Page 28 of 37"])
        self.assertEqual(cleaned, "No material change.")

    def test_source_constants_are_pinned(self):
        self.assertEqual(p.P124_RUN, 42073725379)
        self.assertEqual(p.P157_RUN, 42224436013)
        self.assertEqual(len(p.P124_CSV_SHA), 64)
        self.assertEqual(len(p.P157_CSV_SHA), 64)

    def test_end_to_end_artifacts(self):
        a = os.environ.get("PHASE124_DIR")
        b = os.environ.get("PHASE157_DIR")
        if not a or not b:
            self.skipTest("immutable Phase 124/157 artifacts not supplied")
        with tempfile.TemporaryDirectory() as td:
            s = p.audit(a, b, td)
        self.assertEqual(s["sources"]["raw_submission_hashes_verified"], 600)
        self.assertEqual(s["combined"]["item4_extracted"], 117)
        self.assertEqual(s["by_filing_role"]["INITIAL"]["item4_extracted"], 59)
        self.assertEqual(s["by_filing_role"]["AMENDMENT"]["item4_extracted"], 58)
        self.assertEqual(s["phase157_reconciliation"]["prior_item4_flagged"], 116)
        self.assertEqual(s["phase157_reconciliation"]["recovered_accessions"], ["0001140361-18-032832"])
        self.assertEqual(s["boundary_item_counts"], {"ITEM5": 112, "ITEM6": 2, "ITEM7": 3})
        self.assertFalse(s["decision"]["f80_modified"])
        self.assertFalse(s["decision"]["final_holdout_used"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
