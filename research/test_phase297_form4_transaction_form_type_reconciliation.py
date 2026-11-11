import io
import unittest
import zipfile
from datetime import date

from research.phase297_form4_transaction_form_type_reconciliation import (
    analyze_period, high_precision_flags, normalize_aff, parse_date,
    phase296_candidate, referenced_footnote_text,
)


def make_inner_archive():
    submissions = [
        {"ACCESSION_NUMBER": "0000000001-26-000001", "DOCUMENT_TYPE": "4",
         "FILING_DATE": "01-MAY-2026", "ISSUERCIK": "0000000001", "AFF10B5ONE": "false"},
        {"ACCESSION_NUMBER": "0000000002-26-000001", "DOCUMENT_TYPE": "4",
         "FILING_DATE": "01-MAY-2026", "ISSUERCIK": "0000000002", "AFF10B5ONE": "false"},
    ]
    owners = [
        {"ACCESSION_NUMBER": "0000000001-26-000001", "RPTOWNERCIK": "0000000101"},
        {"ACCESSION_NUMBER": "0000000002-26-000001", "RPTOWNERCIK": "0000000102"},
        {"ACCESSION_NUMBER": "0000000002-26-000001", "RPTOWNERCIK": "0000000103"},
    ]
    transactions = [
        {"ACCESSION_NUMBER": "0000000001-26-000001", "TRANS_FORM_TYPE": "4",
         "TRANS_CODE": "P", "TRANS_ACQUIRED_DISP_CD": "A", "DIRECT_INDIRECT_OWNERSHIP": "D",
         "TRANS_SHARES": "10", "TRANS_PRICEPERSHARE": "5", "TRANS_DATE": "30-APR-2026",
         "SECURITY_TITLE": "Common Stock", "TRANS_SHARES_FN": "F1"},
        {"ACCESSION_NUMBER": "0000000001-26-000001", "TRANS_FORM_TYPE": "5",
         "TRANS_CODE": "P", "TRANS_ACQUIRED_DISP_CD": "A", "DIRECT_INDIRECT_OWNERSHIP": "D",
         "TRANS_SHARES": "5", "TRANS_PRICEPERSHARE": "4", "TRANS_DATE": "30-APR-2026",
         "SECURITY_TITLE": "Common Stock", "TRANS_SHARES_FN": "F2"},
        {"ACCESSION_NUMBER": "0000000002-26-000001", "TRANS_FORM_TYPE": "4",
         "TRANS_CODE": "P", "TRANS_ACQUIRED_DISP_CD": "A", "DIRECT_INDIRECT_OWNERSHIP": "D",
         "TRANS_SHARES": "20", "TRANS_PRICEPERSHARE": "6", "TRANS_DATE": "30-APR-2026",
         "SECURITY_TITLE": "Common Stock", "TRANS_SHARES_FN": ""},
    ]
    footnotes = [
        {"ACCESSION_NUMBER": "0000000001-26-000001", "FOOTNOTE_ID": "F1",
         "FOOTNOTE_TXT": "Purchased in the open market."},
        {"ACCESSION_NUMBER": "0000000001-26-000001", "FOOTNOTE_ID": "F2",
         "FOOTNOTE_TXT": "Purchased in the open market."},
    ]

    def write_table(zf, name, rows):
        fields = sorted({key for row in rows for key in row})
        import csv
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        zf.writestr(name, buf.getvalue())

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        write_table(zf, "SUBMISSION.tsv", submissions)
        write_table(zf, "REPORTINGOWNER.tsv", owners)
        write_table(zf, "NONDERIV_TRANS.tsv", transactions)
        write_table(zf, "FOOTNOTES.tsv", footnotes)
    return out.getvalue(), transactions, submissions


class Phase297Tests(unittest.TestCase):
    def test_parse_date_accepts_both_sec_date_formats(self):
        self.assertEqual(parse_date("31-MAR-2006"), date(2006, 3, 31))
        self.assertEqual(parse_date("2026-05-01"), date(2026, 5, 1))
        self.assertIsNone(parse_date("not-a-date"))

    def test_aff_unknown_is_not_false(self):
        self.assertEqual(normalize_aff(None), "unknown")
        self.assertEqual(normalize_aff(""), "unknown")
        self.assertEqual(normalize_aff("false"), "false")
        self.assertEqual(normalize_aff("1"), "true")

    def test_transaction_form_type_five_is_excluded_from_corrected_table_i_cohort(self):
        _, transactions, submissions = make_inner_archive()
        broad, corrected, lag = phase296_candidate(transactions[0], submissions[0], 1)
        self.assertTrue(broad)
        self.assertTrue(corrected)
        self.assertEqual(lag, 1)
        broad5, corrected5, _ = phase296_candidate(transactions[1], submissions[0], 1)
        self.assertTrue(broad5)
        self.assertFalse(corrected5)

    def test_aff_gate_uses_actual_filing_date(self):
        tx = {"TRANS_FORM_TYPE": "4", "TRANS_CODE": "P", "TRANS_ACQUIRED_DISP_CD": "A",
              "DIRECT_INDIRECT_OWNERSHIP": "D", "SECURITY_TITLE": "Common Stock",
              "TRANS_SHARES": "1", "TRANS_PRICEPERSHARE": "1"}
        pre = {"DOCUMENT_TYPE": "4", "FILING_DATE": "31-MAR-2023", "AFF10B5ONE": "true"}
        post = {"DOCUMENT_TYPE": "4", "FILING_DATE": "03-APR-2023", "AFF10B5ONE": "true"}
        pre_flags = high_precision_flags(tx, pre, "Open market purchase", 1)
        post_flags = high_precision_flags(tx, post, "Open market purchase", 1)
        self.assertFalse(pre_flags["aff_gate_applicable"])
        self.assertTrue(pre_flags["aff_gate_pass"])
        self.assertTrue(post_flags["aff_gate_applicable"])
        self.assertFalse(post_flags["aff_gate_pass"])

    def test_footnote_reference_parser_handles_multiple_and_missing_ids(self):
        tx = {"TRANS_SHARES_FN": "F1, F2", "TRANS_PRICEPERSHARE_FN": "F3"}
        text, refs, missing = referenced_footnote_text(
            tx, "A", {"A": {"F1": "open market", "F2": "purchase"}}
        )
        self.assertEqual(refs, ["F1", "F2", "F3"])
        self.assertEqual(missing, ["F3"])
        self.assertIn("open market", text)
        self.assertIn("purchase", text)

    def test_end_to_end_type_gate_and_high_precision_screen(self):
        inner, _, _ = make_inner_archive()
        result = analyze_period(inner, "2026Q2")
        rec = result["phase296_reconciliation"]
        self.assertEqual(rec["phase296_original_conservative_rows_without_transaction_form_type_gate"], 2)
        self.assertEqual(rec["corrected_table_i_type4_conservative_rows"], 1)
        self.assertEqual(rec["excluded_transaction_form_type_5_rows"], 1)
        self.assertEqual(result["owner_attribution"]["multiple_owner_accessions"], 1)
        hp = result["high_precision_footnote_screen"]
        self.assertEqual(hp["high_precision_rows_before_positive_price_share_gate"], 1)
        self.assertEqual(hp["positive_price_share_rows_after_all_high_precision_gates"], 1)
        self.assertTrue(hp["aff10b5one_gate_applied_by_actual_filing_date"])
        self.assertEqual(result["source_rows"]["missing_referenced_footnote_ids"], 0)


if __name__ == "__main__":
    unittest.main()
