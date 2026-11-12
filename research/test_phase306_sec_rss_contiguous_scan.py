import unittest

from research.phase306_sec_rss_contiguous_scan import (
    analyze_contiguous_scan,
    exact_form_type,
)


def make_row(i, accession=None, role="Issuer", form="4", updated="2026-11-12T00:00:00-05:00"):
    cik = f"{i + 1:010d}"
    accession = accession or f"{cik}-26-{i + 1:06d}"
    compact = accession.replace("-", "")
    return {
        "accession_from_link": accession,
        "entry_id": f"urn:tag:sec.gov,2008:accession-number={accession}",
        "title": f"{form} - Test Company ({cik}) ({role})",
        "form_type_from_title": form,
        "entity_role_from_title": role,
        "entity_cik_from_title": cik,
        "path_cik_from_link": cik,
        "path_cik_matches_title_entity": True,
        "feed_updated_raw": updated,
        "link": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{compact}/{accession}-index.htm",
        "summary_raw": f"summary-{i}",
    }


def page(start, entries, status=200):
    return {
        "start": start,
        "count": 100,
        "http_status": status,
        "status": "ATOM_PARSED" if status == 200 else "QUERY_FAILED",
        "raw_sha256": f"hash-{start}-{len(entries)}",
        "entries": entries,
    }


class Phase306ContiguousScanTests(unittest.TestCase):
    def build_stable_scan(self):
        rows = [make_row(i) for i in range(180)]
        pages = [
            page(0, rows[0:100]),
            page(80, rows[80:180]),
            page(160, rows[160:180]),
        ]
        return pages, page(0, rows[0:100])

    def test_stable_overlapping_scan_is_complete(self):
        pages, recheck = self.build_stable_scan()
        result = analyze_contiguous_scan(pages, recheck, "4")
        self.assertTrue(result["complete_current_snapshot_scan"])
        self.assertTrue(result["all_adjacent_overlaps_match"])
        self.assertEqual([x["shared_entity_rows"] for x in result["overlap_checks"]], [20, 20])
        self.assertEqual(result["unique_target_entity_rows"], 180)
        self.assertEqual(result["unique_target_accessions"], 180)

    def test_overlap_duplicates_are_deduplicated_without_losing_rows(self):
        pages, recheck = self.build_stable_scan()
        result = analyze_contiguous_scan(pages, recheck, "4")
        self.assertEqual(result["raw_entity_row_appearances"], 220)
        self.assertEqual(result["unique_raw_entity_rows"], 180)
        self.assertEqual(result["duplicate_entity_row_appearances_from_overlap"], 40)

    def test_accession_split_across_page_windows_is_reassembled(self):
        rows = [make_row(i) for i in range(180)]
        accession = "0000009000-26-000001"
        rows[79] = make_row(900, accession=accession, role="Reporting")
        rows[80] = make_row(901, accession=accession, role="Reporting")
        pages = [page(0, rows[:100]), page(80, rows[80:180]), page(160, rows[160:180])]
        result = analyze_contiguous_scan(pages, page(0, rows[:100]), "4")
        self.assertEqual(result["unique_target_accessions"], 179)
        self.assertEqual(result["unique_target_entity_rows"], 180)
        self.assertEqual(result["accessions_split_across_page_windows"], 1)

    def test_non_target_prefix_forms_are_counted_but_excluded(self):
        rows = [make_row(i) for i in range(180)]
        rows[90] = make_row(90, form="424B5")
        pages = [page(0, rows[:100]), page(80, rows[80:180]), page(160, rows[160:180])]
        result = analyze_contiguous_scan(pages, page(0, rows[:100]), "4")
        self.assertEqual(result["unique_target_entity_rows"], 179)
        self.assertEqual(result["non_target_form_unique_rows"], 1)
        self.assertEqual(result["non_target_form_unique_row_counts"], {"424B5": 1})

    def test_overlap_mismatch_fails_closed(self):
        pages, recheck = self.build_stable_scan()
        changed = make_row(999)
        pages[1] = page(80, [changed] + pages[1]["entries"][1:])
        result = analyze_contiguous_scan(pages, recheck, "4")
        self.assertFalse(result["complete_current_snapshot_scan"])
        self.assertFalse(result["all_adjacent_overlaps_match"])

    def test_head_recheck_drift_fails_closed(self):
        pages, recheck = self.build_stable_scan()
        changed = make_row(999)
        recheck = page(0, [changed] + recheck["entries"][1:])
        result = analyze_contiguous_scan(pages, recheck, "4")
        self.assertFalse(result["head_page_stable_after_scan"])
        self.assertFalse(result["complete_current_snapshot_scan"])

    def test_page_cap_is_not_misreported_as_complete(self):
        rows = [make_row(i) for i in range(180)]
        pages = [page(0, rows[:100]), page(80, rows[80:180])]
        result = analyze_contiguous_scan(pages, page(0, rows[:100]), "4", capped=True)
        self.assertFalse(result["tail_seen"])
        self.assertTrue(result["scan_capped"])
        self.assertFalse(result["complete_current_snapshot_scan"])

    def test_same_row_key_with_changed_payload_is_a_conflict(self):
        pages, recheck = self.build_stable_scan()
        changed = dict(pages[1]["entries"][0])
        changed["feed_updated_raw"] = "2026-11-12T00:01:00-05:00"
        pages[1] = page(80, [changed] + pages[1]["entries"][1:])
        result = analyze_contiguous_scan(pages, recheck, "4")
        self.assertEqual(result["row_fingerprint_conflicts"], 1)
        self.assertFalse(result["complete_current_snapshot_scan"])

    def test_orphan_target_row_is_structural_error(self):
        orphan = make_row(0)
        orphan["accession_from_link"] = ""
        orphan["entry_id"] = "urn:tag:sec.gov,2008:accession-number="
        result = analyze_contiguous_scan([page(0, [orphan])], page(0, [orphan]), "4")
        self.assertEqual(result["target_structural_errors"]["orphan_entity_rows"], 1)
        self.assertFalse(result["complete_current_snapshot_scan"])

    def test_failed_page_is_not_complete(self):
        rows = [make_row(i) for i in range(100)]
        pages = [page(0, rows), page(80, [], status=503)]
        result = analyze_contiguous_scan(pages, page(0, rows), "4")
        self.assertFalse(result["all_requests_succeeded"])
        self.assertFalse(result["complete_current_snapshot_scan"])

    def test_exact_form_parser_keeps_full_prefixed_form_token(self):
        self.assertEqual(exact_form_type("4 - Example Corp (0000000123) (Issuer)"), "4")
        self.assertEqual(exact_form_type("4/A - Example Corp (0000000123) (Issuer)"), "4/A")
        self.assertEqual(exact_form_type("40-APP/A - Example Fund (0000000123) (Filer)"), "40-APP/A")
        self.assertEqual(exact_form_type("424B5 - Example Corp (0000000123) (Filer)"), "424B5")


if __name__ == "__main__":
    unittest.main()
