import io
import unittest
import zipfile
import csv
from research.phase114_cboe_openclose_eod_sample_audit import POST_2011_REQUIRED, collect_csv_payloads, parse_csv_bytes

def make_row(**overrides):
    row = {name: "0" for name in POST_2011_REQUIRED}
    row.update({
        "quote_date": "03/28/2025", "underlying_symbol": "AAPL", "security_type": "1",
        "option_symbol": "AAPL", "expiration_date": "2025-03-28", "strike_price": "200",
        "call_put_flag": "C", "days_to_expire": "0", "series_type": "S",
        "total_exchange_vol": "10", "total_industry_vol": "100",
        "open_interest": "200", "previous_open_interest": "190",
        "firm_open_buy_vol": "5", "mm_sell_vol": "5",
    })
    row.update(overrides)
    return row

def csv_bytes(rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=POST_2011_REQUIRED)
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()

class Phase114OpenCloseTests(unittest.TestCase):
    def test_post_2011_schema_has_86_fields(self):
        self.assertEqual(len(POST_2011_REQUIRED), 86)

    def test_buy_sell_buckets_reconcile_to_both_sides_exchange_volume(self):
        result = parse_csv_bytes(csv_bytes([make_row()]))
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["missing_required_fields"], [])
        self.assertEqual(result["volume_reconciliation_eligible_rows"], 1)
        self.assertEqual(result["volume_reconciliation_exact_rows"], 1)
        self.assertEqual(result["buy_bucket_volume_sum"], 5)
        self.assertEqual(result["sell_bucket_volume_sum"], 5)

    def test_volume_mismatch_is_reported_not_silently_repaired(self):
        result = parse_csv_bytes(csv_bytes([make_row(total_exchange_vol="11")]))
        self.assertEqual(result["volume_reconciliation_exact_rows"], 0)
        self.assertEqual(result["volume_reconciliation_mismatch_samples"][0]["difference"], -1)

    def test_duplicate_series_key_is_detected(self):
        result = parse_csv_bytes(csv_bytes([make_row(), make_row()]))
        self.assertEqual(result["duplicate_key_excess"], 1)

    def test_negative_or_noninteger_volume_fails_numeric_audit(self):
        result = parse_csv_bytes(csv_bytes([make_row(firm_open_buy_vol="-1", mm_sell_vol="0.5")]))
        self.assertEqual(result["numeric_error_counts"]["negative_volume"], 1)
        self.assertEqual(result["numeric_error_counts"]["invalid_mm_sell_vol"], 1)

    def test_missing_required_field_is_reported(self):
        result = parse_csv_bytes(b"quote_date,underlying_symbol\n03/28/2025,AAPL\n")
        self.assertIn("total_exchange_vol", result["missing_required_fields"])

    def test_nested_zip_csv_is_found(self):
        payload = csv_bytes([make_row()])
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w") as z:
            z.writestr("C1OpenClose_2025-03-28.csv", payload)
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, "w") as z:
            z.writestr("nested.zip", inner.getvalue())
        found, entries = collect_csv_payloads(outer.getvalue(), "outer.zip")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["name"], "outer.zip!nested.zip!C1OpenClose_2025-03-28.csv")
        self.assertTrue(entries)

if __name__ == "__main__":
    unittest.main()
