import unittest

from research.phase136_cboe_volatility_surface_sample_audit import (
    classify_surface, inspect_csv, parse_num, parse_time,
)


class Phase136Tests(unittest.TestCase):
    def test_parse_time_accepts_milliseconds(self):
        self.assertTrue(parse_time("09:40:00.123"))
        self.assertTrue(parse_time("16:00:00"))
        self.assertFalse(parse_time("25:00:00"))

    def test_parse_num_rejects_nan_and_text(self):
        self.assertIsNone(parse_num("nan"))
        self.assertIsNone(parse_num("not-a-number"))
        self.assertEqual(parse_num("12.5"), 12.5)

    def test_classify_constant_maturity_delta_from_schema(self):
        headers = ["underlying_symbol", "maturity", "timestamp", "iv_25_delta"]
        self.assertEqual(classify_surface(headers, "unknown.csv"), "constant_maturity_delta")

    def test_classify_expiration_specific_price_from_filename(self):
        self.assertEqual(
            classify_surface([], "VolatilitySurfaces_ExpirationSpecificPriceRelative_2025-01-02.csv"),
            "expiration_specific_price",
        )

    def test_inspect_csv_counts_confidence_codes_and_duplicate_keys(self):
        payload = (
            "underlying_symbol,expiry,timestamp,underlying_price,"
            "iv_25_delta,iv_50_delta,iv_75_delta,"
            "strike_25_delta,strike_50_delta,strike_75_delta,"
            "conf_25_delta,conf_50_delta,conf_75_delta\n"
            "ABC,2025-01-17,09:40:00.123,100,0.25,0.20,0.22,90,100,110,0.8,0.4,-1\n"
            "ABC,2025-01-17,09:40:00.123,100,0.26,0.21,0.23,90,100,110,0.9,0.7,-5\n"
        ).encode()
        result = inspect_csv(payload, "ExpirationSpecificDeltaRelative.csv")
        self.assertEqual(result["surface_type"], "expiration_specific_delta")
        self.assertTrue(result["schema_ok"])
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["underlying_count"], 1)
        self.assertEqual(result["duplicate_surface_key_rows"], 1)
        self.assertEqual(result["negative_confidence_code_cells"], 2)
        self.assertEqual(result["confidence_below_0_5_cells"], 3)

    def test_inspect_csv_rejects_missing_required_columns(self):
        payload = b"underlying_symbol,timestamp,iv_25_delta\nABC,09:40:00,0.2\n"
        result = inspect_csv(payload, "unknown.csv")
        self.assertFalse(result["schema_ok"])
        self.assertEqual(result["row_count"], 1)


if __name__ == "__main__":
    unittest.main()
