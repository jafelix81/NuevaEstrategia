import json
import tempfile
import unittest
from pathlib import Path

from research.phase193_nport_raw_filing_retrieval import (
    blocked_audit,
    normalize_accession,
    parse_index_listing,
    parse_nport_xml,
    parse_submission_header,
    submission_header_diagnostic,
    run_audit,
)

HEADER = b"""<SEC-HEADER>
ACCESSION NUMBER: 0001752724-20-163166
CONFORMED SUBMISSION TYPE: NPORT-P
CONFORMED PERIOD OF REPORT: 20200731
FILED AS OF DATE: 20200821
ACCEPTANCE-DATETIME: 20200821125543
</SEC-HEADER>
"""

XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/nport">
  <formData>
    <genInfo><seriesId>S000000001</seriesId></genInfo>
    <invstOrSec>
      <name>Example Short Equity</name><cusip>123456789</cusip>
      <balance>-100</balance><units>NS</units><valUSD>-1000</valUSD><pctVal>-1.25</pctVal>
      <payoffProfile>Short</payoffProfile><assetCat>EC</assetCat>
      <issuerCat>CORP</issuerCat><invCountry>US</invCountry>
    </invstOrSec>
    <invstOrSec>
      <name>Example Long Equity</name><cusip>987654321</cusip>
      <balance>100</balance><units>NS</units><valUSD>1000</valUSD><pctVal>1.25</pctVal>
      <payoffProfile>Long</payoffProfile><assetCat>EC</assetCat>
      <issuerCat>CORP</issuerCat><invCountry>US</invCountry>
    </invstOrSec>
    <invstOrSec>
      <name>Example Short Derivative</name><cusip>111111111</cusip>
      <balance>-1</balance><units>NS</units><valUSD>-100</valUSD><pctVal>-0.1</pctVal>
      <payoffProfile>Short</payoffProfile><assetCat>DER</assetCat>
      <issuerCat>CORP</issuerCat><invCountry>US</invCountry>
    </invstOrSec>
    <invstOrSec>
      <name>Sign Mismatch</name><cusip>222222222</cusip>
      <balance>-5</balance><units>NS</units><valUSD>500</valUSD><pctVal>-0.2</pctVal>
      <payoffProfile>Short</payoffProfile><assetCat>EC</assetCat>
      <issuerCat>CORP</issuerCat><invCountry>US</invCountry>
    </invstOrSec>
  </formData>
</edgarSubmission>
"""

class Phase193Tests(unittest.TestCase):
    def test_normalize_accession_removes_non_digits(self):
        self.assertEqual(normalize_accession("0001752724-20-163166"), "000175272420163166")

    def test_header_diagnostic_extracts_acceptance_value(self):
        result = submission_header_diagnostic(HEADER)
        self.assertEqual(result["ACCESSION NUMBER"], "0001752724-20-163166")
        self.assertEqual(result["ACCEPTANCE-DATETIME"], "20200821125543")

    def test_submission_header_reconciles_accession_form_and_acceptance(self):
        result = parse_submission_header(HEADER, "0001752724-20-163166", "NPORT-P")
        self.assertEqual(result["acceptance_datetime_et"], "2020-08-21T12:55:43-04:00")
        self.assertEqual(result["acceptance_datetime_utc"], "2020-08-21T16:55:43+00:00")
        self.assertEqual(result["acceptance_date_matches_filed_date"], True)

    def test_submission_header_rejects_accession_mismatch(self):
        with self.assertRaisesRegex(ValueError, "submission_accession_mismatch"):
            parse_submission_header(HEADER, "0000000000-20-000001", "NPORT-P")

    def test_submission_header_rejects_form_mismatch(self):
        with self.assertRaisesRegex(ValueError, "submission_form_mismatch"):
            parse_submission_header(HEADER, "0001752724-20-163166", "NPORT-P/A")

    def test_submission_header_requires_acceptance_datetime(self):
        bad = HEADER.replace(b"ACCEPTANCE-DATETIME: 20200821125543", b"ACCEPTANCE-DATETIME: unavailable")
        with self.assertRaisesRegex(ValueError, "acceptance_datetime_missing_or_invalid"):
            parse_submission_header(bad, "0001752724-20-163166", "NPORT-P")

    def test_xml_parser_finds_only_direct_short_common_equity_rows(self):
        result = parse_nport_xml(XML)
        self.assertEqual(result["holding_nodes"], 4)
        self.assertEqual(result["series_ids"], ["S000000001"])
        self.assertEqual(result["counts"]["short_payoff_rows"], 3)
        self.assertEqual(result["counts"]["short_ec_corp_us_rows"], 2)
        self.assertEqual(result["counts"]["direct_short_sign_concordant_rows"], 1)
        self.assertEqual(result["counts"]["direct_short_sign_or_unit_mismatch_rows"], 1)
        self.assertEqual(result["direct_short_cusips"], ["123456789", "222222222"])

    def test_xml_parser_does_not_promote_positive_value_sign_to_concordant(self):
        result = parse_nport_xml(XML)
        mismatch = next(x for x in result["direct_short_rows_sample"] if x["cusip"] == "222222222")
        self.assertFalse(mismatch["sign_concordant"])

    def test_index_listing_resolves_exact_primary_and_submission_text(self):
        payload = json.dumps({"directory":{"item":[
            {"name":"primary_doc.xml","size":"1000","last-modified":"2020-08-21 12:00:00"},
            {"name":"0001752724-20-163166.txt","size":"2000","last-modified":"2020-08-21 12:00:00"},
            {"name":"index.htm","size":"500","last-modified":"2020-08-21 12:00:00"}
        ]}}).encode()
        result = parse_index_listing(payload, "0001752724-20-163166", "primary_doc.xml")
        self.assertEqual(result["submission_text_name"], "0001752724-20-163166.txt")
        self.assertEqual(result["primary_document_name"], "primary_doc.xml")

    def test_index_listing_rejects_ambiguous_submission_text(self):
        payload = json.dumps({"directory":{"item":[
            {"name":"primary_doc.xml"},
            {"name":"0001752724-20-163166.txt"},
            {"name":"x000175272420163166.txt"}
        ]}}).encode()
        with self.assertRaisesRegex(ValueError, "complete_submission_text_not_uniquely_resolved"):
            parse_index_listing(payload, "0001752724-20-163166", "primary_doc.xml")

    def test_missing_contact_email_blocks_without_network(self):
        evidence = {"source":"SEC EDGAR test","accessions":[{"accession":"x"}]}
        with tempfile.TemporaryDirectory() as temp:
            result = run_audit("", Path(temp), evidence)
        self.assertEqual(result["status"], "BLOCKED_MISSING_SEC_CONTACT_EMAIL")
        self.assertFalse(result["raw_xml_sha256_verified"])
        self.assertFalse(result["alpha_test_authorized"])
        self.assertTrue(result["f80_frozen"])

    def test_blocked_audit_does_not_claim_attempted_accessions(self):
        result = blocked_audit({"source":"SEC EDGAR test","accessions":[{},{}]})
        self.assertEqual(result["accessions_attempted"], 0)
        self.assertEqual(result["accessions_total"], 2)

    def test_no_acceptance_time_is_promoted_to_first_public_receipt(self):
        evidence = {"source":"SEC EDGAR test","accessions":[{"accession":"x"}]}
        result = blocked_audit(evidence)
        self.assertFalse(result["first_public_receipt_verified"])
        self.assertFalse(result["strict_pit_admitted"])

if __name__ == "__main__":
    unittest.main()
