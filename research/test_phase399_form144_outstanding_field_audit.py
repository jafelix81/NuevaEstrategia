import csv
import json
import tempfile
import unittest
from pathlib import Path

from phase399_form144_outstanding_field_audit import audit


def row(accession, tranches, form="144"):
    return {
        "accession": accession,
        "form": form,
        "filing_date": "2026-01-02",
        "issuer_name": "Test Issuer",
        "candidate_tickers": "TEST",
        "sale_tranches_json": json.dumps(tranches),
    }


class Phase399Tests(unittest.TestCase):
    def run_audit(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            fields = list(rows[0])
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            return audit(path)

    def test_raw_ratio_is_diagnostic_not_authorized_feature(self):
        result = self.run_audit([
            row("wday-like", [{
                "units_numeric": 4223,
                "units_to_be_sold": "4223",
                "outstanding_numeric": 261,
                "units_outstanding": "261",
                "aggregate_market_value": "935114.28",
            }])
        ])
        self.assertEqual(result["raw_ratio_threshold_counts"]["greater_than_100pct"], 1)
        self.assertFalse(result["denominator_unit_metadata_present"])
        self.assertFalse(result["denominator_scale_rule_established"])
        self.assertFalse(result["normalized_outstanding_ratio_authorized"])
        self.assertFalse(result["use_for_feature_engineering"])

    def test_zero_and_missing_denominators_are_not_divided(self):
        result = self.run_audit([
            row("zero", [{
                "units_numeric": 100,
                "units_to_be_sold": "100",
                "outstanding_numeric": 0,
                "units_outstanding": "0",
            }]),
            row("missing", [{
                "units_numeric": 50,
                "units_to_be_sold": "50",
                "outstanding_numeric": None,
                "units_outstanding": "",
            }], form="144/A"),
        ])
        self.assertEqual(result["tranches_with_missing_or_nonpositive_outstanding"], 2)
        self.assertEqual(result["tranches_with_valid_raw_ratio"], 0)
        self.assertIsNone(result["raw_ratio_max"])

    def test_thresholds_use_strict_greater_than(self):
        result = self.run_audit([
            row("thresholds", [
                {"units_numeric": 1, "units_to_be_sold": "1", "outstanding_numeric": 100, "units_outstanding": "100"},
                {"units_numeric": 10, "units_to_be_sold": "10", "outstanding_numeric": 100, "units_outstanding": "100"},
                {"units_numeric": 100, "units_to_be_sold": "100", "outstanding_numeric": 100, "units_outstanding": "100"},
            ])
        ])
        self.assertEqual(result["raw_ratio_threshold_counts"]["greater_than_1pct"], 2)
        self.assertEqual(result["raw_ratio_threshold_counts"]["greater_than_10pct"], 1)
        self.assertEqual(result["raw_ratio_threshold_counts"]["greater_than_100pct"], 0)

    def test_multiple_tranches_are_counted_independently(self):
        result = self.run_audit([
            row("multi", [
                {"units_numeric": 10, "units_to_be_sold": "10", "outstanding_numeric": 1000, "units_outstanding": "1000"},
                {"units_numeric": 20, "units_to_be_sold": "20", "outstanding_numeric": 1000, "units_outstanding": "1000"},
            ])
        ])
        self.assertEqual(result["issuer_event_rows"], 1)
        self.assertEqual(result["tranche_rows"], 2)
        self.assertEqual(result["tranches_with_valid_raw_ratio"], 2)


if __name__ == "__main__":
    unittest.main()
