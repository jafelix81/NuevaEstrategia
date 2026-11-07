import csv
import io
import json
import unittest
import zipfile

from research.phase170_cboe_option_trades_public_sample_audit import BASE_FIELDS, CALCS_FIELDS
from research.phase194_cboe_option_trades_daily_flow_sample_audit import (
    audit_archive,
    audit_member,
    parse_market_date,
)

def make_row(**overrides):
    row = {
        "underlying_symbol": "XYZ",
        "market_date": "1/7/2026",
        "quote_datetime": "99:99.9",
        "sequence_number": "1001",
        "root": "XYZ",
        "expiration": "1/16/2026",
        "strike": "25",
        "option_type": "C",
        "exchange_id": "1",
        "trade_size": "10",
        "trade_price": "1.25",
        "trade_condition_id": "0",
        "canceled_trade_condition_id": "",
        "best_bid_size": "20",
        "best_bid": "1.20",
        "best_ask": "1.25",
        "best_ask_size": "30",
        "underlying_bid": "24.99",
        "underlying_ask": "25.01",
    }
    row.update(overrides)
    return row

def csv_bytes(rows, fields=BASE_FIELDS):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(fields), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return out.getvalue().encode()

class Phase194Tests(unittest.TestCase):
    def test_market_date_accepts_public_sample_us_format(self):
        self.assertEqual(parse_market_date("1/7/2026").isoformat(), "2026-01-07")

    def test_market_date_accepts_iso_format(self):
        self.assertEqual(parse_market_date("2026-01-07").isoformat(), "2026-01-07")

    def test_time_only_field_is_not_required_to_parse_for_daily_row(self):
        payload = csv_bytes([make_row()])
        result = audit_member("UnderlyingOptionsTrades_2026-01-07.csv", payload)
        self.assertEqual(result["valid_trade_rows"], 1)
        self.assertEqual(result["quote_time_only_shape_rows"], 1)
        self.assertFalse(result["quote_time_semantics_assigned"] if "quote_time_semantics_assigned" in result else False)

    def test_opaque_99_99_time_does_not_become_a_timestamp(self):
        result = audit_member("UnderlyingOptionsTrades_2026-01-07.csv", csv_bytes([make_row()]))
        self.assertEqual(result["quote_time_hhmm_range_invalid_rows"], 1)
        self.assertEqual(result["quote_time_mmss_range_valid_rows"], 0)
        self.assertIsNone(result.get("quote_datetime_min_et"))

    def test_time_range_diagnostics_do_not_assign_mmss_semantics(self):
        result = audit_member("UnderlyingOptionsTrades_2026-01-07.csv", csv_bytes([make_row(quote_datetime="25:30.0")]))
        self.assertEqual(result["quote_time_hhmm_range_invalid_rows"], 1)
        self.assertEqual(result["quote_time_mmss_range_valid_rows"], 1)
        self.assertEqual(result["valid_trade_rows"], 1)

    def test_trailing_all_blank_rows_are_ignored_but_reported(self):
        blank = {field: "" for field in BASE_FIELDS}
        result = audit_member("UnderlyingOptionsTrades_2026-01-07.csv", csv_bytes([make_row(), blank, blank]))
        self.assertEqual(result["nonblank_trade_rows"], 1)
        self.assertEqual(result["all_columns_blank_rows"], 2)
        self.assertTrue(result["all_blank_rows_only_trailing"])
        self.assertFalse(result["internal_blank_row_detected"])
        self.assertTrue(result["member_row_gate_pass"])

    def test_internal_blank_row_fails_member_gate(self):
        blank = {field: "" for field in BASE_FIELDS}
        result = audit_member("UnderlyingOptionsTrades_2026-01-07.csv", csv_bytes([make_row(), blank, make_row(sequence_number="1002")]))
        self.assertTrue(result["internal_blank_row_detected"])
        self.assertFalse(result["member_row_gate_pass"])

    def test_market_date_filename_mismatch_fails_member_gate(self):
        result = audit_member("UnderlyingOptionsTrades_2026-01-07.csv", csv_bytes([make_row(market_date="1/8/2026")]))
        self.assertEqual(result["market_date_filename_mismatch_rows"], 1)
        self.assertFalse(result["member_row_gate_pass"])

    def test_exact_ask_and_bid_are_only_candidate_sides(self):
        rows = [
            make_row(sequence_number="1001", trade_price="1.25", best_bid="1.20", best_ask="1.25", trade_size="10"),
            make_row(sequence_number="1002", trade_price="1.20", best_bid="1.20", best_ask="1.25", trade_size="5"),
            make_row(sequence_number="1003", trade_price="1.22", best_bid="1.20", best_ask="1.25", trade_size="7"),
        ]
        result = audit_member("UnderlyingOptionsTrades_2026-01-07.csv", csv_bytes(rows))
        self.assertEqual(result["at_ask_contract_volume"], 10)
        self.assertEqual(result["at_bid_contract_volume"], 5)
        self.assertEqual(result["candidate_signed_contract_volume"], 5)
        self.assertEqual(result["unclassified_contract_volume"], 7)

    def test_trade_condition_ids_are_counted_not_interpreted(self):
        result = audit_member("UnderlyingOptionsTrades_2026-01-07.csv", csv_bytes([make_row(trade_condition_id="7")]))
        self.assertEqual(result["trade_condition_counts"], {"7": 1})

    def test_core_digest_ignores_optional_calcs_columns(self):
        base = csv_bytes([make_row()])
        calc_fields = list(BASE_FIELDS) + list(CALCS_FIELDS)
        calc = csv_bytes([make_row(**{field: "0" for field in CALCS_FIELDS})], calc_fields)
        a = audit_member("UnderlyingOptionsTrades_2026-01-07.csv", base)
        b = audit_member("UnderlyingOptionsTradesCalcs_2026-01-07.csv", calc)
        self.assertEqual(a["core_trade_rows_sha256"], b["core_trade_rows_sha256"])

    def test_archive_requires_matching_core_members_for_daily_candidate(self):
        base = csv_bytes([make_row()])
        calc_fields = list(BASE_FIELDS) + list(CALCS_FIELDS)
        calc = csv_bytes([make_row(**{field: "0" for field in CALCS_FIELDS})], calc_fields)
        buff = io.BytesIO()
        with zipfile.ZipFile(buff, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("UnderlyingOptionsTrades_2026-01-07.csv", base)
            z.writestr("UnderlyingOptionsTradesCalcs_2026-01-07.csv", calc)
        result = audit_archive(buff.getvalue(), "2026-11-07T00:00:00+00:00")
        self.assertTrue(result["core_trade_rows_match_across_members"])
        self.assertTrue(result["daily_flow_measurement_candidate"])
        self.assertFalse(result["strict_pit_admitted"])
        self.assertFalse(result["alpha_admission"])

    def test_no_raw_symbols_contracts_or_clock_values_are_persisted(self):
        result = audit_member("UnderlyingOptionsTrades_2026-01-07.csv", csv_bytes([make_row()]))
        serialized = json.dumps(result)
        self.assertNotIn("XYZ", serialized)
        self.assertNotIn("99:99.9", serialized)
        self.assertFalse(result["raw_symbols_persisted"])
        self.assertFalse(result["raw_contracts_persisted"])
        self.assertFalse(result["raw_clock_values_persisted"] if "raw_clock_values_persisted" in result else False)

    def test_f80_and_alpha_controls_remain_closed(self):
        result = audit_archive(b"not-a-zip")
        self.assertFalse(result["alpha_admission"])
        self.assertFalse(result["strict_pit_admitted"])
        self.assertTrue(result["f80_frozen"])

if __name__ == "__main__":
    unittest.main()
