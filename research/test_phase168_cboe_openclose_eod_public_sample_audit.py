import csv
import io
import json
import unittest
import zipfile

from research.phase168_cboe_openclose_eod_public_sample_audit import (
    audit_archive, bucket_columns, expected_columns_eod, parse_member_name,
)


def make_csv(*, oi="100", industry="500", quote_date="09/30/2026", mutate=None):
    columns = expected_columns_eod()
    if mutate == "missing":
        columns = columns[:-1]
    elif mutate == "extra":
        columns = columns + ["extra_field"]
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=columns)
    writer.writeheader()
    row = {name: "0" for name in columns}
    row.update({
        "quote_date": quote_date, "underlying_symbol": "AAPL", "security_type": "1",
        "option_symbol": "AAPL", "expiration_date": "2026-12-18", "strike_price": "200",
        "call_put_flag": "C", "days_to_expire": "79", "series_type": "S",
        "first_trade_price": "1.00", "high_trade_price": "1.20", "low_trade_price": "0.90",
        "last_trade_price": "1.10", "total_exchange_vol": "1000", "total_industry_vol": industry,
        "open_interest": oi, "previous_open_interest": "90", "previous_close": "250.00",
    })
    writer.writerow({k: row.get(k, "0") for k in columns})
    return out.getvalue().encode()


def make_zip(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return buffer.getvalue()


class Phase168Tests(unittest.TestCase):
    def test_eod_spec_has_86_columns(self):
        cols = expected_columns_eod()
        self.assertEqual(len(cols), 86)
        self.assertEqual(len(bucket_columns()), 68)
        self.assertIn("open_interest", cols)
        self.assertIn("previous_open_interest", cols)
        self.assertNotIn("trading_segment", cols)

    def test_filename_parses_final_and_preliminary(self):
        final = parse_member_name("C1OpenClose_2026-09-30.csv")
        prelim = parse_member_name("C1OpenClose_2026-09-30_p.csv")
        self.assertEqual(final["file_kind"], "FINAL")
        self.assertEqual(prelim["file_kind"], "PRELIMINARY")

    def test_sample_suffix_preserves_exchange_date_but_not_final_role(self):
        parsed = parse_member_name("C1OpenClose_2025-03-28_sample_20pct.csv")
        self.assertEqual(parsed["exchange"], "C1")
        self.assertEqual(parsed["quote_date"], "2025-03-28")
        self.assertEqual(parsed["file_kind"], "SAMPLE_UNSPECIFIED")

    def test_filename_rejects_unknown_exchange(self):
        with self.assertRaisesRegex(ValueError, "filename_unrecognized"):
            parse_member_name("NYSEOpenClose_2026-09-30.csv")

    def test_single_final_sample_passes_schema(self):
        raw = make_zip({"C1OpenClose_2026-09-30.csv": make_csv()})
        result = audit_archive(raw, {"content-type": "application/zip"},
                               retrieved_at_utc="2026-11-06T20:00:00+00:00")
        self.assertEqual(result["status"], "PASS_EOD_SAMPLE_SCHEMA")
        self.assertEqual(result["csv_member_count"], 1)
        self.assertEqual(result["total_rows"], 1)
        self.assertFalse(result["strict_pit"])
        self.assertFalse(result["first_receipt_proven"])

    def test_preliminary_final_pair_reports_differences_without_assuming_equal(self):
        raw = make_zip({
            "C1OpenClose_2026-09-30_p.csv": make_csv(oi="95", industry="490"),
            "C1OpenClose_2026-09-30.csv": make_csv(oi="100", industry="500"),
        })
        result = audit_archive(raw)
        self.assertEqual(result["preliminary_final_pair_count"], 1)
        pair = result["preliminary_final_pairs"][0]
        self.assertEqual(pair["common_series"], 1)
        self.assertEqual(pair["changed_values_on_common_series"]["open_interest"], 1)
        self.assertEqual(pair["changed_values_on_common_series"]["total_industry_vol"], 1)

    def test_quote_date_mismatch_fails_schema(self):
        raw = make_zip({"C1OpenClose_2026-09-30.csv": make_csv(quote_date="10/01/2026")})
        result = audit_archive(raw)
        self.assertEqual(result["status"], "FAIL_EOD_SAMPLE_SCHEMA")
        self.assertEqual(result["file_summaries"][0]["quote_date_mismatch_rows"], 1)

    def test_missing_header_fails_schema(self):
        raw = make_zip({"C1OpenClose_2026-09-30.csv": make_csv(mutate="missing")})
        result = audit_archive(raw)
        self.assertEqual(result["status"], "FAIL_EOD_SAMPLE_SCHEMA")
        self.assertIn("procust_gt_199_close_sell_vol", result["file_summaries"][0]["missing_columns"])
        self.assertEqual(result["file_summaries"][0]["detected_schema"], "EOD_CANDIDATE")

    def test_extra_header_fails_schema(self):
        raw = make_zip({"C1OpenClose_2026-09-30.csv": make_csv(mutate="extra")})
        result = audit_archive(raw)
        self.assertEqual(result["status"], "FAIL_EOD_SAMPLE_SCHEMA")
        self.assertIn("extra_field", result["file_summaries"][0]["extra_columns"])
        self.assertEqual(result["file_summaries"][0]["detected_schema"], "EOD_CANDIDATE")

    def test_negative_open_interest_fails_schema(self):
        columns = expected_columns_eod()
        out = io.StringIO(newline="")
        writer = csv.DictWriter(out, fieldnames=columns)
        writer.writeheader()
        row = {name: "0" for name in columns}
        row.update({"quote_date":"09/30/2026", "underlying_symbol":"AAPL", "security_type":"1",
                    "option_symbol":"AAPL", "expiration_date":"2026-12-18", "strike_price":"200",
                    "call_put_flag":"C", "days_to_expire":"79", "series_type":"S",
                    "open_interest":"-1", "previous_open_interest":"90", "total_exchange_vol":"1",
                    "total_industry_vol":"1", "previous_close":"250"})
        writer.writerow(row)
        result = audit_archive(make_zip({"C1OpenClose_2026-09-30.csv": out.getvalue().encode()}))
        self.assertEqual(result["status"], "FAIL_EOD_SAMPLE_SCHEMA")

    def test_zero_previous_close_is_diagnostic_not_schema_failure(self):
        columns = expected_columns_eod()
        out = io.StringIO(newline="")
        writer = csv.DictWriter(out, fieldnames=columns)
        writer.writeheader()
        row = {name: "0" for name in columns}
        row.update({"quote_date":"09/30/2026", "underlying_symbol":"AAPL", "security_type":"1",
                    "option_symbol":"AAPL", "expiration_date":"2026-12-18", "strike_price":"200",
                    "call_put_flag":"C", "days_to_expire":"79", "series_type":"S",
                    "open_interest":"100", "previous_open_interest":"90", "total_exchange_vol":"1",
                    "total_industry_vol":"1", "previous_close":"0"})
        writer.writerow(row)
        result = audit_archive(make_zip({"C1OpenClose_2026-09-30.csv": out.getvalue().encode()}))
        self.assertEqual(result["status"], "PASS_EOD_SAMPLE_SCHEMA")
        self.assertEqual(result["file_summaries"][0]["zero_previous_close_rows"], 1)

    def test_negative_previous_close_fails_schema(self):
        columns = expected_columns_eod()
        out = io.StringIO(newline="")
        writer = csv.DictWriter(out, fieldnames=columns)
        writer.writeheader()
        row = {name: "0" for name in columns}
        row.update({"quote_date":"09/30/2026", "underlying_symbol":"AAPL", "security_type":"1",
                    "option_symbol":"AAPL", "expiration_date":"2026-12-18", "strike_price":"200",
                    "call_put_flag":"C", "days_to_expire":"79", "series_type":"S",
                    "open_interest":"100", "previous_open_interest":"90", "total_exchange_vol":"1",
                    "total_industry_vol":"1", "previous_close":"-1"})
        writer.writerow(row)
        result = audit_archive(make_zip({"C1OpenClose_2026-09-30.csv": out.getvalue().encode()}))
        self.assertEqual(result["status"], "FAIL_EOD_SAMPLE_SCHEMA")
        self.assertEqual(result["file_summaries"][0]["negative_previous_close_rows"], 1)

    def test_non_numeric_previous_close_fails_schema(self):
        columns = expected_columns_eod()
        out = io.StringIO(newline="")
        writer = csv.DictWriter(out, fieldnames=columns)
        writer.writeheader()
        row = {name: "0" for name in columns}
        row.update({"quote_date":"09/30/2026", "underlying_symbol":"AAPL", "security_type":"1",
                    "option_symbol":"AAPL", "expiration_date":"2026-12-18", "strike_price":"200",
                    "call_put_flag":"C", "days_to_expire":"79", "series_type":"S",
                    "open_interest":"100", "previous_open_interest":"90", "total_exchange_vol":"1",
                    "total_industry_vol":"1", "previous_close":"bad"})
        writer.writerow(row)
        result = audit_archive(make_zip({"C1OpenClose_2026-09-30.csv": out.getvalue().encode()}))
        self.assertEqual(result["status"], "FAIL_EOD_SAMPLE_SCHEMA")
        self.assertEqual(result["file_summaries"][0]["invalid_previous_close_format_rows"], 1)

    def test_mixed_public_archive_separates_intraday_and_eod_members(self):
        intraday = b"trade_datetime,underlying,trading_dt\\n2025-03-28 12:30:00,AAPL,2025-03-28\\n"
        raw = make_zip({
            "Cboe_OpenClose_2025-03-28_12_30_1.csv": intraday,
            "Cboe_OpenClose_2025-03-28_13_16_1.csv": intraday,
            "C1OpenClose_2025-03-28_sample_20pct.csv": make_csv(quote_date="2025-03-28"),
        })
        result = audit_archive(raw)
        self.assertEqual(result["status"], "PASS_EOD_SAMPLE_SCHEMA_IDENTITY_UNRESOLVED")
        self.assertEqual(result["csv_member_count"], 3)
        self.assertEqual(result["eod_member_count"], 1)
        self.assertEqual(result["intraday_member_count"], 2)
        self.assertEqual(result["total_rows"], 1)
        self.assertTrue(result["member_filename_identity_resolved"])
        self.assertFalse(result["file_version_identity_resolved"])
        eod = next(x for x in result["file_summaries"] if x["detected_schema"] == "EOD")
        self.assertEqual(eod["quote_date_format_counts"], {"YYYY-MM-DD": 1})
        self.assertEqual(eod["quote_date"], "2025-03-28")

    def test_raw_symbols_not_persisted(self):
        result = audit_archive(make_zip({"C1OpenClose_2026-09-30.csv": make_csv()}))
        self.assertNotIn("AAPL", json.dumps(result))
        self.assertFalse(result["raw_rows_persisted"])
        self.assertFalse(result["raw_symbols_persisted"])

    def test_generic_filename_can_pass_schema_but_not_identity_gate(self):
        raw = make_zip({"Sample.csv": make_csv()})
        result = audit_archive(raw)
        self.assertEqual(result["status"], "PASS_EOD_SAMPLE_SCHEMA_IDENTITY_UNRESOLVED")
        self.assertFalse(result["member_filename_identity_resolved"])
        self.assertEqual(result["file_summaries"][0]["quote_date"], "2026-09-30")

    def test_intraday_sample_is_identified_and_not_misclassified_as_eod(self):
        payload = b"trade_datetime,underlying,trading_dt\\n2026-09-30 15:20:00,AAPL,2026-09-30\\n"
        result = audit_archive(make_zip({"Sample.csv": payload}))
        self.assertEqual(result["status"], "BLOCKED_SAMPLE_IS_INTRADAY_NOT_EOD")
        self.assertEqual(result["file_summaries"][0]["detected_schema"], "INTRADAY_LIKE")

    def test_unrelated_generic_csv_is_not_promoted_to_eod_candidate(self):
        raw = make_zip({"unrelated.csv": b"foo,bar\\nx,y\\n"})
        result = audit_archive(raw)
        self.assertEqual(result["status"], "FAIL_NO_EOD_MEMBER")
        self.assertEqual(result["file_summaries"][0]["detected_schema"], "UNKNOWN")
        self.assertEqual(result["unknown_member_count"], 1)

    def test_invalid_zip_rejected(self):
        with self.assertRaisesRegex(ValueError, "not_zip"):
            audit_archive(b"not a zip")

    def test_nested_zip_is_supported(self):
        inner = make_zip({"C1OpenClose_2026-09-30.csv": make_csv()})
        outer = make_zip({"nested.zip": inner})
        result = audit_archive(outer)
        self.assertEqual(result["status"], "PASS_EOD_SAMPLE_SCHEMA")
        self.assertEqual(result["csv_member_count"], 1)

    def test_duplicate_series_is_reported(self):
        text = make_csv().decode()
        lines = text.splitlines()
        doubled = ("\n".join(lines + [lines[-1]]) + "\n").encode()
        result = audit_archive(make_zip({"C1OpenClose_2026-09-30.csv": doubled}))
        self.assertEqual(result["file_summaries"][0]["duplicate_series_rows"], 1)
        self.assertEqual(result["status"], "FAIL_EOD_SAMPLE_SCHEMA")

    def test_capacity_and_prelim_final_semantics_are_preserved(self):
        result = audit_archive(make_zip({"C1OpenClose_2026-09-30.csv": make_csv()}))
        self.assertIn("OPRA-sourced", result["preliminary_semantics"])
        self.assertIn("OCC-sourced", result["final_semantics"])
        self.assertIn("2019-10-04", result["historical_convention_breaks"]["C1_open_interest_previous_open_interest_shifted_one_day_through"])


if __name__ == "__main__":
    unittest.main()
