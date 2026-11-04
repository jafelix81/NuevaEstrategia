import unittest
from research.phase78_efts_subject_cik_pilot import (
    CONTROLS, build_query_plan, date_window, extract_total, normalize_accession,
    normalize_form_value, parse_hit,
)


class Phase78EFTSTests(unittest.TestCase):
    def test_positive_controls_are_cross_filer(self):
        self.assertEqual(len(CONTROLS), 4)
        self.assertTrue(all(c["subject_cik"] != c["filer_cik"] for c in CONTROLS))
        self.assertEqual(len({c["accession"] for c in CONTROLS}), 4)

    def test_query_plan_contains_padded_unpadded_and_ciks_controls(self):
        plan = build_query_plan()
        types = {q["query_type"] for q in plan}
        self.assertEqual(types, {"q_padded", "q_unpadded", "ciks_subject", "ciks_filer"})
        self.assertTrue(any(q["query_value"] == '"0001479290"' for q in plan))
        self.assertTrue(any(q["query_value"] == '"1479290"' for q in plan))

    def test_query_plan_groups_two_foxa_accessions(self):
        plan = build_query_plan()
        fox = [q for q in plan if q["subject_cik"] == "0001754301" and q["query_type"] == "q_padded"]
        self.assertEqual(len(fox), 1)
        self.assertEqual(len(fox[0]["expected_accessions"]), 2)

    def test_date_window_is_narrow_and_inclusive(self):
        self.assertEqual(date_window("2025-03-06", 1), ("2025-03-05", "2025-03-07"))

    def test_accession_normalization(self):
        self.assertEqual(normalize_accession("000001961725000296"), "0000019617-25-000296")
        self.assertEqual(normalize_accession("bad"), "")

    def test_extract_total_handles_efts_shapes(self):
        self.assertEqual(extract_total({"hits": {"total": {"value": 7, "relation": "eq"}}}), 7)
        self.assertEqual(extract_total({"hits": {"total": 3}}), 3)

    def test_parse_hit_extracts_accession_and_metadata(self):
        hit = {"_id": "000001961725000296:1", "_source": {
            "adsh": "000001961725000296", "form": "SC 13G/A",
            "file_date": "2025-03-06", "filename": "primary_doc.xml",
            "document_type": "SC 13G/A",
        }}
        parsed = parse_hit(hit)
        self.assertEqual(parsed["accession"], "0000019617-25-000296")
        self.assertEqual(parsed["form"], "SC 13G/A")
        self.assertEqual(parsed["file_date"], "2025-03-06")
        self.assertEqual(parsed["filename"], "primary_doc.xml")

    def test_form_normalization_is_exact(self):
        self.assertEqual(normalize_form_value("SC 13G/A"), "SC 13G/A")
        self.assertNotEqual(normalize_form_value("SC 13G"), normalize_form_value("SC 13G/A"))


if __name__ == "__main__":
    unittest.main()
