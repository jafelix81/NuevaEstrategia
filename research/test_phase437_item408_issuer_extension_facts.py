"""Phase 437 tests for issuer-specific Item 408 XBRL extensions."""
from __future__ import annotations

import unittest

from research.phase433_item408_ixbrl_parser import extract_item408_facts
from research.test_phase433_item408_ixbrl_parser import FIXTURE


CUSTOM_FIXTURE = (
    FIXTURE
    .replace(
        'xmlns:ecd="http://xbrl.sec.gov/ecd/2026"',
        'xmlns:ecd="http://xbrl.sec.gov/ecd/2026" '
        'xmlns:carg="http://xbrl.sec.gov/carg/2024"',
    )
    .replace(
        '<xbrldi:explicitMember dimension="ecd:TradingArrAxis">'
        'now:WilliamRMcDermottRuleTradingArrangementCommonStockMember'
        '</xbrldi:explicitMember>',
        '<xbrldi:explicitMember dimension="ecd:TradingArrAxis">'
        'now:WilliamRMcDermottRuleTradingArrangementCommonStockMember'
        '</xbrldi:explicitMember>'
        '<xbrldi:explicitMember dimension="carg:IndividualAxis">'
        'carg:MatthewQuinnMember</xbrldi:explicitMember>',
    )
    .replace(
        '</body></html>',
        '<ix:nonNumeric name="carg:Rule10B51ArrModifiedFlag" '
        'contextRef="c_william_a">false</ix:nonNumeric>'
        '<ix:nonNumeric name="carg:TrdArrExpirationDate" '
        'contextRef="c_william_b">2025-03-03</ix:nonNumeric>'
        '<ix:nonNumeric name="carg:Revenue" '
        'contextRef="c_william_a">not an Item 408 extension</ix:nonNumeric>'
        '<ix:nonNumeric name="ecd:Rule10b51ArrModifiedFlag" '
        'contextRef="c_william_a">false</ix:nonNumeric>'
        '</body></html>',
    )
)


class Phase437IssuerExtensionTests(unittest.TestCase):
    def setUp(self):
        self.result = extract_item408_facts(
            CUSTOM_FIXTURE,
            accession="0000950170-24-056957",
            issuer_cik="1494259",
        )

    def test_standard_and_issuer_extension_facts_are_separate(self):
        self.assertEqual(self.result["standard_fact_count"], 12)
        self.assertEqual(self.result["issuer_extension_fact_count"], 2)
        self.assertEqual(self.result["item408_fact_count"], 14)

    def test_custom_lifecycle_and_expiration_facts_are_preserved(self):
        facts = self.result["issuer_extension_facts"]
        concepts = {fact["concept"] for fact in facts}
        self.assertEqual(
            concepts,
            {"Rule10B51ArrModifiedFlag", "TrdArrExpirationDate"},
        )

    def test_custom_false_flag_is_preserved_not_dropped(self):
        fact = next(
            f for f in self.result["issuer_extension_facts"]
            if f["concept"] == "Rule10B51ArrModifiedFlag"
        )
        self.assertEqual(fact["value"], "false")
        self.assertEqual(fact["taxonomy_prefix"], "carg")
        self.assertEqual(fact["taxonomy_namespace"], "http://xbrl.sec.gov/carg/2024")

    def test_custom_dimensions_are_preserved_on_extension_fact(self):
        fact = next(
            f for f in self.result["issuer_extension_facts"]
            if f["concept"] == "Rule10B51ArrModifiedFlag"
        )
        self.assertEqual(
            fact["dimensions"]["carg:IndividualAxis"][0]["member"],
            "carg:MatthewQuinnMember",
        )

    def test_standard_ecd_modified_flag_is_recognized(self):
        standard = [
            f for f in self.result["facts"]
            if f["concept"] == "Rule10b51ArrModifiedFlag"
        ]
        self.assertEqual(len(standard), 1)
        self.assertEqual(standard[0]["value"], "false")

    def test_unrelated_issuer_extension_is_not_swept_in(self):
        concepts = {f["concept"] for f in self.result["issuer_extension_facts"]}
        self.assertNotIn("Revenue", concepts)

    def test_extension_only_document_is_not_misclassified_as_no_facts(self):
        self.assertEqual(self.result["extraction_status"], "facts_found")

    def test_original_ecd_facts_remain_dimension_preserving(self):
        self.assertEqual(
            len([f for f in self.result["facts"] if f["concept"] == "TrdArrIndName"]),
            2,
        )


if __name__ == "__main__":
    unittest.main()
