import io
import unittest
import zipfile

from research.phase174_cboe_option_quotes_sample_audit import (
    BASE_REQUIRED, audit_archive, audit_csv_bytes, parse_quote_datetime,
)


def make_csv(header=None, rows=None):
    header = header or list(BASE_REQUIRED) + [
        "active_underlying_price", "implied_underlying_price", "implied_volatility",
        "delta", "gamma", "theta", "vega", "rho", "open_interest",
    ]
    rows = rows if rows is not None else [[
        "SPY", "2025-03-28 09:31:00", "SPY", "2025-04-17", "500", "C",
        "1.0", "1.1", "0.9", "1.05", "10", "20", "1.00", "15", "1.10",
        "570.00", "570.10", "570.05", "0.25", "0.55", "0.02", "0.01",
        "-0.03", "0.10", "0.01", "1200",
    ]]
    lines = [",".join(header)] + [",".join(str(x) for x in row) for row in rows]
    return ("\n".join(lines) + "\n").encode()


class Phase174Tests(unittest.TestCase):
    def test_valid_quote_interval_row_passes(self):
        result = audit_csv_bytes(make_csv())
        self.assertTrue(result["schema_gate_pass"])
        self.assertEqual(result["populated_rows"], 1)
        self.assertEqual(result["underlying_count"], 1)
        self.assertIsNone(result["modal_interval_seconds"])

    def test_end_of_interval_timestamp_accepts_fractional_seconds(self):
        self.assertEqual(parse_quote_datetime("2025-03-28 09:31:00.123").second, 0)

    def test_timezone_suffix_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_quote_datetime("2025-03-28 09:31:00-04:00")

    def test_missing_required_field_fails_schema(self):
        header = [x for x in BASE_REQUIRED if x != "quote_datetime"]
        row = ["SPY", "SPY", "2025-04-17", "500", "C", "1", "1", "1", "1",
               "1", "1", "1", "1", "1", "1", "1"]
        result = audit_csv_bytes(make_csv(header, [row]))
        self.assertIn("quote_datetime", result["missing_required_fields"])
        self.assertFalse(result["schema_gate_pass"])

    def test_invalid_option_type_fails_row_gate(self):
        row = make_csv().decode().splitlines()[1].split(",")
        row[5] = "X"
        result = audit_csv_bytes(make_csv(rows=[row]))
        self.assertFalse(result["row_gate_pass"])
        self.assertEqual(result["invalid_contract_rows"], 1)

    def test_empty_trailing_rows_are_not_counted_as_contracts(self):
        payload = make_csv() + b",,,,,,,,,,,,,,,,,,,,,,,,,\n"
        result = audit_csv_bytes(payload)
        self.assertEqual(result["populated_rows"], 1)
        self.assertEqual(result["empty_rows"], 1)
        self.assertTrue(result["row_gate_pass"])

    def test_duplicate_contract_interval_key_is_detected(self):
        row = make_csv().decode().splitlines()[1]
        result = audit_csv_bytes(make_csv(rows=[row.split(","), row.split(",")]))
        self.assertEqual(result["duplicate_contract_interval_keys"], 1)
        self.assertFalse(result["row_gate_pass"])

    def test_sod_open_interest_must_be_static_within_contract_day(self):
        row1 = make_csv().decode().splitlines()[1].split(",")
        row2 = row1.copy()
        row2[1] = "2025-03-28 09:32:00"
        row2[-1] = "1300"
        result = audit_csv_bytes(make_csv(rows=[row1, row2]))
        self.assertEqual(result["contract_days_with_inconsistent_sod_oi"], 1)

    def test_zero_iv_with_nonzero_greeks_is_counted_not_rejected(self):
        row = make_csv().decode().splitlines()[1].split(",")
        row[19] = "0"
        result = audit_csv_bytes(make_csv(rows=[row]))
        self.assertEqual(result["zero_iv_nonzero_greeks_rows"], 1)
        self.assertTrue(result["row_gate_pass"])

    def test_zero_oi_and_zero_volume_are_valid_observations(self):
        row = make_csv().decode().splitlines()[1].split(",")
        row[10] = "0"
        row[-1] = "0"
        result = audit_csv_bytes(make_csv(rows=[row]))
        self.assertEqual(result["zero_open_interest_rows"], 1)
        self.assertEqual(result["zero_trade_volume_rows"], 1)
        self.assertTrue(result["row_gate_pass"])

    def test_unknown_header_field_is_quarantined(self):
        header = list(BASE_REQUIRED) + ["mystery_field"]
        row = ["SPY", "2025-03-28 09:31:00", "SPY", "2025-04-17", "500", "C",
               "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "extra"]
        result = audit_csv_bytes(make_csv(header, [row]))
        self.assertIn("mystery_field", result["unknown_fields"])
        self.assertFalse(result["schema_gate_pass"])

    def test_archive_audit_does_not_persist_symbols_or_rows(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("sample.csv", make_csv())
        result = audit_archive(buf.getvalue())
        self.assertTrue(result["sample_schema_gate_pass"])
        self.assertFalse(result["sample_admission"])
        self.assertFalse(result["pit_admission"])
        self.assertFalse(result["alpha_admission"])
        self.assertFalse(result["members"][0]["raw_symbols_persisted"])
        self.assertFalse(result["members"][0]["raw_rows_persisted"])

    def test_archive_without_csv_fails_sample_gate(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("readme.txt", "no data")
        result = audit_archive(buf.getvalue())
        self.assertFalse(result["sample_schema_gate_pass"])

    def test_calcs_and_open_interest_are_optional_schema_variants(self):
        base_row = make_csv().decode().splitlines()[1].split(",")[:len(BASE_REQUIRED)]
        result = audit_csv_bytes(make_csv(header=list(BASE_REQUIRED), rows=[base_row]))
        self.assertTrue(result["schema_gate_pass"])
        self.assertFalse(result["calcs_present"])
        self.assertFalse(result["open_interest_present"])


if __name__ == "__main__":
    unittest.main()
