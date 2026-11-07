import csv
import io
import unittest
import zipfile
from datetime import date

from research.phase171_cboe_option_trades_datetime_shape_audit import (
    audit_archive,
    audit_member,
    market_date_shape,
    parse_market_date,
    parse_quote_datetime,
    quote_datetime_shape,
    shape_signature,
)
from research.phase170_cboe_option_trades_public_sample_audit import BASE_FIELDS

def make_csv(rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(BASE_FIELDS))
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")

def make_row(**overrides):
    row = {
        "underlying_symbol": "TEST",
        "market_date": "1/7/2026",
        "quote_datetime": "1/7/2026 9:30:00.123 AM",
        "sequence_number": "1001",
        "root": "TEST",
        "expiration": "1/16/2026",
        "strike": "10",
        "option_type": "C",
        "exchange_id": "1",
        "trade_size": "5",
        "trade_price": "1.25",
        "trade_condition_id": "0",
        "canceled_trade_condition_id": "0",
        "best_bid_size": "10",
        "best_bid": "1.20",
        "best_ask": "1.30",
        "best_ask_size": "12",
        "underlying_bid": "9.99",
        "underlying_ask": "10.01",
    }
    row.update(overrides)
    return row

def make_zip(payload):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("UnderlyingOptionsTrades_2026-01-07.csv", payload)
    return out.getvalue()

class Phase171Tests(unittest.TestCase):
    def test_shape_signature_removes_all_original_values(self):
        signature = shape_signature("1/7/2026 09:30:00.123 AM")
        self.assertEqual(signature, "9/9/9999 99:99:99.999 AA")
        self.assertNotIn("2026", signature)
        self.assertNotIn("AM", signature)

    def test_market_date_shapes(self):
        self.assertEqual(market_date_shape("1/7/2026"), "us_m_d_yyyy")
        self.assertEqual(market_date_shape("2026-01-07"), "yyyy_mm_dd")
        self.assertEqual(market_date_shape(""), "blank")

    def test_us_market_date_parses_calendar_safely(self):
        parsed, label = parse_market_date("1/7/2026")
        self.assertEqual(parsed, date(2026, 1, 7))
        self.assertEqual(label, "us_m_d_yyyy")
        invalid, invalid_label = parse_market_date("2/30/2026")
        self.assertIsNone(invalid)
        self.assertEqual(invalid_label, "invalid_calendar_date")

    def test_quote_datetime_us_12h_fractional_parses(self):
        parsed, label = parse_quote_datetime("1/7/2026 9:30:00.123 AM")
        self.assertIsNotNone(parsed)
        self.assertEqual(label, "us_12h_fractional")
        self.assertEqual(parsed.hour, 9)

    def test_quote_datetime_unknown_suffix_fails_closed(self):
        parsed, label = parse_quote_datetime("1/7/2026 09:30:00.123 ET")
        self.assertIsNone(parsed)
        self.assertEqual(label, "unparsed")
        self.assertEqual(quote_datetime_shape("1/7/2026 09:30:00.123 ET"), "other")

    def test_joint_blankness_and_non_date_core_completeness(self):
        both_blank = make_row(market_date="", quote_datetime="")
        md_only = make_row(quote_datetime="")
        qdt_only = make_row(market_date="")
        result = audit_member(
            "UnderlyingOptionsTrades_2026-01-07.csv",
            make_csv([both_blank, md_only, qdt_only]),
        )
        self.assertEqual(result["date_time_joint_blankness"], {
            "both_blank": 1,
            "market_date_blank_only": 1,
            "quote_datetime_blank_only": 1,
        })
        self.assertEqual(result["both_date_fields_blank_core_complete_rows"], 1)
        self.assertEqual(result["both_date_fields_blank_core_incomplete_rows"], 0)

    def test_blank_non_date_core_fields_are_counted(self):
        row = make_row(market_date="", quote_datetime="", trade_price="")
        result = audit_member("sample.csv", make_csv([row]))
        self.assertEqual(result["core_required_blank_field_counts"], {"trade_price": 1})
        self.assertEqual(result["both_date_fields_blank_core_incomplete_rows"], 1)

    def test_filename_date_match_is_aggregate_only(self):
        result = audit_member(
            "UnderlyingOptionsTrades_2026-01-07.csv",
            make_csv([make_row()]),
        )
        self.assertEqual(result["market_date_filename_match_rows"], 1)
        self.assertEqual(result["market_date_filename_mismatch_rows"], 0)
        self.assertEqual(result["market_date_min"], "2026-01-07")
        self.assertNotIn("TEST", str(result))
        self.assertNotIn("1/7/2026", str(result))

    def test_archive_is_diagnostic_not_alpha_admitted(self):
        result = audit_archive(make_zip(make_csv([make_row()])), "2026-11-07T00:00:00+00:00")
        self.assertEqual(result["status"], "DIAGNOSTIC_COMPLETE")
        self.assertFalse(result["alpha_admission"])
        self.assertFalse(result["strict_pit"])
        self.assertFalse(result["raw_rows_persisted"])
        self.assertFalse(result["raw_symbols_persisted"])
        self.assertFalse(result["raw_contracts_persisted"])
        self.assertFalse(result["raw_timestamps_persisted"])

if __name__ == "__main__":
    unittest.main()
