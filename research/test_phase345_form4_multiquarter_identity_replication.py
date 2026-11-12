from __future__ import annotations

import unittest

from research.phase345_form4_multiquarter_identity_replication import (
    candidate_key, regime_required, verify_candidate_row_regime_aware,
)


def candidate(filing_date="15-MAR-2012", required=False):
    return {
        "accession": "0000000001-12-000001",
        "filing_date": filing_date,
        "transaction_date": "14-MAR-2012",
        "security_title": "Common Stock",
        "transaction_shares": "100.0",
        "transaction_price_per_share": "10.00",
        "transaction_code": "P",
        "direct_or_indirect": "D",
        "acquired_disposed": "A",
        "aff_gate_required": required,
        "aff10b5one": "unknown" if not required else "false",
    }


def xml_row(price="10.0000"):
    return {
        "transaction_kind": "NON_DERIVATIVE",
        "security_title": "Common Stock",
        "transaction_date": "2012-03-14",
        "transaction_code": "P",
        "direct_or_indirect": "D",
        "acquired_disposed": "A",
        "shares": "100",
        "price_per_share": price,
        "transaction_index": 1,
    }


def evidence():
    return (
        [xml_row()],
        {("NON_DERIVATIVE", 1): {"nature": ""}},
        {1: {"footnote_ids": ["F1"], "missing_footnote_ids": [],
             "footnote_texts": ["Purchase of shares in open market transaction."]}},
    )


class Phase345Tests(unittest.TestCase):
    def test_pre_effective_missing_checkbox_is_not_treated_as_false(self):
        row = candidate("15-MAR-2012", False)
        self.assertFalse(regime_required(row))
        xml, raw, footnotes = evidence()
        checked = verify_candidate_row_regime_aware(row, xml, raw, footnotes, 1, "")
        self.assertEqual(checked["xml_match_status"], "UNIQUE_EXACT_TRANSACTION_ROW")
        self.assertTrue(checked["aff_gate_required"])
        self.assertTrue(checked["raw_purchase_screen_pass"])
        self.assertEqual(checked["aff_status_as_filed"], "unknown")

    def test_checkbox_gate_begins_on_actual_effective_date(self):
        self.assertTrue(regime_required(candidate("01-APR-2023", True)))
        self.assertTrue(regime_required(candidate("03-APR-2023", True)))
        self.assertFalse(regime_required(candidate("31-MAR-2023", False)))

    def test_post_effective_unknown_checkbox_fails_closed(self):
        row = candidate("03-APR-2023", True)
        xml, raw, footnotes = evidence()
        checked = verify_candidate_row_regime_aware(row, xml, raw, footnotes, 1, "")
        self.assertFalse(checked["raw_purchase_screen_pass"])
        self.assertFalse(checked["raw_purchase_screen_flags"]["aff_gate"])

    def test_post_effective_explicit_false_checkbox_passes(self):
        row = candidate("03-APR-2023", True)
        xml, raw, footnotes = evidence()
        checked = verify_candidate_row_regime_aware(row, xml, raw, footnotes, 1, "false")
        self.assertTrue(checked["raw_purchase_screen_pass"])
        self.assertEqual(checked["aff_status_as_filed"], "false")

    def test_regime_flag_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "aff10b5one_regime_mismatch"):
            regime_required(candidate("03-APR-2023", False))

    def test_missing_referenced_footnote_never_passes_open_market_screen(self):
        row = candidate("15-MAR-2012", False)
        xml, raw, footnotes = evidence()
        footnotes[1]["missing_footnote_ids"] = ["F2"]
        checked = verify_candidate_row_regime_aware(row, xml, raw, footnotes, 1, "")
        self.assertFalse(checked["raw_purchase_screen_pass"])
        self.assertFalse(checked["raw_purchase_screen_flags"]["explicit_open_market"])

    def test_bulk_and_xml_price_precision_normalize_to_same_key(self):
        row = candidate("15-MAR-2012", False)
        self.assertEqual(candidate_key(row), candidate_key({
            **row, "transaction_date": "2012-03-14",
            "transaction_price_per_share": "10.004",
            "transaction_shares": "100.0000",
        }))


if __name__ == "__main__":
    unittest.main()
