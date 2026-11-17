import unittest
from research.phase458_form4_amendment_owner_audit import norm_flag, summarize_period


def submission(acc, doc, filing, orig="", issuer="100", report="2026-07-14", aff=None):
    row = {"ACCESSION_NUMBER": acc, "DOCUMENT_TYPE": doc, "FILING_DATE": filing,
           "DATE_OF_ORIG_SUB": orig, "ISSUERCIK": issuer, "PERIOD_OF_REPORT": report}
    if aff is not None:
        row["AFF10B5ONE"] = aff
    return row


def owner(acc, cik):
    return {"ACCESSION_NUMBER": acc, "RPTOWNERCIK": cik}


def tx(acc, sk, code="P", ad="A", shares="100", date="2026-07-14"):
    return {"ACCESSION_NUMBER": acc, "NONDERIV_TRANS_SK": sk, "SECURITY_TITLE": "Common Stock",
            "TRANS_DATE": date, "TRANS_CODE": code, "TRANS_FORM_TYPE": "4",
            "TRANS_SHARES": shares, "TRANS_PRICEPERSHARE": "10", "TRANS_ACQUIRED_DISP_CD": ad,
            "DIRECT_INDIRECT_OWNERSHIP": "D", "SHRS_OWND_FOLWNG_TRANS": "200"}


class Phase458Tests(unittest.TestCase):
    def test_aff10b5one_normalizes_both_serializations(self):
        self.assertEqual(norm_flag("1"), "yes")
        self.assertEqual(norm_flag("true"), "yes")
        self.assertEqual(norm_flag("0"), "no")
        self.assertEqual(norm_flag("false"), "no")
        self.assertEqual(norm_flag(""), "unknown")

    def test_joint_owner_purchase_is_not_assignable_from_bulk_transaction_row(self):
        subs = [submission("O1", "4", "2026-07-24", aff="0")]
        owners = [owner("O1", "10"), owner("O1", "20")]
        rows = [tx("O1", "1")]
        r = summarize_period("2026Q3", subs, owners, rows)
        self.assertEqual(r["p_accessions_with_multiple_reporting_owners"], 1)
        self.assertEqual(r["p_rows_in_multi_owner_accessions"], 1)
        self.assertFalse(r["bulk_grain_controls"]["transaction_table_has_reporting_owner_cik"])
        self.assertFalse(r["bulk_grain_controls"]["transaction_to_owner_assignment_from_bulk_alone"])

    def test_amendment_correction_is_an_information_update_not_a_new_trade(self):
        subs = [
            submission("O1", "4", "2026-07-24", aff="0"),
            submission("A1", "4/A", "2026-07-24", orig="2026-07-24", aff="0"),
        ]
        owners = [owner("O1", "10"), owner("A1", "10")]
        rows = [tx("O1", "1", "P", "D"), tx("A1", "1", "P", "A")]
        r = summarize_period("2026Q3", subs, owners, rows)
        amend = r["same_quarter_amendment_link"]
        self.assertEqual(amend["unique_heuristic_pairs"], 1)
        self.assertEqual(amend["p_disposition_to_acquisition_corrections"], 1)
        self.assertEqual(amend["transaction_ad_changes"], {"P|D|A": 1})
        self.assertFalse(amend["is_authoritative_accession_lineage"])

    def test_ambiguous_amendment_link_is_not_forced(self):
        subs = [
            submission("O1", "4", "2026-07-24"),
            submission("O2", "4", "2026-07-24"),
            submission("A1", "4/A", "2026-07-25", orig="2026-07-24"),
        ]
        owners = [owner("O1", "10"), owner("O2", "10"), owner("A1", "10")]
        r = summarize_period("2026Q3", subs, owners, [])
        self.assertEqual(r["same_quarter_amendment_link"]["ambiguous_candidates"], 1)
        self.assertEqual(r["same_quarter_amendment_link"]["unique_heuristic_pairs"], 0)

    def test_missing_historical_flag_is_unknown_not_false(self):
        subs = [submission("O1", "4", "2012-01-10")]
        owners = [owner("O1", "10")]
        r = summarize_period("2012Q1", subs, owners, [tx("O1", "1")])
        self.assertFalse(r["aff10b5one_field_present"])
        self.assertEqual(r["aff10b5one_p_accessions_normalized"], {"unknown": 1})

    def test_p_code_and_disposition_are_kept_as_separate_fields(self):
        subs = [submission("O1", "4", "2026-07-24", aff="0")]
        owners = [owner("O1", "10")]
        r = summarize_period("2026Q3", subs, owners, [tx("O1", "1", "P", "D")])
        self.assertEqual(r["p_acquired_disposed_raw"], {"D": 1})
        self.assertEqual(r["p_coded_nonderivative_rows"], 1)

    def test_duplicate_submission_and_owner_keys_fail_closed(self):
        subs = [submission("O1", "4", "2026-07-24"), submission("O1", "4", "2026-07-24")]
        with self.assertRaisesRegex(ValueError, "duplicate submission accession"):
            summarize_period("2026Q3", subs, [], [])
        with self.assertRaisesRegex(ValueError, "duplicate reporting-owner key"):
            summarize_period("2026Q3", [submission("O1", "4", "2026-07-24")],
                             [owner("O1", "10"), owner("O1", "10")], [])


if __name__ == "__main__":
    unittest.main()
