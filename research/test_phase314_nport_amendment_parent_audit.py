import unittest
import xml.etree.ElementTree as ET

from research.phase314_nport_amendment_parent_audit import (
    TARGET_CIK,
    TARGET_REPORT_DATE,
    TARGET_SERIES_ID,
    TARGET_AMENDMENT,
    accession_raw_filename,
    classify_parent_matches,
    compare_positions,
    parse_header_fields,
    parse_submission,
    parse_short_positions,
    position_key,
    select_candidates,
)

HEADER = """<SEC-HEADER>
ACCESSION NUMBER: 0001145549-22-060851
CONFORMED SUBMISSION TYPE: NPORT-P/A
CENTRAL INDEX KEY: 0000811030
FILED AS OF DATE: 20221003
CONFORMED PERIOD OF REPORT: 20220731
ACCEPTANCE-DATETIME: 20221003120000
<SERIES-ID>S000043717
<SERIES-NAME>Otter Creek Long/Short Opportunity Fund
<CLASS-CONTRACT-ID>C000135565
</SEC-HEADER>
"""

XML = """<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/nport">
  <headerData><submissionType>NPORT-P/A</submissionType></headerData>
  <formData>
    <genInfo>
      <seriesId>S000043717</seriesId>
      <seriesName>Otter Creek Long/Short Opportunity Fund</seriesName>
      <repPdDate>2022-07-31</repPdDate>
      <classId>C000135565</classId>
    </genInfo>
    <invstOrSecs>
      <invstOrSec>
        <name>Example Corp</name><title>Common Stock</title><cusip>123456789</cusip>
        <balance>-100</balance><units>NS</units><valUSD>-1000</valUSD><pctVal>-0.1</pctVal>
        <payoffProfile>Short</payoffProfile><assetCat>EC</assetCat><issuerCat>CORP</issuerCat><invCountry>US</invCountry>
        <identifiers><isin>US1234567890</isin><ticker>EXM</ticker></identifiers>
      </invstOrSec>
      <invstOrSec>
        <name>Long Corp</name><title>Common Stock</title><cusip>987654321</cusip>
        <balance>100</balance><units>NS</units><valUSD>1000</valUSD><pctVal>0.1</pctVal>
        <payoffProfile>Long</payoffProfile><assetCat>EC</assetCat><issuerCat>CORP</issuerCat><invCountry>US</invCountry>
      </invstOrSec>
    </invstOrSecs>
  </formData>
</edgarSubmission>
"""


class Phase314ParentAuditTests(unittest.TestCase):
    def test_accession_raw_filename_removes_hyphens(self):
        self.assertEqual(accession_raw_filename(TARGET_AMENDMENT), "000114554922060851.txt")

    def test_header_fields_capture_filing_period_and_acceptance(self):
        parsed = parse_header_fields(HEADER)
        self.assertEqual(parsed["accession"], TARGET_AMENDMENT)
        self.assertEqual(parsed["form_type"], "NPORT-P/A")
        self.assertEqual(parsed["registrant_cik"], TARGET_CIK)
        self.assertEqual(parsed["filed_as_of_date"], "20221003")
        self.assertEqual(parsed["period_of_report"], "20220731")
        self.assertEqual(parsed["acceptance_datetime_et"], "20221003120000")

    def test_parse_submission_confirms_header_xml_identity_and_short_row(self):
        raw = (HEADER + "<DOCUMENT><TYPE>NPORT-P/A</TYPE><TEXT><XML>" + XML + "</XML></TEXT></DOCUMENT>").encode("utf-8")
        parsed = parse_submission(raw, "NPORT-P/A")
        self.assertEqual(parsed["accession"], TARGET_AMENDMENT)
        self.assertEqual(parsed["report_date"], TARGET_REPORT_DATE)
        self.assertEqual(parsed["series_ids"], [TARGET_SERIES_ID])
        self.assertEqual(parsed["series_identity_state"], "MATCH")
        self.assertEqual(parsed["class_identity_state"], "MATCH")
        self.assertEqual(len(parsed["short_positions"]), 1)
        self.assertEqual(parsed["short_positions"][0]["ticker"], "EXM")

    def test_short_filter_excludes_long_or_positive_positions(self):
        root = ET.fromstring(XML)
        rows = parse_short_positions(root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["cusip"], "123456789")

    def test_position_key_uses_security_identity_and_type(self):
        row = {"cusip":"123456789","payoff_profile":"Short","asset_category":"EC","issuer_type":"CORP","investment_country":"US","units":"NS"}
        self.assertEqual(position_key(row), "CUSIP:123456789|Short|EC|CORP|US|NS")

    def test_original_amendment_comparison_separates_changed_added_removed(self):
        original = [
            {"cusip":"A","payoff_profile":"Short","asset_category":"EC","issuer_type":"CORP","investment_country":"US","units":"NS","balance":"-10","value_usd":"-100","percentage_nav":"-0.1"},
            {"cusip":"C","payoff_profile":"Short","asset_category":"EC","issuer_type":"CORP","investment_country":"US","units":"NS","balance":"-5","value_usd":"-50","percentage_nav":"-0.05"},
        ]
        amendment = [
            {"cusip":"A","payoff_profile":"Short","asset_category":"EC","issuer_type":"CORP","investment_country":"US","units":"NS","balance":"-12","value_usd":"-120","percentage_nav":"-0.12"},
            {"cusip":"B","payoff_profile":"Short","asset_category":"EC","issuer_type":"CORP","investment_country":"US","units":"NS","balance":"-3","value_usd":"-30","percentage_nav":"-0.03"},
        ]
        result = compare_positions(original, amendment)
        self.assertEqual(result["modified_rows"], 1)
        self.assertEqual(result["added_rows"], 1)
        self.assertEqual(result["removed_rows"], 1)
        self.assertEqual(result["unchanged_rows"], 0)

    def test_parent_candidate_requires_cik_report_date_series_and_original_form(self):
        candidate = {
            "accession":"0001145549-22-059179","registrant_cik":TARGET_CIK,
            "form_type":"NPORT-P","report_date":TARGET_REPORT_DATE,
            "series_ids":[TARGET_SERIES_ID],
        }
        status, matches = classify_parent_matches([candidate])
        self.assertEqual(status, "UNIQUE_METADATA_PARENT_CANDIDATE_NOT_AUTHORITATIVE")
        self.assertEqual(len(matches), 1)
        wrong_series = dict(candidate, series_ids=["SOTHER"])
        self.assertEqual(classify_parent_matches([wrong_series])[0], "NO_METADATA_PARENT_CANDIDATE")
        self.assertEqual(classify_parent_matches([candidate, dict(candidate, accession="other")])[0], "AMBIGUOUS_METADATA_PARENT_CANDIDATES")

    def test_candidate_selection_is_scoped_to_exact_registrant_quarter_form_and_date(self):
        rows = [
            {"cik":"811030","quarter":"2022Q3","form_type":"NPORT-P","filing_date":"2022-09-28","accession":"a"},
            {"cik":"811030","quarter":"2022Q3","form_type":"NPORT-P/A","filing_date":"2022-09-28","accession":"b"},
            {"cik":"0711080","quarter":"2022Q3","form_type":"NPORT-P","filing_date":"2022-09-28","accession":"c"},
            {"cik":"811030","quarter":"2022Q4","form_type":"NPORT-P","filing_date":"2022-09-28","accession":"d"},
            {"cik":"811030","quarter":"2022Q3","form_type":"NPORT-P","filing_date":"2022-10-04","accession":"e"},
        ]
        selected = select_candidates(rows, "2022-10-03")
        self.assertEqual([row["accession"] for row in selected], ["a"])


if __name__ == "__main__":
    unittest.main()
