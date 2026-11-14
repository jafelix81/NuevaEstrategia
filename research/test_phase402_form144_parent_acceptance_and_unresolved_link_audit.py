import csv
import json
import tempfile
import unittest
from pathlib import Path

from research.phase402_form144_parent_acceptance_and_unresolved_link_audit import (
    accepted_utc,
    build_pairs,
    norm_acc,
    parse_acceptance_html,
    parse_acceptance_submission,
    path_cik_from_url,
    unique_ciks,
)

class Phase402Tests(unittest.TestCase):
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

    def test_accession_is_normalized(self):
        self.assertEqual(norm_acc("000195917325007544"), "0001959173-25-007544")

    def test_build_pairs_keeps_four_boundary_and_four_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (root / "all_amendment_parent_pairs.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=[
                    "candidate_membership_transition", "child_accession", "parent_accession",
                    "child_filing_date", "parent_filing_date", "child_xml_url", "parent_xml_url",
                    "child_issuer_cik", "parent_issuer_cik", "remarks_explicit_identity_correction"
                ])
                w.writeheader()
                transitions = [
                    "parent_noncandidate_to_child_candidate",
                    "parent_noncandidate_to_child_candidate",
                    "parent_noncandidate_to_child_candidate",
                    "parent_candidate_to_child_noncandidate",
                ]
                for i, transition in enumerate(transitions):
                    w.writerow({
                        "candidate_membership_transition": transition,
                        "child_accession": f"000000000{i}-25-00000{i}",
                        "parent_accession": f"000000000{i}-25-00000{i+1}",
                        "child_filing_date": "2025-12-05", "parent_filing_date": "2025-12-05",
                        "child_xml_url": "", "parent_xml_url": "",
                        "child_issuer_cik": "0000000001", "parent_issuer_cik": "0000000002",
                        "remarks_explicit_identity_correction": "True",
                    })
            with (root / "unresolved_parent_links.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["child_accession", "parent_accession", "status"])
                w.writeheader()
                for i in range(4):
                    w.writerow({
                        "child_accession": f"000000001{i}-24-00000{i}",
                        "parent_accession": f"000000002{i}-24-00000{i}",
                        "status": "parent_xml_unresolved",
                    })
            pairs = build_pairs(root)
            self.assertEqual(len(pairs), 8)
            self.assertEqual(sum(x["pair_type"] == "candidate_boundary" for x in pairs), 4)
            self.assertEqual(sum(x["pair_type"] == "phase401_unresolved" for x in pairs), 4)

if __name__ == "__main__":
    unittest.main()
