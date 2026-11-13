import unittest

from research.phase355_cboe_eod_participant_accounting_audit import (
    BUCKET_PAIRS,
    VOLUME_FIELDS,
    audit_csv,
    bucket_volume_valid,
    parse_nonnegative_int,
)


class Phase355AccountingTests(unittest.TestCase):
    def test_there_are_34_participant_side_volume_fields(self):
        self.assertEqual(len(VOLUME_FIELDS), 34)
        self.assertEqual(len(set(VOLUME_FIELDS)), 34)

    def test_market_maker_fields_are_not_mislabelled_open_close(self):
        self.assertIn("mm_buy_vol", VOLUME_FIELDS)
        self.assertIn("mm_sell_vol", VOLUME_FIELDS)
        self.assertFalse(any(x.startswith("mm_open_") or x.startswith("mm_close_") for x in VOLUME_FIELDS))

    def test_integer_parser_rejects_negative_fraction_and_missing(self):
        self.assertEqual(parse_nonnegative_int("1,234"), 1234)
        self.assertEqual(parse_nonnegative_int("1234.0"), 1234)
        self.assertIsNone(parse_nonnegative_int("-1"))
        self.assertIsNone(parse_nonnegative_int("1.5"))
        self.assertIsNone(parse_nonnegative_int(""))

    def test_customer_size_bucket_aggregate_bounds(self):
        self.assertTrue(bucket_volume_valid(2, 198, "lt_100"))
        self.assertFalse(bucket_volume_valid(2, 200, "lt_100"))
        self.assertTrue(bucket_volume_valid(2, 200, "100_199"))
        self.assertTrue(bucket_volume_valid(2, 398, "100_199"))
        self.assertFalse(bucket_volume_valid(2, 399, "100_199"))
        self.assertTrue(bucket_volume_valid(2, 400, "gt_199"))
        self.assertFalse(bucket_volume_valid(0, 1, "gt_199"))
        self.assertTrue(bucket_volume_valid(0, 0, "lt_100"))

    def test_missing_bucket_pair_is_not_silently_counted_as_zero(self):
        self.assertEqual(len(BUCKET_PAIRS), 24)

    def test_exact_participant_reconciliation_is_required_for_pass(self):
        headers = [
            "quote_date", "underlying_symbol", "security_type", "option_symbol",
            "expiration_date", "strike_price", "call_put_flag", "series_type",
            "total_exchange_vol", "total_industry_vol",
        ] + VOLUME_FIELDS + [
            field[:-4] + "_qty" for field in VOLUME_FIELDS
        ]
        row = {field: "0" for field in headers}
        row.update({
            "quote_date": "03/28/2025",
            "underlying_symbol": "XYZ",
            "security_type": "1",
            "option_symbol": "XYZ",
            "expiration_date": "2025-04-17",
            "strike_price": "100",
            "call_put_flag": "C",
            "series_type": "S",
            "total_exchange_vol": "10",
            "total_industry_vol": "20",
            "firm_open_buy_vol": "10",
            "firm_open_buy_qty": "1",
        })
        import csv
        import io
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerow(row)
        result = audit_csv(stream.getvalue().encode(), "sample.csv")
        self.assertEqual(result["participant_volume_exact_match_rows"], 1)
        self.assertEqual(result["participant_volume_exact_match_rate"], 1.0)
        self.assertTrue(result["accounting_gate"]["overall_pass"])

    def test_participant_reconciliation_mismatch_is_not_hidden(self):
        headers = [
            "quote_date", "underlying_symbol", "security_type", "option_symbol",
            "expiration_date", "strike_price", "call_put_flag", "series_type",
            "total_exchange_vol", "total_industry_vol",
        ] + VOLUME_FIELDS + [
            field[:-4] + "_qty" for field in VOLUME_FIELDS
        ]
        row = {field: "0" for field in headers}
        row.update({
            "quote_date": "03/28/2025",
            "underlying_symbol": "XYZ",
            "security_type": "1",
            "option_symbol": "XYZ",
            "expiration_date": "2025-04-17",
            "strike_price": "100",
            "call_put_flag": "C",
            "series_type": "S",
            "total_exchange_vol": "10",
            "total_industry_vol": "20",
            "firm_open_buy_vol": "9",
            "firm_open_buy_qty": "1",
        })
        import csv
        import io
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerow(row)
        result = audit_csv(stream.getvalue().encode(), "sample.csv")
        self.assertEqual(result["participant_volume_mismatch_rows"], 1)
        self.assertFalse(result["accounting_gate"]["overall_pass"])

    def test_size_bucket_violations_are_separate_from_volume_reconciliation(self):
        self.assertTrue(bucket_volume_valid(1, 200, "gt_199"))
        self.assertFalse(bucket_volume_valid(1, 199, "gt_199"))


if __name__ == "__main__":
    unittest.main()
