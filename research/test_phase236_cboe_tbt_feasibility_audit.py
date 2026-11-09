import unittest
from research.phase236_cboe_tbt_feasibility_audit import (
    build_audit, classify_trade_date, strict_pit_gate, validate_row_semantics
)

class Phase236TBTTests(unittest.TestCase):
    def test_archive_start_is_not_live_pit(self):
        self.assertEqual(
            classify_trade_date("2019-10-07"),
            "RETROSPECTIVE_BACKFILL_NOT_STRICT_PIT"
        )

    def test_day_before_documented_live_floor_is_backfill(self):
        self.assertEqual(
            classify_trade_date("2026-02-19"),
            "RETROSPECTIVE_BACKFILL_NOT_STRICT_PIT"
        )

    def test_documented_live_floor_requires_receipt(self):
        self.assertEqual(
            classify_trade_date("2026-02-20"),
            "LIVE_PRODUCT_WINDOW_RECEIPT_REQUIRED"
        )

    def test_invalid_trade_date_fails_closed(self):
        self.assertEqual(classify_trade_date("not-a-date"), "UNKNOWN_INVALID_DATE")

    def test_missing_receipt_blocks_strict_pit(self):
        r = strict_pit_gate(
            trade_date="2026-03-02", first_receipt_utc=None,
            raw_sha256="a"*64, vintage_id="v1", schema_version="1.1",
            security_identity_resolved=True, internal_license_confirmed=True
        )
        self.assertFalse(r["eligible"])
        self.assertIn("FIRST_RECEIPT_TIMESTAMP_MISSING_OR_NAIVE", r["reasons"])

    def test_naive_receipt_blocks_strict_pit(self):
        r = strict_pit_gate(
            trade_date="2026-03-02", first_receipt_utc="2026-03-03T05:30:00",
            raw_sha256="a"*64, vintage_id="v1", schema_version="1.1",
            security_identity_resolved=True, internal_license_confirmed=True
        )
        self.assertFalse(r["eligible"])

    def test_manual_receipt_is_not_pit(self):
        r = strict_pit_gate(
            trade_date="2026-03-02", first_receipt_utc="2026-03-03T05:30:00Z",
            raw_sha256="a"*64, vintage_id="v1", schema_version="1.1",
            security_identity_resolved=True, internal_license_confirmed=True,
            event_name="workflow_dispatch"
        )
        self.assertFalse(r["eligible"])
        self.assertIn("NON_SCHEDULED_RECEIPT_NOT_PIT", r["reasons"])

    def test_valid_t_plus_one_receipt_can_pass_data_gate(self):
        r = strict_pit_gate(
            trade_date="2026-03-02", first_receipt_utc="2026-03-03T05:30:00Z",
            raw_sha256="a"*64, vintage_id="20260302__v1",
            schema_version="1.1", security_identity_resolved=True,
            internal_license_confirmed=True
        )
        self.assertTrue(r["eligible"])
        self.assertEqual(r["status"], "STRICT_PIT_DATA_GATE_PASS")

    def test_same_day_receipt_fails_t_plus_one(self):
        r = strict_pit_gate(
            trade_date="2026-03-02", first_receipt_utc="2026-03-02T23:30:00Z",
            raw_sha256="a"*64, vintage_id="v1", schema_version="1.1",
            security_identity_resolved=True, internal_license_confirmed=True
        )
        self.assertFalse(r["eligible"])
        self.assertIn("T_PLUS_ONE_RECEIPT_NOT_AFTER_TRADE_DATE", r["reasons"])

    def test_invalid_hash_blocks_pit(self):
        r = strict_pit_gate(
            trade_date="2026-03-02", first_receipt_utc="2026-03-03T05:30:00Z",
            raw_sha256="bad", vintage_id="v1", schema_version="1.1",
            security_identity_resolved=True, internal_license_confirmed=True
        )
        self.assertIn("RAW_SHA256_MISSING_OR_INVALID", r["reasons"])

    def test_unresolved_identity_and_license_block_pit(self):
        r = strict_pit_gate(
            trade_date="2026-03-02", first_receipt_utc="2026-03-03T05:30:00Z",
            raw_sha256="a"*64, vintage_id="v1", schema_version="1.1",
            security_identity_resolved=False, internal_license_confirmed=False
        )
        self.assertIn("EFFECTIVE_DATED_SECURITY_IDENTITY_UNRESOLVED", r["reasons"])
        self.assertIn("INTERNAL_USE_LICENSE_NOT_CONFIRMED", r["reasons"])

    def test_valid_documented_row_does_not_infer_aggressor_or_owner(self):
        row = {
            "SIDE":"B", "OPEN_CLOSE":"O", "CAPACITY":"Customer", "SIZE":10,
            "TRANSACT_TIME":"2026-03-03T14:30:00", "TRADING_DT":"2026-03-02",
            "UNDERLYING":"XYZ", "OSI_ROOT":"XYZ", "TRADE_TYPE":"AIM Agency"
        }
        r = validate_row_semantics(row)
        self.assertTrue(r["valid_documented_fields"])
        self.assertFalse(r["aggressor_side_inferred"])
        self.assertFalse(r["beneficial_owner_identified"])

    def test_provisional_trade_type_is_separately_flagged(self):
        row = {
            "SIDE":"S", "OPEN_CLOSE":"C", "CAPACITY":"MarketMaker", "SIZE":1,
            "TRANSACT_TIME":"2026-03-03T14:30:00", "TRADING_DT":"2026-03-02",
            "UNDERLYING":"XYZ", "OSI_ROOT":"XYZ", "TRADE_TYPE":"Provisional"
        }
        r = validate_row_semantics(row)
        self.assertTrue(r["valid_documented_fields"])
        self.assertTrue(r["provisional_trade_type"])
        self.assertTrue(r["trade_type_requires_separate_bucket"])

    def test_invalid_capacity_is_rejected(self):
        row = {
            "SIDE":"B", "OPEN_CLOSE":"O", "CAPACITY":"Institution", "SIZE":10,
            "TRANSACT_TIME":"2026-03-03T14:30:00", "TRADING_DT":"2026-03-02",
            "UNDERLYING":"XYZ", "OSI_ROOT":"XYZ", "TRADE_TYPE":"AIM Agency"
        }
        self.assertFalse(validate_row_semantics(row)["valid_documented_fields"])

    def test_audit_keeps_c1_only_and_no_alpha(self):
        a = build_audit()
        self.assertEqual(a["source"]["venue_scope"], ["C1"])
        self.assertFalse(a["admission"]["strict_historical_pit"])
        self.assertFalse(a["admission"]["alpha_test_authorized"])
        self.assertTrue(a["admission"]["f80_frozen"])

if __name__ == "__main__":
    unittest.main()
