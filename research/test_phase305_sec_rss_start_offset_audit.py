import unittest

from research.phase305_sec_rss_start_offset_audit import analyze_offset_pages, exact_form_type


def row(accession, role, cik, path_cik, updated="2026-11-12T00:00:00-05:00", form="4"):
    compact = accession.replace("-", "")
    return {
        "accession_from_link": accession,
        "entry_id": f"urn:tag:sec.gov,2008:accession-number={accession}",
        "title": f"{form} - Test Company ({cik}) ({role})",
        "form_type_from_title": form,
        "entity_role_from_title": role,
        "entity_cik_from_title": cik,
        "path_cik_from_link": path_cik,
        "path_cik_matches_title_entity": True,
        "feed_updated_raw": updated,
        "link": f"https://www.sec.gov/Archives/edgar/data/{path_cik}/{compact}/{accession}-index.htm",
    }


def page(start, entries, digest):
    return {
        "start": start,
        "count": 100,
        "form_type": "4",
        "http_status": 200,
        "raw_sha256": digest,
        "entries": entries,
    }


class Phase305OffsetTests(unittest.TestCase):
    def test_offset_pages_preserve_accession_split_across_page_boundary(self):
        a = "0000000123-26-000001"
        p0 = page(0, [row(a, "Issuer", "0000000123", "123")], "a")
        p100 = page(100, [row(a, "Reporting", "0000000456", "456")], "b")
        result = analyze_offset_pages([p0, p100])
        self.assertEqual(result["unique_accessions_union"], 1)
        self.assertEqual(result["unique_entity_rows_union"], 2)
        self.assertEqual(result["accessions_seen_on_multiple_pages"], 1)
        self.assertEqual(result["boundary_checks"][0]["accession_split_count"], 1)

    def test_identical_page_responses_mean_offset_not_observed_as_effective(self):
        a = "0000000123-26-000001"
        entries = [row(a, "Issuer", "0000000123", "123")]
        result = analyze_offset_pages([page(0, entries, "same"), page(100, entries, "same")])
        self.assertFalse(result["offset_parameter_effective"])
        self.assertEqual(result["entity_rows_repeated_across_pages"], 1)

    def test_different_offset_response_is_detected(self):
        a = "0000000123-26-000001"
        b = "0000000123-26-000002"
        result = analyze_offset_pages([
            page(0, [row(a, "Issuer", "0000000123", "123")], "a"),
            page(100, [row(b, "Issuer", "0000000123", "123")], "b"),
        ])
        self.assertTrue(result["offset_parameter_effective"])
        self.assertEqual(result["unique_accessions_union"], 2)

    def test_multiple_reporting_owners_are_not_collapsed(self):
        a = "0000000123-26-000001"
        result = analyze_offset_pages([
            page(0, [
                row(a, "Issuer", "0000000123", "123"),
                row(a, "Reporting", "0000000456", "456"),
            ], "a"),
            page(100, [
                row(a, "Reporting", "0000000789", "789"),
            ], "b"),
        ])
        self.assertEqual(result["unique_accessions_union"], 1)
        self.assertEqual(result["unique_entity_rows_union"], 3)
        self.assertEqual(result["accessions_seen_on_multiple_pages"], 1)

    def test_empty_later_page_is_valid_and_offset_changes_response(self):
        a = "0000000123-26-000001"
        result = analyze_offset_pages([
            page(0, [row(a, "Issuer", "0000000123", "123")], "a"),
            page(100, [], "empty"),
        ])
        self.assertTrue(result["offset_parameter_effective"])
        self.assertEqual(result["unique_accessions_union"], 1)

    def test_exact_form_parser_does_not_truncate_prefixed_forms(self):
        self.assertEqual(exact_form_type("4 - Example Corp (0000000123) (Issuer)"), "4")
        self.assertEqual(exact_form_type("4/A - Example Corp (0000000123) (Issuer)"), "4/A")
        self.assertEqual(exact_form_type("40-APP/A - Example Fund (0000000123) (Filer)"), "40-APP/A")
        self.assertEqual(exact_form_type("424B5 - Example Corp (0000000123) (Filer)"), "424B5")

    def test_type4_prefix_spillover_is_counted_but_excluded_from_form4_union(self):
        a = "0000000123-26-000001"
        b = "0000000123-26-000002"
        c = "0000000123-26-000003"
        result = analyze_offset_pages([
            page(0, [row(a, "Issuer", "0000000123", "123")], "a"),
            page(100, [
                row(b, "Issuer", "0000000123", "123"),
                row(c, "Filer", "0000000123", "123", form="424B5"),
            ], "b"),
        ])
        self.assertEqual(result["unique_accessions_union"], 2)
        self.assertEqual(result["non_target_form_rows"], 1)
        self.assertIn("424B5", result["non_target_form_types"])
        self.assertEqual(result["structural_error_count"], 0)

    def test_structural_mismatch_is_counted(self):
        item = row("0000000123-26-000001", "Issuer", "0000000123", "123")
        item["entry_id"] = "urn:tag:sec.gov,2008:accession-number=0000000999-26-000001"
        result = analyze_offset_pages([page(0, [item], "a")])
        self.assertEqual(result["structural_error_count"], 1)


if __name__ == "__main__":
    unittest.main()
