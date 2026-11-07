import csv, io, unittest, zipfile
from research.phase170_cboe_option_trades_public_sample_audit import BASE_FIELDS
from research.phase172_cboe_option_trades_blank_row_time_shape_audit import audit_archive, audit_member

def row(**kw):
    d={"underlying_symbol":"TEST","market_date":"1/7/2026","quote_datetime":"09:30.0",
       "sequence_number":"1001","root":"TEST","expiration":"1/16/2026","strike":"10",
       "option_type":"C","exchange_id":"1","trade_size":"5","trade_price":"1.25",
       "trade_condition_id":"0","canceled_trade_condition_id":"0","best_bid_size":"10",
       "best_bid":"1.20","best_ask":"1.30","best_ask_size":"12","underlying_bid":"9.99","underlying_ask":"10.01"}
    d.update(kw); return d

def payload(rows):
    s=io.StringIO(); w=csv.DictWriter(s,fieldnames=list(BASE_FIELDS)); w.writeheader(); w.writerows(rows)
    return s.getvalue().encode()

def zipped(data):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z: z.writestr("UnderlyingOptionsTrades_2026-01-07.csv",data)
    return b.getvalue()

class Phase172Tests(unittest.TestCase):
    def test_trailing_blank_rows_are_only_a_candidate(self):
        blank={f:"" for f in BASE_FIELDS}
        r=audit_member("UnderlyingOptionsTrades_2026-01-07.csv",payload([row(),blank,blank]))
        self.assertEqual(r["all_columns_blank_rows"],2)
        self.assertEqual(r["all_columns_blank_runs"],1)
        self.assertEqual(r["trailing_all_columns_blank_rows"],2)
        self.assertTrue(r["all_blank_rows_only_trailing"])
        self.assertEqual(r["all_blank_row_pattern"],"TRAILING_PADDING_CANDIDATE")

    def test_internal_blank_block_is_not_trailing(self):
        blank={f:"" for f in BASE_FIELDS}
        r=audit_member("sample.csv",payload([row(),blank,row()]))
        self.assertEqual(r["all_blank_row_pattern"],"ONE_CONTIGUOUS_INTERNAL_BLOCK")
        self.assertFalse(r["all_blank_rows_only_trailing"])

    def test_both_dates_blank_but_other_data_is_reported(self):
        r=audit_member("sample.csv",payload([row(market_date="",quote_datetime="",trade_price="1.25")]))
        self.assertEqual(r["both_date_fields_blank_any_column_nonblank_rows"],1)
        self.assertEqual(r["both_date_fields_blank_all_columns_blank_rows"],0)
        self.assertEqual(r["nonblank_fields_when_both_dates_blank"],{"trade_price":1})

    def test_time_only_clock_range_is_checked_not_converted(self):
        r=audit_member("sample.csv",payload([row(quote_datetime="09:30.0")]))
        self.assertEqual(r["quote_time_only_shape_rows"],1)
        self.assertEqual(r["quote_time_only_valid_clock_rows"],1)
        self.assertEqual(r["quote_time_only_hour_minute_min"],"09:30")
        self.assertEqual(r["quote_time_only_hour_minute_max"],"09:30")

    def test_invalid_clock_is_counted(self):
        r=audit_member("sample.csv",payload([row(quote_datetime="25:70.9")]))
        self.assertEqual(r["quote_time_only_shape_rows"],1)
        self.assertEqual(r["quote_time_only_invalid_clock_rows"],1)

    def test_no_raw_symbols_or_clock_values_are_persisted(self):
        blank={f:"" for f in BASE_FIELDS}
        r=audit_member("sample.csv",payload([row(),blank]))
        self.assertNotIn("TEST",str(r)); self.assertNotIn("09:30.0",str(r))
        self.assertFalse(r["raw_rows_persisted"]); self.assertFalse(r["raw_clock_values_persisted"])

    def test_archive_is_diagnostic_only(self):
        r=audit_archive(zipped(payload([row()])),"2026-11-07T00:00:00+00:00")
        self.assertEqual(r["status"],"DIAGNOSTIC_COMPLETE")
        self.assertFalse(r["alpha_admission"]); self.assertFalse(r["strict_pit"])
        self.assertFalse(r["f80_change"])

if __name__=="__main__": unittest.main()
