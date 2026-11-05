import unittest
from phase118_sec_13dg_phase84_adjudication import (
    classify_form_relationship,
    is_13dg_form,
    parse_submission,
    parse_sec_acceptance_utc,
)


class Phase118Tests(unittest.TestCase):
    def test_recognizes_13dg_forms(self):
        for form in ("SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"):
            self.assertTrue(is_13dg_form(form))
        self.assertFalse(is_13dg_form("SC TO-T/A"))

    def test_parses_sec_header_and_document_types(self):
        raw = """<SEC-HEADER>\nCONFORMED SUBMISSION TYPE:\tSC TO-T/A\n</SEC-HEADER>\n<DOCUMENT>\n<TYPE>SC TO-T/A\n</DOCUMENT>\n<DOCUMENT>\n<TYPE>EX-99.(A)(5)(B)\n</DOCUMENT>"""
        form, docs = parse_submission(raw)
        self.assertEqual(form, "SC TO-T/A")
        self.assertEqual(docs, ["SC TO-T/A", "EX-99.(A)(5)(B)"])

    def test_index_only_13dg_alias_is_quarantined(self):
        docs = ["SC TO-T/A", "EX-99.(A)(5)(B)"]
        self.assertEqual(
            classify_form_relationship("SC 13D/A", "SC TO-T/A", docs),
            "index_alias_non_13dg",
        )

    def test_true_13dg_document_conflict_is_not_quarantined(self):
        docs = ["SC 13D/A", "EX-99"]
        self.assertEqual(
            classify_form_relationship("SC 13D/A", "SC TO-T/A", docs),
            "unresolved_form_conflict",
        )

    def test_acceptance_timestamp_is_recomputed_in_new_york_timezone(self):
        raw = "<SEC-HEADER>\n<ACCEPTANCE-DATETIME>20260507172214\n</SEC-HEADER>"
        dt = parse_sec_acceptance_utc(raw)
        self.assertEqual(dt.isoformat(), "2026-05-07T21:22:14+00:00")

    def test_missing_acceptance_timestamp_is_rejected(self):
        self.assertIsNone(parse_sec_acceptance_utc("<SEC-HEADER>\n</SEC-HEADER>"))

    def test_exact_form_match_passes(self):
        self.assertEqual(
            classify_form_relationship("SC 13G/A", "SC 13G/A", ["SC 13G/A"]),
            "match",
        )


if __name__ == "__main__":
    unittest.main()
