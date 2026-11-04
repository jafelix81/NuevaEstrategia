import unittest
import xml.etree.ElementTree as ET

from research.phase65_form144_event_field_coverage_audit import (
    extract_tranches,
    normalize_accession,
    parse_date,
    parse_number,
    select_sample,
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
        self.assertEqual(len(first), 2 * (7 + 7 + 7))
        self.assertEqual(
            sum(row["sample_stratum"] == "unique_candidate" for row in first),
            14,
        )

    def test_extracts_multiple_tranches_without_collapsing(self):
        xml = """<edgarSubmission>
          <securitiesToBeSold>
            <securitiesClassTitle>Common Stock</securitiesClassTitle>
            <noOfUnitsSold>1,000</noOfUnitsSold>
            <aggregateMarketValue>$50,000</aggregateMarketValue>
            <approxSaleDate>11/10/2026</approxSaleDate>
          </securitiesToBeSold>
          <securitiesToBeSold>
            <securitiesClassTitle>Class B</securitiesClassTitle>
            <noOfUnitsSold>250</noOfUnitsSold>
            <aggregateMarketValue>$12,500</aggregateMarketValue>
            <approxSaleDate>2026-11-12</approxSaleDate>
          </securitiesToBeSold>
        </edgarSubmission>"""
        root = ET.fromstring(xml)
        parsed = {
            "security_class": ["Common Stock", "Class B"],
            "units_to_be_sold": "1,000",
            "aggregate_market_value": "$50,000",
            "approx_sale_date": "11/10/2026",
        }
        rows = extract_tranches(root, parsed)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["units_numeric"], 1000.0)
        self.assertEqual(rows[1]["value_numeric"], 12500.0)
        self.assertEqual(rows[1]["approx_sale_date_iso"], "2026-11-12")

    def test_fallback_single_tranche_when_wrapper_absent(self):
        root = ET.fromstring("<edgarSubmission/>")
        parsed = {
            "security_class": ["Common Stock"],
            "units_to_be_sold": "100",
            "aggregate_market_value": "2000",
            "approx_sale_date": "11/10/2026",
        }
        rows = extract_tranches(root, parsed)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["units_numeric"], 100.0)


if __name__ == "__main__":
    unittest.main()
