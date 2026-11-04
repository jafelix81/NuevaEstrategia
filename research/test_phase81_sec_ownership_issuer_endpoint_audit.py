import unittest

from research.phase81_sec_ownership_issuer_endpoint_audit import (
    CONTROLS,
    build_endpoint,
    build_query_plan,
    cik_url_value,
    extract_accessions,
    normalize_accession,
    normalize_cik,
)


class Phase81OwnershipEndpointTests(unittest.TestCase):
    def test_endpoint_templates_match_sec_page_javascript(self):
        issuer = build_endpoint("issuer", "0001479290")
        reporter = build_endpoint("reporter", "0000019617")
        self.assertEqual(
            issuer,
            "https://www.sec.gov/cgi-bin/own-disp?action=getissuer&CIK=1479290",
        )
        self.assertEqual(
            reporter,
            "https://www.sec.gov/cgi-bin/own-disp?action=getowner&CIK=19617",
        )

    def test_cik_normalization_and_url_value(self):
        self.assertEqual(normalize_cik("1479290"), "0001479290")
        self.assertEqual(cik_url_value("0001479290"), "1479290")
        self.assertEqual(cik_url_value("bad"), "")

    def test_accession_extraction_accepts_dashed_and_compact(self):
        found = extract_accessions(
            "a 0000019617-25-000296 b 000106299325015044",
            "/Archives/edgar/data/2083861/000106299325015044/index.html",
        )
        self.assertEqual(
            found,
            ["0000019617-25-000296", "0001062993-25-015044"],
        )
        self.assertEqual(normalize_accession("000001961725000296"), "0000019617-25-000296")

    def test_query_plan_is_bounded_to_three_issuers_and_four_reporters(self):
        plan = build_query_plan()
        issuer = [q for q in plan if q["endpoint_kind"] == "issuer"]
        reporter = [q for q in plan if q["endpoint_kind"] == "reporter"]
        self.assertEqual(len(issuer), 3)
        self.assertEqual(len(reporter), 4)
        self.assertEqual(sum(len(q["expected_accessions"]) for q in issuer), 4)
        self.assertEqual(sum(len(q["expected_accessions"]) for q in reporter), 4)
        self.assertEqual(len(CONTROLS), 4)

    def test_fox_controls_are_kept_together_under_subject_cik(self):
        plan = build_query_plan()
        fox = next(q for q in plan if q["endpoint_kind"] == "issuer" and q["cik"] == "0001754301")
        self.assertEqual(
            set(fox["expected_accessions"]),
            {"0000950157-25-000788", "0000950170-25-114595"},
        )


if __name__ == "__main__":
    unittest.main()
