import unittest
import xml.etree.ElementTree as ET

from research.phase65_form144_event_field_coverage_audit import (
    extract_acquisition_lots,
    extract_prior_sales,
    extract_sale_tranches,
    normalize_accession,
    parse_date,
    parse_number,
    select_sample,
    resolve_candidate_role,
)


class TestPhase65Form144FieldCoverage(unittest.TestCase):
    def test_parse_edgar_and_iso_dates(self):
        self.assertEqual(parse_date("11/04/2026"), "2026-11-04")
        self.assertEqual(parse_date("2026-11-04"), "2026-11-04")
        self.assertIsNone(parse_date("not-a-date"))

    def test_parse_numeric_fields(self):
        self.assertEqual(parse_number("$1,234.50"), 1234.5)
        self.assertEqual(parse_number("(1,234.50)"), -1234.5)
        self.assertIsNone(parse_number("N/A"))

    def test_normalize_previous_accession(self):
        self.assertEqual(
            normalize_accession("0000019617-23-000374"),
            "0000019617-23-000374",
        )
        self.assertIsNone(normalize_accession("bad-accession"))

    def test_sample_is_deterministic_and_stratified(self):
        rows = []
        for form in ("144", "144/A"):
            for stratum in ("unique_candidate", "ambiguous", "control"):
                for i in range(7):
                    rows.append({
                        "year": 2025,
                        "quarter": 1,
                        "form": form,
                        "accession": f"{form}-{stratum}-{i}",
                        "pair_class": stratum,
                        "filing_date": "2025-01-02",
                    })
        first = select_sample(rows)
        second = select_sample(rows)
        self.assertEqual(
            [row["accession"] for row in first],
            [row["accession"] for row in second],
        )
        self.assertEqual(len(first), 42)
        self.assertEqual(
            sum(row["sample_stratum"] == "unique_candidate" for row in first),
            14,
        )

    def test_sale_tranches_are_separate_from_acquisition_lots(self):
        xml = """<edgarSubmission>
          <formData>
            <securitiesInformation>
              <securitiesClassTitle>Common Stock</securitiesClassTitle>
              <brokerOrMarketmakerDetails><name>Broker A</name></brokerOrMarketmakerDetails>
              <noOfUnitsSold>1,000</noOfUnitsSold>
              <aggregateMarketValue>50000.00</aggregateMarketValue>
              <noOfUnitsOutstanding>1000000</noOfUnitsOutstanding>
              <approxSaleDate>11/10/2026</approxSaleDate>
              <securitiesExchangeName>NASDAQ</securitiesExchangeName>
            </securitiesInformation>
            <securitiesInformation>
              <securitiesClassTitle>Class B</securitiesClassTitle>
              <brokerOrMarketmakerDetails><name>Broker B</name></brokerOrMarketmakerDetails>
              <noOfUnitsSold>250</noOfUnitsSold>
              <aggregateMarketValue>12500.00</aggregateMarketValue>
              <noOfUnitsOutstanding>500000</noOfUnitsOutstanding>
              <approxSaleDate>11/12/2026</approxSaleDate>
              <securitiesExchangeName>NYSE</securitiesExchangeName>
            </securitiesInformation>
            <securitiesToBeSold>
              <securitiesClassTitle>Common Stock</securitiesClassTitle>
              <acquiredDate>01/01/2020</acquiredDate>
              <natureOfAcquisitionTransaction>Stock Award</natureOfAcquisitionTransaction>
              <nameOfPersonfromWhomAcquired>Issuer</nameOfPersonfromWhomAcquired>
              <isGiftTransaction>N</isGiftTransaction>
              <amountOfSecuritiesAcquired>1000</amountOfSecuritiesAcquired>
              <paymentDate>01/01/2020</paymentDate>
              <natureOfPayment>Cash</natureOfPayment>
            </securitiesToBeSold>
            <securitiesSoldInPast3Months>
              <sellerDetails><name>Seller A</name></sellerDetails>
              <securitiesClassTitle>Common Stock</securitiesClassTitle>
              <saleDate>10/01/2026</saleDate>
              <amountOfSecuritiesSold>100</amountOfSecuritiesSold>
              <grossProceeds>4900.00</grossProceeds>
            </securitiesSoldInPast3Months>
          </formData>
        </edgarSubmission>"""
        root = ET.fromstring(xml)
        sales = extract_sale_tranches(root)
        acquisitions = extract_acquisition_lots(root)
        prior = extract_prior_sales(root)
        self.assertEqual(len(sales), 2)
        self.assertEqual(sales[0]["units_numeric"], 1000.0)
        self.assertEqual(sales[1]["value_numeric"], 12500.0)
        self.assertEqual(sales[1]["broker_or_market_maker"], "Broker B")
        self.assertEqual(len(acquisitions), 1)
        self.assertEqual(acquisitions[0]["amount_acquired_numeric"], 1000.0)
        self.assertEqual(len(prior), 1)
        self.assertEqual(prior[0]["amount_sold_numeric"], 100.0)

    def test_no_sale_information_does_not_fallback_to_acquisition_lots(self):
        root = ET.fromstring("""<edgarSubmission><securitiesToBeSold>
          <securitiesClassTitle>Common Stock</securitiesClassTitle>
          <amountOfSecuritiesAcquired>100</amountOfSecuritiesAcquired>
        </securitiesToBeSold></edgarSubmission>""")
        self.assertEqual(extract_sale_tranches(root), [])
        self.assertEqual(len(extract_acquisition_lots(root)), 1)



    def test_unique_candidate_filer_only_is_resolved_but_excluded_as_issuer(self):
        examples = [
            ("0001549802", "0001857816", "0001549802"),
            ("0000804328", "0001891027", "0000804328"),
        ]
        for candidate, issuer, filer in examples:
            identity = {
                "xml_issuer_cik": issuer,
                "xml_filer_cik": filer,
                "both_xml_ciks_in_pair": True,
                "unique_candidate_role": "filer",
            }
            result = resolve_candidate_role("unique_candidate", identity, [candidate])
            self.assertTrue(result["identity_resolved"])
            self.assertFalse(result["candidate_is_issuer"])
            self.assertTrue(result["candidate_is_filer_only"])

    def test_unique_candidate_issuer_is_target(self):
        identity = {
            "xml_issuer_cik": "0000000001",
            "xml_filer_cik": "0000000002",
            "both_xml_ciks_in_pair": True,
            "unique_candidate_role": "issuer",
        }
        result = resolve_candidate_role("unique_candidate", identity, ["0000000001"])
        self.assertTrue(result["identity_resolved"])
        self.assertTrue(result["candidate_is_issuer"])
        self.assertFalse(result["candidate_is_filer_only"])

    def test_ambiguous_pair_is_resolved_by_xml_roles(self):
        identity = {
            "xml_issuer_cik": "0000000001",
            "xml_filer_cik": "0000000002",
            "both_xml_ciks_in_pair": True,
            "unique_candidate_role": "ambiguous",
        }
        result = resolve_candidate_role("ambiguous", identity, ["0000000001", "0000000002"])
        self.assertTrue(result["identity_resolved"])
        self.assertTrue(result["candidate_is_issuer"])
        self.assertTrue(result["candidate_is_filer"])

    def test_unresolved_candidate_pair_does_not_pass(self):
        identity = {
            "xml_issuer_cik": "0000000003",
            "xml_filer_cik": "0000000004",
            "both_xml_ciks_in_pair": False,
            "unique_candidate_role": "unresolved",
        }
        result = resolve_candidate_role("unique_candidate", identity, ["0000000001"])
        self.assertFalse(result["identity_resolved"])
        self.assertFalse(result["candidate_is_issuer"])

if __name__ == "__main__":
    unittest.main()
