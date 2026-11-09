import hashlib, json, unittest
from unittest.mock import patch
from datetime import date, datetime
from research import phase174_cboe_option_quotes_sample_audit as p174
from research import phase175_cboe_option_quotes_date_locale_audit as p175
from research import phase231_cboe_option_quotes_full_row_reparse as p231

class Phase231Tests(unittest.TestCase):
    def test_unique_us_expiration(self):
        self.assertEqual(p231.parse_unique_expiration("09/22/2023"),date(2023,9,22))
    def test_ambiguous_expiration_rejected(self):
        with self.assertRaisesRegex(ValueError,"ambiguous_expiration_format"):
            p231.parse_unique_expiration("01/02/2023")
    def test_unique_slash_timestamp_preserves_minute_precision(self):
        self.assertEqual(p231.parse_unique_quote_datetime("09/21/2023 10:30"),
                         datetime(2023,9,21,10,30))
    def test_iso_seconds_preserved(self):
        self.assertEqual(p231.parse_unique_quote_datetime("2022-02-02 09:39:00"),
                         datetime(2022,2,2,9,39,0))
    def test_ambiguous_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError,"ambiguous_quote_datetime_format"):
            p231.parse_unique_quote_datetime("01/02/2023 09:30")
    def test_timezone_rejected(self):
        with self.assertRaisesRegex(ValueError,"unexpected_timezone"):
            p231.parse_unique_quote_datetime("2025-03-28 09:31:00-04:00")
    def test_clean_subset_gate_and_no_raw_data(self):
        payload=b"pinned-test-payload"
        fake_summary={"member_index":0,"populated_rows":10,"short_rows":0,"long_rows":0,
          "invalid_contract_rows":0,"invalid_timestamp_rows":0,"numeric_error_rows":0,
          "duplicate_contract_interval_keys":0,"contract_days_with_inconsistent_sod_oi":0,
          "open_interest_present":True,"row_gate_pass":True,"schema_gate_pass":True}
        def fake_csv(data,member_index=0): return dict(fake_summary)
        def fake_archive(data):
            m=p174.audit_csv_bytes(b"dummy",0)
            return {"members":[m],"sample_schema_gate_pass":m["schema_gate_pass"],
                    "archive_sha256":hashlib.sha256(payload).hexdigest(),
                    "download_status":"PASS","sample_admission":False}
        diag={"expiration_interpretation_counts":{"single_format_interpretation":10},
              "quote_datetime_interpretation_counts":{"single_format_interpretation":10},
              "expiry_before_quote_date_rows":0}
        with patch.object(p174,"audit_csv_bytes",fake_csv), \
             patch.object(p174,"audit_archive",fake_archive), \
             patch.object(p175,"diagnose_csv_bytes",lambda data:diag), \
             patch.object(p231,"EXPECTED_ARCHIVE_SHA256",hashlib.sha256(payload).hexdigest()):
            result=p231.audit_archive(payload)
        self.assertTrue(result["archive_integrity_match"])
        self.assertTrue(result["clean_unambiguous_subset_gate_pass"])
        self.assertTrue(result["all_member_date_counter_reconciliation_pass"])
        self.assertFalse(result["pit_admission"])
        self.assertFalse(result["alpha_admission"])
        self.assertFalse(result["raw_rows_persisted"])
        self.assertEqual(result["total_unambiguous_valid_rows"],10)
        self.assertNotIn("SPY",json.dumps(result))
    def test_ambiguous_expiration_is_quarantined_and_not_admitted(self):
        payload=b"pinned-test-payload"
        def fake_csv(data,member_index=0):
            try: p174.parse_expiration("01/02/2023")
            except ValueError:
                return {"member_index":0,"populated_rows":10,"short_rows":0,"long_rows":0,
                  "invalid_contract_rows":1,"invalid_timestamp_rows":0,"numeric_error_rows":0,
                  "duplicate_contract_interval_keys":0,"contract_days_with_inconsistent_sod_oi":0,
                  "open_interest_present":True,"row_gate_pass":False,"schema_gate_pass":False}
        def fake_archive(data):
            m=p174.audit_csv_bytes(b"dummy",0)
            return {"members":[m],"sample_schema_gate_pass":m["schema_gate_pass"],
                    "archive_sha256":hashlib.sha256(payload).hexdigest(),
                    "download_status":"PASS","sample_admission":False}
        diag={"expiration_interpretation_counts":{"ambiguous_multiple_interpretations":1},
              "quote_datetime_interpretation_counts":{"single_format_interpretation":10},
              "expiry_before_quote_date_rows":0}
        with patch.object(p174,"audit_csv_bytes",fake_csv), \
             patch.object(p174,"audit_archive",fake_archive), \
             patch.object(p175,"diagnose_csv_bytes",lambda data:diag), \
             patch.object(p231,"EXPECTED_ARCHIVE_SHA256",hashlib.sha256(payload).hexdigest()):
            result=p231.audit_archive(payload)
        self.assertTrue(result["archive_integrity_match"])
        self.assertFalse(result["sample_schema_gate_pass"])
        self.assertTrue(result["clean_unambiguous_subset_gate_pass"])
        self.assertEqual(result["total_ambiguous_expiration_rows"],1)
        self.assertEqual(result["total_quarantined_ambiguous_date_rows"],1)
        self.assertEqual(result["total_unambiguous_valid_rows"],9)
        self.assertIn("QUARANTINED",result["overall_status"])
    def test_hash_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"phase174_archive_hash_mismatch"):
            p231.audit_archive(b"not-the-pinned-sample")

if __name__=="__main__": unittest.main()
