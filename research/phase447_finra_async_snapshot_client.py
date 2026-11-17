#!/usr/bin/env python3
"""FINRA consolidated short-interest asynchronous snapshot client.

This module is deliberately separate from the killed Phase 31 panel. It submits
one settlement-date-filtered async query, polls at FINRA's documented cadence,
downloads the pre-signed result URL without Authorization, and admits a snapshot
only when FINRA's completion headers reconcile exactly to the downloaded rows.

Raw results and manifests are written to a caller-supplied private directory.
No workflow, artifact upload, alpha test, or production integration is included.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urljoin, urlparse

import requests

BASE_URL = "https://api.finra.org"
DATASET_URL = BASE_URL + "/data/group/otcMarket/name/consolidatedShortInterest"
FIP_TOKEN_URL = "https://ews.fip.finra.org/fip/rest/ews/oauth2/access_token?grant_type=client_credentials"
MAX_ASYNC_RECORDS = 100_000
MIN_POLL_INTERVAL_SECONDS = 60

FIELDS = [
    "settlementDate",
    "symbolCode",
    "issueName",
    "marketClassCode",
    "issuerServicesGroupExchangeCode",
    "currentShortPositionQuantity",
    "previousShortPositionQuantity",
    "changePreviousNumber",
    "changePercent",
    "averageDailyVolumeQuantity",
    "daysToCoverQuantity",
    "revisionFlag",
    "stockSplitFlag",
]


class SnapshotContractError(RuntimeError):
    """The provider response cannot prove a complete settlement snapshot."""


class PartitionRequired(SnapshotContractError):
    """The result exceeds the one-request async ceiling and needs partitioning."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime | None = None) -> str:
    value = value or utc_now()
    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    raw = str(value).strip()
    if raw.endswith(" UTC"):
        parsed = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S UTC")
        return parsed.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp has no timezone")
    return parsed.astimezone(timezone.utc)


def header(headers: Mapping[str, Any], name: str, required: bool = False) -> str | None:
    wanted = name.lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            return str(value).strip()
    if required:
        raise SnapshotContractError(f"missing response header: {name}")
    return None


def int_header(headers: Mapping[str, Any], name: str, required: bool = True) -> int | None:
    value = header(headers, name, required=required)
    if value is None:
        return None
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise SnapshotContractError(f"invalid integer response header {name}: {value!r}") from exc
    if result < 0:
        raise SnapshotContractError(f"negative response header {name}: {result}")
    return result


def validate_settlement_date(value: str) -> str:
    parsed = datetime.strptime(value, "%Y-%m-%d")
    return parsed.date().isoformat()


def obtain_access_token(
    session: requests.Session, client_id: str, client_secret: str
) -> tuple[str, int]:
    """Exchange FINRA API client credentials for a short-lived OAuth bearer token."""
    if not client_id or not client_secret:
        raise RuntimeError("FINRA_CLIENT_ID and FINRA_CLIENT_SECRET are both required")
    raw = f"{client_id}:{client_secret}".encode("utf-8")
    basic = base64.b64encode(raw).decode("ascii")
    response = session.post(
        FIP_TOKEN_URL,
        headers={"Authorization": f"Basic {basic}", "Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    try:
        body = response.json()
    except Exception as exc:
        raise SnapshotContractError("FINRA FIP token response is not JSON") from exc
    token = str(body.get("access_token") or "")
    try:
        expires_in = int(body.get("expires_in"))
    except (TypeError, ValueError) as exc:
        raise SnapshotContractError("FINRA FIP response has invalid expires_in") from exc
    if not token or expires_in <= 0:
        raise SnapshotContractError("FINRA FIP response lacks a valid access_token/expires_in")
    return token, expires_in


def build_async_payload(settlement_date: str) -> dict[str, Any]:
    """Build a narrow, one-settlement async request; no broad unfiltered pull."""
    day = validate_settlement_date(settlement_date)
    return {
        "async": True,
        "limit": MAX_ASYNC_RECORDS,
        "offset": 0,
        "fields": FIELDS,
        "compareFilters": [
            {
                "compareType": "EQUAL",
                "fieldName": "settlementDate",
                "fieldValue": day,
            }
        ],
    }


def parse_submission(status_code: int, headers: Mapping[str, Any]) -> dict[str, Any]:
    if status_code != 202:
        raise SnapshotContractError(f"async submission expected HTTP 202, received {status_code}")
    location = header(headers, "Location", required=True)
    status_url = urljoin(BASE_URL + "/", location)
    parsed = urlparse(status_url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "api.finra.org":
        raise SnapshotContractError("async status Location is not an HTTPS api.finra.org URL")
    if "/async-requests/" not in parsed.path:
        raise SnapshotContractError("async status Location has an unexpected path")
    request_id = parsed.path.rstrip("/").split("/")[-1]
    if not request_id:
        raise SnapshotContractError("async status Location does not contain a request id")
    return {
        "request_id": request_id,
        "status_url": status_url,
        "tracking_id": header(headers, "FINRA-api-request-id"),
    }


def parse_completed_headers(headers: Mapping[str, Any]) -> dict[str, Any]:
    """Read the headers on the completed status response, not the result URL."""
    total = int_header(headers, "Record-Total")
    offset = int_header(headers, "Record-Offset")
    limit = int_header(headers, "Record-Limit")
    page_rows = int_header(headers, "Total-Records-On-Page", required=False)
    if limit is None or limit <= 0:
        raise SnapshotContractError("Record-Limit must be positive")
    if offset != 0:
        raise SnapshotContractError("settlement snapshot must start at offset 0")
    return {
        "record_total": total,
        "record_offset": offset,
        "record_limit": limit,
        "total_records_on_page": page_rows,
        "record_max_limit": int_header(headers, "Record-Max-Limit", required=False),
        "response_payload_max_size": header(headers, "Response-Payload-Max-Size"),
        "finra_tracking_id": header(headers, "FINRA-api-request-id"),
    }


def parse_status(
    status_code: int,
    body: Mapping[str, Any],
    headers: Mapping[str, Any],
    expected_request_id: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    request_id = str(body.get("requestId") or "")
    status = str(body.get("status") or "").lower()
    if request_id != expected_request_id:
        raise SnapshotContractError("async status requestId does not match submitted request")
    if status_code == 202:
        if status != "pending":
            raise SnapshotContractError(f"HTTP 202 requires pending status, received {status!r}")
        return {"status": "pending", "request_id": request_id}
    if status_code != 200 or status != "complete":
        raise SnapshotContractError(
            f"unexpected async status response: HTTP {status_code}, status={status!r}"
        )
    result_link = str(body.get("resultLink") or "")
    if not result_link:
        raise SnapshotContractError("completed async response has no resultLink")
    parsed_link = urlparse(result_link)
    if parsed_link.scheme != "https" or not parsed_link.netloc.lower().endswith("amazonaws.com"):
        raise SnapshotContractError("pre-signed resultLink must be an HTTPS AWS S3 URL")
    expires_raw = body.get("expires")
    if not expires_raw:
        raise SnapshotContractError("completed async response has no expires timestamp")
    expires_at = parse_utc(str(expires_raw))
    if expires_at <= (now or utc_now()).astimezone(timezone.utc):
        raise SnapshotContractError("pre-signed resultLink is already expired")
    metadata = parse_completed_headers(headers)
    if metadata["record_total"] > MAX_ASYNC_RECORDS:
        raise PartitionRequired(
            f"Record-Total={metadata['record_total']} exceeds the async ceiling; "
            "partition by a metadata-verified disjoint field before retrieval"
        )
    if metadata["record_limit"] > MAX_ASYNC_RECORDS:
        raise SnapshotContractError("provider Record-Limit exceeds documented async ceiling")
    return {
        "status": "complete",
        "request_id": request_id,
        "result_link": result_link,
        "expires_at": iso_utc(expires_at),
        **metadata,
    }


def poll_status(
    session: requests.Session,
    token: str,
    submission: Mapping[str, Any],
    poll_interval_seconds: int = MIN_POLL_INTERVAL_SECONDS,
    max_wait_seconds: int = 3600,
    sleep_fn: Callable[[float], None] = time.sleep,
    monotonic_fn: Callable[[], float] = time.monotonic,
    clock_fn: Callable[[], datetime] = utc_now,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if poll_interval_seconds < MIN_POLL_INTERVAL_SECONDS:
        raise ValueError("FINRA recommends polling async status no more than once per minute")
    started = monotonic_fn()
    auth_headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    while True:
        response = session.get(submission["status_url"], headers=auth_headers, timeout=60)
        try:
            body = response.json()
        except Exception as exc:
            raise SnapshotContractError("async status response is not JSON") from exc
        parsed = parse_status(
            response.status_code,
            body,
            response.headers,
            str(submission["request_id"]),
            now=clock_fn(),
        )
        if parsed["status"] == "complete":
            return parsed, {
                "status_checked_at_utc": iso_utc(clock_fn()),
                "status_http": response.status_code,
            }
        if monotonic_fn() - started + poll_interval_seconds > max_wait_seconds:
            raise TimeoutError("FINRA async request did not complete within max_wait_seconds")
        sleep_fn(poll_interval_seconds)


def parse_result_json(response: Any) -> tuple[list[dict[str, Any]], bytes]:
    response.raise_for_status()
    content_type = str(response.headers.get("Content-Type", "")).lower()
    raw = response.content
    if "json" not in content_type:
        raise SnapshotContractError(
            f"expected application/json result because request Accept is JSON; got {content_type!r}"
        )
    try:
        records = response.json()
    except Exception as exc:
        raise SnapshotContractError("async result file is not valid JSON") from exc
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        raise SnapshotContractError("async result must be a JSON array of row objects")
    return records, raw


def validate_records(
    records: list[dict[str, Any]],
    settlement_date: str,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    day = validate_settlement_date(settlement_date)
    total = int(metadata["record_total"])
    limit = int(metadata["record_limit"])
    offset = int(metadata["record_offset"])
    if offset != 0:
        raise SnapshotContractError("nonzero offset cannot prove a complete settlement snapshot")
    if total > limit:
        raise PartitionRequired(
            f"Record-Total={total} exceeds Record-Limit={limit}; snapshot is incomplete"
        )
    if total > MAX_ASYNC_RECORDS:
        raise PartitionRequired("snapshot exceeds the documented 100,000-row async ceiling")
    if len(records) != total:
        raise SnapshotContractError(
            f"downloaded row count {len(records)} does not reconcile to Record-Total {total}"
        )
    page_rows = metadata.get("total_records_on_page")
    if page_rows is not None and int(page_rows) != len(records):
        raise SnapshotContractError(
            f"Total-Records-On-Page {page_rows} does not reconcile to downloaded rows {len(records)}"
        )
    for index, row in enumerate(records):
        if str(row.get("settlementDate") or "") != day:
            raise SnapshotContractError(
                f"row {index} has settlementDate {row.get('settlementDate')!r}, expected {day}"
            )
        if not str(row.get("symbolCode") or "").strip():
            raise SnapshotContractError(f"row {index} has no symbolCode")
    return {
        "snapshot_complete": True,
        "row_count": len(records),
        "record_total": total,
        "zero_inference_allowed": False,
        "zero_inference_blocker": "effective-dated security identity and scope are separate gates",
    }


def retrieve_snapshot(
    settlement_date: str,
    output_dir: str | Path,
    token: str | None = None,
    session: requests.Session | None = None,
    poll_interval_seconds: int = MIN_POLL_INTERVAL_SECONDS,
    max_wait_seconds: int = 3600,
    sleep_fn: Callable[[float], None] = time.sleep,
    clock_fn: Callable[[], datetime] = utc_now,
) -> dict[str, Any]:
    token = token or os.getenv("FINRA_ACCESS_TOKEN")
    client_id = os.getenv("FINRA_CLIENT_ID")
    client_secret = os.getenv("FINRA_CLIENT_SECRET")
    if not token and not (client_id and client_secret):
        raise RuntimeError(
            "Provide FINRA_ACCESS_TOKEN or both FINRA_CLIENT_ID and FINRA_CLIENT_SECRET; no request was made"
        )
    day = validate_settlement_date(settlement_date)
    if poll_interval_seconds < MIN_POLL_INTERVAL_SECONDS:
        raise ValueError("FINRA recommends polling async status no more than once per minute")
    if max_wait_seconds <= 0:
        raise ValueError("max_wait_seconds must be positive")
    owned_session = session is None
    session = session or requests.Session()
    submitted_at = clock_fn()
    auth_mode = "provided_bearer_token"
    token_expires_in = None
    try:
        if not token:
            token, token_expires_in = obtain_access_token(session, client_id, client_secret)
            auth_mode = "oauth_client_credentials"
        auth_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response = session.post(
            DATASET_URL,
            headers=auth_headers,
            json=build_async_payload(day),
            timeout=60,
        )
        submission = parse_submission(response.status_code, response.headers)
        completed, status_audit = poll_status(
            session,
            token,
            submission,
            poll_interval_seconds=poll_interval_seconds,
            max_wait_seconds=max_wait_seconds,
            sleep_fn=sleep_fn,
            clock_fn=clock_fn,
        )
        # IMPORTANT: the pre-signed URL embeds authorization. Do not pass a
        # FINRA Authorization header on this GET (FINRA documents HTTP 400 otherwise).
        result_response = session.get(completed["result_link"], timeout=120)
        records, raw_bytes = parse_result_json(result_response)
        downloaded_at = clock_fn()
        if parse_utc(completed["expires_at"]) <= downloaded_at.astimezone(timezone.utc):
            raise SnapshotContractError("resultLink expired before download completed")
        reconciliation = validate_records(records, day, completed)
        output = Path(output_dir)
        output.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(output, 0o700)
        request_id = str(submission["request_id"])
        safe_id = "".join(ch for ch in request_id if ch.isalnum() or ch in "-_")
        raw_path = output / f"finra_consolidated_si_{day}_{safe_id}.json"
        manifest_path = output / f"finra_consolidated_si_{day}_{safe_id}.manifest.json"
        raw_path.write_bytes(raw_bytes)
        os.chmod(raw_path, 0o600)
        digest = hashlib.sha256(raw_bytes).hexdigest()
        manifest = {
            "source": "FINRA Query API otcMarket/consolidatedShortInterest",
            "auth_mode": auth_mode,
            "token_expires_in_seconds": token_expires_in,
            "settlement_date": day,
            "submitted_at_utc": iso_utc(submitted_at),
            "status_checked_at_utc": status_audit["status_checked_at_utc"],
            "downloaded_at_utc": iso_utc(downloaded_at),
            "request_id": request_id,
            "submission_tracking_id": submission.get("tracking_id"),
            "completion_tracking_id": completed.get("finra_tracking_id"),
            "result_expires_at_utc": completed["expires_at"],
            "record_total": completed["record_total"],
            "record_offset": completed["record_offset"],
            "record_limit": completed["record_limit"],
            "total_records_on_page": completed["total_records_on_page"],
            "record_max_limit": completed["record_max_limit"],
            "response_payload_max_size": completed["response_payload_max_size"],
            "row_count": len(records),
            "raw_sha256": digest,
            "raw_file": raw_path.name,
            "snapshot_complete": reconciliation["snapshot_complete"],
            "zero_inference_allowed": False,
            "zero_inference_blocker": reconciliation["zero_inference_blocker"],
            "signal_eligible": False,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        os.chmod(manifest_path, 0o600)
        return manifest
    finally:
        if owned_session:
            session.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--settlement-date", required=True, help="YYYY-MM-DD")
    parser.add_argument(
        "--output-dir",
        default=str(Path(tempfile.gettempdir()) / "finra_private_short_interest"),
        help="Private local output directory; do not upload raw files to public GitHub",
    )
    parser.add_argument("--poll-interval-seconds", type=int, default=60)
    parser.add_argument("--max-wait-seconds", type=int, default=3600)
    args = parser.parse_args()
    manifest = retrieve_snapshot(
        args.settlement_date,
        args.output_dir,
        poll_interval_seconds=args.poll_interval_seconds,
        max_wait_seconds=args.max_wait_seconds,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
