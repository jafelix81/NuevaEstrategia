import gzip
import unittest

from research.phase50_form144_global_index_pilot import (
    archive_index_urls,
    date_relation,
    decode_http_body,
    days_event_minus_filing,
    normalize_form,
    norm_cik,
    parse_edgar_date,
    parse_form144_xml,
    parse_index_page,
    parse_master_index,
    select_xml_sample,
    ticker_from_sec_row,
)

INDEX_HTML = b"""<html><body>
<h1>Form 144 - Report of proposed sale of securities:</h1>
<p>SEC Accession No. 0001959173-25-004176</p>
<p>Filing Date 2025-06-17</p><p>Accepted 2025-06-17 16:04:03</p>
<p>ORACLE CORP (Subject) CIK: 0001341439</p>
<p>CONRADES GEORGE H (Reporting) CIK: 0001106231</p>
</body></html>"""

INDEX_HTML_ANCHORED = b"""<html><body>
<h1>Form 144 - Report of proposed sale of securities:</h1>
<p>SEC Accession No. 0001959173-25-004176</p>
<p>Filing Date 2025-06-17</p><p>Accepted 2025-06-17 16:04:03</p>
<p><a href="/Archives/edgar/data/1341439">ORACLE CORP</a> (<a href="/Archives/edgar/data/1341439">Subject</a>) CIK: <a href="/Archives/edgar/data/1341439">0001341439 (see all company filings)</a></p>
<p>CONRADES GEORGE H (<a href="/Archives/edgar/data/1106231">Reporting</a>) CIK: <a href="/Archives/edgar/data/1106231">0001106231 (see all company filings)</a></p>
</body></html>"""

XML = """<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/ownership">
  <headerData>
    <submissionType>144/A</submissionType>
    <filerInfo><filer><filerCredentials><cik>0001106231</cik></filerCredentials></filer></filerInfo>
    <previousAccessionNumber>0001959173-25-004175</previousAccessionNumber>
  </headerData>
  <formData>
    <issuerInfo>
      <issuerCik>0001341439</issuerCik>
      <issuerName>ORACLE CORP</issuerName>
      <nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold>George H. Conrades</nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold>
      <relationshipsToIssuer><relationshipToIssuer>Director</relationshipToIssuer></relationshipsToIssuer>
    </issuerInfo>
    <securitiesInformation>
      <securitiesClassTitle>Common Stock</securitiesClassTitle>
      <noOfUnitsSold>1000</noOfUnitsSold>
      <aggregateMarketValue>50000</aggregateMarketValue>
      <approxSaleDate>06/16/2025</approxSaleDate>
    </securitiesInformation>
    <noticeSignature><noticeDate>06/17/2025</noticeDate></noticeSignature>
    <remarks>Sale pursuant to a Rule 10b5-1 plan.</remarks>
  </formData>
</edgarSubmission>
"""


class Form144GlobalIndexTests(unittest.TestCase):

    def test_gzip_magic_byte_decode(self):
        payload = b'{"ok":true}'
        self.assertEqual(decode_http_body(gzip.compress(payload)), payload)

    def test_sec_mutual_fund_ticker_uses_symbol_field(self):
        row = {
            "cik": 36405, "seriesId": "S000002839",
            "classId": "C000092055", "symbol": "VOO",
        }
        self.assertEqual(ticker_from_sec_row(row), "VOO")
        self.assertEqual(ticker_from_sec_row({"ticker": "AAPL"}), "AAPL")
        self.assertEqual(ticker_from_sec_row({"classTicker": "VFIAX"}), "VFIAX")

    def test_form_normalization(self):
        self.assertEqual(normalize_form("144"), "144")
        self.assertEqual(normalize_form("144/A"), "144/A")
        self.assertEqual(normalize_form("Form 144/A"), "144/A")
        self.assertEqual(normalize_form("Schedule 144"), "144")
        self.assertIsNone(normalize_form("4"))

    def test_master_index_parses_both_forms_and_archive_path(self):
        raw = (
            "Description: SEC filing index\n"
            "CIK|Company Name|Form Type|Date Filed|Filename\n"
            "0001341439|ORACLE CORP|144|2025-06-17|edgar/data/1341439/000195917325004176/0001959173-25-004176.txt\n"
            "0001106231|CONRADES GEORGE H|144|2025-06-17|edgar/data/1341439/000195917325004176/0001959173-25-004176.txt\n"
            "0001341439|ORACLE CORP|144/A|2025-06-18|edgar/data/1341439/000195917325004177/0001959173-25-004177.txt\n"
        )
        rows = parse_master_index(raw)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["form"], "144")
        self.assertEqual(rows[0]["archive_path_cik"], "1341439")
        self.assertEqual(rows[0]["master_index_row_count"], 2)
        self.assertEqual(rows[1]["form"], "144/A")

    def test_index_page_separates_subject_reporting_and_timestamp(self):
        parsed = parse_index_page(INDEX_HTML)
        self.assertEqual(parsed["accession"], "0001959173-25-004176")
        self.assertEqual(parsed["form"], "144")
        self.assertEqual(parsed["subject_cik"], "0001341439")
        self.assertEqual(parsed["reporting_cik"], "0001106231")
        self.assertEqual(parsed["accepted_at"], "2025-06-17 16:04:03")

    def test_index_page_role_labels_survive_anchor_markup_whitespace(self):
        parsed = parse_index_page(INDEX_HTML_ANCHORED)
        self.assertEqual(parsed["subject_cik"], "0001341439")
        self.assertEqual(parsed["reporting_cik"], "0001106231")
        self.assertEqual(parsed["accepted_at"], "2025-06-17 16:04:03")

    def test_xml_separates_issuer_filer_and_extracts_notice(self):
        parsed = parse_form144_xml(XML)
        self.assertEqual(parsed["issuer_cik"], "0001341439")
        self.assertEqual(parsed["filer_cik"], "0001106231")
        self.assertEqual(parsed["submission_type"], "144/A")
        self.assertEqual(parsed["previous_accession"], "0001959173-25-004175")
        self.assertTrue(parsed["mentions_10b5_1"])
        self.assertTrue(parsed["field_presence"]["units_to_be_sold"])

    def test_edgar_date_formats(self):
        self.assertEqual(str(parse_edgar_date("06/16/2025")), "2025-06-16")
        self.assertEqual(str(parse_edgar_date("06-16-2025")), "2025-06-16")
        self.assertEqual(str(parse_edgar_date("2025-06-16")), "2025-06-16")
        self.assertIsNone(parse_edgar_date("not-a-date"))

    def test_sale_date_relation_handles_month_day_year_without_execution_claim(self):
        self.assertEqual(date_relation("06/16/2025", "2025-06-17"), "before_filing")
        self.assertEqual(date_relation("06/17/2025", "2025-06-17"), "same_day")
        self.assertEqual(date_relation("06/18/2025", "2025-06-17"), "after_filing")
        self.assertEqual(days_event_minus_filing("06/16/2025", "2025-06-17"), -1)

    def test_archive_index_urls_prefer_master_index_archive_path(self):
        group = {
            "accession": "0001959173-25-004176",
            "archive_path_cik": "1341439",
            "master_index_ciks": ["0001106231", "0001341439"],
        }
        urls = archive_index_urls(group)
        self.assertIn(
            "https://www.sec.gov/Archives/edgar/data/1341439/000195917325004176/0001959173-25-004176-index.htm",
            urls,
        )

    def test_xml_sample_is_stratified_by_form_and_subject_status(self):
        rows = []
        for form in ("144", "144/A"):
            for i in range(30):
                rows.append({
                    "accession": "{}-{:02d}".format(form, i),
                    "master_index_form": form,
                    "subject_cik": "0000000001" if i < 15 else "0000000002",
                })
        sample = select_xml_sample(rows, {"0000000001"}, sample_per_form=5)
        self.assertEqual(sum(row["master_index_form"] == "144" for row in sample), 10)
        self.assertEqual(sum(row["master_index_form"] == "144/A" for row in sample), 10)
        self.assertEqual(sum(row["subject_cik"] == "0000000001" for row in sample), 10)
        self.assertEqual(sum(row["subject_cik"] == "0000000002" for row in sample), 10)


if __name__ == "__main__":
    unittest.main()
