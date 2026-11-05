import csv
import tempfile
import unittest
from pathlib import Path

from research.phase120_sec_13dg_predecessor_content_audit import (
    choose_mirror, compare_pair, form_family, legacy_fields, norm_cusip,
    parse_header, parse_submission, load_manifest,
)

HEADER = """<SEC-HEADER>
<ACCEPTANCE-DATETIME>20250122120000
ACCESSION NUMBER: 0000038777-24-000179
CONFORMED SUBMISSION TYPE: SCHEDULE 13G/A
FILED AS OF DATE: 20241107
SUBJECT COMPANY:
 COMPANY DATA:
  COMPANY CONFORMED NAME: Example Issuer
  CENTRAL INDEX KEY: 0001808898
FILED BY:
 COMPANY DATA:
  COMPANY CONFORMED NAME: Example Filer
  CENTRAL INDEX KEY: 0000038777
</SEC-HEADER>
"""

XML_13G = """<XML><edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13g">
<headerData><submissionType>SCHEDULE 13G/A</submissionType><filerInfo><filer><filerCredentials><cik>0000038777</cik></filerCredentials></filer></filerInfo></headerData>
<formData><coverPageHeader><amendmentNo>2</amendmentNo><securitiesClassTitle>Common Stock</securitiesClassTitle>
<issuerInfo><issuerCik>0001808898</issuerCik><issuerCusip>08205P209</issuerCusip></issuerInfo></coverPageHeader>
<coverPageHeaderReportingPersonDetails><reportingPersonName>Example Filer</reportingPersonName>
<reportingPersonBeneficiallyOwnedAggregateNumberOfShares>1000</reportingPersonBeneficiallyOwnedAggregateNumberOfShares><classPercent>5.0</classPercent></coverPageHeaderReportingPersonDetails>
</formData></edgarSubmission></XML>"""

XML_13D = """<XML><edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13d">
<headerData><submissionType>SCHEDULE 13D/A</submissionType><filerInfo><filer><filerCredentials><cik>0000038777</cik></filerCredentials></filer></filerInfo></headerData>
<formData><coverPageHeader><amendmentNo>3</amendmentNo><securitiesClassTitle>Common Stock</securitiesClassTitle>
<issuerInfo><issuerCik>0001808898</issuerCik><issuerCusip>08205P209</issuerCusip></issuerInfo></coverPageHeader>
<reportingPersonInfo><reportingPersonCIK>0000038777</reportingPersonCIK><reportingPersonName>Example Filer</reportingPersonName>
<aggregateAmountOwned>1000</aggregateAmountOwned><percentOfClass>5.0</percentOfClass></reportingPersonInfo>
</formData></edgarSubmission></XML>"""

class Phase120Tests(unittest.TestCase):
    def test_form_family_schedule_aliases(self):
        self.assertEqual(form_family("SCHEDULE 13D/A"), "13D")
        self.assertEqual(form_family("SC 13G"), "13G")
        self.assertIsNone(form_family("SC 13F"))

    def test_header_roles_are_separate_and_zero_padded(self):
        h = parse_header(HEADER)
        self.assertEqual(h["accession"], "0000038777-24-000179")
        self.assertEqual(h["header_subject_cik"], "0001808898")
        self.assertEqual(h["header_filer_cik"], "0000038777")
        self.assertEqual(h["filed_date"], "2024-11-07")
        self.assertEqual(h["acceptance_datetime"], "20250122120000")

    def test_13g_parser_uses_13g_reporting_person_nodes(self):
        p = parse_submission(HEADER + XML_13G, "13G")
        self.assertTrue(p["xml_present"])
        self.assertEqual(p["xml_issuer_cik"], "0001808898")
        self.assertEqual(p["xml_filer_cik"], "0000038777")
        self.assertEqual(p["cusip"], "08205P209")
        self.assertEqual(len(p["persons"]), 1)
        self.assertEqual(p["persons"][0]["name"], "Example Filer")

    def test_13d_parser_uses_13d_reporting_person_nodes(self):
        header = HEADER.replace("13G/A", "13D/A")
        p = parse_submission(header + XML_13D, "13D")
        self.assertEqual(len(p["persons"]), 1)
        self.assertEqual(p["persons"][0]["cik"], "0000038777")

    def test_legacy_html_extracts_only_unambiguous_cusip(self):
        raw = """<DOCUMENT><TYPE>SC 13G</TYPE><TEXT><html><body>
        Title of Class of Securities: Common Stock
        CUSIP No. 08205P209
        </body></html></TEXT></DOCUMENT>"""
        f = legacy_fields(raw)
        self.assertFalse(f["xml_present"])
        self.assertEqual(f["cusip"], "08205P209")
        self.assertEqual(norm_cusip("000000000"), None)

    def test_mirror_selection_requires_identical_content(self):
        same = [{"valid":True,"sha256":"a"},{"valid":True,"sha256":"a"}]
        chosen,status = choose_mirror(same)
        self.assertIsNotNone(chosen)
        self.assertEqual(status,"IDENTICAL_MIRRORS")
        chosen,status = choose_mirror([{"valid":True,"sha256":"a"},{"valid":True,"sha256":"b"}])
        self.assertIsNone(chosen)
        self.assertEqual(status,"MIRROR_CONTENT_CONFLICT")

    def test_pair_flags_cusip_mismatch_and_never_calls_it_a_pass(self):
        manifest={"current_form":"SC 13G/A","current_accession":"c","previous_accession":"p",
                  "current_filing_date":"2025-01-01","current_issuer_cik":"0001808898",
                  "current_filer_cik":"0000038777","current_cusip":"08205P209"}
        current={"accession":"c","form":"SC 13G/A","filed_date":"2025-01-01",
                 "header_subject_cik":"0001808898","header_filer_cik":"0000038777",
                 "cusip":"08205P209","class_title":"Common Stock","xml_present":False,"persons":[]}
        previous={"accession":"p","form":"SC 13G","filed_date":"2024-01-01",
                  "header_subject_cik":"0001808898","header_filer_cik":"0000038777",
                  "cusip":"99999A101","class_title":"Common Stock","xml_present":False,"persons":[]}
        result=compare_pair(current,previous,manifest,"IDENTICAL_MIRRORS")
        self.assertEqual(result["header_status"],"PASS")
        self.assertEqual(result["security_status"],"CUSIP_MISMATCH")
        self.assertEqual(result["lineage_status"],"SECURITY_CONFLICT")

    def test_manifest_requires_45_unique_predecessors_and_safe_paths(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"manifest.csv"
            fields=["current_accession","previous_accession","current_form","current_filing_date",
                    "current_issuer_cik","current_filer_cik","current_cusip","previous_paths_pipe","current_raw_file"]
            with path.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
                for i in range(45):
                    w.writerow({"current_accession":f"c{i}","previous_accession":f"p{i}",
                                "current_form":"SC 13G/A","current_filing_date":"2025-01-01",
                                "current_issuer_cik":"1","current_filer_cik":"2",
                                "previous_paths_pipe":f"edgar/data/1/p{i}.txt",
                                "current_raw_file":"raw_submissions/c.txt"})
            self.assertEqual(len(load_manifest(path)),45)

if __name__ == "__main__":
    unittest.main()
