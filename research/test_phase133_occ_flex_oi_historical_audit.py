import io
import unittest
import zipfile

from research.phase133_occ_flex_oi_historical_audit import (
    flex_url, inspect_table, parse_flex_payload, parse_osi_root, parse_number,
)


class OCCFlexOITests(unittest.TestCase):
    def test_url_uses_documented_parameters(self):
        url = flex_url("2026-11-04")
        self.assertIn("reportType=OI", url)
        self.assertIn("optionType=E", url)
        self.assertIn("reportDate=20261104", url)

    def test_parse_number(self):
        self.assertEqual(parse_number("1,234"), 1234.0)
        self.assertEqual(parse_number("0"), 0.0)
        self.assertIsNone(parse_number("N/A"))

    def test_osi_root(self):
        self.assertEqual(parse_osi_root("AAPL  260116C00150000"), "AAPL")
        self.assertEqual(parse_osi_root("NVDA  260116P00100000"), "NVDA")
        self.assertIsNone(parse_osi_root("not-an-osi-symbol"))

    def test_csv_contract_level_schema(self):
        raw = (
            b"Underlying,Option Symbol,Expiration,Strike,Put/Call,Open Interest\n"
            b"AAPL,AAPL  260116C00150000,2026-01-16,150,C,1200\n"
            b"NVDA,NVDA  260116P00100000,2026-01-16,100,P,800\n"
        )
        parsed = parse_flex_payload(raw)
        metrics = inspect_table(parsed)
        self.assertTrue(metrics["contract_level_schema"])
        self.assertEqual(metrics["row_count"], 2)
        self.assertEqual(metrics["open_interest_nonnull_rows"], 2)
        self.assertEqual(metrics["unique_underlying_roots"], 2)
        self.assertEqual(metrics["unique_contract_keys"], 2)

    def test_zip_payload(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr(
                "oi.csv",
                "Underlying,Option Symbol,Open Interest\nAAPL,AAPL  260116C00150000,100\n",
            )
        parsed = parse_flex_payload(stream.getvalue())
        metrics = inspect_table(parsed)
        self.assertEqual(parsed["format"], "ZIP")
        self.assertEqual(parsed["member"], "oi.csv")
        self.assertTrue(metrics["contract_level_schema"])

    def test_underlying_can_be_reconstructed_from_osi(self):
        parsed = parse_flex_payload(
            b"Option Symbol,Open Interest\nNVDA  260116C00100000,500\n"
        )
        metrics = inspect_table(parsed)
        self.assertEqual(metrics["unique_underlying_roots"], 1)

    def test_non_tabular_html_does_not_pass(self):
        parsed = parse_flex_payload(b"<html><body>No report</body></html>")
        metrics = inspect_table(parsed)
        self.assertFalse(metrics["contract_level_schema"])
        self.assertEqual(metrics["row_count"], 0)


if __name__ == "__main__":
    unittest.main()
