import unittest
from research.phase80_sec_entity_landing_page_audit import (
    PAGES, accession_present, build_page_url, extract_candidate_endpoints, normalize_accession,
)


class Phase80EntityLandingPageTests(unittest.TestCase):
    def test_three_subject_issuers_and_four_cross_filer_controls(self):
        self.assertEqual(len(PAGES), 5)
        self.assertEqual(len({p["cik"] for p in PAGES}), 3)
        self.assertEqual(sum(len(p["expected"]) for p in PAGES), 6)

    def test_page_urls_use_subject_cik_and_owner_variants(self):
        default = build_page_url(PAGES[0])
        excluded = build_page_url(PAGES[1])
        included = build_page_url(PAGES[2])
        self.assertIn("CIK=1479290", default)
        self.assertNotIn("owner=", default)
        self.assertIn("owner=exclude", excluded)
        self.assertIn("owner=include", included)

    def test_accession_presence_accepts_dashed_or_compact(self):
        self.assertTrue(accession_present("x 0000019617-25-000296 y", "0000019617-25-000296"))
        self.assertTrue(accession_present("x 000001961725000296 y", "0000019617-25-000296"))
        self.assertFalse(accession_present("none", "0000019617-25-000296"))

    def test_normalize_accession(self):
        self.assertEqual(normalize_accession("000001961725000296"), "0000019617-25-000296")

    def test_candidate_endpoint_extraction_is_bounded_to_relevant_terms(self):
        text = 'const a="https://www.sec.gov/edgar/browse/data.json"; const b="/api/ownership/list";'
        found = extract_candidate_endpoints(text)
        self.assertTrue(any("browse/data.json" in x for x in found))
        self.assertTrue(any("ownership" in x for x in found))


if __name__ == "__main__":
    unittest.main()
