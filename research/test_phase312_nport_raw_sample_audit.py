import unittest

from research.phase312_nport_raw_sample_audit import (
    decimal_value,
    extract_primary_xml,
    parse_holding_rows,
    parse_submission,
    _series_state,
)

ACCESSION = "0001145549-22-056239"
CIK = "0001511699"
XML = """<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/nport">
  <headerData><submissionType>NPORT-P</submissionType></headerData>
  <formData>
    <genInfo>
      <regCik>0001511699</regCik>
      <seriesId>S000052217</seriesId>
      <seriesName>Nuance Concentrated Value Long-Short Fund</seriesName>
      <repPdDate>2022-07-31</repPdDate>
      <repPdEnd>2023-04-30</repPdEnd>
    </genInfo>
    <fundInfo><totAssets>247938106.000000000000</totAssets><netAssets>131304983.470000000000</netAssets></fundInfo>
    <invstOrSecs>
      <invstOrSec>
        <name>American Express Co</name><title>Issuer description without stock wording</title>
        <cusip>025816109</cusip><identifiers><isin value="US0258161092"/><ticker value="AXP"/></identifiers>
        <balance>-5560.000000000000</balance><units>NS</units><valUSD>-856351.200000000000</valUSD>
        <pctVal>-0.6521848428</pctVal><payoffProfile>Short</payoffProfile><assetCat>EC</assetCat>
        <issuerCat>CORP</issuerCat><invCountry>US</invCountry>
      </invstOrSec>
      <invstOrSec>
        <name>Negative control</name><title>Common Stock</title><cusip>111111111</cusip>
        <balance>100</balance><units>NS</units><valUSD>1000</valUSD><pctVal>0.5</pctVal>
        <payoffProfile>Short</payoffProfile><assetCat>EC</assetCat><issuerCat>CORP</issuerCat><invCountry>US</invCountry>
      </invstOrSec>
      <invstOrSec>
        <name>Wrong country</name><title>Common Stock</title><cusip>222222222</cusip>
        <balance>-10</balance><units>NS</units><valUSD>-100</valUSD><pctVal>-1</pctVal>
        <payoffProfile>Short</payoffProfile><assetCat>EC</assetCat><issuerCat>CORP</issuerCat><invCountry>CA</invCountry>
      </invstOrSec>
    </invstOrSecs>
  </formData>
</edgarSubmission>
"""
SUBMISSION = f"""<SEC-DOCUMENT>{ACCESSION}.txt : 20220915
<SEC-HEADER>{ACCESSION}.hdr.sgml : 20220915
<ACCEPTANCE-DATETIME>20220915142322
ACCESSION NUMBER: {ACCESSION}
CONFORMED SUBMISSION TYPE: NPORT-P
PUBLIC DOCUMENT COUNT: 2
CONFORMED PERIOD OF REPORT: 20220731
FILED AS OF DATE: 20220915
FILER:
  COMPANY DATA:
    CENTRAL INDEX KEY: {CIK}
<SERIES-AND-CLASSES-CONTRACTS-DATA>
<SERIES-ID>S000052217</SERIES-ID>
<CLASS-CONTRACT-ID>C000164257</CLASS-CONTRACT-ID>
</SEC-HEADER>
<DOCUMENT>
<TYPE>NPORT-P
<SEQUENCE>1
<FILENAME>primary_doc.xml
<TEXT>
<XML>
{XML}
</XML>
</TEXT>
</DOCUMENT>
"""


class Phase312NportRawSampleTests(unittest.TestCase):
    def expected(self):
        return {
            "accession": ACCESSION,
            "cik": CIK,
            "company_name": "Managed Portfolio Series",
            "form_type": "NPORT-P",
            "filing_date": "2022-09-15",
            "filename": "edgar/data/1511699/0001145549-22-056239.txt",
        }

    def test_parse_submission_reconciles_header_and_xml(self):
        meta, rows = parse_submission(SUBMISSION.encode(), self.expected())
        self.assertTrue(meta["core_reconciliation_pass"])
        self.assertEqual(meta["header_accession"], ACCESSION)
        self.assertEqual(meta["acceptance_datetime_et"], "20220915142322")
        self.assertEqual(meta["xml_report_date"], "2022-07-31")
        self.assertEqual(meta["series_identity_state"], "MATCH")
        self.assertEqual(meta["class_identity_state"], "HEADER_ONLY")
        self.assertEqual(meta["holding_rows_total"], 3)

    def test_strict_short_filter_uses_structured_fields_not_title_text(self):
        meta, rows = parse_submission(SUBMISSION.encode(), self.expected())
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(1 for row in rows if row["sign_concordant"]), 1)
        self.assertEqual(rows[0]["issuer_name"], "American Express Co")
        self.assertEqual(rows[0]["issue_title"], "Issuer description without stock wording")
        self.assertTrue(rows[0]["sign_concordant"])
        self.assertEqual(rows[0]["cusip"], "025816109")
        self.assertEqual(rows[0]["isin"], "US0258161092")
        self.assertEqual(rows[0]["ticker"], "AXP")
        self.assertTrue(rows[0]["cusip_valid_format"])
        self.assertTrue(rows[0]["isin_valid_format"])
        self.assertTrue(rows[0]["ticker_reported"])

    def test_nonnegative_signs_are_not_sign_concordant(self):
        from research.phase312_nport_raw_sample_audit import parse_holding_rows
        import xml.etree.ElementTree as ET
        root = ET.fromstring(XML)
        candidates, total = parse_holding_rows(root)
        self.assertEqual(total, 3)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(sum(1 for x in candidates if x["sign_concordant"]), 1)

    def test_wrong_country_is_excluded(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(XML)
        candidates, total = parse_holding_rows(root)
        self.assertEqual(len(candidates), 2)
        self.assertNotIn("Wrong country", [x["issuer_name"] for x in candidates])

    def test_n_a_placeholders_are_not_counted_as_security_identifiers(self):
        from research.phase312_nport_raw_sample_audit import normalize_identifier, is_valid_cusip, is_valid_isin
        self.assertEqual(normalize_identifier("N/A"), "")
        self.assertFalse(is_valid_cusip("N/A"))
        self.assertFalse(is_valid_isin("N/A"))
        self.assertTrue(is_valid_cusip("025816109"))
        self.assertTrue(is_valid_isin("US0258161092"))

    def test_decimal_value_rejects_nonfinite_and_invalid(self):
        self.assertIsNone(decimal_value("NaN"))
        self.assertIsNone(decimal_value("Infinity"))
        self.assertIsNone(decimal_value("not-a-number"))
        self.assertEqual(str(decimal_value("-1.25")), "-1.25")

    def test_extract_primary_xml_selects_exact_form(self):
        text = "<DOCUMENT><TYPE>EX-99</TYPE><TEXT>other</TEXT></DOCUMENT>" + \
               "<DOCUMENT><TYPE>NPORT-P</TYPE><TEXT><XML>" + XML + "</XML></TEXT></DOCUMENT>"
        self.assertIn("<edgarSubmission", extract_primary_xml(text, "NPORT-P"))

    def test_missing_primary_xml_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "primary_nport_xml_root_missing"):
            extract_primary_xml("<DOCUMENT><TYPE>NPORT-P</TYPE><TEXT>bad</TEXT></DOCUMENT>", "NPORT-P")

    def test_series_identity_states(self):
        self.assertEqual(_series_state(["S1"], ["S1"]), "MATCH")
        self.assertEqual(_series_state(["S1"], []), "HEADER_ONLY")
        self.assertEqual(_series_state([], ["S1"]), "XML_ONLY")
        self.assertEqual(_series_state(["S1"], ["S2"]), "MISMATCH")
        self.assertEqual(_series_state([], []), "MISSING_BOTH")

    def test_missing_acceptance_fails_closed(self):
        text = SUBMISSION.replace("<ACCEPTANCE-DATETIME>20220915142322", "")
        with self.assertRaisesRegex(ValueError, "acceptance_datetime"):
            parse_submission(text.encode(), self.expected())

    def test_wrong_header_form_does_not_reconcile(self):
        text = SUBMISSION.replace("CONFORMED SUBMISSION TYPE: NPORT-P", "CONFORMED SUBMISSION TYPE: NPORT-P/A")
        meta, rows = parse_submission(text.encode(), self.expected())
        self.assertFalse(meta["header_form_match"])
        self.assertFalse(meta["core_reconciliation_pass"])

    def test_class_identity_missing_in_xml_is_explicit(self):
        self.assertEqual(_series_state(["C000164257"], []), "HEADER_ONLY")


if __name__ == "__main__":
    unittest.main()
