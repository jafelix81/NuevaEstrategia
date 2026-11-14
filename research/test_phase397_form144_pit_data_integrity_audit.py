import csv
import json
import tempfile
import unittest
from pathlib import Path
from phase397_form144_pit_data_integrity_audit import audit

FIELDS = [
    "accession", "form", "filing_date", "notice_date", "candidate_tickers",
    "candidate_role_status", "xml_issuer_cik", "xml_filer_cik", "issuer_name",
    "seller_name", "sale_tranche_count", "sale_units_total", "sale_value_total",
    "sale_units_all_numeric", "sale_value_all_numeric", "sale_outstanding_all_numeric",
    "sale_tranches_json", "previous_accession", "previous_accession_in_14q_census",
    "mentions_10b5_1", "plan_adoption_dates",
]

def make_row(accession, form, filing_date, notice_date, tickers, tranches,
             previous="", previous_in="False", b10="False"):
    units = sum(float(t.get("units_numeric", 0)) for t in tranches)
    value = sum(float(t.get("value_numeric", 0)) for t in tranches)
    return {
        "accession": accession, "form": form, "filing_date": filing_date,
        "notice_date": notice_date, "candidate_tickers": tickers,
        "candidate_role_status": "issuer_match", "xml_issuer_cik": "0000000001",
        "xml_filer_cik": "0000000002", "issuer_name": "Example Issuer",
        "seller_name": "Example Seller", "sale_tranche_count": str(len(tranches)),
        "sale_units_total": str(units), "sale_value_total": str(value),
        "sale_units_all_numeric": "True", "sale_value_all_numeric": "True",
        "sale_outstanding_all_numeric": "True", "sale_tranches_json": json.dumps(tranches),
        "previous_accession": previous, "previous_accession_in_14q_census": previous_in,
        "mentions_10b5_1": b10, "plan_adoption_dates": "",
    }

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "issuer_event_raw.csv"
        normal = [{"security_class": "Common", "units_numeric": 100, "value_numeric": 1000, "outstanding_numeric": 10000}]
        multi_bad = [
            {"security_class": "Class A", "units_numeric": 0, "value_numeric": 0, "outstanding_numeric": 0},
            {"security_class": "Class B", "units_numeric": 50, "value_numeric": 500, "outstanding_numeric": 1000},
        ]
        data = [
            make_row("0000000001-23-000001", "144", "2023-05-01", "05/01/2023", "AAA", normal),
            make_row("0000000001-23-000002", "144", "2023-05-02", "04/29/2023", "AAA;AAB", multi_bad),
            make_row("0000000001-23-000003", "144/A", "2023-05-03", "05/04/2023", "BBB", normal,
                     previous="0000000001-23-000001", previous_in="True", b10="True"),
        ]
        with self.path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(data)

    def tearDown(self):
        self.tmp.cleanup()

    def test_notice_date_is_not_assumed_to_be_filing_date(self):
        result = audit(self.path)
        self.assertEqual(result["notice_date_mismatch_rows"], 2)
        self.assertEqual(result["notice_date_earlier_than_filing_rows"], 1)
        self.assertEqual(result["notice_date_later_than_filing_rows"], 1)

    def test_ticker_ambiguity_and_tranche_quality_are_separate_gates(self):
        result = audit(self.path)
        self.assertEqual(result["multi_candidate_ticker_rows"], 1)
        self.assertEqual(result["multi_tranche_events"], 1)
        self.assertEqual(result["zero_or_invalid_units_events"], 1)
        self.assertEqual(result["zero_or_invalid_value_events"], 1)
        self.assertEqual(result["zero_or_invalid_outstanding_events"], 1)

    def test_acceptance_timestamp_absence_and_amendment_lineage(self):
        result = audit(self.path)
        self.assertEqual(result["accepted_timestamp_columns"], [])
        self.assertEqual(result["accepted_timestamp_gate"], "NOT_TESTED_NOT_PRESENT_IN_PHASE67_EVENT_CSV")
        self.assertEqual(result["form144a_rows"], 1)
        self.assertEqual(result["form144a_parent_reference_in_census"], 1)
        self.assertEqual(result["mentions_10b5_1_rows"], 1)
        self.assertFalse(result["economic_test_authorized"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
