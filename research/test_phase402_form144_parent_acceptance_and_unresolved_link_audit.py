import unittest

from research.phase402_form144_parent_acceptance_and_unresolved_link_audit import (
    PHASE401_ARTIFACT_ID,
    PHASE401_ARTIFACT_SHA256,
    PHASE401_RUN_ID,
    accepted_utc,
    build_pairs,
    extract_edgar_xml_blocks,
    norm_acc,
    parse_acceptance_html,
    parse_daily_master_index,
    parse_acceptance_submission,
    path_cik_from_url,
    unique_ciks,
)

class Phase402Tests(unittest.TestCase):
    def test_daily_master_index_file_name_header(self):
        raw = ("Description: Daily Master Index\\n"
               "CIK|Company Name|Form Type|Date Filed|File Name\\n"
               "1927719|Freightos Ltd|144|2023-12-05|edgar/data/1927719/000197640823000153/0001976408-23-000153.txt\\n")
        rows = parse_daily_master_index(raw)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["accession"], "0001976408-23-000153")
        self.assertEqual(rows[0]["archive_path_cik"], "0001927719")

    def test_parse_acceptance_from_filing_detail_html(self):
        html = "<td>Accepted</td><td>2025-12-05 12:03:06</td>"
        self.assertEqual(parse_acceptance_html(html), "2025-12-05 12:03:06")

    def test_parse_acceptance_from_submission_header(self):
        text = "ACCESSION NUMBER: 0001959173-25-007544\nACCEPTANCE-DATETIME: 20251205120306\n"
        self.assertEqual(parse_acceptance_submission(text), "2025-12-05 12:03:06")

    def test_acceptance_et_converts_with_dst(self):
        self.assertEqual(accepted_utc("2025-12-05 12:03:06"), "2025-12-05T17:03:06+00:00")
        self.assertEqual(accepted_utc("2023-08-24 12:03:06"), "2023-08-24T16:03:06+00:00")

    def test_cik_candidates_are_normalized_and_deduplicated(self):
        self.assertEqual(unique_ciks(["0000012345", 12345], ["0000000001", None]), ["0000012345", "0000000001"])

    def test_archive_path_cik_is_extracted(self):
        self.assertEqual(path_cik_from_url("https://www.sec.gov/Archives/edgar/data/1603923/000195917325007544/primary_doc.xml"), "0001603923")

    def test_extract_xml_block_from_complete_submission_text(self):
        raw = b"<SEC-HEADER>header</SEC-HEADER>\n<XML><edgarSubmission><headerData/></edgarSubmission></XML>"
        blocks = extract_edgar_xml_blocks(raw)
        self.assertEqual(len(blocks), 1)
        self.assertIn(b"edgarSubmission", blocks[0])

    def test_accession_is_normalized(self):
        self.assertEqual(norm_acc("000195917325007544"), "0001959173-25-007544")

    def test_build_pairs_accepts_only_frozen_phase401_scope(self):
        pairs = []
        for i in range(4):
            pairs.append({"pair_id": f"boundary:{i}", "pair_type": "candidate_boundary",
                          "child_accession": f"000000000{i}-25-00000{i}",
                          "parent_accession": f"000000000{i}-25-00000{i+1}"})
        for i in range(4):
            pairs.append({"pair_id": f"unresolved:{i}", "pair_type": "phase401_unresolved",
                          "child_accession": f"000000001{i}-24-00000{i}",
                          "parent_accession": f"000000002{i}-24-00000{i}"})
        manifest = {
            "source_run_id": PHASE401_RUN_ID,
            "source_artifact_id": PHASE401_ARTIFACT_ID,
            "source_artifact_sha256": PHASE401_ARTIFACT_SHA256,
            "pairs": pairs,
        }
        self.assertEqual(len(build_pairs(manifest)), 8)

    def test_build_pairs_rejects_wrong_artifact_digest(self):
        manifest = {
            "source_run_id": PHASE401_RUN_ID,
            "source_artifact_id": PHASE401_ARTIFACT_ID,
            "source_artifact_sha256": "0" * 64,
            "pairs": [],
        }
        with self.assertRaises(ValueError):
            build_pairs(manifest)

if __name__ == "__main__":
    unittest.main()
