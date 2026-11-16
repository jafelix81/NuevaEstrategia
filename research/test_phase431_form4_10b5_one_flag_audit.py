import io
import unittest
import zipfile

from research.phase431_form4_10b5_one_flag_audit import normalize_aff10b5one, summarize_period


def make_inner_zip(submission_header, submission_rows, transaction_rows):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("SUBMISSION.tsv", submission_header + "\n" + "\n".join(submission_rows) + "\n")
        archive.writestr("NONDERIV_TRANS.tsv", "ACCESSION_NUMBER\tTRANS_CODE\n" + "\n".join(transaction_rows) + "\n")
    return buffer.getvalue()


class Phase431Tests(unittest.TestCase):
    def test_normalizes_source_variants_without_coercing_unknown(self):
        self.assertEqual(normalize_aff10b5one("1"), "checked")
        self.assertEqual(normalize_aff10b5one("true"), "checked")
        self.assertEqual(normalize_aff10b5one("0"), "unchecked")
        self.assertEqual(normalize_aff10b5one("false"), "unchecked")
        self.assertEqual(normalize_aff10b5one(""), "unknown")
        self.assertEqual(normalize_aff10b5one(None), "unknown")
        self.assertEqual(normalize_aff10b5one("unexpected"), "unrecognized")

    def test_missing_historical_field_is_not_false(self):
        header = "ACCESSION_NUMBER\tDOCUMENT_TYPE"
        rows = ["a\t4", "b\t4/A"]
        result = summarize_period(make_inner_zip(header, rows, []), "2012Q1")
        self.assertFalse(result["submission_has_AFF10B5ONE"])
        self.assertEqual(result["form4_and_4a_flag_counts"]["unknown"], 2)
        self.assertEqual(result["form4_and_4a_flag_counts"]["unchecked"], 0)

    def test_flag_is_accession_level_and_mixed_codes_are_visible(self):
        header = "ACCESSION_NUMBER\tDOCUMENT_TYPE\tAFF10B5ONE"
        rows = ["a\t4\t1", "b\t4\t0", "c\t4\ttrue"]
        tx = ["a\tP", "a\tS", "b\tP", "c\tS"]
        result = summarize_period(make_inner_zip(header, rows, tx), "fixture")
        self.assertEqual(result["form4_and_4a_flag_counts"]["checked"], 2)
        self.assertEqual(result["checked_form4_with_multiple_transaction_codes"], 1)
        self.assertEqual(result["checked_form4_with_P_and_other_codes"], 1)
        self.assertEqual(result["transaction_code_stats"]["P"]["filing_flag_counts"]["checked"], 1)
        self.assertEqual(result["transaction_code_stats"]["S"]["filing_flag_counts"]["checked"], 2)

    def test_excludes_form5_transactions_from_form4_feature_counts(self):
        header = "ACCESSION_NUMBER\tDOCUMENT_TYPE\tAFF10B5ONE"
        rows = ["a\t4\t0", "b\t5\t"]
        tx = ["a\tP", "b\tP"]
        result = summarize_period(make_inner_zip(header, rows, tx), "fixture")
        self.assertEqual(result["transaction_code_stats"]["P"]["transaction_rows"], 1)
        self.assertEqual(result["non_form4_P_or_S_transaction_rows_excluded"]["P"], 1)

    def test_unrecognized_flag_is_not_unchecked(self):
        header = "ACCESSION_NUMBER\tDOCUMENT_TYPE\tAFF10B5ONE"
        rows = ["a\t4\tmaybe"]
        result = summarize_period(make_inner_zip(header, rows, []), "fixture")
        self.assertEqual(result["form4_and_4a_flag_counts"]["unrecognized"], 1)
        self.assertEqual(result["form4_and_4a_flag_counts"]["unchecked"], 0)


if __name__ == "__main__":
    unittest.main()
