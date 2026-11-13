import csv
import gzip
import io
import unittest
import zipfile
from research.phase351_cboe_tbt_public_sample_audit import (
    EXPECTED_COLUMNS, audit_zip_bytes, _parse_datetime,
)


def make_archive(rows):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        csv_buffer = io.StringIO(newline="")
        writer = csv.DictWriter(csv_buffer, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
        zf.writestr("C1_TBT_2026-01-05.csv.gz", gzip.compress(csv_buffer.getvalue().encode()))
    return buffer.getvalue()


def row(**overrides):
    value = {
        "TRANSACT_TIME": "2026-01-05 10:00:00.000",
        "TRADING_DT": "2026-01-05",
        "FLOOR_ACTION_TS": "",
        "UNDERLYING": "TEST",
        "OSI_ROOT": "TEST",
        "EXPIRE_DATE": "2026-01-16",
        "CALL_PUT_FLAG": "C",
        "STRIKE_PRICE": "100",
        "SIZE": "10",
        "PRICE": "1.20",
        "NBBO_BID": "1.10",
        "NBBO_ASK": "1.30",
        "BBO_BID": "1.10",
        "BBO_ASK": "1.30",
        "SIDE": "B",
        "OPEN_CLOSE": "O",
        "CAPACITY": "Customer",
        "TRADE_TYPE": "AIM Agency - Simple",
        "EXEC_ID": "E1",
        "COMPLEX_EXEC_ID": "",
        "SESSION": "RTH",
        "TRADING_SEGMENT": "2",
    }
    value.update(overrides)
    return value


class Phase351TbtSampleTests(unittest.TestCase):
    def test_nested_zip_and_extensionless_gzip_csv_member(self):
        inner = io.BytesIO()
        csv_buffer = io.StringIO(newline="")
        writer = csv.DictWriter(csv_buffer, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        writer.writerow(row())
        with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as nested:
            nested.writestr("C1_TBT_SAMPLE", gzip.compress(csv_buffer.getvalue().encode()))
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("sample_bundle.zip", inner.getvalue())
        result = audit_zip_bytes(outer.getvalue())
        self.assertEqual(result["rows"], 1)
        self.assertEqual(result["unique_underlyings"], 1)

    def test_blank_trade_type_is_preserved_as_unknown(self):
        result = audit_zip_bytes(make_archive([row(TRADE_TYPE="")]))
        self.assertEqual(result["trade_type_counts"], {"UNKNOWN_BLANK": 1})
        self.assertEqual(result["missing_required_cells"]["TRADE_TYPE"], 1)

    def test_blank_open_close_is_preserved_as_unknown(self):
        result = audit_zip_bytes(make_archive([row(OPEN_CLOSE="")]))
        self.assertEqual(result["open_close_counts"], {"UNKNOWN_BLANK": 1})
        self.assertEqual(result["missing_required_cells"]["OPEN_CLOSE"], 1)

    def test_incomplete_contract_identity_is_counted_without_fabrication(self):
        result = audit_zip_bytes(make_archive([
            row(OSI_ROOT="", CALL_PUT_FLAG="")
        ]))
        self.assertEqual(result["incomplete_contract_identity_rows"], 1)
        self.assertEqual(result["unique_option_series_complete_identity_only"], 0)
        self.assertEqual(result["call_put_counts"], {"UNKNOWN_BLANK": 1})

    def test_schema_and_basic_counts(self):
        result = audit_zip_bytes(make_archive([row()]))
        self.assertEqual(result["rows"], 1)
        self.assertEqual(result["unique_underlyings"], 1)
        self.assertEqual(result["capacity_counts"], {"Customer": 1})
        self.assertFalse(result["gates"]["historical_pit_admitted"])

    def test_execution_id_pairing_is_measured_not_assumed(self):
        result = audit_zip_bytes(make_archive([
            row(SIDE="B", CAPACITY="Customer"),
            row(SIDE="S", CAPACITY="MarketMaker"),
        ]))
        self.assertEqual(result["execution_id"]["unique_ids"], 1)
        self.assertEqual(result["execution_id"]["ids_with_both_buy_and_sell_sides"], 1)
        self.assertEqual(result["execution_id"]["ids_spanning_multiple_capacities"], 1)

    def test_complex_id_leg_cardinality(self):
        result = audit_zip_bytes(make_archive([
            row(EXEC_ID="E1", COMPLEX_EXEC_ID="CX1", OSI_ROOT="TEST1"),
            row(EXEC_ID="E2", COMPLEX_EXEC_ID="CX1", OSI_ROOT="TEST2", CALL_PUT_FLAG="P"),
        ]))
        self.assertEqual(result["complex_execution_id"]["unique_ids"], 1)
        self.assertEqual(result["complex_execution_id"]["ids_spanning_multiple_option_series"], 1)

    def test_exact_duplicate_rows_are_counted(self):
        r = row()
        result = audit_zip_bytes(make_archive([r, r]))
        self.assertEqual(result["exact_duplicate_rows"], 1)

    def test_gth_calendar_date_mismatch_is_preserved(self):
        result = audit_zip_bytes(make_archive([
            row(TRANSACT_TIME="2026-01-06 01:00:00", TRADING_DT="2026-01-05", SESSION="GTH")
        ]))
        self.assertEqual(result["trading_date_calendar_mismatch_rows"], 1)
        self.assertEqual(result["trade_dates"], ["2026-01-05"])

    def test_crossed_nbbo_is_reported(self):
        result = audit_zip_bytes(make_archive([row(NBBO_BID="1.40", NBBO_ASK="1.20")]))
        self.assertEqual(result["quote_diagnostics"]["crossed_nbbo_rows"], 1)

    def test_floor_late_threshold(self):
        result = audit_zip_bytes(make_archive([
            row(TRANSACT_TIME="2026-01-05 10:02:00",
                FLOOR_ACTION_TS="2026-01-05 10:00:00")
        ]))
        self.assertEqual(result["floor_action_diagnostics"]["late_rows_ge_90_seconds"], 1)

    def test_unknown_capacity_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_zip_bytes(make_archive([row(CAPACITY="Unknown")]))
    
    def test_noninteger_or_nonpositive_size_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_zip_bytes(make_archive([row(SIZE="1.5")]))
        with self.assertRaises(ValueError):
            audit_zip_bytes(make_archive([row(SIZE="0")]))

    def test_missing_required_trade_field_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_zip_bytes(make_archive([row(SIDE="")]))

    def test_timestamp_parser_does_not_invent_timezone(self):
        parsed = _parse_datetime("2026-01-05 10:00:00")
        self.assertIsNone(parsed.tzinfo)


if __name__ == "__main__":
    unittest.main()
