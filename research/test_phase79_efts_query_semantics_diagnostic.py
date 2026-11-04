import unittest
from research.phase79_efts_query_semantics_diagnostic import (
    build_queries, extract_total, normalize_accession, parse_hit,
)


class Phase79EFTSDiagnosticTests(unittest.TestCase):
    def test_query_matrix_includes_generic_baseline_and_name_cik_variants(self):
        queries = build_queries()
        ids = {q["id"] for q in queries}
        self.assertIn("generic_apple_10k", ids)
        self.assertIn("revance_name_no_form", ids)
        self.assertIn("revance_cik_unpadded", ids)
        self.assertIn("revance_cik_padded", ids)
        self.assertIn("revance_cik_quoted", ids)
        self.assertIn("revance_name_ciks_subject", ids)
        self.assertIn("revance_name_ciks_filer", ids)

    def test_expected_controls_are_preserved(self):
        queries = build_queries()
        fox = next(q for q in queries if q["id"] == "fox_name")
        self.assertEqual(set(fox["expected"]), {
            "0000950157-25-000788", "0000950170-25-114595"
        })

    def test_accession_normalization(self):
        self.assertEqual(normalize_accession("000001961725000296"), "0000019617-25-000296")
        self.assertEqual(normalize_accession("bad"), "")

    def test_extract_total_shapes(self):
        self.assertEqual(extract_total({"hits": {"total": {"value": 4}}}), 4)
        self.assertEqual(extract_total({"hits": {"total": 2}}), 2)

    def test_parse_hit(self):
        hit = {"_id": "0000019617-25-000296:primary_doc.xml",
               "_source": {"adsh": "000001961725000296", "form": "SC 13G/A",
                           "file_date": "2025-03-06", "filename": "primary_doc.xml"}}
        parsed = parse_hit(hit)
        self.assertEqual(parsed["accession"], "0000019617-25-000296")
        self.assertEqual(parsed["form"], "SC 13G/A")


if __name__ == "__main__":
    unittest.main()
