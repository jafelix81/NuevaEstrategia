import unittest
import xml.etree.ElementTree as ET
from research.phase119_sec_13dg_xml_lineage_audit import (
    family_for_form, norm_cik, parse_persons, group_signature,
    validate_previous_link, security_key,
)


class Phase119Tests(unittest.TestCase):
    def test_form_family_normalizes_schedule_alias(self):
        self.assertEqual(family_for_form("SC 13D/A"), "13D")
        self.assertEqual(family_for_form("SCHEDULE 13G"), "13G")
        self.assertIsNone(family_for_form("SC TO-T/A"))

    def test_cik_zero_padding(self):
        self.assertEqual(norm_cik("1910592"), "0001910592")

    def test_13d_and_13g_person_nodes_use_separate_schemas(self):
        d = ET.fromstring("""<root><reportingPersonInfo><reportingPersonCIK>123</reportingPersonCIK><reportingPersonName>Person D</reportingPersonName><percentOfClass>6</percentOfClass><aggregateAmountOwned>100</aggregateAmountOwned></reportingPersonInfo></root>""")
        g = ET.fromstring("""<root><coverPageHeaderReportingPersonDetails><reportingPersonName>Person G</reportingPersonName><classPercent>7</classPercent><reportingPersonBeneficiallyOwnedAggregateNumberOfShares>200</reportingPersonBeneficiallyOwnedAggregateNumberOfShares></coverPageHeaderReportingPersonDetails></root>""")
        dp = parse_persons(d, "13D")
        gp = parse_persons(g, "13G")
        self.assertEqual(dp[0]["cik"], "0000000123")
        self.assertEqual(dp[0]["percent"], "6")
        self.assertIsNone(gp[0]["cik"])
        self.assertEqual(gp[0]["percent"], "7")
        self.assertEqual(gp[0]["amount"], "200")

    def test_previous_link_requires_all_identity_and_time_checks(self):
        current = {"family":"13G", "issuer_cik":"0000000001", "filer_cik":"0000000002", "filing_date":"2025-11-10"}
        good = [{"cik":"0000000001","form":"SCHEDULE 13G","date":"2025-08-12"},
                {"cik":"0000000002","form":"SCHEDULE 13G","date":"2025-08-12"}]
        self.assertTrue(validate_previous_link(current, good)["validated"])
        bad = [{"cik":"0000000001","form":"SCHEDULE 13G","date":"2025-11-12"}]
        self.assertFalse(validate_previous_link(current, bad)["validated"])

    def test_group_signature_uses_reporting_persons_and_filer(self):
        d = {"family":"13D", "filer_cik":"0000000002", "persons":[{"cik":"0000000002","name":"Person D"}]}
        g = {"family":"13G", "filer_cik":"0000000002", "persons":[{"cik":None,"name":"Person G"}]}
        self.assertIn("CIK:0000000002", group_signature(d))
        self.assertIn("FILER:0000000002", group_signature(g))

    def test_security_key_prevents_cross_class_group_merge(self):
        a = {"issuer_cusip":"464287457", "class_title":"Common Stock"}
        b = {"issuer_cusip":"46435G672", "class_title":"Common Stock"}
        self.assertNotEqual(security_key(a), security_key(b))


if __name__ == "__main__":
    unittest.main()
