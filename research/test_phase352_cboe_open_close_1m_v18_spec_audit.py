import unittest

from research.phase352_cboe_open_close_1m_v18_spec_audit import (
    REQUIRED_CHECKS,
    audit_spec_text,
)


SPEC_TEXT = """
v1.8 20261108
C2, BZX, EDGX (REGULAR TRADING HOURS ONLY)
C1 (GLOBAL TRADING HOURS AND REGULAR TRADING HOURS)
The 1-minute interval files are generated from real-time streaming feeds sourced directly
from the Cboe exchanges' matching engines. To minimize delivery latency, files are published
on a real-time cadence. During rare high-volume bursts, a small number of trades may be
processed slightly late and therefore be reflected in a later 1-minute snapshot.
Please note that these files do incorporate subsequent trade corrections. As a result,
trades that are later broken/canceled will be removed in the subsequent 1-minute snapshots.
Trade count and volume within buckets are aggregated throughout the day, not just the latest interval.
The GTH session can span multiple calendar days and have multiple time intervals for the same market date.
Files in the first trading segment will have _1 in the file name and files in the second segment _2.
Normal RTH Session. Normal GTH Session. Extended GTH Session.
1 or 2 for C1. NULL for C2, BZX, and EDGX.
Empty, not included in 1-minute intervals.
Empty, not included in 1-minute intervals.
Empty, not included in 1-minute intervals.
Empty, not included in 1-minute intervals.
Empty, not included in 1-minute intervals.
Empty, not included in 1-minute intervals.
Empty, not included in 1-minute intervals.
Empty, not included in 1-minute intervals.
Firm F, L, J. Broker-Dealer B. Market Maker M, N. Customer C. Pro-Customer U, W.
87 trading_dt. 88 trading_segment.
"""


class Phase352OpenCloseOneMinuteSpecTests(unittest.TestCase):
    def test_official_v18_semantics_pass(self):
        result = audit_spec_text(SPEC_TEXT)
        self.assertEqual(result["status"], "PASS_SPEC_SEMANTICS", msg=result["failed_checks"])
        self.assertEqual(result["failed_checks"], [])
        self.assertEqual(result["snapshot_model"], "CUMULATIVE_DAY_TO_DATE")

    def test_cumulative_snapshot_semantics_are_mandatory(self):
        result = audit_spec_text(SPEC_TEXT.replace(
            "Trade count and volume within buckets are aggregated throughout the day, not just the latest interval.",
            "Trade count and volume are interval-only."
        ))
        self.assertFalse(result["checks"]["cumulative_day_to_date_snapshots"])
        self.assertIn("cumulative_day_to_date_snapshots", result["failed_checks"])

    def test_correction_semantics_are_mandatory(self):
        result = audit_spec_text(SPEC_TEXT.replace("subsequent trade corrections", "trade updates"))
        self.assertFalse(result["checks"]["subsequent_corrections_are_reflected"])

    def test_busted_trade_removal_is_mandatory(self):
        result = audit_spec_text(SPEC_TEXT.replace(
            "broken/canceled will be removed in the subsequent 1-minute snapshots",
            "broken/canceled are retained"
        ))
        self.assertFalse(result["checks"]["later_busted_or_cancelled_trades_are_removed"])

    def test_all_eight_eod_only_fields_must_be_blank(self):
        result = audit_spec_text(SPEC_TEXT.replace(
            "Empty, not included in 1-minute intervals.",
            "Available in 1-minute intervals.",
            1
        ))
        self.assertFalse(result["checks"]["fields_10_to_17_empty_in_1m"])

    def test_capacity_mapping_must_be_complete(self):
        result = audit_spec_text(SPEC_TEXT.replace("Pro-Customer U, W", "Pro-Customer U"))
        self.assertFalse(result["checks"]["capacity_code_mapping_present"])

    def test_segment_convention_must_be_product_specific(self):
        result = audit_spec_text(SPEC_TEXT.replace("Extended GTH Session.", "Holiday session."))
        self.assertFalse(result["checks"]["c1_segment_is_product_specific"])

    def test_version_is_pinned(self):
        result = audit_spec_text(SPEC_TEXT.replace("v1.8 20261108", "v1.7 20261001"))
        self.assertFalse(result["checks"]["version_v1_8_20261108"])

    def test_pdf_linebreaks_and_hyphenation_are_normalized(self):
        text = SPEC_TEXT.replace("real-time", "real-\\ntime")
        text = text.replace("Normal RTH Session", "Normal\\nRTH Session")
        text = text.replace("Extended GTH Session", "Extended GTH\\nSession")
        result = audit_spec_text(text)
        self.assertTrue(result["checks"]["real_time_publication_cadence"])
        self.assertTrue(result["checks"]["c1_segment_is_product_specific"])

    def test_pit_and_alpha_gates_remain_closed(self):
        result = audit_spec_text(SPEC_TEXT)
        self.assertFalse(result["historical_pit_admitted"])
        self.assertFalse(result["prospective_pit_admitted"])
        self.assertFalse(result["alpha_admission"])
        self.assertFalse(result["return_test_authorized"])
        self.assertFalse(result["holdout_used"])
        self.assertTrue(result["f80_frozen"])

    def test_every_required_check_is_evaluated(self):
        result = audit_spec_text(SPEC_TEXT)
        self.assertEqual(set(result["checks"]), set(REQUIRED_CHECKS))


if __name__ == "__main__":
    unittest.main()
