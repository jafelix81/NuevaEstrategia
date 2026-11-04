import csv
import json
import tempfile
import unittest
from pathlib import Path

from research.phase84_13dg_role_aware_identity_audit import (
    acceptance_to_utc, build_manifest, candidate_role_resolved, target_role_flags,
)


class Phase84RoleAwareIdentityTests(unittest.TestCase):
    def test_acceptance_timestamp_converts_eastern_to_utc(self):
        self.assertEqual(
            acceptance_to_utc("20261104100000"),
            "2026-11-04T15:00:00+00:00",
        )
        self.assertEqual(acceptance_to_utc("bad"), "")

    def test_filer_only_candidate_is_resolved_but_not_a_subject_event(self):
        flags = target_role_flags(
            {"subject_cik": "0000000002", "filer_cik": "0000000001"},
            {"0000000001"}, True,
        )
        self.assertFalse(flags["subject_target_hit"])
        self.assertTrue(flags["filer_target_hit"])
        self.assertTrue(flags["filer_only_target_hit"])

    def test_subject_and_filer_can_both_be_targets_but_subject_role_is_preserved(self):
        flags = target_role_flags(
            {"subject_cik": "0000000002", "filer_cik": "0000000001"},
            {"0000000001", "0000000002"}, True,
        )
        self.assertTrue(flags["subject_target_hit"])
        self.assertTrue(flags["filer_target_hit"])
        self.assertTrue(flags["both_subject_and_filer_target_hit"])
        self.assertFalse(flags["filer_only_target_hit"])

    def test_unresolved_candidate_fails_role_resolution(self):
        row = {
            "all_candidate_ciks": ["0000000001", "0000000003"],
            "unresolved_candidate_ciks": ["0000000003"],
            "candidate_role": "filer",
        }
        self.assertFalse(candidate_role_resolved(row))

    def test_disjoint_manifest_is_deterministic_and_weighted(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            candidate = tmp / "candidate.csv"
            p83 = tmp / "p83.csv"
            roles = tmp / "roles.csv"
            fields = [
                "accession", "form", "form_family", "is_amendment", "filing_date",
                "master_index_ciks", "master_index_names", "archive_path_ciks",
                "candidate_identity_ciks", "filenames", "raw_rows", "index_pair_type",
                "metadata_conflict_reasons", "metadata_conflict", "malformed_rows_in_quarter",
                "master_candidate_ciks", "path_candidate_ciks", "all_candidate_ciks",
                "candidate_class",
            ]
            rows = []
            for i in range(20):
                cls = "unique_candidate" if i < 10 else "control"
                cik = "0000000001" if cls == "unique_candidate" else ""
                rows.append({
                    "accession": f"0000000001-25-{i+1:06d}",
                    "form": "SC 13G", "form_family": "13G", "is_amendment": "False",
                    "filing_date": "2025-03-01", "master_index_ciks": json.dumps([cik] if cik else []),
                    "master_index_names": "{}", "archive_path_ciks": json.dumps([cik] if cik else []),
                    "candidate_identity_ciks": json.dumps([cik] if cik else []), "filenames": "[]",
                    "raw_rows": "1", "index_pair_type": "single_cik", "metadata_conflict_reasons": "[]",
                    "metadata_conflict": "False", "malformed_rows_in_quarter": "0",
                    "master_candidate_ciks": json.dumps([cik] if cik else []),
                    "path_candidate_ciks": json.dumps([cik] if cik else []),
                    "all_candidate_ciks": json.dumps([cik] if cik else []), "candidate_class": cls,
                })
            with candidate.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
            with p83.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["accession"])
                w.writeheader(); w.writerow({"accession": rows[0]["accession"]})
            with roles.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["sample_stratum", "n83", "subject_target_n", "filer_only_n", "unresolved_n"])
                w.writeheader()
                w.writerow({
                    "sample_stratum": "13G|False|13g_mandatory_xml|unique_candidate",
                    "n83": 1, "subject_target_n": 0, "filer_only_n": 1, "unresolved_n": 0,
                })
            one, population, phase83 = build_manifest(candidate, p83, roles, limit=10)
            two, _, _ = build_manifest(candidate, p83, roles, limit=10)
            self.assertEqual([x["accession"] for x in one], [x["accession"] for x in two])
            self.assertEqual(len(one), 10)
            self.assertNotIn(rows[0]["accession"], {x["accession"] for x in one})
            self.assertEqual(population["13G|False|13g_mandatory_xml|unique_candidate"], 10)
            self.assertEqual(phase83["13G|False|13g_mandatory_xml|unique_candidate"]["n83"], "1")
            self.assertTrue(all(x["population_stratum_n"] >= x["phase84_sample_stratum_n"] for x in one))


if __name__ == "__main__":
    unittest.main()
