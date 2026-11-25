"""Offline regressions for Phase 605 SEC 13F manager relationship parsing."""
from __future__ import annotations

import unittest

from research.phase605_sec_13f_manager_relationship_graph_audit import (
    ManagerGraphError,
    audit_manager_relationship_graph,
    normalize_file_number,
)


SUB_H = ["ACCESSION_NUMBER", "FILING_DATE", "SUBMISSIONTYPE", "CIK", "PERIODOFREPORT"]
COV_H = ["ACCESSION_NUMBER", "FORM13FFILENUMBER", "REPORTTYPE", "FILINGMANAGER_NAME"]
OM_H = ["ACCESSION_NUMBER", "OTHERMANAGER_SK", "CIK", "FORM13FFILENUMBER", "NAME"]
OM2_H = ["ACCESSION_NUMBER", "SEQUENCENUMBER", "CIK", "FORM13FFILENUMBER", "NAME"]
INFO_H = ["ACCESSION_NUMBER", "INFOTABLE_SK", "OTHERMANAGER"]


def base_inputs():
    submissions = [
        ["NOTICE1", "15-MAY-2026", "13F-NT", "100", "31-MAR-2026"],
        ["HOLD1", "15-MAY-2026", "13F-HR", "200", "31-MAR-2026"],
        ["INCL1", "15-MAY-2026", "13F-HR", "300", "31-MAR-2026"],
    ]
    cover = [
        ["NOTICE1", "028-00001", "13F NOTICE", "Notice Filer"],
        ["HOLD1", "028-00002", "13F HOLDINGS REPORT", "Reporting Manager"],
        ["INCL1", "028-00003", "13F HOLDINGS REPORT", "Included Manager"],
    ]
    othermanager = [["NOTICE1", "1", "", "28-2", "Reporting Manager"]]
    othermanager2 = [["HOLD1", "1", "300", "028 - 00003", "Included Manager"]]
    infotable = [["HOLD1", "1", "1"]]
    return submissions, cover, othermanager, othermanager2, infotable


def audit(submissions=None, cover=None, othermanager=None, othermanager2=None, infotable=None):
    defaults = base_inputs()
    values = [
        submissions if submissions is not None else defaults[0],
        cover if cover is not None else defaults[1],
        othermanager if othermanager is not None else defaults[2],
        othermanager2 if othermanager2 is not None else defaults[3],
        infotable if infotable is not None else defaults[4],
    ]
    return audit_manager_relationship_graph(
        SUB_H, values[0], COV_H, values[1], OM_H, values[2],
        OM2_H, values[3], INFO_H, values[4]
    )


class Phase605Tests(unittest.TestCase):
    def test_file_number_variants_normalize_to_one_canonical_key(self):
        self.assertEqual(normalize_file_number("028-04545"), "028-04545")
        self.assertEqual(normalize_file_number("28-4545"), "028-04545")
        self.assertEqual(normalize_file_number("028 - 4545"), "028-04545")
        self.assertIsNone(normalize_file_number(""))
        with self.assertRaisesRegex(ManagerGraphError, "invalid_form13f_file_number"):
            normalize_file_number("manager-4545")

    def test_notice_roster_is_a_directed_edge_to_reporting_manager(self):
        result = audit()
        edge = result["othermanager_reporting_for_filer"]["edges"][0]
        self.assertEqual(result["status"], "PASS_ROLE_AWARE_RELATIONSHIP_INTEGRITY")
        self.assertEqual(edge["from_filer_cik"], "0000000100")
        self.assertEqual(edge["to_reporting_manager_cik"], "0000000200")
        self.assertEqual(edge["relationship_type"], "FILER_TO_REPORTING_MANAGER")
        self.assertEqual(edge["resolution_status"], "RESOLVED_BY_FILE_NUMBER")
        self.assertFalse(edge["name_used_for_identity"])

    def test_included_manager_edge_and_infotable_sequence_join(self):
        result = audit()
        edge = result["othermanager2_included_in_filing"]["edges"][0]
        refs = result["infotable_sequence_references"]
        self.assertEqual(edge["from_reporting_filer_cik"], "0000000200")
        self.assertEqual(edge["to_included_manager_cik"], "0000000300")
        self.assertEqual(edge["relationship_type"], "REPORTING_FILER_TO_INCLUDED_MANAGER")
        self.assertEqual(refs["referenced_sequence_tokens"], 1)
        self.assertEqual(refs["resolved_sequence_tokens"], 1)
        self.assertEqual(refs["dangling_sequence_tokens"], 0)

    def test_multiple_infotable_manager_references_are_resolved_individually(self):
        submissions, cover, om, om2, _ = base_inputs()
        om2.append(["HOLD1", "2", "100", "028-00001", "Notice Filer"])
        result = audit(submissions, cover, om, om2, [["HOLD1", "1", "1, 2"]])
        refs = result["infotable_sequence_references"]
        self.assertEqual(refs["referenced_sequence_tokens"], 2)
        self.assertEqual(refs["resolved_sequence_tokens"], 2)
        self.assertEqual(refs["dangling_sequence_tokens"], 0)

    def test_explicit_cik_and_file_number_conflict_is_not_silently_resolved(self):
        submissions, cover, om, om2, info = base_inputs()
        om[0][2] = "999"
        result = audit(submissions, cover, om, om2, info)
        edge = result["othermanager_reporting_for_filer"]["edges"][0]
        self.assertEqual(edge["resolution_status"], "IDENTITY_CONFLICT")
        self.assertIsNone(edge["to_reporting_manager_cik"])
        self.assertEqual(result["identity_resolution"]["identity_conflicts"], 1)
        self.assertEqual(result["status"], "BLOCKED_RELATIONSHIP_OR_IDENTITY_EXCEPTIONS")

    def test_ambiguous_file_number_does_not_resolve_without_explicit_cik(self):
        submissions, cover, om, om2, info = base_inputs()
        submissions.append(["HOLD2", "15-MAY-2026", "13F-HR", "400", "31-MAR-2026"])
        cover.append(["HOLD2", "028-00002", "13F HOLDINGS REPORT", "Second Reporting Manager"])
        result = audit(submissions, cover, om, om2, info)
        edge = result["othermanager_reporting_for_filer"]["edges"][0]
        self.assertEqual(edge["resolution_status"], "AMBIGUOUS_FILE_NUMBER")
        self.assertIsNone(edge["to_reporting_manager_cik"])
        self.assertEqual(result["identity_resolution"]["file_number_to_cik_conflict_count"], 1)

    def test_names_are_never_used_as_a_fallback_identity(self):
        submissions, cover, _, om2, info = base_inputs()
        othermanager = [["NOTICE1", "1", "", "", "Reporting Manager"]]
        result = audit(submissions, cover, othermanager, om2, info)
        edge = result["othermanager_reporting_for_filer"]["edges"][0]
        self.assertEqual(edge["resolution_status"], "UNRESOLVED_NO_IDENTIFIER")
        self.assertIsNone(edge["to_reporting_manager_cik"])
        self.assertFalse(edge["name_used_for_identity"])

    def test_notice_without_othermanager_roster_is_flagged(self):
        submissions, cover, _, om2, info = base_inputs()
        result = audit(submissions, cover, [], om2, info)
        self.assertEqual(result["notice_controls"]["notice_accessions_without_roster"], 1)
        self.assertEqual(result["status"], "BLOCKED_RELATIONSHIP_OR_IDENTITY_EXCEPTIONS")

    def test_notice_with_infotable_rows_is_flagged_not_treated_as_a_portfolio(self):
        submissions, cover, om, om2, info = base_inputs()
        info.append(["NOTICE1", "99", ""])
        result = audit(submissions, cover, om, om2, info)
        self.assertEqual(result["notice_controls"]["notice_accessions_with_infotable_rows"], 1)
        self.assertEqual(result["status"], "BLOCKED_RELATIONSHIP_OR_IDENTITY_EXCEPTIONS")

    def test_dangling_sequence_reference_is_flagged(self):
        result = audit(infotable=[["HOLD1", "1", "2"]])
        self.assertEqual(result["infotable_sequence_references"]["dangling_sequence_tokens"], 1)
        self.assertEqual(result["status"], "BLOCKED_RELATIONSHIP_OR_IDENTITY_EXCEPTIONS")

    def test_malformed_sequence_reference_is_flagged(self):
        result = audit(infotable=[["HOLD1", "1", "1;2"]])
        self.assertEqual(result["infotable_sequence_references"]["malformed_sequence_tokens"], 1)

    def test_duplicate_othermanager_key_is_flagged(self):
        submissions, cover, om, om2, info = base_inputs()
        om.append(om[0].copy())
        result = audit(submissions, cover, om, om2, info)
        self.assertEqual(result["othermanager_reporting_for_filer"]["duplicate_accession_key_rows"], 1)
        self.assertEqual(result["status"], "BLOCKED_RELATIONSHIP_OR_IDENTITY_EXCEPTIONS")

    def test_duplicate_othermanager2_sequence_is_flagged(self):
        submissions, cover, om, om2, info = base_inputs()
        om2.append(om2[0].copy())
        result = audit(submissions, cover, om, om2, info)
        self.assertEqual(result["othermanager2_included_in_filing"]["duplicate_accession_sequence_rows"], 1)

    def test_noncontiguous_positive_included_manager_sequences_are_allowed(self):
        submissions, cover, om, om2, _ = base_inputs()
        om2[0][1] = "7"
        result = audit(submissions, cover, om, om2, [["HOLD1", "1", "7"]])
        self.assertEqual(result["infotable_sequence_references"]["resolved_sequence_tokens"], 1)
        self.assertEqual(result["infotable_sequence_references"]["dangling_sequence_tokens"], 0)

    def test_combination_report_preserves_both_relationship_directions(self):
        submissions, cover, om, om2, info = base_inputs()
        submissions[0][2] = "13F-HR"
        cover[0][2] = "13F COMBINATION REPORT"
        result = audit(submissions, cover, om, om2, info)
        self.assertEqual(
            result["othermanager_reporting_for_filer"]["edges"][0]["relationship_type"],
            "FILER_TO_REPORTING_MANAGER"
        )
        self.assertEqual(
            result["othermanager2_included_in_filing"]["edges"][0]["relationship_type"],
            "REPORTING_FILER_TO_INCLUDED_MANAGER"
        )

    def test_13f_nt_report_type_discordance_is_flagged(self):
        submissions, cover, om, om2, info = base_inputs()
        cover[0][2] = "13F HOLDINGS REPORT"
        result = audit(submissions, cover, om, om2, info)
        self.assertEqual(len(result["report_type_submission_type_discordance_accessions"]), 1)

    def test_notice_roster_does_not_create_zero_holdings_signal(self):
        result = audit()
        self.assertFalse(result["signal_eligible"])
        self.assertEqual(result["notice_controls"]["notice_accessions_with_infotable_rows"], 0)


if __name__ == "__main__":
    unittest.main()
