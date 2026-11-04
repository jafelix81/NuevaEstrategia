import unittest
import pandas as pd

from research.phase72_13dg_structured_xml_corpus_audit import (
    build_lineage_edge,
    expected_submission_type,
    stratified_sample,
    normalize_accession,
)


class Phase72CorpusAuditHelperTests(unittest.TestCase):
    def test_stratified_sample_covers_form_and_period_groups(self):
        rows = []
        for form in ["SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"]:
            for date in ["2024-06-01", "2025-06-01"]:
                for i in range(10):
                    rows.append({"form": form, "filing_date": date, "accession": f"{form}-{date}-{i}"})
        sample = stratified_sample(pd.DataFrame(rows), 8)
        self.assertEqual(len(sample), 8)
        self.assertEqual(set(sample["form"]), {"SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"})
        self.assertTrue(sample["filing_date"].isin(["2024-06-01", "2025-06-01"]).all())

    def test_accession_normalization(self):
        self.assertEqual(normalize_accession("0001493152-25-012122"), "000149315225012122")
        self.assertEqual(normalize_accession(" 000149315225012122 "), "000149315225012122")

    def test_form_normalization(self):
        self.assertEqual(expected_submission_type("SC 13G/A"), "SCHEDULE 13G/A")
        self.assertEqual(expected_submission_type("SC 13D"), "SCHEDULE 13D")

    def test_lineage_edge_same_issuer(self):
        current = {"accession": "0001213902-25-012345", "issuer_cik": "0001130166", "form": "SC 13G/A", "filing_date": "2025-09-01"}
        index = {"000149315225012122": {"issuer_cik": "0001130166", "form": "SC 13G", "filing_date": "2025-08-01"}}
        edge = build_lineage_edge(current, "0001493152-25-012122", index)
        self.assertEqual(edge["lineage_status"], "predecessor_in_panel_same_issuer")
        self.assertTrue(edge["predecessor_same_issuer"])

    def test_lineage_edge_cross_issuer_is_flagged(self):
        current = {"accession": "0001213902-25-012345", "issuer_cik": "0001130166", "form": "SC 13G/A", "filing_date": "2025-09-01"}
        index = {"000149315225012122": {"issuer_cik": "0000999999", "form": "SC 13G", "filing_date": "2025-08-01"}}
        edge = build_lineage_edge(current, "0001493152-25-012122", index)
        self.assertEqual(edge["lineage_status"], "predecessor_in_panel_cross_issuer")

    def test_lineage_edge_outside_input_panel_is_left_censored(self):
        current = {"accession": "0001213902-25-012345", "issuer_cik": "0001130166", "form": "SC 13G/A", "filing_date": "2025-09-01"}
        edge = build_lineage_edge(current, "0001493152-25-012122", {})
        self.assertEqual(edge["lineage_status"], "predecessor_outside_input_panel")


if __name__ == "__main__":
    unittest.main()
