#!/usr/bin/env python3
"""Regression tests for Phase 226 group-flag and ownership-overlap audit."""
from __future__ import annotations

import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import phase226_13dg_group_flag_overlap_audit as audit


class GroupFlagTests(unittest.TestCase):
    def test_affirmative_group_flag(self):
        self.assertEqual(audit.classify_group_flag("a"), "AFFIRMED_GROUP")

    def test_disclaimer_or_relationship_flag(self):
        self.assertEqual(audit.classify_group_flag("b"), "DISCLAIMED_OR_RELATIONSHIP_WITHOUT_AFFIRMATION")

    def test_missing_is_unreported_not_no_group(self):
        self.assertEqual(audit.classify_group_flag(""), "UNREPORTED")

    def test_unexpected_value_is_quarantined(self):
        self.assertEqual(audit.classify_group_flag("x"), "INVALID_OR_UNEXPECTED")

    def test_family_specific_13d_group_element(self):
        node = ET.fromstring("<reportingPersonInfo><memberOfGroup>a</memberOfGroup><aggregateAmountOwned>10</aggregateAmountOwned></reportingPersonInfo>")
        parsed = audit.parse_owner(node, "13D")
        self.assertEqual(parsed["group_raw"], "a")
        self.assertEqual(parsed["group_status"], "AFFIRMED_GROUP")

    def test_family_specific_13g_group_element(self):
        node = ET.fromstring("<coverPageHeaderReportingPersonDetails><memberGroup>b</memberGroup><reportingPersonBeneficiallyOwnedAggregateNumberOfShares>20</reportingPersonBeneficiallyOwnedAggregateNumberOfShares></coverPageHeaderReportingPersonDetails>")
        parsed = audit.parse_owner(node, "13G")
        self.assertEqual(parsed["group_raw"], "b")
        self.assertEqual(parsed["group_status"], "DISCLAIMED_OR_RELATIONSHIP_WITHOUT_AFFIRMATION")

    def test_missing_group_field_does_not_create_negative_status(self):
        node = ET.fromstring("<reportingPersonInfo><reportingPersonName>Example</reportingPersonName></reportingPersonInfo>")
        parsed = audit.parse_owner(node, "13D")
        self.assertEqual(parsed["group_status"], "UNREPORTED")
        self.assertNotEqual(parsed["group_status"], "DISCLAIMED_OR_RELATIONSHIP_WITHOUT_AFFIRMATION")

    def test_mixed_filing_group_flags_are_explicit(self):
        owners = [
            {"group_status": "AFFIRMED_GROUP"},
            {"group_status": "DISCLAIMED_OR_RELATIONSHIP_WITHOUT_AFFIRMATION"},
        ]
        self.assertEqual(audit.filing_group_status(owners), "MIXED_AFFIRMED_AND_DISCLAIMED")


class OwnershipOverlapTests(unittest.TestCase):
    def owner(self, group="UNREPORTED", aggregate="100"):
        return {
            "group_status": group,
            "aggregate": aggregate,
            "percent": "5.0",
            "sole_voting": "0",
            "shared_voting": "100",
            "sole_dispositive": "0",
            "shared_dispositive": "100",
            "owner_cik_present": False,
        }

    def test_signature_normalizes_decimal_format(self):
        a = self.owner(aggregate="100.00")
        b = self.owner(aggregate="1e2")
        self.assertEqual(audit.signature(a), audit.signature(b))

    def test_repeated_tuple_is_counted_but_not_summed(self):
        summary = audit.summarize_family([{"owners": [
            self.owner("DISCLAIMED_OR_RELATIONSHIP_WITHOUT_AFFIRMATION"),
            self.owner("DISCLAIMED_OR_RELATIONSHIP_WITHOUT_AFFIRMATION"),
        ]}])
        self.assertEqual(summary["filings_with_repeated_ownership_signatures"], 1)
        self.assertEqual(summary["repeated_signature_groups"], 1)
        self.assertEqual(summary["owner_rows_inside_repeated_signature_groups"], 2)
        self.assertEqual(summary["repeated_signature_groups_with_mixed_group_flags"], 0)

    def test_mixed_flags_inside_duplicate_tuple_are_detected_not_resolved(self):
        summary = audit.summarize_family([{"owners": [
            self.owner("AFFIRMED_GROUP"), self.owner("UNREPORTED")
        ]}])
        self.assertEqual(summary["repeated_signature_groups_with_mixed_group_flags"], 1)

    def test_empty_ownership_tuples_are_not_treated_as_duplicate_positions(self):
        empty = self.owner("UNREPORTED", aggregate="")
        empty.update({"percent": "", "sole_voting": "", "shared_voting": "", "sole_dispositive": "", "shared_dispositive": ""})
        summary = audit.summarize_family([{"owners": [empty, empty.copy()]}])
        self.assertEqual(summary["repeated_signature_groups"], 0)


class ArtifactIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(os.getenv("PHASE124_INPUT_DIR") and os.getenv("PHASE124_SOURCE_ZIP"), "set Phase 124 artifact paths for full integration")
    def test_full_hash_pinned_phase124_artifact(self):
        result = audit.audit(Path(os.environ["PHASE124_INPUT_DIR"]), Path(os.environ["PHASE124_SOURCE_ZIP"]))
        self.assertEqual(result["source"]["source_index_rows"], 600)
        self.assertEqual(result["source"]["actual_13dg_filings"], 599)
        self.assertEqual(result["source"]["structured_xml_filings"], 102)
        self.assertTrue(result["source"]["artifact_zip_sha256_verified_in_this_run"])
        self.assertEqual(result["by_family"]["13D"]["owner_group_flag_status"], {
            "AFFIRMED_GROUP": 31,
            "DISCLAIMED_OR_RELATIONSHIP_WITHOUT_AFFIRMATION": 65,
            "UNREPORTED": 56,
        })
        self.assertEqual(result["by_family"]["13G"]["owner_group_flag_status"], {
            "AFFIRMED_GROUP": 2,
            "DISCLAIMED_OR_RELATIONSHIP_WITHOUT_AFFIRMATION": 43,
            "UNREPORTED": 113,
        })
        self.assertEqual(result["by_family"]["13D"]["filings_with_repeated_ownership_signatures"], 21)
        self.assertEqual(result["by_family"]["13G"]["filings_with_repeated_ownership_signatures"], 27)
        self.assertEqual(result["by_family"]["13D"]["repeated_signature_groups_with_mixed_group_flags"], 0)
        self.assertEqual(result["by_family"]["13G"]["repeated_signature_groups_with_mixed_group_flags"], 0)
        self.assertFalse(result["controls"]["alpha_test_performed"])
        self.assertFalse(result["controls"]["f80_changed"])

    def test_wrong_source_zip_digest_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.zip"
            path.write_bytes(b"not the Phase 124 artifact")
            with self.assertRaisesRegex(ValueError, "phase124_artifact_zip_sha256_mismatch"):
                audit.audit(Path(temp), path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
