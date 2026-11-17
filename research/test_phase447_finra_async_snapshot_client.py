import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from phase447_finra_async_snapshot_client import (
    FIP_TOKEN_URL,
    MAX_ASYNC_RECORDS,
    PartitionRequired,
    SnapshotContractError,
    build_async_payload,
    parse_completed_headers,
    parse_status,
    parse_submission,
    obtain_access_token,
    retrieve_snapshot,
    validate_records,
)


def complete_headers(total=2, limit=MAX_ASYNC_RECORDS, offset=0):
    return {
        "Record-Total": str(total),
        "Record-Offset": str(offset),
        "Record-Limit": str(limit),
        "Total-Records-On-Page": str(total),
        "Record-Max-Limit": "100000",
        "FINRA-api-request-id": "tracking-complete",
    }


class FakeResponse:
    def __init__(self, status_code, headers=None, body=None, content=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._body = body
        self.content = content if content is not None else json.dumps(body).encode()

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, records):
        self.records = records
        self.get_calls = []
        self.post_call = None
        self.fip_call = None
        self.status_count = 0
        self.closed = False

    def post(self, url, headers=None, json=None, timeout=None):
        if url == FIP_TOKEN_URL:
            self.fip_call = {"url": url, "headers": headers, "timeout": timeout}
            return FakeResponse(
                200,
                {"Content-Type": "application/json"},
                {"access_token": "synthetic-oauth-token", "expires_in": 43170},
            )
        self.post_call = {"url": url, "headers": headers, "json": json, "timeout": timeout}
        return FakeResponse(
            202,
            {"Location": "https://api.finra.org/async-requests/group/otcMarket/name/consolidatedShortInterest/request-123",
             "FINRA-api-request-id": "tracking-submit"},
            {},
        )

    def get(self, url, headers=None, timeout=None):
        self.get_calls.append({"url": url, "headers": headers, "timeout": timeout})
        if "async-requests" in url:
            self.status_count += 1
            if self.status_count == 1:
                return FakeResponse(202, {}, {"requestId": "request-123", "status": "pending"})
            return FakeResponse(
                200,
                complete_headers(total=len(self.records)),
                {
                    "requestId": "request-123",
                    "status": "complete",
                    "resultLink": "https://bucket.s3.amazonaws.com/presigned?token=embedded",
                    "expires": "2026-11-17T00:00:00Z",
                },
            )
        return FakeResponse(
            200,
            {"Content-Type": "application/json"},
            self.records,
            json.dumps(self.records).encode(),
        )

    def close(self):
        self.closed = True


class Phase447Tests(unittest.TestCase):
    def setUp(self):
        self.day = "2026-09-30"
        self.records = [
            {"settlementDate": self.day, "symbolCode": "AAA", "currentShortPositionQuantity": 100},
            {"settlementDate": self.day, "symbolCode": "BBB", "currentShortPositionQuantity": 200},
        ]

    def test_oauth_client_credentials_exchange(self):
        session = FakeSession(self.records)
        token, expires = obtain_access_token(session, "client-id", "client-secret")
        self.assertEqual(token, "synthetic-oauth-token")
        self.assertEqual(expires, 43170)
        expected = "Basic " + __import__("base64").b64encode(b"client-id:client-secret").decode()
        self.assertEqual(session.fip_call["headers"]["Authorization"], expected)

    def test_retrieval_can_use_client_credentials_without_stored_bearer(self):
        session = FakeSession(self.records)
        env = {
            "FINRA_ACCESS_TOKEN": "",
            "FINRA_CLIENT_ID": "client-id",
            "FINRA_CLIENT_SECRET": "client-secret",
        }
        with patch.dict(os.environ, env):
            with tempfile.TemporaryDirectory() as tmp:
                manifest = retrieve_snapshot(
                    self.day, tmp, session=session, sleep_fn=lambda seconds: None,
                    clock_fn=lambda: datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc),
                )
        self.assertEqual(manifest["auth_mode"], "oauth_client_credentials")
        self.assertEqual(manifest["token_expires_in_seconds"], 43170)
        self.assertIsNotNone(session.fip_call)
        self.assertIsNotNone(session.post_call)

    def test_missing_credentials_fail_before_any_request(self):
        session = FakeSession(self.records)
        env = {"FINRA_ACCESS_TOKEN": "", "FINRA_CLIENT_ID": "", "FINRA_CLIENT_SECRET": ""}
        with patch.dict(os.environ, env):
            with self.assertRaises(RuntimeError):
                retrieve_snapshot(self.day, tempfile.gettempdir(), session=session)
        self.assertIsNone(session.fip_call)
        self.assertIsNone(session.post_call)

    def test_payload_is_narrow_and_async(self):
        payload = build_async_payload(self.day)
        self.assertTrue(payload["async"])
        self.assertEqual(payload["limit"], 100000)
        self.assertEqual(payload["offset"], 0)
        self.assertEqual(payload["compareFilters"][0]["fieldName"], "settlementDate")
        self.assertEqual(payload["compareFilters"][0]["fieldValue"], self.day)

    def test_submission_requires_accepted_status_and_valid_location(self):
        parsed = parse_submission(202, {
            "Location": "https://api.finra.org/async-requests/group/otcMarket/name/consolidatedShortInterest/abc",
            "FINRA-api-request-id": "tracking-1",
        })
        self.assertEqual(parsed["request_id"], "abc")
        self.assertEqual(parsed["tracking_id"], "tracking-1")
        with self.assertRaises(SnapshotContractError):
            parse_submission(200, {"Location": "https://api.finra.org/async-requests/x/y"})
        with self.assertRaises(SnapshotContractError):
            parse_submission(202, {"Location": "https://evil.example/async-requests/x/y"})

    def test_pending_status_is_not_snapshot_complete(self):
        parsed = parse_status(
            202, {"requestId": "abc", "status": "pending"}, {},
            "abc", now=datetime(2026, 11, 16, tzinfo=timezone.utc)
        )
        self.assertEqual(parsed["status"], "pending")

    def test_completed_status_captures_headers_and_result_link(self):
        parsed = parse_status(
            200,
            {"requestId": "abc", "status": "complete",
             "resultLink": "https://bucket.s3.amazonaws.com/result?sig=x",
             "expires": "2026-11-17T00:00:00Z"},
            complete_headers(),
            "abc",
            now=datetime(2026, 11, 16, tzinfo=timezone.utc),
        )
        self.assertEqual(parsed["record_total"], 2)
        self.assertEqual(parsed["record_offset"], 0)
        self.assertEqual(parsed["record_limit"], 100000)
        self.assertTrue(parsed["result_link"].startswith("https://"))

    def test_completed_status_rejects_expired_result_link(self):
        with self.assertRaises(SnapshotContractError):
            parse_status(
                200,
                {"requestId": "abc", "status": "complete",
                 "resultLink": "https://bucket.s3.amazonaws.com/result?sig=x",
                 "expires": "2026-11-15T00:00:00Z"},
                complete_headers(), "abc",
                now=datetime(2026, 11, 16, tzinfo=timezone.utc),
            )

    def test_completed_status_requires_reconciliation_headers(self):
        with self.assertRaises(SnapshotContractError):
            parse_completed_headers({"Record-Total": "2", "Record-Offset": "0"})

    def test_row_count_and_date_must_reconcile(self):
        metadata = {"record_total": 2, "record_limit": 100000,
                    "record_offset": 0, "total_records_on_page": 2}
        result = validate_records(self.records, self.day, metadata)
        self.assertTrue(result["snapshot_complete"])
        self.assertFalse(result["zero_inference_allowed"])
        with self.assertRaises(SnapshotContractError):
            validate_records(self.records[:1], self.day, metadata)
        wrong_day = [{"settlementDate": "2026-09-29", "symbolCode": "AAA"}]
        with self.assertRaises(SnapshotContractError):
            validate_records(wrong_day, self.day, {
                "record_total": 1, "record_limit": 100000,
                "record_offset": 0, "total_records_on_page": 1,
            })

    def test_over_limit_requires_partition(self):
        with self.assertRaises(PartitionRequired):
            validate_records(self.records, self.day, {
                "record_total": 100001, "record_limit": 100000,
                "record_offset": 0, "total_records_on_page": 2,
            })

    def test_retrieval_uses_no_authorization_header_for_presigned_result(self):
        session = FakeSession(self.records)
        fixed_now = lambda: datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            manifest = retrieve_snapshot(
                self.day, tmp, token="not-a-real-token", session=session,
                sleep_fn=lambda seconds: None, clock_fn=fixed_now,
            )
            self.assertTrue(manifest["snapshot_complete"])
            self.assertFalse(manifest["zero_inference_allowed"])
            self.assertEqual(manifest["row_count"], 2)
            self.assertTrue(Path(tmp, manifest["raw_file"]).exists())
            result_call = [x for x in session.get_calls if "s3.amazonaws.com" in x["url"]][0]
            self.assertIsNone(result_call["headers"])
            self.assertEqual(session.post_call["json"]["compareFilters"][0]["fieldValue"], self.day)

    def test_poll_interval_cannot_be_faster_than_finra_guidance(self):
        session = FakeSession(self.records)
        with self.assertRaises(ValueError):
            retrieve_snapshot(
                self.day, tempfile.gettempdir(), token="x", session=session,
                poll_interval_seconds=59,
            )
        self.assertIsNone(session.post_call)

    def test_result_link_must_be_https_aws_s3(self):
        with self.assertRaises(SnapshotContractError):
            parse_status(
                200,
                {"requestId": "abc", "status": "complete",
                 "resultLink": "https://untrusted.example.test/result?sig=x",
                 "expires": "2026-11-17T00:00:00Z"},
                complete_headers(), "abc",
                now=datetime(2026, 11, 16, tzinfo=timezone.utc),
            )


if __name__ == "__main__":
    unittest.main()
