from __future__ import annotations

import unittest

from research.phase352_sec_13dg_identity_security_crosswalk import (
    cik_overlap,
    cusip_status,
    extract_header_fields,
    extract_primary_cusips,
    extract_structured_reporting_person_names,
    name_overlap,
    normalize_cik,
    normalize_name,
)


class Phase352NormalizationTests(unittest.TestCase):
    def test_cik_normalization(self):
        self.assertEqual(normalize_cik("0000723612"), "723612")

    def test_name_normalization(self):
        self.assertEqual(normalize_name("Goldman Sachs & Co. LLC"), "GOLDMANSACHSCO LLC".replace(" ", ""))

    def test_cik_overlap_requires_child_ciks(self):
        self.assertEqual(cik_overlap("769993", []), "CHILD_REPORTING_PERSON_CIK_UNAVAILABLE")
        self.assertEqual(cik_overlap("0000769993", ["769993", "123"]), "OVERLAP")
        self.assertEqual(cik_overlap("723612", ["769993"]), "NO_OVERLAP")


class Phase352DocumentParsingTests(unittest.TestCase):
    def test_extract_subject_and_filed_by_header_identity(self):
        raw = """<SEC-HEADER>
SUBJECT COMPANY:
 COMPANY DATA:
  COMPANY CONFORMED NAME: AVIS BUDGET GROUP INC
  CENTRAL INDEX KEY: 0000723612
FILED BY:
 COMPANY DATA:
  COMPANY CONFORMED NAME: GOLDMAN SACHS & CO LLC
  CENTRAL INDEX KEY: 0000769993
</SEC-HEADER>"""
        result = extract_header_fields(raw)
        self.assertEqual(result["parent_subject_cik"], "723612")
        self.assertEqual(result["parent_filed_by_cik"], "769993")
        self.assertEqual(result["parent_filed_by_name"], "GOLDMAN SACHS & CO LLC")

    def test_extract_xml_issuer_cusip(self):
        raw = "<root><issuerCUSIP>053774105</issuerCUSIP></root>"
        self.assertEqual(extract_primary_cusips(raw), ["053774105"])

    def test_extract_html_cusip_with_space(self):
        raw = "<html><body>CUSIP NO. 46131T 507</body></html>"
        self.assertEqual(extract_primary_cusips(raw), ["46131T507"])

    def test_extract_structured_reporting_person_names(self):
        raw = "<root><reportingPersonName>THE GOLDMAN SACHS GROUP, INC.</reportingPersonName><reportingPersonName>GOLDMAN SACHS &amp; CO. LLC</reportingPersonName></root>"
        names = extract_structured_reporting_person_names(raw)
        self.assertIn("THEGOLDMANSACHSGROUPINC", names)
        self.assertIn("GOLDMANSACHSCO LLC".replace(" ", ""), names)


class Phase352ContinuityTests(unittest.TestCase):
    def test_cusip_statuses(self):
        self.assertEqual(cusip_status("053774105", ["053774105"]), "MATCH")
        self.assertEqual(cusip_status("053774105", ["111111111"]), "MISMATCH")
        self.assertEqual(cusip_status("053774105", []), "PARENT_CUSIP_MISSING")
        self.assertEqual(cusip_status("000000000", ["000000000"]), "CHILD_CUSIP_INVALID")
        self.assertEqual(cusip_status("053774105", [], parent_retrieved=False), "UNRESOLVED_PARENT_NOT_RETRIEVED")

    def test_name_overlap_states(self):
        self.assertEqual(name_overlap(["Goldman Sachs Group Inc"], ["THE GOLDMAN SACHS GROUP, INC."]), "EXACT_OVERLAP")
        self.assertEqual(name_overlap(["Goldman Sachs"], ["THE GOLDMAN SACHS GROUP, INC."]), "SUBSTRING_CANDIDATE")
        self.assertEqual(name_overlap(["Other"], ["THE GOLDMAN SACHS GROUP, INC."]), "NO_OVERLAP")
        self.assertEqual(name_overlap([], ["THE GOLDMAN SACHS GROUP, INC."]), "NAME_SET_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
