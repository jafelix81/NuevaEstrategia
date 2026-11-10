import unittest

from research.phase271_form4_open_market_purchase_screen import (
    classify_purchase_row,
    normalize_aff,
)

BASE = {
    "DOCUMENT_TYPE": "4",
    "TRANS_FORM_TYPE": "4",
    "TRANS_CODE": "P",
    "TRANS_ACQUIRED_DISP_CD": "A",
    "SECURITY_TITLE": "Common Stock",
    "DIRECT_INDIRECT_OWNERSHIP": "D",
}


def classify(**kwargs):
    row = dict(BASE)
    row.update(kwargs.pop("row", {}))
    return classify_purchase_row(
        row,
        kwargs.pop("footnote_text", "Open market purchase of common stock."),
        kwargs.pop("owner_count", 1),
        kwargs.pop("aff_value", "false"),
        kwargs.pop("require_known_false", True),
    )


class Phase271Form4OpenMarketScreenTests(unittest.TestCase):
    def test_original_form4_table_i_purchase_is_base(self):
        self.assertTrue(classify()["base"])

    def test_form4_amendment_is_not_base_event(self):
        self.assertFalse(classify(row={"DOCUMENT_TYPE": "4/A"})["base"])

    def test_form5_transaction_inside_form4_is_not_base_event(self):
        self.assertFalse(classify(row={"TRANS_FORM_TYPE": "5"})["base"])

    def test_sale_code_is_not_purchase(self):
        self.assertFalse(classify(row={"TRANS_CODE": "S"})["base"])

    def test_disposed_direction_is_not_purchase(self):
        self.assertFalse(classify(row={"TRANS_ACQUIRED_DISP_CD": "D"})["base"])

    def test_explicit_open_market_phrase_required(self):
        self.assertFalse(classify(footnote_text="Shares acquired pursuant to compensation.")["explicit_open_market"])

    def test_private_wording_is_flagged(self):
        self.assertFalse(classify(footnote_text="Private purchase, not an open-market trade.")["no_private_disclosure"])

    def test_plan_wording_is_flagged(self):
        self.assertFalse(classify(footnote_text="Open market purchases under an employee stock purchase plan.")["no_plan_disclosure"])

    def test_10b5_wording_is_flagged(self):
        self.assertFalse(classify(footnote_text="Open market purchase under Rule 10b5-1 plan.")["no_plan_disclosure"])

    def test_mechanical_compensation_wording_is_flagged(self):
        self.assertFalse(classify(footnote_text="Open market acquisition through employee matching award.")["no_mechanical_disclosure"])

    def test_indirect_ownership_is_excluded(self):
        self.assertFalse(classify(row={"DIRECT_INDIRECT_OWNERSHIP": "I"})["direct_ownership"])

    def test_multiple_reporting_owners_are_excluded(self):
        self.assertFalse(classify(owner_count=2)["single_reporting_owner"])

    def test_non_common_security_title_is_excluded(self):
        self.assertFalse(classify(row={"SECURITY_TITLE": "Preferred Stock"})["common_stock_title"])

    def test_post_checkbox_era_requires_explicit_false(self):
        self.assertTrue(classify(aff_value="0")["aff_gate"])
        self.assertFalse(classify(aff_value="1")["aff_gate"])
        self.assertFalse(classify(aff_value="")["aff_gate"])

    def test_pre_checkbox_era_keeps_plan_status_unknown_not_false(self):
        flags = classify(aff_value="", require_known_false=False)
        self.assertEqual(flags["aff_status"], "unknown")
        self.assertTrue(flags["aff_gate"])

    def test_aff_normalization_handles_sec_encodings(self):
        self.assertEqual(normalize_aff("1"), "true")
        self.assertEqual(normalize_aff("true"), "true")
        self.assertEqual(normalize_aff("0"), "false")
        self.assertEqual(normalize_aff("false"), "false")
        self.assertEqual(normalize_aff(""), "unknown")


if __name__ == "__main__":
    unittest.main()
