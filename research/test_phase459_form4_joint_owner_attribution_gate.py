import unittest

from research.phase459_form4_joint_owner_attribution_gate import audit_ownership_xml


def xml(body: str) -> str:
    return f"<ownershipDocument>{body}</ownershipDocument>"


def owner(cik: str) -> str:
    return f"<reportingOwner><reportingOwnerId><rptOwnerCik>{cik}</rptOwnerCik></reportingOwnerId></reportingOwner>"


def tx(extra: str = "", tag: str = "nonDerivativeTransaction") -> str:
    return f"<{tag}><transactionAmounts><transactionShares><value>100</value></transactionShares></transactionAmounts>{extra}</{tag}>"


class Phase459Tests(unittest.TestCase):
    def test_single_owner_is_attributed_at_filing_grain(self):
        result = audit_ownership_xml(xml(owner("123") + tx()))
        self.assertEqual(result["disposition"], "single_owner_filing")
        self.assertEqual(result["line_assignments"][0]["owner_cik"], "0000000123")
        self.assertTrue(result["owner_breadth_eligible"])

    def test_multi_owner_without_line_reference_is_quarantined(self):
        result = audit_ownership_xml(xml(owner("123") + owner("456") + tx()))
        self.assertEqual(result["disposition"], "quarantine_unresolved_owner_attribution")
        self.assertIsNone(result["line_assignments"][0]["owner_cik"])
        self.assertFalse(result["owner_breadth_eligible"])

    def test_signature_count_does_not_assign_owner(self):
        body = owner("123") + owner("456") + tx()
        body += "<ownerSignature><signatureName>Signer A</signatureName></ownerSignature>"
        body += "<ownerSignature><signatureName>Signer B</signatureName></ownerSignature>"
        result = audit_ownership_xml(xml(body))
        self.assertEqual(result["owner_signature_count_diagnostic_only"], 2)
        self.assertEqual(result["disposition"], "quarantine_unresolved_owner_attribution")
        self.assertFalse(result["signature_count_used_for_attribution"])

    def test_explicit_unique_line_reference_can_be_attributed(self):
        body = owner("123") + owner("456") + tx("<reportingOwnerCik>0000000456</reportingOwnerCik>")
        result = audit_ownership_xml(xml(body))
        self.assertEqual(result["disposition"], "explicit_line_owner_mapping")
        self.assertEqual(result["line_assignments"][0]["owner_cik"], "0000000456")

    def test_unknown_line_reference_fails_closed(self):
        body = owner("123") + owner("456") + tx("<reportingOwnerCik>999</reportingOwnerCik>")
        result = audit_ownership_xml(xml(body))
        self.assertEqual(result["line_assignments"][0]["status"], "unresolved_or_nonunique_owner_reference")
        self.assertFalse(result["owner_breadth_eligible"])

    def test_multiple_line_references_are_ambiguous(self):
        refs = "<reportingOwnerCik>123</reportingOwnerCik><reportingOwnerCik>456</reportingOwnerCik>"
        result = audit_ownership_xml(xml(owner("123") + owner("456") + tx(refs)))
        self.assertIsNone(result["line_assignments"][0]["owner_cik"])
        self.assertFalse(result["owner_breadth_eligible"])

    def test_derivative_and_nonderivative_lines_are_both_checked(self):
        body = owner("123") + tx() + tx(tag="derivativeTransaction")
        result = audit_ownership_xml(xml(body))
        self.assertEqual(result["transaction_line_count"], 2)
        self.assertEqual(result["uniquely_attributed_line_count"], 2)

    def test_duplicate_owner_cik_is_rejected(self):
        with self.assertRaises(ValueError):
            audit_ownership_xml(xml(owner("123") + owner("0000000123") + tx()))

    def test_namespaced_xml_is_supported(self):
        body = owner("123") + tx()
        result = audit_ownership_xml(
            '<ownershipDocument xmlns="urn:sec:ownership">' + body + "</ownershipDocument>"
        )
        self.assertEqual(result["disposition"], "single_owner_filing")


if __name__ == "__main__":
    unittest.main()
