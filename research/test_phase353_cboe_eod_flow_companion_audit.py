import csv
import io
import unittest
import zipfile

from research.phase353_cboe_eod_flow_companion_audit import (
    OPEN_CLOSE_REQUIRED,
    OPTION_EOD_REQUIRED,
    OPTION_EOD_CALCS,
    _audit_csv,
    _extract_csv_members,
    audit_archive,
    audit_intraday_sample,
    audit_spec_text,
)


def make_csv(headers, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


class Phase353CboeEodPairTests(unittest.TestCase):
    def test_open_close_schema_has_86_columns(self):
        self.assertEqual(len(OPEN_CLOSE_REQUIRED), 86)
        self.assertEqual(len(set(OPEN_CLOSE_REQUIRED)), 86)

    def test_option_eod_core_schema_and_calc_set(self):
        self.assertIn("open_interest", OPTION_EOD_REQUIRED)
        self.assertIn("implied_volatility_1545", OPTION_EOD_CALCS)
        self.assertIn("delta_1545", OPTION_EOD_CALCS)

    def test_open_close_sample_row_is_audited_without_inventing_signal(self):
        row = {key: "0" for key in OPEN_CLOSE_REQUIRED}
        row.update({
            "quote_date": "11/12/2026", "underlying_symbol": "XYZ",
            "security_type": "1", "option_symbol": "XYZ",
            "expiration_date": "2026-12-18", "strike_price": "100",
            "call_put_flag": "C", "days_to_expire": "36", "series_type": "S",
        })
        result = _audit_csv(make_csv(OPEN_CLOSE_REQUIRED, [row]), name="sample.csv", product="open_close_eod")
        self.assertEqual(result["status"], "PASS_SAMPLE_SCHEMA")
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["underlying_count"], 1)

    def test_duplicate_option_series_are_counted(self):
        row = {key: "0" for key in OPEN_CLOSE_REQUIRED}
        row.update({
            "quote_date": "11/12/2026", "underlying_symbol": "XYZ",
            "security_type": "1", "option_symbol": "XYZ",
            "expiration_date": "2026-12-18", "strike_price": "100",
            "call_put_flag": "C", "days_to_expire": "36", "series_type": "S",
        })
        result = _audit_csv(make_csv(OPEN_CLOSE_REQUIRED, [row, row]), name="sample.csv", product="open_close_eod")
        self.assertEqual(result["duplicate_series_key_rows"], 1)

    def test_option_eod_zero_iv_is_counted_separately_from_missing(self):
        row = {key: "1" for key in OPTION_EOD_REQUIRED}
        row.update({
            "underlying_symbol": "XYZ", "quote_date": "2026-11-12", "root": "XYZ",
            "expiration": "2026-12-18", "strike": "100", "option_type": "C",
            "implied_volatility_1545": "0", "delta_1545": "0.5",
        })
        headers = OPTION_EOD_REQUIRED + OPTION_EOD_CALCS
        result = _audit_csv(make_csv(headers, [row]), name="sample.csv", product="option_eod")
        self.assertEqual(result["status"], "PASS_SAMPLE_SCHEMA")
        self.assertEqual(result["zero_cells"]["implied_volatility_1545"], 1)
        self.assertEqual(result["calc_columns_present"], OPTION_EOD_CALCS)

    def test_required_column_missing_fails(self):
        row = {key: "0" for key in OPTION_EOD_REQUIRED if key != "open_interest"}
        result = _audit_csv(make_csv(list(row), [row]), name="sample.csv", product="option_eod")
        self.assertEqual(result["status"], "FAIL_REQUIRED_COLUMNS")
        self.assertIn("open_interest", result["missing_columns"])

    def test_open_close_bundle_filters_to_eod_member(self):
        eod_row = {key: "0" for key in OPEN_CLOSE_REQUIRED}
        eod_row.update({
            "quote_date": "03/28/2025", "underlying_symbol": "XYZ",
            "security_type": "1", "option_symbol": "XYZ",
            "expiration_date": "2025-04-17", "strike_price": "100",
            "call_put_flag": "C", "days_to_expire": "20", "series_type": "S",
        })
        eod_csv = make_csv(OPEN_CLOSE_REQUIRED, [eod_row])
        intraday_csv = make_csv(["a", "b", "c", "d", "e"], [{"a":"1","b":"2","c":"3","d":"4","e":"5"}])
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("C1 OpenClose EOD Sample & Spec/sample.csv", eod_csv)
            zf.writestr("C1 OpenClose 10m Sample & Spec/intraday.csv", intraday_csv)
        result = audit_archive(archive.getvalue(), product="open_close_eod")
        self.assertEqual(result["status"], "PASS_SAMPLE_SCHEMA")
        self.assertEqual(result["member_count"], 1)
        self.assertEqual(result["row_count_across_members"], 1)

    def test_nested_zip_csv_is_found(self):
        csv_bytes = make_csv(["a", "b", "c", "d", "e"], [{"a":"1","b":"2","c":"3","d":"4","e":"5"}])
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("sample.csv", csv_bytes)
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("nested.zip", inner.getvalue())
        members = _extract_csv_members(outer.getvalue())
        self.assertEqual(len(members), 1)
        self.assertIn("sample.csv", members[0][0])

    def test_intraday_sample_date_is_pre_cutover(self):
        content = b"underlying,quote_datetime,field_a,field_b,field_c\nXYZ,2026-09-30,1,2,3\n"
        result = audit_intraday_sample(content)
        self.assertEqual(result["status"], "PRE_CUTOVER_DATE_OLD_SCHEMA")
        self.assertFalse(result["v18_schema_present"])
        self.assertFalse(result["post_cutover_sample_verified"])

    def test_pre_cutover_link_can_have_new_headers_without_proving_live_cutover(self):
        content = b"underlying,quote_datetime,trading_dt,trading_segment,field_x\nXYZ,2026-09-30,2026-09-30,1,3\n"
        result = audit_intraday_sample(content)
        self.assertEqual(result["status"], "PRE_CUTOVER_DATE_NEW_SCHEMA")
        self.assertTrue(result["v18_schema_present"])
        self.assertFalse(result["post_cutover_sample_verified"])

    def test_spec_gate_requires_both_vintages_and_sod_oi_semantics(self):
        oc = "v1.3 20251110 1 preliminary file and 1 final file per day typically delivered between 00:30AM to 01:00AM U.S. EST the next morning final file sources authoritative values from the OCC firm F, L, J broker-dealer B market maker M, N pro-customer U, W"
        oe = "start-of-day (SOD) open interest implied_volatility_1545 delta_1545 gamma_1545 15:45 implied volatility will be zero 12:45 pm ET OPRA market data feed"
        result = audit_spec_text(oc, oe)
        self.assertEqual(result["status"], "PASS_EOD_SPEC_SEMANTICS")
        self.assertFalse(result.get("historical_pit_admitted", False))


if __name__ == "__main__":
    unittest.main()
