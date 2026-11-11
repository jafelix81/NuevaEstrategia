import hashlib
import unittest

from research.phase168_cboe_openclose_eod_public_sample_audit import bucket_columns
from research.phase249_cboe_openclose_real_sample_reprocessing import (
    FEATURE_SPECS,
    analyze_rows,
    parse_eod_rows,
)


def make_row(symbol="ABC", security_type="1", series_type="S", call_put="C", option_symbol="ABCOPT"):
    row = {
        "quote_date": "03/28/2025",
        "underlying_symbol": symbol,
        "security_type": security_type,
        "option_symbol": option_symbol,
        "expiration_date": "2025-04-18",
        "strike_price": "100",
        "call_put_flag": call_put,
        "days_to_expire": "21",
        "series_type": series_type,
        "first_trade_price": "1.00",
        "high_trade_price": "1.20",
        "low_trade_price": "0.90",
        "last_trade_price": "1.10",
        "total_exchange_vol": "0",
        "total_industry_vol": "0",
        "open_interest": "100",
        "previous_open_interest": "90",
        "previous_close": "100",
    }
    for field in bucket_columns():
        row[field] = "0"
    return row


def set_volume(row, field, value):
    row[field] = str(value)
    volume_fields = [name for name in bucket_columns() if name.endswith("_vol")]
    row["total_exchange_vol"] = str(sum(int(row[name]) for name in volume_fields))


def analyze(rows):
    return analyze_rows(
        rows,
        member_name="C1OpenClose_2025-03-28_sample_20pct.csv",
        member_sha256=hashlib.sha256(b"member").hexdigest(),
        archive_sha256=hashlib.sha256(b"archive").hexdigest(),
        archive_bytes=7,
        retrieved_at_utc="2026-11-09T23:30:00+00:00",
    )


class Phase249RealSampleReprocessingTests(unittest.TestCase):
    def test_customer_and_pro_customer_opening_features_are_built(self):
        row = make_row()
        set_volume(row, "cust_lt_100_open_buy_vol", 12)
        set_volume(row, "procust_100_199_open_buy_vol", 8)
        result = analyze([row])
        features = result["feature_aggregation"]["cross_sectional_diagnostics"]
        self.assertEqual(features["customer_open_all"]["positive_net_groups"], 1)
        self.assertEqual(features["pro_customer_open_all"]["positive_net_groups"], 1)

    def test_put_sign_convention_is_applied_on_real_row_shape(self):
        row = make_row(call_put="P")
        set_volume(row, "cust_lt_100_open_sell_vol", 7)
        result = analyze([row])
        feature = result["feature_aggregation"]["cross_sectional_diagnostics"]["customer_open_all"]
        self.assertEqual(feature["positive_net_groups"], 1)

    def test_flex_rows_are_excluded_without_discarding_standard_rows(self):
        standard = make_row(symbol="ABC", series_type="S", option_symbol="ABCOPT1")
        flex = make_row(symbol="ABC", series_type="F", option_symbol="ABCOPT2")
        set_volume(standard, "cust_lt_100_open_buy_vol", 5)
        set_volume(flex, "cust_lt_100_open_sell_vol", 99)
        result = analyze([standard, flex])
        self.assertEqual(result["primary_equity_etf"]["flex_rows_excluded"], 1)
        self.assertEqual(result["primary_equity_etf"]["rows_after_flex_exclusion"], 1)
        feature = result["feature_aggregation"]["cross_sectional_diagnostics"]["customer_open_all"]
        self.assertEqual(feature["positive_net_groups"], 1)

    def test_equity_and_etf_are_kept_in_separate_groups(self):
        equity = make_row(symbol="ABC", security_type="1", option_symbol="ABCOPT1")
        etf = make_row(symbol="ABC", security_type="2", option_symbol="ABCOPT2")
        result = analyze([equity, etf])
        self.assertEqual(result["primary_equity_etf"]["underlying_groups"], 2)
        self.assertEqual(result["primary_equity_etf"]["underlying_groups_by_security_type"], {"1": 1, "2": 1})

    def test_index_rows_are_excluded_from_stock_selection_panel(self):
        equity = make_row(symbol="ABC", security_type="1", option_symbol="ABCOPT1")
        index = make_row(symbol="SPX", security_type="3", option_symbol="SPXOPT")
        result = analyze([equity, index])
        self.assertEqual(result["primary_equity_etf"]["index_and_warrant_rows_excluded"], 1)
        self.assertEqual(result["primary_equity_etf"]["underlying_groups"], 1)

    def test_duplicate_series_keys_fail_closed(self):
        first = make_row()
        second = make_row()
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OPTION_SERIES_KEYS"):
            analyze([first, second])

    def test_participant_volume_reconciliation_must_be_exact(self):
        row = make_row()
        row["cust_lt_100_open_buy_vol"] = "10"
        with self.assertRaisesRegex(ValueError, "PARTICIPANT_VOLUME_RECONCILIATION_FAILED"):
            analyze([row])

    def test_mixed_dates_fail_closed(self):
        first = make_row()
        second = make_row(symbol="XYZ", option_symbol="XYZOPT")
        second["quote_date"] = "03/31/2025"
        with self.assertRaisesRegex(ValueError, "MIXED_QUOTE_DATES"):
            analyze([first, second])

    def test_result_does_not_persist_underlying_names_or_raw_rows(self):
        result = analyze([make_row()])
        serialized = str(result)
        self.assertNotIn("ABC", serialized)
        self.assertNotIn("option_symbol", serialized)
        self.assertFalse(result["limitations"]["raw_rows_persisted"])
        self.assertFalse(result["limitations"]["raw_symbols_persisted"])

    def test_all_preregistered_features_are_reported(self):
        result = analyze([make_row()])
        features = result["feature_aggregation"]["cross_sectional_diagnostics"]
        self.assertEqual(set(features), {name for name, *_ in FEATURE_SPECS})
        self.assertEqual(result["feature_aggregation"]["expected_underlying_feature_groups"], len(FEATURE_SPECS))
        self.assertEqual(result["feature_aggregation"]["built_underlying_feature_groups"], len(FEATURE_SPECS))

    def test_sample_reprocessing_keeps_pit_alpha_and_f80_controls_closed(self):
        result = analyze([make_row()])
        gates = result["limitations"]
        self.assertFalse(gates["strict_pit_admitted"])
        self.assertFalse(gates["returns_tested"])
        self.assertFalse(gates["alpha_admission"])
        self.assertTrue(gates["f80_frozen"])
        self.assertFalse(gates["consumed_holdout_used"])


if __name__ == "__main__":
    unittest.main()
