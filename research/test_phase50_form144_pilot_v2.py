import unittest

from research.phase50_form144_pilot_v2 import (
    archive_path_candidates,
    classify_sale_date,
    hit_accession,
    normalize_accession,
    parse_accepted_timestamp,
    parse_form144_xml,
    query_url,
    xml_links,
)

XML = """<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/ownership">
  <headerData>
    <submissionType>144/A</submissionType>
    <filerInfo><filer><filerCredentials><cik>0001657309</cik></filerCredentials></filer></filerInfo>
    <previousAccessionNumber>0001950047-24-000080</previousAccessionNumber>
  </headerData>
  <formData>
    <issuerInfo>
      <issuerCik>0001261333</issuerCik>
      <issuerName>DOCUSIGN, INC.</issuerName>
      <nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold>Allan C. Thygesen</nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold>
      <relationshipsToIssuer><relationshipToIssuer>Director</relationshipToIssuer><relationshipToIssuer>Officer</relationshipToIssuer></relationshipsToIssuer>
    </issuerInfo>
    <securitiesInformation>
      <securitiesClassTitle>Common Stock</securitiesClassTitle>
      <noOfUnitsSold>1000</noOfUnitsSold>
      <aggregateMarketValue>50000</aggregateMarketValue>
      <approxSaleDate>2026-11-10</approxSaleDate>
      <securitiesExchangeName>NASDAQ</securitiesExchangeName>
    </securitiesInformation>
    <securitiesToBeSold>
      <securitiesClassTitle>Common Stock</securitiesClassTitle>
      <acquiredDate>2022-01-01</acquiredDate>
      <natureOfAcquisitionTransaction>Stock Option Exercise</natureOfAcquisitionTransaction>
      <amountOfSecuritiesAcquired>1000</amountOfSecuritiesAcquired>
      <paymentDate>2022-01-01</paymentDate>
      <natureOfPayment>Compensation</natureOfPayment>
      <isGiftTransaction>N</isGiftTransaction>
    </securitiesToBeSold>
    <noticeSignature><noticeDate>2026-11-03</noticeDate><signature>/s/ Allan Thygesen</signature></noticeSignature>
  </formData>
</edgarSubmission>
"""

class Form144PilotV2Tests(unittest.TestCase):
    def test_accession_normalization(self):
        self.assertEqual(normalize_accession("000195004724000080"), "0001950047-24-000080")
        self.assertEqual(hit_accession({"_id": "0001950047-24-000080:primary_doc.xml"}), "0001950047-24-000080")

    def test_xml_schema_and_identity_separation(self):
        parsed = parse_form144_xml(XML)
        self.assertEqual(parsed["submission_type"], "144/A")
        self.assertEqual(parsed["issuer_cik"], "0000126133")
        self.assertEqual(parsed["filer_cik"], "0000165730")
        self.assertNotEqual(parsed["issuer_cik"], parsed["filer_cik"])
        self.assertEqual(parsed["previous_accession"], "0001950047-24-000080")
        self.assertEqual(parsed["seller_name"], "Allan C. Thygesen")
        self.assertEqual(parsed["relationships"], ["Director", "Officer"])
        self.assertEqual(len(parsed["tranches"]), 1)
        self.assertTrue(parsed["field_presence"]["units_to_be_sold"])

    def test_archive_candidates_use_efts_ciks_and_keep_accession_prefix_fallback(self):
        hit = {
            "_id": "0001950047-24-000080:primary_doc.xml",
            "_source": {"ciks": ["0001657309", "0001261333"]},
        }
        self.assertEqual(archive_path_candidates(hit), ["1657309", "1261333", "1950047"])

    def test_accepted_timestamp_is_retained_raw(self):
        page = "<div>Accepted</div><div>2024-01-02 16:45:01</div>"
        self.assertEqual(parse_accepted_timestamp(page), "2024-01-02 16:45:01")

    def test_xml_link_parser_prefers_raw_primary_document(self):
        page = '<a href="xsl144X01/primary_doc.xml">XSL</a><a href="primary_doc.xml">XML</a><a href="ex99.pdf">EX</a>'
        links = xml_links(page)
        self.assertEqual(links[0], "primary_doc.xml")

    def test_sale_date_classification_does_not_call_it_execution(self):
        self.assertEqual(classify_sale_date("2026-11-02", "2026-11-03"), "sale_date_precedes_filing")
        self.assertEqual(classify_sale_date("2026-11-10", "2026-11-03"), "not_before_filing")
        self.assertEqual(classify_sale_date(None, "2026-11-03"), "unknown")

    def test_query_includes_originals_amendments_and_zero_padded_cik(self):
        url = query_url("1261333", "2025-01-01", "2025-03-31", 100)
        self.assertIn("forms=144%2C144%2FA", url)
        self.assertIn("ciks=0001261333", url)
        self.assertIn("from=100", url)

if __name__ == "__main__":
    unittest.main()
