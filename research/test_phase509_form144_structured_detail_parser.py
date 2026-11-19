import csv
import tempfile
import unittest
from pathlib import Path

from research import phase509_form144_structured_detail_parser as p509


XML = """<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns:com="http://www.sec.gov/edgar/common">
  <submissionType>144</submissionType>
  <filerCredentials><cik>0000123456</cik></filerCredentials>
  <issuerInfo>
    <issuerCik>0000654321</issuerCik>
    <issuerName>Example Corp</issuerName>
    <relationshipsToIssuer>
      <relationshipToIssuer>Officer</relationshipToIssuer>
      <relationshipToIssuer>Director</relationshipToIssuer>
    </relationshipsToIssuer>
  </issuerInfo>
  <nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold>Jane Seller</nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold>
  <previousAccessionNumber>000000000126000001</previousAccessionNumber>
  <securitiesInformation>
    <securitiesClassTitle>Class A Common Stock</securitiesClassTitle>
    <brokerOrMarketmakerDetails><name>Example Broker</name></brokerOrMarketmakerDetails>
    <noOfUnitsSold>1,250</noOfUnitsSold>
    <aggregateMarketValue>125000.50</aggregateMarketValue>
    <noOfUnitsOutstanding>10000000</noOfUnitsOutstanding>
    <approxSaleDate>11/20/2026</approxSaleDate>
    <securitiesExchangeName>NASDAQ</securitiesExchangeName>
  </securitiesInformation>
  <securitiesInformation>
    <securitiesClassTitle>Class A Common Stock</securitiesClassTitle>
    <brokerOrMarketmakerDetails><name>Second Broker</name></brokerOrMarketmakerDetails>
    <noOfUnitsSold>250</noOfUnitsSold>
    <aggregateMarketValue>25000</aggregateMarketValue>
    <noOfUnitsOutstanding>10000000</noOfUnitsOutstanding>
    <approxSaleDate>11/19/2026</approxSaleDate>
    <securitiesExchangeName>NASDAQ</securitiesExchangeName>
  </securitiesInformation>
  <securitiesToBeSold>
    <securitiesClassTitle>Class A Common Stock</securitiesClassTitle>
    <acquiredDate>11/01/2026</acquiredDate>
    <natureOfAcquisitionTransaction>Restricted Stock Units</natureOfAcquisitionTransaction>
    <nameOfPersonfromWhomAcquired>Issuer</nameOfPersonfromWhomAcquired>
    <isGiftTransaction>N</isGiftTransaction>
    <amountOfSecuritiesAcquired>1,500</amountOfSecuritiesAcquired>
    <paymentDate>11/01/2026</paymentDate>
    <natureOfPayment>N/A</natureOfPayment>
  </securitiesToBeSold>
  <nothingToReportFlagOnSecuritiesSoldInPast3Months>N</nothingToReportFlagOnSecuritiesSoldInPast3Months>
  <securitiesSoldInPast3Months>
    <sellerDetails><name>Jane Seller</name></sellerDetails>
    <securitiesClassTitle>Class A Common Stock</securitiesClassTitle>
    <saleDate>10/15/2026</saleDate>
    <amountOfSecuritiesSold>500</amountOfSecuritiesSold>
    <grossProceeds>50000</grossProceeds>
  </securitiesSoldInPast3Months>
  <remarks>Sales are intended to cover tax withholding. No statement that this is an active 10b5-1 plan.</remarks>
  <noticeSignature>
    <noticeDate>11/19/2026</noticeDate>
    <planAdoptionDates><planAdoptionDate>11/01/2025</planAdoptionDate></planAdoptionDates>
    <signature>/s/ Jane Seller</signature>
  </noticeSignature>
</edgarSubmission>
"""


class Phase509Tests(unittest.TestCase):
    def test_extracts_proposed_sales_acquisitions_and_prior_sales_separately(self):
        parsed = p509.parse_form144_details(XML)
        self.assertEqual(parsed["submission_type"], "144")
        self.assertEqual(parsed["issuer_cik"], "0000654321")
        self.assertEqual(parsed["filer_cik"], "0000123456")
        self.assertEqual(parsed["seller_name"], "Jane Seller")
        self.assertEqual(parsed["previous_accession"], "0000000001-26-000001")
        self.assertEqual(parsed["relationships_to_issuer"], ["Officer", "Director"])
        self.assertEqual(len(parsed["sale_tranches"]), 2)
        self.assertEqual(parsed["sale_tranches"][0]["proposed_units_numeric"], "1250")
        self.assertEqual(parsed["sale_tranches"][0]["aggregate_market_value_numeric"], "125000.5")
        self.assertEqual(parsed["sale_tranches"][0]["broker_or_market_maker"], "Example Broker")
        self.assertEqual(len(parsed["acquisition_lots"]), 1)
        self.assertEqual(parsed["acquisition_lots"][0]["amount_acquired_numeric"], "1500")
        self.assertEqual(parsed["acquisition_lots"][0]["nature_of_acquisition"], "Restricted Stock Units")
        self.assertEqual(len(parsed["prior_sales"]), 1)
        self.assertEqual(parsed["prior_sales"][0]["prior_sale_amount_numeric"], "500")
        self.assertEqual(parsed["prior_sales"][0]["prior_sale_gross_proceeds_numeric"], "50000")

    def test_notice_plan_and_remarks_are_descriptive_not_an_active_plan_signal(self):
        parsed = p509.parse_form144_details(XML)
        self.assertEqual(parsed["notice_date_iso"], "2026-11-19")
        self.assertEqual(parsed["plan_adoption_dates"], ["11/01/2025"])
        self.assertTrue(parsed["mentions_10b5_1_in_remarks"])
        self.assertNotIn("active_10b5_1_plan", parsed)
        self.assertEqual(parsed["nothing_to_report_flag"], "N")

    def test_approximate_sale_date_relation_is_only_a_date_comparison(self):
        parsed = p509.parse_form144_details(XML)
        rows = p509.build_detail_rows(
            {"accession": "0000000001-26-000002", "form": "144",
             "xml_sha256": "abc", "first_seen_at_utc": "2026-11-19T21:00:00Z",
             "first_seen_interval_status": "BOUNDED_BY_SUCCESSIVE_SUCCESSFUL_POLLS",
             "research_observation_eligible": True},
            {"xml_sha256": "abc", "structured_details": parsed, "structured_parse_status": "parsed"},
        )
        proposed = [r for r in rows if r["detail_section"] == "securities_information"]
        self.assertEqual(proposed[0]["approx_sale_date_relation_to_notice"], "after_notice_date")
        self.assertEqual(proposed[1]["approx_sale_date_relation_to_notice"], "same_as_notice_date")
        self.assertTrue(all(r["signal_eligible"] is False for r in rows))
        self.assertTrue(all(r["same_day_intraday_use_authorized"] is False for r in rows))

    def test_missing_and_invalid_numbers_dates_remain_missing_not_zero(self):
        xml = """<edgarSubmission><submissionType>144</submissionType>
        <issuerInfo><issuerCik>0000000001</issuerCik><issuerName>Test</issuerName></issuerInfo>
        <securitiesInformation><noOfUnitsSold>unknown</noOfUnitsSold>
        <aggregateMarketValue></aggregateMarketValue><noOfUnitsOutstanding>0</noOfUnitsOutstanding>
        <approxSaleDate>not-a-date</approxSaleDate></securitiesInformation>
        </edgarSubmission>"""
        parsed = p509.parse_form144_details(xml)
        tranche = parsed["sale_tranches"][0]
        self.assertIsNone(tranche["proposed_units_numeric"])
        self.assertIsNone(tranche["aggregate_market_value_numeric"])
        self.assertEqual(tranche["units_outstanding_numeric"], "0")
        self.assertIsNone(tranche["approx_sale_date_iso"])

    def test_wrong_root_and_form_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "root"):
            p509.parse_form144_details("<root><submissionType>144</submissionType></root>")
        with self.assertRaisesRegex(ValueError, "submissionType"):
            p509.parse_form144_details("<edgarSubmission><submissionType>4</submissionType></edgarSubmission>")

    def test_source_hash_mismatch_is_preserved_and_not_promoted(self):
        parsed = p509.parse_form144_details(XML)
        event = {"accession": "0000000001-26-000002", "form": "144",
                 "xml_sha256": "old-hash", "research_observation_eligible": True}
        metadata = {"xml_sha256": "new-hash", "structured_details": parsed,
                    "structured_parse_status": "parsed"}
        rows = p509.build_detail_rows(event, metadata)
        self.assertTrue(rows)
        self.assertTrue(all(r["parse_status"] == "source_hash_mismatch" for r in rows))
        self.assertTrue(all(r["source_xml_hash_matches_event"] is False for r in rows))
        self.assertTrue(all(r["signal_eligible"] is False for r in rows))

    def test_append_is_idempotent_and_preserves_separate_row_types(self):
        parsed = p509.parse_form144_details(XML)
        event = {"accession": "0000000001-26-000002", "form": "144",
                 "xml_sha256": "abc", "first_seen_at_utc": "2026-11-19T21:00:00Z"}
        metadata = {"xml_sha256": "abc", "structured_details": parsed,
                    "structured_parse_status": "parsed"}
        rows = p509.build_detail_rows(event, metadata)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sale_details.csv"
            self.assertEqual(p509.append_detail_rows(path, rows), len(rows))
            self.assertEqual(p509.append_detail_rows(path, rows), 0)
            with path.open("r", newline="", encoding="utf-8") as handle:
                stored = list(csv.DictReader(handle))
            self.assertEqual(len(stored), len(rows))
            self.assertEqual({x["detail_section"] for x in stored},
                             {"filing_header", "securities_information",
                              "securities_to_be_sold", "securities_sold_in_past_3_months"})
            self.assertIn(event["accession"], p509.read_completed_accessions(path))

    def test_no_units_outstanding_ratio_is_computed_or_authorized(self):
        parsed = p509.parse_form144_details(XML)
        rows = p509.build_detail_rows(
            {"accession": "0000000001-26-000002", "form": "144", "xml_sha256": "abc"},
            {"xml_sha256": "abc", "structured_details": parsed, "structured_parse_status": "parsed"},
        )
        self.assertNotIn("outstanding_ratio", {k for row in rows for k in row})
        self.assertTrue(all(row["signal_eligible"] is False for row in rows))


    def test_parse_number_handles_parenthetical_negative_currency_and_invalid_values(self):
        self.assertEqual(p509.parse_number("($1,234.50)"), "-1234.5")
        self.assertEqual(p509.parse_number("USD 1,000"), "1000")
        self.assertIsNone(p509.parse_number("N/A"))

    def test_parse_date_supports_two_digit_year_and_timestamp(self):
        self.assertEqual(p509.parse_date("11/19/26"), "2026-11-19")
        self.assertEqual(p509.parse_date("2026-11-19T12:34:56"), "2026-11-19")


    def test_detail_ledger_preserves_source_path_and_separate_retrieval_clock(self):
        parsed = p509.parse_form144_details(XML)
        event = {
            "accession": "0000000001-26-000002", "form": "144",
            "feed_name": "144", "feed_names": '["144"]',
            "feed_path_cik": "0000654321", "first_seen_at_utc": "2026-11-19T21:00:00Z",
            "xml_sha256": "abc",
        }
        metadata = {
            "xml_sha256": "abc", "structured_details": parsed,
            "structured_parse_status": "parsed",
            "xml_source": "complete_submission_xml_block",
            "submission_txt_status": "retrieved",
            "xml_retrieved_at_utc": "2026-11-19T22:27:00Z",
        }
        row = p509.build_detail_rows(event, metadata)[0]
        self.assertEqual(row["feed_name"], "144")
        self.assertEqual(row["archive_path_cik"], "0000654321")
        self.assertEqual(row["xml_source"], "complete_submission_xml_block")
        self.assertEqual(row["submission_txt_status"], "retrieved")
        self.assertEqual(row["detail_retrieved_at_utc"], "2026-11-19T22:27:00Z")
        self.assertNotEqual(row["detail_retrieved_at_utc"], row["first_seen_at_utc"])


if __name__ == "__main__":
    unittest.main()
