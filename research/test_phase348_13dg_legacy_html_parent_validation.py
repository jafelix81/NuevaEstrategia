import unittest
from research.phase348_13dg_legacy_html_parent_validation import (
    cusip_checksum_valid, parse_acceptance_et, parse_legacy_submission, summarize_results, validate_parent,
)

class Phase348LegacyParentTests(unittest.TestCase):
    def test_acceptance_uses_eastern_dst_conversion(self):
        self.assertEqual(parse_acceptance_et("20240424171835"), "2024-04-24T21:18:35+00:00")
        self.assertEqual(parse_acceptance_et("bad"), "")

    def test_cusip_checksum(self):
        self.assertTrue(cusip_checksum_valid("72200N700"))
        self.assertTrue(cusip_checksum_valid("35242N202"))
        self.assertFalse(cusip_checksum_valid("80512Q302"))

    def test_parse_legacy_html_schedule(self):
        raw = b"""<SEC-HEADER>ACCESSION NUMBER: 0001140361-24-021787
CONFORMED SUBMISSION TYPE: SC 13D
FILED AS OF DATE: 20240424
<ACCEPTANCE-DATETIME>20240424171835
SUBJECT COMPANY: COMPANY CONFORMED NAME: PIMCO FUND CENTRAL INDEX KEY: 0001140411 FILED BY: COMPANY CONFORMED NAME: BANK OF AMERICA CENTRAL INDEX KEY: 0000070858</SEC-HEADER>
<DOCUMENT><TYPE>SC 13D</TYPE><FILENAME>sample.htm</FILENAME><TEXT>72200N700 (CUSIP Number)</TEXT></DOCUMENT>"""
        row = parse_legacy_submission(raw)
        self.assertEqual(row["accession"], "0001140361-24-021787")
        self.assertEqual(row["subject_cik"], "0001140411")
        self.assertEqual(row["primary_cusips"], ["72200N700"])
        self.assertEqual(row["primary_filename"], "sample.htm")

    def test_summary_compares_parent_and_child_subject_ciks(self):
        row = {
            "explicit_reference_validated": True, "legacy_html": True,
            "parent_cusip": "72200N700", "child_cusip": "72200N700",
            "parent_acceptance_utc": "2024-04-24T21:18:35+00:00",
            "child_acceptance_utc": "2025-08-06T00:57:32+00:00",
            "subject_cik": "0001140411", "child_subject_cik": "0000000001",
        }
        self.assertFalse(summarize_results([row])["all_subject_ciks_match"])

    def test_parent_requires_same_subject_family_earlier_time_and_cusip(self):
        child = {"family":"13D","subject_cik":"0001140411","filing_date":"2025-08-05","acceptance_utc":"2025-08-06T00:57:32+00:00","cusips":'["72200N700"]'}
        parent = {"accession":"0001140361-24-021787","form":"SC 13D","subject_cik":"0001140411","filing_date":"2024-04-24","acceptance_utc":"2024-04-24T21:18:35+00:00","primary_cusips":["72200N700"]}
        header = {"accession":"0001140361-24-021787","subject_cik":"0001140411","header_form":"SC 13D","acceptance_utc":"2024-04-24T21:18:35+00:00"}
        self.assertEqual(validate_parent(child,"0001140361-24-021787",header,parent),[])
        bad=dict(parent); bad["subject_cik"]="0000000001"
        self.assertIn("parent_subject_cik_mismatch",validate_parent(child,"0001140361-24-021787",header,bad))
        bad=dict(parent); bad["primary_cusips"]=["35242N202"]
        self.assertIn("parent_child_cusip_not_exact_single_match",validate_parent(child,"0001140361-24-021787",header,bad))

if __name__=="__main__":
    unittest.main()
