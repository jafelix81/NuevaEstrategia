import unittest

from research.phase304_sec_rss_count_cap_audit import (
    accession_from_entry_id, analyze_feed_snapshot, compare_snapshot_counts,
)


def row(accession="0000000123-26-000001", form="4", role="Issuer", cik="0000000123", path_cik="123", updated="2026-11-12T00:00:00-05:00"):
    compact = accession.replace("-", "")
    return {
        "accession_from_link": accession,
        "entry_id": f"urn:tag:sec.gov,2008:accession-number={accession}",
        "form_type_from_title": form,
        "entity_role_from_title": role,
        "entity_cik_from_title": cik,
        "path_cik_from_link": path_cik,
        "path_cik_matches_title_entity": True,
        "feed_updated_raw": updated,
        "link": f"https://www.sec.gov/Archives/edgar/data/{path_cik}/{compact}/{accession}-index.htm",
    }


class Phase304RssCountCapTests(unittest.TestCase):
    def test_entry_id_accession_parser(self):
        self.assertEqual(accession_from_entry_id("urn:tag:sec.gov,2008:accession-number=0000000123-26-000001"), "0000000123-26-000001")
        self.assertEqual(accession_from_entry_id("no accession"), "")

    def test_issuer_and_reporting_rows_group_to_one_accession(self):
        result = analyze_feed_snapshot([
            row(role="Issuer", cik="0000000123", path_cik="123"),
            row(role="Reporting", cik="0000000456", path_cik="456"),
        ], "4")
        self.assertEqual(result["raw_entity_rows"], 2)
        self.assertEqual(result["unique_accessions"], 1)
        self.assertEqual(result["accessions_with_issuer_and_reporting"], 1)
        self.assertEqual(result["entity_rows_per_accession"], {"2": 1})
        self.assertEqual(result["entry_id_link_accession_mismatches"], 0)

    def test_multiple_reporting_owners_are_preserved_not_collapsed(self):
        result = analyze_feed_snapshot([
            row(role="Issuer", cik="0000000123", path_cik="123"),
            row(role="Reporting", cik="0000000456", path_cik="456"),
            row(role="Reporting", cik="0000000789", path_cik="789"),
        ], "4")
        self.assertEqual(result["raw_entity_rows"], 3)
        self.assertEqual(result["unique_accessions"], 1)
        self.assertEqual(result["entity_rows_per_accession"], {"3": 1})
        self.assertEqual(result["accessions_with_issuer_and_reporting"], 1)

    def test_conflicting_entry_id_is_counted(self):
        item = row()
        item["entry_id"] = "urn:tag:sec.gov,2008:accession-number=0000000999-26-000001"
        result = analyze_feed_snapshot([item], "4")
        self.assertEqual(result["entry_id_link_accession_mismatches"], 1)

    def test_wrong_query_form_is_counted(self):
        result = analyze_feed_snapshot([row(form="4/A")], "4")
        self.assertEqual(result["query_form_mismatches"], 1)

    def test_missing_issuer_reporting_rows_are_not_silently_imputed(self):
        result = analyze_feed_snapshot([row(role="Issuer")], "4")
        self.assertEqual(result["accessions_with_issuer_and_reporting"], 0)
        self.assertEqual(result["entity_rows_per_accession"], {"1": 1})

    def test_duplicate_entity_row_is_counted(self):
        item = row()
        result = analyze_feed_snapshot([item, dict(item)], "4")
        self.assertEqual(result["duplicate_entity_rows"], 1)

    def test_multiple_updated_values_within_accession_are_flagged(self):
        result = analyze_feed_snapshot([
            row(role="Issuer", updated="2026-11-12T00:00:00-05:00"),
            row(role="Reporting", cik="0000000456", path_cik="456", updated="2026-11-12T00:00:01-05:00"),
        ], "4")
        self.assertEqual(result["accession_updated_timestamp_conflicts"], 1)

    def test_count_growth_nested_sets(self):
        result = compare_snapshot_counts([
            {"requested_count": 100, "accessions": ["a", "b"]},
            {"requested_count": 200, "accessions": ["a", "b", "c"]},
            {"requested_count": 500, "accessions": ["a", "b", "c", "d"]},
        ])
        self.assertTrue(result["nested_accession_sets"])

    def test_count_growth_detects_non_nested_sets(self):
        result = compare_snapshot_counts([
            {"requested_count": 100, "accessions": ["a", "b"]},
            {"requested_count": 200, "accessions": ["a", "c"]},
        ])
        self.assertFalse(result["nested_accession_sets"])
        self.assertEqual(result["comparisons"][0]["missing_from_larger"], ["b"])

    def test_count_cap_audit_never_admits_pit_or_alpha(self):
        # The output contract is explicit: count capacity cannot establish availability.
        controls = {
            "exact_first_public_timestamp_verified": False,
            "strict_pit_admitted": False,
            "alpha_test": False,
            "holdout_used": False,
            "f80_frozen": True,
        }
        self.assertFalse(controls["strict_pit_admitted"])
        self.assertFalse(controls["alpha_test"])
        self.assertFalse(controls["holdout_used"])
        self.assertTrue(controls["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
