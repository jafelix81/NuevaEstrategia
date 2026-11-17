import tempfile
import unittest
from pathlib import Path

from research.phase461_form4_xsd_owner_reference_audit import audit_schema_dir

XS = "http://www.w3.org/2001/XMLSchema"

COMMON = f"""<xs:schema xmlns:xs="{XS}">
  <xs:complexType name="REPORTING_OWNER"><xs:sequence>
    <xs:element name="reportingOwnerId" type="REPORTING_ID"/>
  </xs:sequence></xs:complexType>
  <xs:complexType name="REPORTING_ID"><xs:sequence>
    <xs:element name="rptOwnerCik" type="xs:string"/>
    <xs:element name="rptOwnerName" type="xs:string"/>
  </xs:sequence></xs:complexType>
  <xs:complexType name="OWNERSHIP_NATURE"><xs:sequence>
    <xs:element name="directOrIndirectOwnership" type="xs:string"/>
  </xs:sequence></xs:complexType>
</xs:schema>"""

def form_schema(form4a=False, owner_ref=False, wildcard=False, keyref=False, owner_max="10"):
    extra = '<xs:element name="reportingOwnerCik" type="xs:string"/>' if owner_ref else ""
    any_element = '<xs:any minOccurs="0" maxOccurs="unbounded"/>' if wildcard else ""
    keyref_element = '<xs:keyref name="ownerRef" refer="ownerKey"><xs:selector xpath="."/><xs:field xpath="."/></xs:keyref>' if keyref else ""
    doc_type = "4/A" if form4a else "4"
    return f"""<xs:schema xmlns:xs="{XS}">
      <xs:complexType name="NONDERIVATIVE_TRANSACTION"><xs:sequence>
        <xs:element name="securityTitle" type="xs:string"/>
        <xs:element name="ownershipNature" type="OWNERSHIP_NATURE"/>
        {extra}
      </xs:sequence></xs:complexType>
      <xs:complexType name="DERIVATIVE_TRANSACTION"><xs:sequence>
        <xs:element name="securityTitle" type="xs:string"/>
        <xs:element name="ownershipNature" type="OWNERSHIP_NATURE"/>
      </xs:sequence></xs:complexType>
      <xs:complexType name="NONDERIVATIVE_TABLE"><xs:choice minOccurs="0" maxOccurs="30">
        <xs:element name="nonDerivativeTransaction" type="NONDERIVATIVE_TRANSACTION"/>
      </xs:choice></xs:complexType>
      <xs:complexType name="DERIVATIVE_TABLE"><xs:choice minOccurs="0" maxOccurs="30">
        <xs:element name="derivativeTransaction" type="DERIVATIVE_TRANSACTION"/>
      </xs:choice></xs:complexType>
      <xs:element name="ownershipDocument"><xs:complexType><xs:sequence>
        <xs:element name="documentType" type="xs:string"/>
        <xs:element name="reportingOwner" type="REPORTING_OWNER" minOccurs="1" maxOccurs="{owner_max}"/>
        <xs:element name="nonDerivativeTable" type="NONDERIVATIVE_TABLE" minOccurs="0"/>
        <xs:element name="derivativeTable" type="DERIVATIVE_TABLE" minOccurs="0"/>
        {any_element}
      </xs:sequence></xs:complexType></xs:element>
      {keyref_element}
      <xs:annotation><xs:documentation>Form {doc_type}</xs:documentation></xs:annotation>
    </xs:schema>"""


class Phase461SchemaAuditTests(unittest.TestCase):
    def _audit(self, *, form4=None, form4a=None):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "ownership4Document.xsd.xml").write_text(
                form4 or form_schema(), encoding="utf-8"
            )
            (directory / "ownership4ADocument.xsd.xml").write_text(
                form4a or form_schema(form4a=True), encoding="utf-8"
            )
            (directory / "ownershipDocumentCommon.xsd.xml").write_text(
                COMMON, encoding="utf-8"
            )
            return audit_schema_dir(directory)

    def test_no_transaction_owner_link_and_per_table_caps(self):
        result = self._audit()
        self.assertEqual(result["status"], "NO_SCHEMA_DEFINED_TRANSACTION_TO_OWNER_LINK")
        self.assertEqual(result["transaction_owner_reference_elements"], [])
        self.assertEqual(result["reporting_owner_max_occurs"], "10")
        self.assertEqual(result["nonderivative_table_max_rows"], "30")
        self.assertEqual(result["derivative_table_max_rows"], "30")
        self.assertFalse(result["multi_owner_line_attribution_allowed"])

    def test_owner_reference_in_transaction_requires_manual_review(self):
        result = self._audit(form4=form_schema(owner_ref=True), form4a=form_schema(form4a=True, owner_ref=True))
        self.assertEqual(result["status"], "OWNER_REFERENCE_PRESENT_REQUIRES_MANUAL_REVIEW")
        self.assertEqual(result["transaction_owner_reference_elements"], ["reportingOwnerCik"])
        self.assertFalse(result["multi_owner_line_attribution_allowed"])

    def test_wildcard_fails_closed(self):
        result = self._audit(form4=form_schema(wildcard=True))
        self.assertEqual(result["status"], "NOT_VERIFIED_FAIL_CLOSED")
        self.assertTrue(any("wildcard" in item for item in result["errors"]))

    def test_identity_constraint_fails_closed(self):
        result = self._audit(form4=form_schema(keyref=True))
        self.assertEqual(result["status"], "NOT_VERIFIED_FAIL_CLOSED")
        self.assertTrue(any("identity constraints" in item for item in result["errors"]))

    def test_form4_and_form4a_divergence_fails_closed(self):
        result = self._audit(form4=form_schema(), form4a=form_schema(form4a=True, owner_ref=True))
        self.assertEqual(result["status"], "NOT_VERIFIED_FAIL_CLOSED")
        self.assertTrue(any("differ" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
