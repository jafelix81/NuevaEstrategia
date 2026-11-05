import gzip, io, unittest, zipfile
from research.phase113_cboe_tbt_sample_audit import REQUIRED_FIELDS, collect_csv_payloads, parse_trade_csv

HEADER = ",".join(REQUIRED_FIELDS) + "\n"

def row(**overrides):
    values = {
        "TRANSACT_TIME":"2026-01-07 09:30:00.123", "TRADING_DT":"2026-01-07",
        "FLOOR_ACTION_TS":"", "UNDERLYING":"AAPL", "OSI_ROOT":"AAPL",
        "EXPIRE_DATE":"2026-01-09", "CALL_PUT_FLAG":"C", "STRIKE_PRICE":"250",
        "SIZE":"10", "PRICE":"1.25", "NBBO_BID":"1.20", "NBBO_ASK":"1.30",
        "BBO_BID":"1.20", "BBO_ASK":"1.30", "SIDE":"B", "OPEN_CLOSE":"O",
        "CAPACITY":"Customer", "TRADE_TYPE":"AIM Agency - Simple", "EXEC_ID":"E1",
        "COMPLEX_EXEC_ID":"", "SESSION":"RTH", "TRADING_SEGMENT":"2"
    }
    values.update(overrides)
    return ",".join(values[k] for k in REQUIRED_FIELDS) + "\n"

class Phase113TBTTests(unittest.TestCase):
    def test_required_schema_and_core_classifications(self):
        r = parse_trade_csv((HEADER + row()).encode())
        self.assertEqual(r["row_count"], 1)
        self.assertEqual(r["missing_required_fields"], [])
        self.assertEqual(r["side_counts"], {"B":1})
        self.assertEqual(r["open_close_counts"], {"O":1})
        self.assertEqual(r["capacity_counts"], {"CUSTOMER":1})
        self.assertEqual(r["parsed_transact_time_count"], 1)

    def test_both_sides_under_same_execution_id_are_not_duplicates(self):
        r = parse_trade_csv((HEADER + row(SIDE="B") + row(SIDE="S")).encode())
        self.assertEqual(r["exec_id_repeated_group_count"], 1)
        self.assertEqual(r["exec_id_groups_with_both_sides"], 1)
        self.assertEqual(r["exact_duplicate_row_excess"], 0)

    def test_complex_execution_id_is_counted_separately(self):
        r = parse_trade_csv((HEADER + row(EXEC_ID="", COMPLEX_EXEC_ID="CX1")).encode())
        self.assertEqual(r["complex_exec_id_nonblank_rows"], 1)
        self.assertEqual(r["complex_exec_id_unique_count"], 1)

    def test_floor_late_threshold_is_90_seconds(self):
        r = parse_trade_csv((HEADER + row(TRANSACT_TIME="2026-01-07 09:32:00",
            FLOOR_ACTION_TS="2026-01-07 09:30:00")).encode())
        self.assertEqual(r["floor_action_delay_counts"], {"late_ge_90s":1})

    def test_trading_date_can_differ_from_calendar_date(self):
        r = parse_trade_csv((HEADER + row(TRANSACT_TIME="2026-01-08 01:00:00",
            TRADING_DT="2026-01-07", SESSION="GTH", TRADING_SEGMENT="1")).encode())
        self.assertEqual(r["trading_dt_vs_transact_calendar_date_mismatch_count"], 1)
        self.assertEqual(r["session_counts"], {"GTH":1})

    def test_invalid_side_is_reported(self):
        r = parse_trade_csv((HEADER + row(SIDE="X")).encode())
        self.assertEqual(r["invalid_side_rows"], 1)

    def test_missing_required_field_is_reported(self):
        r = parse_trade_csv(b"TRANSACT_TIME,TRADING_DT\n2026-01-07 09:30:00,2026-01-07\n")
        self.assertIn("SIDE", r["missing_required_fields"])

    def test_nested_zip_and_gzip_csv_are_found(self):
        inner = gzip.compress((HEADER + row()).encode())
        b1 = io.BytesIO()
        with zipfile.ZipFile(b1, "w") as z: z.writestr("C1_TBT_2026-01-07.csv.gz", inner)
        b2 = io.BytesIO()
        with zipfile.ZipFile(b2, "w") as z: z.writestr("nested.zip", b1.getvalue())
        found, entries = collect_csv_payloads(b2.getvalue(), "outer.zip")
        self.assertEqual(len(found), 1)
        self.assertIn("TRANSACT_TIME", found[0]["content"].decode())
        self.assertTrue(entries)

if __name__ == "__main__":
    unittest.main()
