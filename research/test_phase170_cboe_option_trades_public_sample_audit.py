import io
import unittest
import zipfile
import csv
from decimal import Decimal
from research.phase170_cboe_option_trades_public_sample_audit import (
    BASE_FIELDS, CALCS_FIELDS, audit_archive, audit_csv,
    classify_trade_vs_nbbo, schema_check,
)

def csv_bytes(calcs=False, rows=None, extra=None):
    fields = list(BASE_FIELDS) + (list(CALCS_FIELDS) if calcs else [])
    if extra:
        fields += list(extra)
    if rows is None:
        row = {
            "underlying_symbol": "TEST", "market_date": "2026-11-05",
            "quote_datetime": "2026-11-05 15:59:59.123", "sequence_number": "1001",
            "root": "TEST", "expiration": "2026-11-20", "strike": "10",
            "option_type": "C", "exchange_id": "1", "trade_size": "5",
            "trade_price": "1.25", "trade_condition_id": "0",
            "canceled_trade_condition_id": "0", "best_bid_size": "10",
            "best_bid": "1.20", "best_ask": "1.30", "best_ask_size": "12",
            "underlying_bid": "9.99", "underlying_ask": "10.01", "number_of_exchanges": "0",
        }
        if calcs:
            row.update({name: "0" for name in CALCS_FIELDS})
            row["trade_delta"] = "0.51"
        rows = [row]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()

def zip_bytes(payload):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("sample.csv", payload)
    return out.getvalue()

class Phase170Tests(unittest.TestCase):
    def test_base_schema_has_twenty_fields(self):
        self.assertEqual(len(BASE_FIELDS), 20)

    def test_calcs_schema_has_six_optional_fields(self):
        self.assertEqual(len(CALCS_FIELDS), 6)

    def test_base_schema_passes(self):
        result = schema_check(list(BASE_FIELDS))
        self.assertEqual(result["schema_status"], "PASS")
        self.assertFalse(result["calcs_included"])

    def test_full_calcs_schema_passes(self):
        result = schema_check(list(BASE_FIELDS) + list(CALCS_FIELDS))
        self.assertEqual(result["schema_status"], "PASS")
        self.assertTrue(result["calcs_included"])

    def test_missing_base_field_fails(self):
        result = schema_check(list(BASE_FIELDS[:-1]))
        self.assertEqual(result["schema_status"], "FAIL")
        self.assertIn("number_of_exchanges", result["missing_columns"])

    def test_extra_field_fails_closed(self):
        result = schema_check(list(BASE_FIELDS) + ["unknown_field"])
        self.assertEqual(result["schema_status"], "FAIL")
        self.assertEqual(result["extra_columns"], ["unknown_field"])

    def test_duplicate_header_fails(self):
        result = schema_check(list(BASE_FIELDS) + ["trade_price"])
        self.assertEqual(result["schema_status"], "FAIL")
        self.assertEqual(result["duplicate_columns"], ["trade_price"])

    def test_partial_calcs_group_fails(self):
        result = schema_check(list(BASE_FIELDS) + ["trade_iv"])
        self.assertTrue(result["partial_calcs_group"])

    def test_quote_classification_at_ask(self):
        self.assertEqual(classify_trade_vs_nbbo(Decimal("1.30"), Decimal("1.20"), Decimal("1.30")), "at_ask_candidate")

    def test_quote_classification_at_bid(self):
        self.assertEqual(classify_trade_vs_nbbo(Decimal("1.20"), Decimal("1.20"), Decimal("1.30")), "at_bid_candidate")

    def test_quote_classification_midpoint_is_unclassified(self):
        self.assertEqual(classify_trade_vs_nbbo(Decimal("1.25"), Decimal("1.20"), Decimal("1.30")), "midpoint_unclassified")

    def test_quote_classification_inside_spread_is_unclassified(self):
        self.assertEqual(classify_trade_vs_nbbo(Decimal("1.24"), Decimal("1.20"), Decimal("1.30")), "inside_spread_unclassified")

    def test_quote_classification_outside_quote_is_not_signed(self):
        self.assertEqual(classify_trade_vs_nbbo(Decimal("1.35"), Decimal("1.20"), Decimal("1.30")), "outside_above_ask")

    def test_quote_classification_crossed(self):
        self.assertEqual(classify_trade_vs_nbbo(Decimal("1.25"), Decimal("1.30"), Decimal("1.20")), "invalid_or_crossed_nbbo")

    def test_quote_classification_missing(self):
        self.assertEqual(classify_trade_vs_nbbo(Decimal("1.25"), Decimal("0"), Decimal("0")), "missing_nbbo")

    def test_valid_base_sample_passes_without_calcs(self):
        result = audit_csv("sample.csv", csv_bytes())
        self.assertEqual(result["schema_status"], "PASS")
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["underlying_count"], 1)
        self.assertFalse(result["raw_symbols_persisted"])

    def test_calcs_zero_is_counted_not_rejected(self):
        result = audit_csv("sample.csv", csv_bytes(calcs=True))
        self.assertEqual(result["schema_status"], "PASS")
        self.assertEqual(result["calcs_zero_counts"]["trade_iv"], 1)
        self.assertEqual(result["invalid_core_rows"], 0)

    def test_gth_calendar_date_mismatch_is_diagnostic_not_schema_failure(self):
        row = {
            "underlying_symbol": "TEST", "market_date": "2026-11-06",
            "quote_datetime": "2026-11-05 20:01:00.000", "sequence_number": "1002",
            "root": "TEST", "expiration": "2026-11-20", "strike": "10",
            "option_type": "P", "exchange_id": "1", "trade_size": "1",
            "trade_price": "1.00", "trade_condition_id": "0",
            "canceled_trade_condition_id": "0", "best_bid_size": "0",
            "best_bid": "0", "best_ask": "1.10", "best_ask_size": "5",
            "underlying_bid": "0", "underlying_ask": "0", "number_of_exchanges": "0",
        }
        result = audit_csv("sample.csv", csv_bytes(rows=[row]))
        self.assertEqual(result["schema_status"], "PASS")
        self.assertEqual(result["quote_datetime_market_date_mismatch_rows"], 1)

    def test_nonzero_legacy_fields_are_reported(self):
        row = {
            "underlying_symbol": "TEST", "market_date": "2026-11-05",
            "quote_datetime": "2026-11-05 15:59:59.123", "sequence_number": "1003",
            "root": "TEST", "expiration": "2026-11-20", "strike": "10",
            "option_type": "C", "exchange_id": "1", "trade_size": "5",
            "trade_price": "1.25", "trade_condition_id": "0",
            "canceled_trade_condition_id": "7", "best_bid_size": "10",
            "best_bid": "1.20", "best_ask": "1.30", "best_ask_size": "12",
            "underlying_bid": "9.99", "underlying_ask": "10.01", "number_of_exchanges": "2",
        }
        result = audit_csv("sample.csv", csv_bytes(rows=[row]))
        self.assertEqual(result["nonzero_canceled_trade_condition_rows"], 1)
        self.assertEqual(result["nonzero_number_of_exchanges_rows"], 1)

    def test_archive_summary_does_not_persist_raw_data(self):
        result = audit_archive(zip_bytes(csv_bytes()))
        self.assertEqual(result["status"], "PASS_SCHEMA_SAMPLE")
        self.assertFalse(result["raw_archive_persisted"])
        self.assertFalse(result["raw_rows_persisted"])
        self.assertFalse(result["raw_symbols_persisted"])

    def test_non_zip_fails(self):
        with self.assertRaisesRegex(ValueError, "sample_not_zip"):
            audit_archive(b"not a zip")

if __name__ == "__main__":
    unittest.main()
