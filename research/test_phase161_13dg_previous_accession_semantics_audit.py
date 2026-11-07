import unittest

from phase161_13dg_previous_accession_semantics_audit import (
    PREVIOUS_ACCESSION, SAMPLE_ROWS, audit, normalize_accession
)


class Phase161PreviousAccessionSemanticsTests(unittest.TestCase):
    def test_accession_padding_is_canonical(self):
        self.assertEqual(
            normalize_accession("1445546-21-2430"),
            "0001445546-21-002430",
        )

    def test_fixture_has_eight_unique_child_filings(self):
        groups, summary = audit(SAMPLE_ROWS)
        self.assertEqual(summary["valid_unique_child_rows"], 8)
        self.assertEqual(summary["children_with_previous_accession"], 8)

    def test_all_children_reuse_one_previous_accession(self):
        groups, summary = audit(SAMPLE_ROWS)
        self.assertEqual(summary["unique_previous_accessions"], 1)
        self.assertEqual(groups[0]["previous_accession"], PREVIOUS_ACCESSION)
        self.assertEqual(groups[0]["child_count"], 8)

    def test_reused_reference_spans_five_issuer_ciks(self):
        _, summary = audit(SAMPLE_ROWS)
        self.assertEqual(summary["distinct_issuer_cik_count"], 5)

    def test_reused_reference_spans_eight_cusips(self):
        _, summary = audit(SAMPLE_ROWS)
        self.assertEqual(summary["distinct_cusip_count"], 8)

    def test_group_is_cross_issuer_quarantined(self):
        groups, _ = audit(SAMPLE_ROWS)
        self.assertEqual(
            groups[0]["status"],
            "CROSS_ISSUER_REFERENCE_REUSE_QUARANTINE",
        )

    def test_no_parent_is_verified_without_parent_document(self):
        groups, summary = audit(SAMPLE_ROWS)
        self.assertFalse(groups[0]["parent_document_inspected"])
        self.assertFalse(groups[0]["issuer_security_parent_verified"])
        self.assertEqual(summary["issuer_security_parent_verified"], 0)

    def test_same_issuer_multiple_cusips_is_not_security_continuity(self):
        rows = [dict(r) for r in SAMPLE_ROWS if r["issuer_cik"] == "0001667919"][:2]
        groups, _ = audit(rows)
        self.assertEqual(groups[0]["status"], "MULTI_SECURITY_REFERENCE_REUSE_QUARANTINE")

    def test_parent_document_issuer_mismatch_is_rejected(self):
        rows = [dict(SAMPLE_ROWS[0])]
        parent_docs = {
            PREVIOUS_ACCESSION: {
                "issuer_cik": "0000904112",
                "cusips": ["617477104"],
            }
        }
        groups, _ = audit(rows, parent_docs)
        self.assertEqual(groups[0]["status"], "PARENT_DOCUMENT_ISSUER_MISMATCH")
        self.assertFalse(groups[0]["issuer_security_parent_verified"])

    def test_parent_document_cusip_mismatch_is_not_verified(self):
        rows = [dict(SAMPLE_ROWS[0])]
        parent_docs = {
            PREVIOUS_ACCESSION: {
                "issuer_cik": "0001667919",
                "cusips": ["33740F466"],
            }
        }
        groups, _ = audit(rows, parent_docs)
        self.assertEqual(
            groups[0]["status"],
            "PARENT_DOCUMENT_SECURITY_MISMATCH_OR_CUSIP_TRANSITION",
        )

    def test_same_issuer_and_cusip_is_only_a_continuity_candidate(self):
        rows = [dict(SAMPLE_ROWS[0])]
        parent_docs = {
            PREVIOUS_ACCESSION: {
                "issuer_cik": "0001667919",
                "cusips": ["33740F342"],
            }
        }
        groups, _ = audit(rows, parent_docs)
        self.assertEqual(
            groups[0]["status"],
            "PARENT_DOCUMENT_ISSUER_CUSIP_CONTINUITY_CANDIDATE",
        )
        self.assertFalse(groups[0]["issuer_security_parent_verified"])

    def test_missing_previous_accession_is_not_grouped(self):
        rows = [dict(SAMPLE_ROWS[0])]
        rows[0]["previous_accession"] = ""
        groups, summary = audit(rows)
        self.assertEqual(groups, [])
        self.assertEqual(summary["unique_previous_accessions"], 0)

    def test_duplicate_child_accession_is_quarantined(self):
        rows = [dict(SAMPLE_ROWS[0]), dict(SAMPLE_ROWS[0])]
        groups, summary = audit(rows)
        self.assertEqual(summary["valid_unique_child_rows"], 1)
        self.assertEqual(summary["invalid_or_duplicate_child_rows"], 1)
        self.assertEqual(groups[0]["child_count"], 1)

    def test_summary_forbids_economic_or_production_claims(self):
        _, summary = audit(SAMPLE_ROWS)
        self.assertFalse(summary["forward_returns_used"])
        self.assertFalse(summary["final_holdout_used"])
        self.assertFalse(summary["production_changed"])
        self.assertEqual(summary["sample_design"], "TARGETED_NON_RANDOM_PUBLIC_SEC_XML_CONTROL_SET")


if __name__ == "__main__":
    unittest.main()
