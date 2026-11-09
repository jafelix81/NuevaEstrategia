import os, unittest
from pathlib import Path
import phase227_13dg_overlap_adjudication as audit

class Phase227Tests(unittest.TestCase):
    def test_positive(self): self.assertEqual(audit.classify(("100","5","0","100","0","100")),"POSITIVE_POSITION")
    def test_all_zero_is_not_positive_overlap(self): self.assertEqual(audit.classify(("0","0","0","0","0","0")),"ZERO_POSITION")
    def test_empty(self): self.assertEqual(audit.classify(("","","","","","")),"EMPTY")
    def test_partial_is_unknown(self): self.assertEqual(audit.classify(("100","5","","100","0","100")),"UNKNOWN_OR_PARTIAL")
    def test_negative_or_inconsistent(self): self.assertEqual(audit.classify(("-1","0","0","0","0","0")),"NONPOSITIVE_OR_INCONSISTENT")
    def test_13d_13g_fields_remain_separate(self):
        self.assertEqual(audit.GROUP["13D"],"memberOfGroup")
        self.assertEqual(audit.GROUP["13G"],"memberGroup")
    @unittest.skipUnless(os.getenv("PHASE124_INPUT_DIR") and os.getenv("PHASE124_SOURCE_ZIP"),"set Phase 124 artifact paths")
    def test_full_hash_pinned_source(self):
        r=audit.run(Path(os.environ["PHASE124_INPUT_DIR"]),Path(os.environ["PHASE124_SOURCE_ZIP"]))
        c=r["summary"]["combined"]
        self.assertEqual((c["groups"],c["positive"],c["zero"]),(58,50,8))
        self.assertEqual((c["positive_rows"],c["zero_rows"]),(162,27))
        self.assertEqual((c["positive_filings"],c["zero_only_filings"],c["mixed_filings"]),(41,7,1))

if __name__=="__main__":unittest.main(verbosity=2)
