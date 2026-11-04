import unittest
from research.phase74_13dg_global_subject_audit import (
    candidate_evidence, classify_candidate_role, complete_submission_url, submission_url_candidates,
    normalize_form, normalize_accession, parse_master_index_13dg,
    stratified_sample, timing_regime,
)


class Phase74Global13DGTests(unittest.TestCase):
    def setUp(self):
        self.master = """Description: SEC Master Index
Last Data Received: 2026-11-04
CIK|Company Name|Form Type|Date Filed|Filename
0000315066|FMR LLC|SC 13G|2025-05-07|edgar/data/1061736/000031506625001108/0000315066-25-001108.txt
0001061736|MEXICAN ECONOMIC DEVELOPMENT INC|SC 13G|2025-05-07|edgar/data/1061736/000031506625001108/0000315066-25-001108.txt
0001140361|HELU CARLOS|SC 13D/A|2024-05-10|edgar/data/1129137/000114036124025446/0001140361-24-025446.txt
0001129137|AMERICA MOVIL SAB DE CV|SC 13D/A|2024-05-10|edgar/data/1129137/000114036124025446/0001140361-24-025446.txt
0000000000|Other filer|10-K|2025-05-07|edgar/data/1/000000000025000001/0000000000-25-000001.txt
"""

    def test_normalize_forms_and_accessions(self):
        self.assertEqual(normalize_form("SCHEDULE 13G/A"), "SC 13G/A")
        self.assertEqual(normalize_form("SC 13D"), "SC 13D")
        self.assertEqual(normalize_accession("000031506625001108"), "0000315066-25-001108")
        self.assertEqual(normalize_accession("bad"), "")

    def test_master_index_groups_two_ciks_and_archive_path(self):
        rows = parse_master_index_13dg(self.master, "2025Q2")
        self.assertEqual(len(rows), 2)
        row = next(r for r in rows if r["accession"] == "0000315066-25-001108")
        self.assertEqual(row["master_index_ciks"], ["0000315066", "0001061736"])
        self.assertEqual(row["archive_path_ciks"], ["0001061736"])
        self.assertEqual(row["form"], "SC 13G")
        self.assertEqual(row["raw_rows"], 2)
        self.assertFalse(row["metadata_conflict"])

    def test_candidate_role_uses_header_not_index_assumption(self):
        row = {"master_index_ciks": ["0000315066", "0001061736"],
               "archive_path_ciks": ["0001061736"], "all_candidate_ciks": ["0001061736"]}
        role = classify_candidate_role(row, {"subject_cik": "0001061736", "filer_cik": "0000315066"})
        self.assertEqual(role["candidate_role"], "subject")
        self.assertTrue(role["subject_in_master_index_ciks"])
        self.assertTrue(role["filer_in_master_index_ciks"])
        self.assertTrue(role["subject_in_archive_path_ciks"])
        self.assertFalse(role["filer_in_archive_path_ciks"])

    def test_filer_only_candidate_is_not_subject_event(self):
        row = {"master_index_ciks": ["0000315066", "0001061736"],
               "archive_path_ciks": ["0001061736"], "all_candidate_ciks": ["0000315066"]}
        role = classify_candidate_role(row, {"subject_cik": "0001061736", "filer_cik": "0000315066"})
        self.assertEqual(role["candidate_role"], "filer")

    def test_candidate_evidence_separates_index_and_path(self):
        row = {"master_index_ciks": ["0000315066"], "archive_path_ciks": ["0001061736"]}
        evidence = candidate_evidence(row, {"0001061736"})
        self.assertEqual(evidence["master_candidate_ciks"], [])
        self.assertEqual(evidence["path_candidate_ciks"], ["0001061736"])
        self.assertEqual(evidence["candidate_class"], "unique_candidate")

    def test_form_specific_timing_regimes(self):
        self.assertEqual(timing_regime("13D", "2024-02-04"), "13d_legacy_deadline")
        self.assertEqual(timing_regime("13D", "2024-02-05"), "13d_revised_deadline_pre_xml")
        self.assertEqual(timing_regime("13G", "2024-09-29"), "13g_legacy_deadline")
        self.assertEqual(timing_regime("13G", "2024-09-30"), "13g_revised_deadline_pre_xml")
        self.assertEqual(timing_regime("13G", "2024-12-18"), "13g_mandatory_xml")

    def test_complete_submission_url_uses_explicit_archive_cik(self):
        self.assertEqual(
            complete_submission_url("0001061736", "0000315066-25-001108"),
            "https://www.sec.gov/Archives/edgar/data/1061736/000031506625001108/0000315066-25-001108.txt",
        )
        with self.assertRaises(ValueError):
            complete_submission_url("0001061736", "invalid")

    def test_submission_url_candidates_try_archive_path_then_master_ciks_then_accession_prefix(self):
        row = {
            "accession": "0000315066-25-001108",
            "archive_path_ciks": ["0001061736"],
            "master_index_ciks": ["0000315066", "0001061736"],
        }
        candidates = submission_url_candidates(row)
        self.assertEqual([c for c, _ in candidates], ["0001061736", "0000315066"])
        self.assertIn("/1061736/", candidates[0][1])
        self.assertIn("/315066/", candidates[1][1])

    def test_ambiguous_pair_can_be_resolved_as_one_subject_and_one_filer(self):
        row = {
            "master_index_ciks": ["0000315066", "0001061736"],
            "archive_path_ciks": ["0001061736"],
            "all_candidate_ciks": ["0000315066", "0001061736"],
        }
        role = classify_candidate_role(row, {"subject_cik": "0001061736", "filer_cik": "0000315066"})
        self.assertEqual(role["candidate_role"], "subject")
        self.assertEqual(role["candidate_cik"], "0001061736")
        self.assertEqual(role["filer_candidate_ciks"], ["0000315066"])

    def test_sample_is_deterministic_and_preserves_form_strata(self):
        rows = parse_master_index_13dg(self.master, "2025Q2")
        one = stratified_sample(rows, {"0001061736"}, 10)
        two = stratified_sample(rows, {"0001061736"}, 10)
        self.assertEqual([r["accession"] for r in one], [r["accession"] for r in two])
        self.assertEqual({r["form_family"] for r in one}, {"13D", "13G"})
        self.assertTrue(all("candidate_class" in r for r in one))


if __name__ == "__main__":
    unittest.main()
