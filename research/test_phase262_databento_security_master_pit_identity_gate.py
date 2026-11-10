import unittest
from phase262_databento_security_master_pit_identity_gate import (
    assess_pit_record, identity_key, is_us_common_equity, AUTHORIZED_SCOPE, build_audit_result
)

BASE = {
    "ts_effective": "2026-10-01T00:00:00Z",
    "ts_record": "2026-10-02T12:00:00Z",
    "ts_created": "2026-10-03T12:00:00Z",
}
DECISION = "2026-11-10T20:00:00Z"
OBSERVED = "2026-10-03T12:01:00Z"
HASH = "a" * 64

def assess(record=None, decision=DECISION, observed=OBSERVED, sha=HASH, license=AUTHORIZED_SCOPE):
    return assess_pit_record(record or BASE, decision, first_observed_at=observed, raw_sha256=sha, license_scope=license)

class Phase262Tests(unittest.TestCase):
    def test_valid_prospective_capture_passes(self):
        self.assertTrue(assess()["strict_pit_eligible"])

    def test_effective_time_is_not_availability(self):
        r=assess(observed=None)
        self.assertFalse(r["strict_pit_eligible"])
        self.assertIn("FIRST_CUSTOMER_AVAILABILITY_UNPROVEN", r["reasons"])

    def test_aapl_historical_example_not_pit_for_2005(self):
        a={"ts_effective":"2004-11-19T00:00:00Z","ts_record":"2004-12-06T15:09:30Z","ts_created":"2024-11-11T22:41:24.780487Z"}
        r=assess(a, decision="2005-01-03T00:00:00Z", observed="2024-11-11T22:41:25Z")
        self.assertFalse(r["strict_pit_eligible"])
        self.assertIn("ADDED_TO_DATABASE_AFTER_DECISION", r["reasons"])

    def test_aapl_historical_example_still_needs_our_receipt_in_2025(self):
        a={"ts_effective":"2004-11-19T00:00:00Z","ts_record":"2004-12-06T15:09:30Z","ts_created":"2024-11-11T22:41:24.780487Z"}
        r=assess(a, decision="2025-01-03T00:00:00Z", observed=None)
        self.assertFalse(r["strict_pit_eligible"])

    def test_future_effective_rejected(self):
        a={**BASE,"ts_effective":"2026-12-01T00:00:00Z"}
        self.assertIn("NOT_YET_EFFECTIVE_AT_DECISION",assess(a)["reasons"])

    def test_future_record_change_rejected(self):
        a={**BASE,"ts_record":"2026-12-01T00:00:00Z"}
        self.assertIn("RECORD_LAST_CHANGED_AFTER_DECISION",assess(a)["reasons"])

    def test_future_database_creation_rejected(self):
        a={**BASE,"ts_created":"2026-12-01T00:00:00Z"}
        self.assertIn("ADDED_TO_DATABASE_AFTER_DECISION",assess(a)["reasons"])

    def test_future_first_capture_rejected(self):
        r=assess(observed="2026-11-11T00:00:00Z")
        self.assertIn("FIRST_CAPTURE_AFTER_DECISION",r["reasons"])

    def test_capture_before_database_ingestion_rejected(self):
        r=assess(observed="2026-10-02T00:00:00Z")
        self.assertIn("CAPTURE_PRECEDES_DATABASE_INGESTION",r["reasons"])

    def test_capture_before_record_change_rejected(self):
        r=assess(observed="2026-10-01T00:00:00Z")
        self.assertIn("CAPTURE_PRECEDES_RECORDED_CHANGE",r["reasons"])

    def test_missing_raw_hash_rejected(self):
        self.assertIn("IMMUTABLE_RAW_SHA256_REQUIRED",assess(sha=None)["reasons"])

    def test_malformed_raw_hash_rejected(self):
        self.assertIn("IMMUTABLE_RAW_SHA256_REQUIRED",assess(sha="xyz")["reasons"])

    def test_missing_license_rejected(self):
        self.assertIn("AUTHORIZED_INTERNAL_RESEARCH_LICENSE_REQUIRED",assess(license=None)["reasons"])

    def test_personal_or_unknown_license_rejected(self):
        self.assertIn("AUTHORIZED_INTERNAL_RESEARCH_LICENSE_REQUIRED",assess(license="personal_only")["reasons"])

    def test_naive_decision_time_rejected(self):
        with self.assertRaises(ValueError):
            assess(decision="2026-11-10T20:00:00")

    def test_non_utc_decision_time_rejected(self):
        with self.assertRaises(ValueError):
            assess(decision="2026-11-10T15:00:00-05:00")

    def test_naive_vendor_timestamp_fails_closed(self):
        a={**BASE,"ts_record":"2026-10-02T12:00:00"}
        self.assertFalse(assess(a)["strict_pit_eligible"])

    def test_missing_vendor_timestamp_fails_closed(self):
        a={**BASE}; a.pop("ts_created")
        self.assertFalse(assess(a)["strict_pit_eligible"])

    def test_malformed_vendor_timestamp_fails_closed(self):
        a={**BASE,"ts_effective":"not-a-date"}
        self.assertFalse(assess(a)["strict_pit_eligible"])

    def test_listing_level_key(self):
        self.assertEqual(identity_key({"listing_id":"L-1"},"listing"),"L-1")

    def test_security_level_key(self):
        self.assertEqual(identity_key({"security_id":"S-1"},"security"),"S-1")

    def test_issuer_level_key(self):
        self.assertEqual(identity_key({"issuer_id":"I-1"},"issuer"),"I-1")

    def test_ticker_only_is_rejected(self):
        with self.assertRaises(ValueError):
            identity_key({"symbol":"ABC"},"listing")

    def test_missing_listing_id_is_rejected(self):
        with self.assertRaises(ValueError):
            identity_key({"security_id":"S-1"},"listing")

    def test_missing_security_id_is_rejected(self):
        with self.assertRaises(ValueError):
            identity_key({"listing_id":"L-1"},"security")

    def test_missing_issuer_id_is_rejected(self):
        with self.assertRaises(ValueError):
            identity_key({"security_id":"S-1"},"issuer")

    def test_unknown_identity_level_rejected(self):
        with self.assertRaises(ValueError):
            identity_key({"symbol":"ABC"},"ticker")

    def test_us_common_equity_filter(self):
        self.assertTrue(is_us_common_equity({"listing_country":"US","security_type":"EQS"}))

    def test_etf_not_common_equity(self):
        self.assertFalse(is_us_common_equity({"listing_country":"US","security_type":"ETF"}))

    def test_non_us_equity_not_in_us_common_panel(self):
        self.assertFalse(is_us_common_equity({"listing_country":"GB","security_type":"EQS"}))

    def test_missing_security_type_not_admitted(self):
        self.assertFalse(is_us_common_equity({"listing_country":"US"}))

    def test_audit_result_is_not_pit_admitted(self):
        r=build_audit_result()
        self.assertFalse(r["decision"]["strict_pit_admitted"])
        self.assertFalse(r["decision"]["feature_admitted"])

    def test_audit_result_records_cadence_conflict(self):
        r=build_audit_result()
        self.assertFalse(r["documentation_conflicts"]["cadence_adjudicated"])

    def test_audit_result_records_no_vendor_request(self):
        r=build_audit_result()
        self.assertFalse(r["licensing"]["api_request_made"])
        self.assertFalse(r["licensing"]["purchase_or_contact"])

    def test_audit_result_keeps_f80_frozen(self):
        r=build_audit_result()
        self.assertTrue(r["decision"]["f80_frozen"])
        self.assertFalse(r["decision"]["holdout_used"])

if __name__ == "__main__":
    unittest.main()
