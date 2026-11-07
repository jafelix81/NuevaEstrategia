import csv
import io
import unittest
import zipfile

from research.phase187_orats_near_eod_public_sample_pit_audit import (
    EXPECTED_SAMPLE_DATE, audit_archive, audit_csv
)

HEADERS = [
    "ticker", "tradeDate", "expirDate", "strike", "callVolume", "putVolume",
    "callOpenInterest", "putOpenInterest", "updatedAt", "callMidIv",
    "putMidIv", "smvVol", "stockPrice"
]
HEADERS_NO_TIMESTAMP = [h for h in HEADERS if h != "updatedAt"]


def sample_row(**overrides):
    row = {
        "ticker": "TEST", "tradeDate": EXPECTED_SAMPLE_DATE,
        "expirDate": "2024-02-16", "strike": "100",
        "callVolume": "10", "putVolume": "8",
        "callOpenInterest": "100", "putOpenInterest": "120",
        "updatedAt": "2024-01-03T20:46:00Z",
        "callMidIv": "0.25", "putMidIv": "0.27",
        "smvVol": "0.26", "stockPrice": "100.50"
    }
    row.update(overrides)
    return row


def csv_payload(rows, headers=HEADERS):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def zip_payload(data, member="ORATS_SMV_Strikes_20240103.csv"):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, data)
    return stream.getvalue()


class Phase187OratsNearEodTests(unittest.TestCase):
    def test_public_sample_schema_passes_without_api_only_timestamp(self):
        r = audit_archive(zip_payload(csv_payload(
            [sample_row(), sample_row(ticker="OTHER", strike="105")],
            HEADERS_NO_TIMESTAMP
        )), "2026-11-07T00:00:00+00:00")
        self.assertTrue(r["sample_schema_pass"])
        self.assertTrue(r["sample_overall_pass"])
        self.assertEqual(r["member_audits"][0]["row_count"], 2)
        self.assertEqual(r["member_audits"][0]["unique_underlying_count"], 2)
        self.assertFalse(r["timestamp_field_present"])
        self.assertEqual(r["member_audits"][0]["updated_at_absent_rows"], 2)
        self.assertFalse(r["timestamp_diagnostic_pass"])
        self.assertEqual(
            r["overall_status"],
            "PUBLIC_SAMPLE_SCHEMA_AND_ROW_DIAGNOSTICS_PASS_TIMESTAMP_ABSENT"
        )

    def test_trade_date_must_match_sample_filename_date(self):
        r = audit_archive(zip_payload(csv_payload(
            [sample_row(tradeDate="2024-01-04")], HEADERS_NO_TIMESTAMP
        )))
        self.assertFalse(r["sample_overall_pass"])
        self.assertEqual(r["member_audits"][0]["trade_date_filename_mismatch_rows"], 1)

    def test_duplicate_contract_keys_are_counted_and_fail_sample_gate(self):
        r = audit_archive(zip_payload(csv_payload(
            [sample_row(), sample_row()], HEADERS_NO_TIMESTAMP
        )))
        self.assertEqual(r["member_audits"][0]["duplicate_contract_key_rows"], 1)
        self.assertEqual(r["duplicate_contract_key_rows"], 1)
        self.assertFalse(r["sample_overall_pass"])

    def test_optional_aware_timestamp_is_diagnosed_when_present(self):
        r = audit_archive(zip_payload(csv_payload([sample_row(), sample_row(ticker="OTHER")])))
        self.assertTrue(r["sample_overall_pass"])
        self.assertTrue(r["timestamp_field_present"])
        self.assertEqual(r["timestamp_aware_rows"], 2)
        self.assertTrue(r["timestamp_diagnostic_pass"])

    def test_optional_naive_timestamp_does_not_break_structural_gate(self):
        r = audit_archive(zip_payload(csv_payload(
            [sample_row(updatedAt="2024-01-03T15:46:00")]
        )))
        self.assertTrue(r["sample_overall_pass"])
        self.assertEqual(r["timestamp_naive_rows"], 1)
        self.assertFalse(r["timestamp_diagnostic_pass"])

    def test_optional_malformed_timestamp_is_separate_from_schema_gate(self):
        r = audit_archive(zip_payload(csv_payload(
            [sample_row(updatedAt="not-a-time")]
        )))
        self.assertTrue(r["sample_overall_pass"])
        self.assertEqual(r["timestamp_parse_fail_rows"], 1)
        self.assertFalse(r["timestamp_diagnostic_pass"])

    def test_missing_required_header_fails_schema_gate(self):
        headers = [x for x in HEADERS_NO_TIMESTAMP if x != "putOpenInterest"]
        r = audit_csv("sample_20240103.csv", csv_payload([sample_row()], headers=headers))
        self.assertFalse(r["schema_pass"])
        self.assertIn("put_oi", r["missing_required_fields"])

    def test_zero_iv_is_unavailable_not_zero_volatility(self):
        r = audit_csv("sample_20240103.csv", csv_payload(
            [sample_row(callMidIv="0", putMidIv="")]
        ))
        self.assertEqual(r["iv_zero_or_missing_counts"]["call_mid_iv"], 1)
        self.assertEqual(r["iv_zero_or_missing_counts"]["put_mid_iv"], 1)

    def test_flow_and_owner_identity_are_never_inferred(self):
        r = audit_archive(zip_payload(csv_payload(
            [sample_row()], HEADERS_NO_TIMESTAMP
        )))
        self.assertFalse(r["aggressor_side_available"])
        self.assertFalse(r["open_close_available"])
        self.assertFalse(r["participant_capacity_available"])
        self.assertFalse(r["beneficial_owner_identity_available"])
        self.assertIn(
            "not interval increments or signed flow",
            r["measurement_semantics"]["call_put_volume"]
        )

    def test_raw_symbols_and_rows_are_not_persisted(self):
        r = audit_archive(zip_payload(csv_payload(
            [sample_row()], HEADERS_NO_TIMESTAMP
        )))
        self.assertNotIn("TEST", str(r))
        self.assertFalse(r["controls"]["raw_rows_persisted"])
        self.assertFalse(r["controls"]["raw_symbols_persisted"])

    def test_archive_without_csv_fails_closed(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("README.txt", "sample")
        with self.assertRaises(ValueError):
            audit_archive(stream.getvalue())


if __name__ == "__main__":
    unittest.main()
