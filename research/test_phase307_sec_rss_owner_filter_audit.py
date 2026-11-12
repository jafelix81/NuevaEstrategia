import unittest

from research.phase307_sec_rss_owner_filter_audit import (
    analyze_mode_form,
    evaluate_owner_filter_semantics,
)


def make_row(i, accession=None, role="Issuer", form="4"):
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
        "feed_updated_raw": "2026-11-12T00:00:00-05:00",
        "link": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{compact}/{accession}-index.htm",
        "summary_raw": f"summary-{i}",
    }


def page(start, entries, status=200):
    return {
        "start": start,
        "http_status": status,
        "status": "ATOM_PARSED" if status == 200 else "QUERY_FAILED",
        "entries": entries,
    }


class Phase307OwnerFilterTests(unittest.TestCase):
    def stable_pages(self, form="4", n=180):
        rows = [make_row(i, form=form) for i in range(n)]
        return [page(0, rows[:100]), page(80, rows[80:180]), page(160, rows[160:180])], page(0, rows[:100])

    def test_owner_only_contiguous_pages_complete_when_tail_and_recheck_stable(self):
        pages, recheck = self.stable_pages("4")
        result = analyze_mode_form(pages, recheck, "4")
        self.assertTrue(result["complete_current_snapshot_scan"])
        self.assertTrue(result["all_adjacent_overlaps_match"])
        self.assertEqual(result["unique_target_accessions"], 180)

    def test_non_target_prefix_rows_are_counted_not_misclassified(self):
        pages, recheck = self.stable_pages("4")
        pages[1]["entries"][25] = make_row(999, form="424B2", role="Filer")
        result = analyze_mode_form(pages, recheck, "4")
        self.assertEqual(result["non_target_form_unique_row_counts"], {"424B2": 1})
        self.assertEqual(result["unique_target_accessions"], 179)

    def test_owner_only_filter_semantics_pass_with_clean_controls(self):
        only4, only4_recheck = self.stable_pages("4")
        only4a, only4a_recheck = self.stable_pages("4/A")
        include4, _ = self.stable_pages("4")
        include4[0]["entries"].append(make_row(1000, form="424B2", role="Filer"))
        exclude4 = [page(0, [make_row(2000, form="424B2", role="Filer")]), page(80, [])]
        exclude4a = [page(0, [make_row(2001, form="424B2", role="Filer")]), page(80, [])]
        results = {
            "only": {
                "form4": {"analysis": analyze_mode_form(only4, only4_recheck, "4")},
                "form4a": {"analysis": analyze_mode_form(only4a, only4a_recheck, "4/A")},
            },
            "include": {
                "form4": {"analysis": analyze_mode_form(include4, None, "4")},
                "form4a": {"analysis": analyze_mode_form([page(0, [make_row(3000, form="4/A")])], None, "4/A")},
            },
            "exclude": {
                "form4": {"analysis": analyze_mode_form(exclude4, None, "4")},
                "form4a": {"analysis": analyze_mode_form(exclude4a, None, "4/A")},
            },
        }
        result = evaluate_owner_filter_semantics(results)
        self.assertTrue(result["owner_only_isolates_ownership_forms"])
        self.assertTrue(result["owner_only_preserves_include_page0_accession_set"])
        self.assertTrue(result["owner_only_filter_useful_for_capture"])

    def test_owner_only_non_target_form_breaks_isolation(self):
        only4, recheck = self.stable_pages("4")
        only4[0]["entries"][0] = make_row(999, form="424B5", role="Filer")
        pages4a, recheck4a = self.stable_pages("4/A")
        include4, _ = self.stable_pages("4")
        include4[0]["entries"].append(make_row(1000, form="424B2", role="Filer"))
        exclude4 = [page(0, [make_row(2000, form="424B2", role="Filer")])]
        exclude4a = [page(0, [make_row(2001, form="424B2", role="Filer")])]
        results = {
            "only": {
                "form4": {"analysis": analyze_mode_form(only4, recheck, "4")},
                "form4a": {"analysis": analyze_mode_form(pages4a, recheck4a, "4/A")},
            },
            "include": {
                "form4": {"analysis": analyze_mode_form(include4, None, "4")},
                "form4a": {"analysis": analyze_mode_form([page(0, [make_row(3000, form="4/A")])], None, "4/A")},
            },
            "exclude": {
                "form4": {"analysis": analyze_mode_form(exclude4, None, "4")},
                "form4a": {"analysis": analyze_mode_form(exclude4a, None, "4/A")},
            },
        }
        self.assertFalse(evaluate_owner_filter_semantics(results)["owner_only_isolates_ownership_forms"])

    def test_owner_exclude_target_rows_break_negative_control(self):
        only4, only4_recheck = self.stable_pages("4")
        only4a, only4a_recheck = self.stable_pages("4/A")
        include4, _ = self.stable_pages("4")
        include4[0]["entries"].append(make_row(1000, form="424B2", role="Filer"))
        exclude4 = [page(0, [make_row(2000, form="4")])]
        exclude4a = [page(0, [make_row(2001, form="4/A")])]
        results = {
            "only": {
                "form4": {"analysis": analyze_mode_form(only4, only4_recheck, "4")},
                "form4a": {"analysis": analyze_mode_form(only4a, only4a_recheck, "4/A")},
            },
            "include": {
                "form4": {"analysis": analyze_mode_form(include4, None, "4")},
                "form4a": {"analysis": analyze_mode_form([page(0, [make_row(3000, form="4/A")])], None, "4/A")},
            },
            "exclude": {
                "form4": {"analysis": analyze_mode_form(exclude4, None, "4")},
                "form4a": {"analysis": analyze_mode_form(exclude4a, None, "4/A")},
            },
        }
        self.assertFalse(evaluate_owner_filter_semantics(results)["owner_only_isolates_ownership_forms"])

    def test_exact_form4a_is_not_counted_as_exact_form4(self):
        rows = [make_row(1, form="4"), make_row(2, form="4/A")]
        result = analyze_mode_form([page(0, rows)], page(0, rows), "4")
        self.assertEqual(result["unique_target_entity_rows"], 1)
        self.assertEqual(result["non_target_form_unique_row_counts"], {"4/A": 1})

    def test_filer_identity_and_duplicate_rows_remain_reproducible(self):
        accession = "0000009000-26-000001"
        a = make_row(1, accession=accession, role="Filer", form="424B5")
        b = make_row(2, accession=accession, role="Filer", form="424B5")
        result = analyze_mode_form([page(0, [a, b])], page(0, [a, b]), "4")
        self.assertEqual(result["unique_raw_entity_rows"], 2)
        self.assertEqual(result["duplicate_raw_entity_row_appearances"], 0)

    def test_failed_page_prevents_complete_snapshot_claim(self):
        rows = [make_row(i) for i in range(100)]
        pages = [page(0, rows), page(80, [], status=503)]
        result = analyze_mode_form(pages, page(0, rows), "4")
        self.assertFalse(result["all_requests_succeeded"])
        self.assertFalse(result["complete_current_snapshot_scan"])


if __name__ == "__main__":
    unittest.main()
