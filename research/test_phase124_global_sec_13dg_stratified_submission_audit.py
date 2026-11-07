import csv
import tempfile
import unittest
from pathlib import Path

from research.phase124_global_sec_13dg_stratified_submission_audit import (
    allocate_strata, exclusion_set, parse_json_list, parse_rule_designations,
    sample_hash, weighted_rate, classify_sampled_submission,
    cusip_source_label, is_success_status,
)

class Phase124Tests(unittest.TestCase):
    def test_allocation_hits_exact_target_with_minimum_per_stratum(self):
        counts = {"a": 100, "b": 200, "c": 300, "d": 400}
        allocation = allocate_strata(counts, target=20, minimum=2)
        self.assertEqual(sum(allocation.values()), 20)
        self.assertTrue(all(allocation[k] >= 2 for k in counts))
        self.assertTrue(all(allocation[k] <= counts[k] for k in counts))

    def test_allocation_is_deterministic(self):
        counts = {"2016Q1|13D|false": 100, "2016Q1|13G|true": 500, "2026Q3|13D|true": 40}
        self.assertEqual(
            allocate_strata(counts, target=12, minimum=2),
            allocate_strata(counts, target=12, minimum=2),
        )

    def test_allocation_rejects_impossible_minimum(self):
        with self.assertRaises(ValueError):
            allocate_strata({"a": 1, "b": 1, "c": 1}, target=2, minimum=1)

    def test_sample_hash_is_stable_and_accession_specific(self):
        self.assertEqual(sample_hash("0000000000-26-000001"), sample_hash("0000000000-26-000001"))
        self.assertNotEqual(sample_hash("0000000000-26-000001"), sample_hash("0000000000-26-000002"))
        self.assertEqual(len(sample_hash("0000000000-26-000001")), 64)

    def test_parse_json_list_is_safe(self):
        self.assertEqual(parse_json_list('["0000000001","0000000002"]'), ["0000000001","0000000002"])
        self.assertEqual(parse_json_list("not-json"), [])

    def test_exclusion_set_removes_all_prior_pilot_accessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p82, p84, p120 = (root / x for x in ("p82","p84","p120"))
            for d in (p82,p84,p120):
                d.mkdir()
            for path, header, row in [
                (p82/"pilot_manifest.csv","accession","A"),
                (p84/"pilot_header_validation.csv","accession","B"),
                (p120/"phase120_predecessor_audit.csv","current_accession,previous_accession","C,D"),
            ]:
                with path.open("w",newline="",encoding="utf-8") as f:
                    w=csv.writer(f); w.writerow(header.split(",")); w.writerow(row.split(","))
            self.assertEqual(exclusion_set(p82,p84,p120), {"A","B","C","D"})

    def test_13g_rule_designations_are_extracted_only_from_xml(self):
        raw = """<XML><edgarSubmission><formData><designateRulesPursuantThisScheduleFiled>
        <designateRulePursuantThisScheduleFiled>Rule 13d-1(b)</designateRulePursuantThisScheduleFiled>
        </designateRulesPursuantThisScheduleFiled></formData></edgarSubmission></XML>"""
        self.assertEqual(parse_rule_designations(raw,"13G"), ["Rule 13d-1(b)"])
        self.assertEqual(parse_rule_designations(raw,"13D"), [])

    def test_weighted_rate_uses_post_stratification_weights(self):
        rows = [
            {"sample_weight": 10, "flag": True},
            {"sample_weight": 30, "flag": False},
        ]
        self.assertAlmostEqual(weighted_rate(rows,"flag"), 0.25)

    def test_weighted_rate_ignores_missing_values(self):
        rows = [
            {"sample_weight": 10, "flag": True},
            {"sample_weight": 100, "flag": None},
        ]
        self.assertAlmostEqual(weighted_rate(rows,"flag"), 1.0)

    def test_non_13dg_sec_index_alias_is_quarantined_not_counted_as_download_failure(self):
        accession = "0001104659-25-001464"
        raw = """<SEC-HEADER>
ACCESSION NUMBER: 0001104659-25-001464
CONFORMED SUBMISSION TYPE: SC TO-T/A
FILED AS OF DATE: 20250107
</SEC-HEADER>
<DOCUMENT><TYPE>SC TO-T/A</TYPE></DOCUMENT>
<DOCUMENT><TYPE>EX-99.(A)(5)(B)</TYPE></DOCUMENT>"""
        header = {"accession": accession, "filed_date": "2025-01-07"}
        status, header_form, document_types = classify_sampled_submission(
            "SC 13D/A", header, raw, accession, "2025-01-07"
        )
        self.assertEqual(status, "INDEX_ALIAS_NON_13DG")
        self.assertEqual(header_form, "SC TO-T/A")
        self.assertEqual(document_types, ["SC TO-T/A", "EX-99.(A)(5)(B)"])

    def test_actual_13dg_form_and_index_match_is_valid(self):
        accession = "0000000000-26-000001"
        raw = """<SEC-HEADER>
ACCESSION NUMBER: 0000000000-26-000001
CONFORMED SUBMISSION TYPE: SC 13D/A
FILED AS OF DATE: 20260105
</SEC-HEADER>
<DOCUMENT><TYPE>SC 13D/A</TYPE></DOCUMENT>"""
        header = {"accession": accession, "filed_date": "2026-01-05"}
        status, header_form, document_types = classify_sampled_submission(
            "SC 13D/A", header, raw, accession, "2026-01-05"
        )
        self.assertEqual(status, "VALID_13DG")

    def test_cusip_source_label_uses_actual_presence_and_source(self):
        self.assertEqual(cusip_source_label(True, "037833100"), "13DG_XML")
        self.assertEqual(cusip_source_label(False, "037833100"), "LEGACY_HTML_HEURISTIC")
        self.assertEqual(cusip_source_label(False, None), "NONE")
        self.assertEqual(cusip_source_label(True, None), "NONE")

    def test_alias_quarantine_status_is_a_successful_audit_status(self):
        self.assertTrue(is_success_status("PASS_WITH_INDEX_ALIAS_QUARANTINE"))
        self.assertTrue(is_success_status("PASS_GLOBAL_STRATIFIED_SAMPLE_WITH_CAVEATS"))
        self.assertFalse(is_success_status("INCOMPLETE"))

    def test_form_conflict_with_13dg_document_is_not_silently_quarantined(self):
        accession = "0000000000-26-000002"
        raw = """<SEC-HEADER>
ACCESSION NUMBER: 0000000000-26-000002
CONFORMED SUBMISSION TYPE: SC TO-T/A
FILED AS OF DATE: 20260105
</SEC-HEADER>
<DOCUMENT><TYPE>SC TO-T/A</TYPE></DOCUMENT>
<DOCUMENT><TYPE>SC 13D/A</TYPE></DOCUMENT>"""
        header = {"accession": accession, "filed_date": "2026-01-05"}
        status, _, _ = classify_sampled_submission(
            "SC 13D/A", header, raw, accession, "2026-01-05"
        )
        self.assertEqual(status, "UNRESOLVED_FORM_CONFLICT")

    def test_identity_mismatch_is_not_quarantined_as_index_alias(self):
        accession = "0000000000-26-000003"
        raw = """<SEC-HEADER>
ACCESSION NUMBER: 0000000000-26-000003
CONFORMED SUBMISSION TYPE: SC TO-T/A
FILED AS OF DATE: 20260105
</SEC-HEADER>
<DOCUMENT><TYPE>SC TO-T/A</TYPE></DOCUMENT>"""
        header = {"accession": "0000000000-26-000004", "filed_date": "2026-01-05"}
        status, _, _ = classify_sampled_submission(
            "SC 13D/A", header, raw, accession, "2026-01-05"
        )
        self.assertEqual(status, "INVALID_IDENTITY")

if __name__ == "__main__":
    unittest.main()
