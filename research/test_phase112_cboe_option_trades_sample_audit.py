import unittest

from research.phase112_cboe_option_trades_sample_audit import classify_quote_datetime, parse_market_date, parse_trade_csv


HEADER = (
    "underlying_symbol,market_date,quote_datetime,sequence_number,root,expiration,"
    "strike,option_type,exchange_id,trade_size,trade_price,trade_condition_id,"
    "canceled_trade_condition_id,best_bid_size,best_bid,best_ask,best_ask_size,"
    "underlying_bid,underlying_ask,number_of_exchanges\n"
)


def row(symbol="AAPL", seq=1, price="1.05", bid="1.00", ask="1.10", size=10):
    return (
        f"{symbol},2025-03-28,2025-03-28 10:00:00.123,{seq},AAPL,2025-04-17,"
        f"200,C,1,{size},{price},0,0,100,{bid},{ask},100,199.90,200.10\n"
    )


class Phase112OptionTradesTests(unittest.TestCase):
    def test_required_schema_and_nbbo_parse(self):
        result = parse_trade_csv((HEADER + row()).encode())
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["unique_underlyings"], 1)
        self.assertEqual(result["quote_state_counts"]["valid_nbbo"], 1)
        self.assertEqual(result["trade_location_counts"]["exact_midpoint"], 1)

    def test_non_midpoint_inside_spread_is_unclassified(self):
        result = parse_trade_csv((HEADER + row(price="1.06")).encode())
        self.assertEqual(result["trade_location_counts"]["inside_spread"], 1)

    def test_ask_touch_is_descriptive_only(self):
        result = parse_trade_csv((HEADER + row(price="1.10")).encode())
        self.assertEqual(result["trade_location_counts"]["at_or_above_ask"], 1)

    def test_bid_touch_is_descriptive_only(self):
        result = parse_trade_csv((HEADER + row(price="1.00")).encode())
        self.assertEqual(result["trade_location_counts"]["at_or_below_bid"], 1)

    def test_crossed_quote_is_unclassified(self):
        result = parse_trade_csv((HEADER + row(bid="1.20", ask="1.10")).encode())
        self.assertEqual(result["quote_state_counts"]["crossed_nbbo"], 1)
        self.assertEqual(result["trade_location_counts"]["unclassified_crossed_nbbo"], 1)

    def test_zero_quote_is_unclassified(self):
        result = parse_trade_csv((HEADER + row(bid="0", ask="0")).encode())
        self.assertEqual(result["quote_state_counts"]["zero_or_missing_nbbo"], 1)

    def test_duplicate_sequence_key_is_detected(self):
        result = parse_trade_csv((HEADER + row(seq=1) + row(seq=1)).encode())
        self.assertEqual(result["sequence_key_duplicate_count"], 1)

    def test_missing_required_column_is_reported(self):
        result = parse_trade_csv(b"underlying_symbol,market_date\nAAPL,2025-03-28\n")
        self.assertIn("quote_datetime", result["missing_required_fields"])


    def test_empty_or_non_csv_payload_is_not_misidentified(self):
        from research.phase112_cboe_option_trades_sample_audit import collect_csv_payloads
        import io
        import zipfile

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("readme.txt", "sample only")
        found, entries = collect_csv_payloads(buffer.getvalue())
        self.assertEqual(found, [])
        self.assertEqual(len(entries), 1)


    def test_market_date_us_format_and_partial_clock_are_preserved(self):
        date_value, date_format = parse_market_date("1/7/2026")
        quote_format, quote_value = classify_quote_datetime("21:30.4")
        self.assertEqual(date_value.isoformat(), "2026-01-07")
        self.assertEqual(date_format, "%m/%d/%Y")
        self.assertEqual(quote_format, "two_component_clock")
        self.assertIsNone(quote_value)

    def test_sample_style_date_and_clock_row_parses(self):
        sample_header = HEADER.replace("2025-03-28", "1/7/2026")
        sample_row = row().replace("2025-03-28,2025-03-28 10:00:00.123", "1/7/2026,21:30.4")
        result = parse_trade_csv((sample_header + sample_row).encode())
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["market_dates"], ["2026-01-07"])
        self.assertEqual(result["quote_datetime_format_counts"]["two_component_clock"], 1)
        self.assertEqual(result["errors"], {})


if __name__ == "__main__":
    unittest.main()
