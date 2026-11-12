import unittest

from research.phase315_nport_position_identifier_attribute_audit import (
    exposure_metrics,
    identifier_metrics,
    phase314_signature,
)


class Phase315IdentifierAuditTests(unittest.TestCase):
    def test_identifier_metrics_counts_missing_values_and_valid_checks(self):
        rows = [
            {"cusip":"037833100","isin":"US0378331005","ticker":"AAPL"},
            {"cusip":"594918104","isin":"US5949181045","ticker":""},
        ]
        result = identifier_metrics(rows)
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["cusip_present"], 2)
        self.assertEqual(result["isin_present"], 2)
        self.assertEqual(result["ticker_present"], 1)

    def test_exposure_metrics_sums_absolute_reported_values(self):
        rows = [
            {"value_usd":"-100.50","percentage_nav":"-1.25"},
            {"value_usd":"-200.25","percentage_nav":"-0.75"},
        ]
        result = exposure_metrics(rows)
        self.assertEqual(result["absolute_reported_short_value_usd"], "300.75")
        self.assertEqual(result["absolute_reported_short_pct_nav_points"], "2.00")

    def test_phase314_signature_includes_security_identifiers(self):
        row = {
            "cusip":"037833100","isin":"US0378331005","ticker":"AAPL",
            "balance":"-10","value_usd":"-1000","percentage_nav":"-0.1",
        }
        self.assertEqual(
            phase314_signature(row),
            ("037833100","US0378331005","AAPL","-10","-1000","-0.1"),
        )

    def test_exposure_metrics_rejects_missing_numeric_values(self):
        with self.assertRaises(Exception):
            exposure_metrics([{"value_usd":"","percentage_nav":"-1"}])


if __name__ == "__main__":
    unittest.main()
