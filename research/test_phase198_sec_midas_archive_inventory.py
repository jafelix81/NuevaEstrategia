import unittest

from research.phase198_sec_midas_archive_inventory import (
    DISPUTED_QUARTERS,
    build_result,
    expected_quarters,
    parse_inventory,
    summarize_zip_probe,
)


def sample_html(quarters=None):
    labels = expected_quarters() if quarters is None else quarters
    links = []
    for index, label in enumerate(labels):
        links.append(
            f'<a href="https://www.sec.gov/files/sample_{index}.zip"><span>{label}</span></a>'
        )
    return (
        "<html><body>" + "".join(links)
        + "<p>Last Reviewed or Updated: June 30, 2026</p></body></html>"
    )


class Phase198Tests(unittest.TestCase):
    def test_expected_archive_has_58_consecutive_quarters(self):
        quarters = expected_quarters()
        self.assertEqual(len(quarters), 58)
        self.assertEqual(quarters[0], "2012 Q1")
        self.assertEqual(quarters[-1], "2026 Q2")

    def test_parser_finds_complete_consecutive_sec_inventory(self):
        result = parse_inventory(sample_html())
        self.assertEqual(result["quarter_count"], 58)
        self.assertTrue(result["consecutive_2012q1_to_2026q2"])
        self.assertEqual(result["missing_quarters"], [])
        self.assertEqual(result["page_last_reviewed_or_updated"], "June 30, 2026")

    def test_parser_detects_missing_quarter(self):
        quarters = [q for q in expected_quarters() if q != "2016 Q3"]
        result = parse_inventory(sample_html(quarters))
        self.assertEqual(result["missing_quarters"], ["2016 Q3"])
        self.assertFalse(result["consecutive_2012q1_to_2026q2"])

    def test_disputed_quarters_are_in_declared_probe_set(self):
        self.assertEqual(
            set(DISPUTED_QUARTERS),
            {"2014 Q2", "2016 Q1", "2016 Q2", "2016 Q3", "2016 Q4", "2019 Q4"},
        )

    def test_zip_probe_requires_zip_magic(self):
        good = summarize_zip_probe(
            206, {"Content-Range": "bytes 0-3/1234"}, b"PK\x03\x04", "https://www.sec.gov/a.zip"
        )
        bad = summarize_zip_probe(
            200, {"Content-Type": "text/html"}, b"<htm", "https://www.sec.gov/a.zip"
        )
        self.assertTrue(good["zip_signature_valid"])
        self.assertFalse(bad["zip_signature_valid"])

    def test_build_result_never_admits_pit_or_alpha(self):
        inventory = parse_inventory(sample_html())
        probes = {
            q: {"http_status": 206, "zip_signature_valid": True}
            for q in DISPUTED_QUARTERS
        }
        result = build_result(inventory, probes)
        self.assertEqual(result["status"], "SEC_ARCHIVE_INDEX_COMPLETE_AND_DISPUTED_ZIPS_REACHABLE")
        self.assertFalse(result["interpretation"]["strict_pit_admitted"])
        self.assertFalse(result["interpretation"]["alpha_test_authorized"])
        self.assertTrue(result["interpretation"]["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
