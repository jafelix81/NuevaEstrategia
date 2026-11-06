import csv
import gzip
import io
import json
import unittest

from research.phase167_cboe_openclose_v18_public_sample_audit import (
    SAMPLE_URL, SampleAuditError, audit_payload, bucket_columns,
    expected_columns, parse_sample_filename,
)


def synthetic_gzip(rows=1, *, interval=1, mutate_header=None):
    columns = expected_columns(interval)
    if mutate_header == "missing":
        columns = columns[:-1]
    elif mutate_header == "extra":
        columns = columns + ["unexpected"]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    base = {name: "0" for name in columns}
    base.update({
        "trade_datetime": "2026-09-30 15:20:00", "underlying": "AAPL",
        "security_type": "1", "option_symbol": "AAPL  261218C00200000",
        "expiration_date": "20261218", "strike_price": "200",
        "call_or_put": "C", "days_to_expire": "79", "series_type": "S",
        "previous_close": "250", "trading_dt": "2026-09-30", "trading_segment": "1",
    })
    if interval == 10:
        base["call_put_flag"] = "C"
        base.pop("call_or_put", None)
    for _ in range(rows):
        writer.writerow({k: base.get(k, "0") for k in columns})
    return gzip.compress(buffer.getvalue().encode("utf-8"))


class Phase167Tests(unittest.TestCase):
    def test_1m_schema_has_80_columns(self):
        columns = expected_columns(1)
        self.assertEqual(len(columns), 80)
        self.assertIn("call_or_put", columns)
        self.assertNotIn("call_put_flag", columns)

    def test_10m_schema_has_80_columns(self):
        columns = expected_columns(10)
        self.assertEqual(len(columns), 80)
        self.assertIn("call_put_flag", columns)
        self.assertNotIn("call_or_put", columns)

    def test_bucket_column_count(self):
        self.assertEqual(len(bucket_columns()), 68)

    def test_10m_pdf_name_keeps_qty_suffix(self):
        columns = expected_columns(10)
        self.assertIn("cust_gt_199_close_buy_qty", columns)
        self.assertNotIn("cust_gt_199_clsoe_buy_qty", columns)
        self.assertNotIn("cust_gt_199_close_buy", columns)

    def test_1m_columns_are_lowercase(self):
        self.assertTrue(all(c == c.lower() for c in expected_columns(1)))

    def test_sample_filename_parses(self):
        parsed = parse_sample_filename(SAMPLE_URL)
        self.assertEqual(parsed["market_date"], "2026-09-30")
        self.assertEqual(parsed["snapshot_time_et"], "15:20")
        self.assertEqual(parsed["trading_segment_suffix"], 1)

    def test_sample_filename_rejects_unknown_path(self):
        with self.assertRaisesRegex(SampleAuditError, "filename_unrecognized"):
            parse_sample_filename("https://example.com/sample.csv.gz")

    def test_clean_synthetic_sample_passes_schema(self):
        result = audit_payload(synthetic_gzip(), {"content-type": "application/gzip", "etag": "fixture"},
                               retrieved_at_utc="2026-11-06T19:00:00+00:00")
        self.assertEqual(result["status"], "PASS_SCHEMA_SAMPLE")
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["actual_column_count"], 80)
        self.assertEqual(result["unique_underlying_count"], 1)
        self.assertFalse(result["strict_pit"])
        self.assertEqual(result["capture_mode"], "PUBLIC_SAMPLE_ARCHIVE_BACKFILL")

    def test_raw_symbol_is_not_persisted_in_summary(self):
        result = audit_payload(synthetic_gzip())
        self.assertNotIn("AAPL", json.dumps(result))
        self.assertFalse(result["raw_rows_persisted"])
        self.assertFalse(result["raw_sample_persisted"])

    def test_duplicate_series_is_diagnostic_not_silently_deduped(self):
        result = audit_payload(synthetic_gzip(rows=2))
        self.assertEqual(result["duplicate_series_rows"], 1)
        self.assertEqual(result["row_quality_status"], "PASS_WITH_ROW_DIAGNOSTICS")

    def test_invalid_bucket_is_counted(self):
        columns = expected_columns(1)
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=columns)
        writer.writeheader()
        row = {name: "0" for name in columns}
        row.update({
            "trade_datetime": "2026-09-30 15:20:00", "underlying": "AAPL",
            "security_type": "1", "option_symbol": "OPT1", "expiration_date": "20261218",
            "strike_price": "200", "call_or_put": "C", "days_to_expire": "79",
            "series_type": "S", "previous_close": "250", "trading_dt": "2026-09-30",
            "trading_segment": "1", "firm_open_buy_vol": "-1",
        })
        writer.writerow(row)
        result = audit_payload(gzip.compress(buffer.getvalue().encode()))
        self.assertEqual(result["invalid_bucket_values"], 1)

    def test_invalid_trade_datetime_is_not_repaired(self):
        columns = expected_columns(1)
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=columns)
        writer.writeheader()
        row = {name: "0" for name in columns}
        row.update({
            "trade_datetime": "2026/09/30 15:20:00", "underlying": "AAPL",
            "security_type": "1", "option_symbol": "OPT1", "expiration_date": "20261218",
            "strike_price": "200", "call_or_put": "C", "days_to_expire": "79",
            "series_type": "S", "previous_close": "250", "trading_dt": "2026-09-30",
            "trading_segment": "1",
        })
        writer.writerow(row)
        result = audit_payload(gzip.compress(buffer.getvalue().encode()))
        self.assertEqual(result["invalid_trade_datetime"], 1)

    def test_filename_time_match_is_measured(self):
        result = audit_payload(synthetic_gzip())
        self.assertEqual(result["trade_datetime_filename_time_match_rows"], 1)
        self.assertEqual(result["trade_datetime_filename_date_match_rows"], 1)

    def test_segment_suffix_is_checked(self):
        columns = expected_columns(1)
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=columns)
        writer.writeheader()
        row = {name: "0" for name in columns}
        row.update({
            "trade_datetime": "2026-09-30 15:20:00", "underlying": "AAPL",
            "security_type": "1", "option_symbol": "OPT1", "expiration_date": "20261218",
            "strike_price": "200", "call_or_put": "C", "days_to_expire": "79",
            "series_type": "S", "previous_close": "250", "trading_dt": "2026-09-30",
            "trading_segment": "2",
        })
        writer.writerow(row)
        result = audit_payload(gzip.compress(buffer.getvalue().encode()))
        self.assertEqual(result["trading_segment_filename_suffix_match_rows"], 0)
        self.assertEqual(result["trading_segment_filename_suffix_mismatch_rows"], 1)

    def test_missing_column_fails_schema(self):
        result = audit_payload(synthetic_gzip(mutate_header="missing"))
        self.assertEqual(result["status"], "FAIL_SCHEMA_SAMPLE")
        self.assertIn("trading_segment", result["missing_columns"])

    def test_extra_column_fails_schema(self):
        result = audit_payload(synthetic_gzip(mutate_header="extra"))
        self.assertEqual(result["status"], "FAIL_SCHEMA_SAMPLE")
        self.assertIn("unexpected", result["extra_columns"])

    def test_invalid_gzip_rejected(self):
        with self.assertRaisesRegex(SampleAuditError, "not_gzip"):
            audit_payload(b"not gzip")

    def test_empty_csv_rejected(self):
        with self.assertRaisesRegex(SampleAuditError, "no_rows"):
            audit_payload(gzip.compress(",".join(expected_columns(1)).encode()))

    def test_intraday_omits_eod_only_fields(self):
        result = audit_payload(synthetic_gzip())
        self.assertTrue(result["omitted_eod_only_fields_absent"])


if __name__ == "__main__":
    unittest.main()
