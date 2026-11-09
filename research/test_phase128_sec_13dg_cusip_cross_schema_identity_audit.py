import unittest

from research.phase128_sec_13dg_cusip_cross_schema_identity_audit import (
    source_mix, cross_schema_identity_match, same_body_name_different_header_cik,
    is_obvious_body_name_contamination,
)


class Phase128Tests(unittest.TestCase):
    def test_legacy_only_source_mix(self):
        self.assertEqual(source_mix(["LEGACY_HTML_EXACT_TOKEN", "LEGACY_HTML_EXACT_TOKEN"]), "LEGACY_ONLY")

    def test_xml_only_source_mix(self):
        self.assertEqual(source_mix(["13DG_XML"]), "XML_ONLY")

    def test_cross_schema_source_mix(self):
        self.assertEqual(source_mix(["LEGACY_HTML_EXACT_TOKEN", "13DG_XML"]), "CROSS_SCHEMA")

    def test_cross_schema_identity_requires_same_cik_and_name(self):
        legacy = [{"header_subject_cik": "0001522727", "body_issuer_name": "USA Compression Partners, LP"}]
        xml = [{"xml_issuer_cik": "1522727", "xml_issuer_name": "USA Compression Partners LP"}]
        self.assertTrue(cross_schema_identity_match(legacy, xml))

    def test_cross_schema_identity_rejects_cik_conflict(self):
        legacy = [{"header_subject_cik": "0001549575", "body_issuer_name": "Seritage Growth Properties"}]
        xml = [{"xml_issuer_cik": "1628063", "xml_issuer_name": "Seritage Growth Properties"}]
        self.assertFalse(cross_schema_identity_match(legacy, xml))

    def test_cross_schema_identity_rejects_name_conflict(self):
        legacy = [{"header_subject_cik": "1522727", "body_issuer_name": "Different Company"}]
        xml = [{"xml_issuer_cik": "1522727", "xml_issuer_name": "USA Compression Partners LP"}]
        self.assertFalse(cross_schema_identity_match(legacy, xml))

    def test_same_body_name_with_multiple_header_ciks_is_flagged(self):
        rows = [
            {"header_subject_cik": "1549575", "body_issuer_name": "Seritage Growth Properties"},
            {"header_subject_cik": "1628063", "body_issuer_name": "Seritage Growth Properties"},
        ]
        self.assertTrue(same_body_name_different_header_cik(rows))

    def test_separator_and_boilerplate_candidates_are_rejected(self):
        self.assertTrue(is_obvious_body_name_contamination("-----------------------"))
        self.assertTrue(is_obvious_body_name_contamination("SECURITIES & EXCHANGE COMMISSION On Holding AG"))
        self.assertTrue(is_obvious_body_name_contamination("1934 Infoblox, Inc."))
        self.assertTrue(is_obvious_body_name_contamination("Converted by EDGARwiz JAYHAWK ENERGY, INC."))

    def test_clean_candidate_is_not_obvious_contamination(self):
        self.assertFalse(is_obvious_body_name_contamination("USA Compression Partners, LP"))


if __name__ == "__main__":
    unittest.main()
