import unittest

from research.phase459_form4_joint_owner_attribution_gate import audit_ownership_xml


def xml(body: str) -> str:
    return f"<ownershipDocument>{body}</ownershipDocument>"


def owner(cik: str, extra: str = "") -> str:
    return (
        "<reportingOwner><reportingOwnerId>"
        f"<rptOwnerCik>{cik}</rptOwnerCik>"
        "</reportingOwnerId>"
        f"{extra}</reportingOwner>"
    )


def tx(extra: str = "", tag: str = "nonDerivativeTransaction") -> str:
    return (
        f"<{tag}><transactionAmounts><transactionShares><value>100</value>"
        f"</transactionShares></transactionAmounts>{extra}</{tag}>"
    )


class Phase459Tests(unittest.TestCase):
    def test_single_owner_is_attributed_only_at_filing_grain(self):
        result = audit_ownership_xml(xml(owner("123") + tx()))
        self.assertEqual(result["disposition"], "single_owner_filing_grain_only")
        self.assertEqual(result["line_assignments"][0]["owner_cik"], "0000000123")
        self.assertTrue(result["owner_breadth_eligible"])
        self.assertEqual(result["explicit_line_owner_mapping_count"], 0)

    def test_multi_owner_without_line_reference_is_quarantined(self):
        result = audit_ownership_xml(xml(owner("123") + owner("456") + tx()))
        self.assertEqual(result["disposition"], "quarantine_all_multi_owner_transaction_lines")
        self.assertIsNone(result["line_assignments"][0]["owner_cik"])
        self.assertFalse(result["owner_breadth_eligible"])

    def test_signature_count_does_not_assign_owner(self):
        body = owner("123") + owner("456") + tx()
        body += "<ownerSignature><signatureName>Signer A</signatureName></ownerSignature>"
        body += "<ownerSignature><signatureName>Signer B</signatureName></ownerSignature>"
        result = audit_ownership_xml(xml(body))
        self.assertEqual(result["owner_signature_count_diagnostic_only"], 2)
        self.assertEqual(result["disposition"], "quarantine_all_multi_owner_transaction_lines")
        self.assertFalse(result["signature_count_used_for_attribution"])

    def test_unverified_reference_like_tag_cannot_assign_owner(self):
        body = owner("123") + owner("456") + tx(
            "<reportingOwnerCik>0000000456</reportingOwnerCik>"
        )
        result = audit_ownership_xml(xml(body))
        self.assertIsNone(result["line_assignments"][0]["owner_cik"])
        self.assertEqual(result["explicit_line_owner_mapping_count"], 0)
        self.assertEqual(
            result["line_assignments"][0]["status"],
            "multi_owner_line_quarantined",
        )
        self.assertEqual(result["unverified_owner_reference_tags_seen"], ["reportingOwnerCik"])

    def test_owner_cik_nested_inside_transaction_is_not_counted_as_owner_block(self):
        body = owner("123") + owner("456") + tx(
            "<rptOwnerCik>0000000456</rptOwnerCik>"
        )
        result = audit_ownership_xml(xml(body))
        self.assertEqual(result["reporting_owner_count"], 2)
        self.assertIsNone(result["line_assignments"][0]["owner_cik"])

    def test_derivative_and_nonderivative_lines_are_both_quarantined(self):
        body = owner("123") + owner("456") + tx() + tx(tag="derivativeTransaction")
        result = audit_ownership_xml(xml(body))
        self.assertEqual(result["transaction_line_count"], 2)
        self.assertEqual(result["uniquely_attributed_line_count"], 0)
        self.assertEqual(result["ambiguous_line_count"], 2)

    def test_duplicate_owner_cik_is_rejected(self):
        with self.assertRaises(ValueError):
            audit_ownership_xml(xml(owner("123") + owner("0000000123") + tx()))

    def test_namespaced_xml_is_supported(self):
        body = owner("123") + tx()
        result = audit_ownership_xml(
            '<ownershipDocument xmlns="urn:sec:ownership">' + body + "</ownershipDocument>"
        )
        self.assertEqual(result["disposition"], "single_owner_filing_grain_only")

    def test_current_x0609_multi_owner_shape_is_quarantined(self):
        body = (
            "<schemaVersion>X0609</schemaVersion>"
            "<issuer><issuerForeignTradingSymbol></issuerForeignTradingSymbol></issuer>"
            + owner("1305473", "<reportingOwnerAddress><rptOwnerNonUSAddressFlag>false</rptOwnerNonUSAddressFlag></reportingOwnerAddress>")
            + owner("2133811", "<reportingOwnerAddress><rptOwnerNonUSAddressFlag>false</rptOwnerNonUSAddressFlag></reportingOwnerAddress>")
            + "<aff10b5One>0</aff10b5One>"
            + "<nonDerivativeTable>" + tx() + "</nonDerivativeTable>"
        )
        result = audit_ownership_xml(xml(body))
        self.assertEqual(result["schema_version"], "X0609")
        self.assertEqual(result["reporting_owner_count"], 2)
        self.assertEqual(result["disposition"], "quarantine_all_multi_owner_transaction_lines")
        self.assertEqual(result["schema_reference_gate"], "NOT_VERIFIED_FAIL_CLOSED")

    def test_no_reporting_owner_fails_closed(self):
        result = audit_ownership_xml(xml(tx()))
        self.assertEqual(result["disposition"], "no_reporting_owner")
        self.assertFalse(result["owner_breadth_eligible"])

    def test_no_transaction_lines_fails_closed(self):
        result = audit_ownership_xml(xml(owner("123")))
        self.assertEqual(result["disposition"], "no_transaction_lines")
        self.assertFalse(result["owner_breadth_eligible"])


if __name__ == "__main__":
    unittest.main()
