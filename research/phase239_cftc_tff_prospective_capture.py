"""Prospective, append-only capture of CFTC Traders in Financial Futures (TFF).

This is a data-admission logger, not a signal or return backtest. Scheduled
pipeline receipt is a conservative known-by timestamp; it is not claimed to be
the CFTC's exact first-publication timestamp.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import urllib.request
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

INDEX_URL = "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
BASE_URL = "https://www.cftc.gov"
TFF_LINKS = {
    "futures_only": "FinFutWk.txt",
    "futures_options_combined": "FinComWk.txt",
}
EXPECTED_FIELDS = 87
CAPTURE_PROTOCOL_VERSION = 2
ET = ZoneInfo("America/New_York")


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.text_parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            attrs = dict(attrs)
            self.href = attrs.get("href")
            self.text_parts = []

    def handle_data(self, data):
        if self.href is not None:
            self.text_parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.href is not None:
            self.links.append((self.href, " ".join(self.text_parts).strip()))
            self.href = None
            self.text_parts = []


def parse_date(value: str) -> date:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unsupported CFTC date value: {value!r}")


def _integer(value: str, field: str, *, allow_suppressed: bool = False):
    value = value.strip()
    if allow_suppressed and value in {"", "."}:
        return None
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid numeric field {field}: {value!r}") from exc
    if number != number.to_integral_value():
        raise ValueError(f"non-integer count in {field}: {value!r}")
    return int(number)


def _decimal(value: str, field: str):
    value = value.strip()
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid numeric field {field}: {value!r}") from exc


def parse_tff_file(raw_bytes: bytes, expected_kind: str) -> dict:
    if expected_kind not in TFF_LINKS:
        raise ValueError(f"unsupported TFF stream: {expected_kind}")
    text = raw_bytes.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text, newline=""))
    rows = []
    report_dates = set()
    as_of_dates = set()
    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue
        if row[0].strip().lower() == "market_and_exchange_names":
            continue
        if len(row) != EXPECTED_FIELDS:
            raise ValueError(
                f"expected {EXPECTED_FIELDS} fields, got {len(row)}"
            )
        row = [cell.strip() for cell in row]
        as_of = parse_date(row[1])
        report_date = parse_date(row[2])
        if as_of != report_date:
            raise ValueError(
                f"as-of/report date mismatch: {as_of.isoformat()} != {report_date.isoformat()}"
            )
        report_dates.add(report_date)
        as_of_dates.add(as_of)
        if row[86] != ("FutOnly" if expected_kind == "futures_only" else "Combined"):
            raise ValueError(f"report-type mismatch for {expected_kind}: {row[86]!r}")

        open_interest = _integer(row[7], "Open_Interest_All")
        if open_interest is None or open_interest <= 0:
            raise ValueError("Open_Interest_All must be a positive integer")
        for index in range(8, 24):
            number = _integer(row[index], f"position_{index}")
            if number is None or number < 0:
                raise ValueError(f"position field {index} must be non-negative")
        for index in range(24, 41):
            _integer(row[index], f"change_{index}")
        for index in range(41, 58):
            number = _decimal(row[index], f"percent_{index}")
            if number < 0 or number > 100:
                raise ValueError(f"percentage field {index} outside [0,100]")
        trader_counts = [
            _integer(row[index], f"traders_{index}", allow_suppressed=True)
            for index in range(58, 73)
        ]
        for index in range(73, 81):
            number = _decimal(row[index], f"concentration_{index}")
            if number < 0 or number > 100:
                raise ValueError(f"concentration field {index} outside [0,100]")

        key = (row[3], row[4], row[6], row[85], row[86])
        rows.append({
            "key": key,
            "market_name": row[0],
            "trader_count_missing_cells": sum(x is None for x in trader_counts),
            "trader_count_zero_cells": sum(x == 0 for x in trader_counts),
        })

    if not rows:
        raise ValueError("CFTC TFF file contains no data rows")
    keys = [item["key"] for item in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate CFTC contract-market key")
    if len(report_dates) != 1 or len(as_of_dates) != 1:
        raise ValueError("CFTC TFF file contains mixed report/as-of dates")
    report_date = next(iter(report_dates))
    as_of_date = next(iter(as_of_dates))
    return {
        "stream": expected_kind,
        "report_date": report_date.isoformat(),
        "as_of_date": as_of_date.isoformat(),
        "row_count": len(rows),
        "unique_contract_market_count": len(keys),
        "trader_count_missing_cells": sum(x["trader_count_missing_cells"] for x in rows),
        "trader_count_zero_cells": sum(x["trader_count_zero_cells"] for x in rows),
        "equity_index_candidate_names": sorted({
            x["market_name"] for x in rows
            if "S&P 500" in x["market_name"].upper()
            or "NASDAQ-100" in x["market_name"].upper()
            or "NASDAQ 100" in x["market_name"].upper()
        }),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "raw_bytes": len(raw_bytes),
        "field_count": EXPECTED_FIELDS,
    }


def extract_tff_urls(index_html: str) -> dict:
    parser = LinkCollector()
    parser.feed(index_html)
    found = {}
    for href, _label in parser.links:
        absolute = urljoin(BASE_URL, href)
        parsed = urlparse(absolute)
        if parsed.scheme != "https" or parsed.hostname not in {"www.cftc.gov", "cftc.gov"}:
            continue
        basename = parsed.path.rsplit("/", 1)[-1]
        for stream, expected_name in TFF_LINKS.items():
            if basename.lower() == expected_name.lower():
                clean = parsed._replace(query="", fragment="").geturl()
                prior = found.get(stream)
                if prior is not None and prior != clean:
                    raise ValueError(f"multiple URLs found for {stream}")
                found[stream] = clean
    if set(found) != set(TFF_LINKS):
        missing = sorted(set(TFF_LINKS) - set(found))
        raise ValueError(f"missing current TFF links: {missing}")
    return found


def _iso_z(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("receipt timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _scheduled_after_release(event_name: str, receipt_time: datetime) -> bool:
    if receipt_time.tzinfo is None:
        raise ValueError("receipt timestamp must be timezone-aware")
    et = receipt_time.astimezone(ET)
    return event_name == "schedule" and et.weekday() < 5 and (et.hour, et.minute) >= (15, 30)


def _metadata_records(root: Path, stream: str) -> list[dict]:
    folder = root / "data" / "cftc_tff" / "metadata"
    if not folder.exists():
        return []
    records = []
    for path in sorted(folder.glob(f"{stream}__*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"malformed existing metadata: {path}") from exc
        if record.get("stream") == stream and record.get("capture_protocol_version") == CAPTURE_PROTOCOL_VERSION:
            records.append(record)
    return records


def _latest_scheduled(root: Path, stream: str) -> Optional[dict]:
    records = [
        x for x in _metadata_records(root, stream)
        if x.get("event_name") == "schedule"
        and x.get("state_usable_after_receipt") is True
    ]
    return max(records, key=lambda x: x.get("observed_at_utc", "")) if records else None


def _write_gzip_once(path: Path, raw_bytes: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(gzip.compress(raw_bytes, mtime=0))


def _write_json_once(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _classify(parsed: dict, raw_hash: str, prior: Optional[dict],
              event_name: str, receipt_time: datetime,
              previously_observed_report_date: bool = False) -> dict:
    scheduled = _scheduled_after_release(event_name, receipt_time)
    if not scheduled:
        return {
            "event_type": "MANUAL_OR_NONQUALIFYING_OBSERVATION",
            "state_usable_after_receipt": False,
            "event_signal_eligible": False,
            "pit_eligible_from_pipeline_receipt": False,
            "report_date_gap_days": None,
            "sequence_gap_detected": False,
        }
    if prior is None:
        return {
            "event_type": "INITIAL_BASELINE_STATE_ONLY",
            "state_usable_after_receipt": True,
            "event_signal_eligible": False,
            "pit_eligible_from_pipeline_receipt": False,
            "report_date_gap_days": None,
            "sequence_gap_detected": False,
        }
    current_date = date.fromisoformat(parsed["report_date"])
    prior_date = date.fromisoformat(prior["report_date"])
    if current_date < prior_date:
        return {
            "event_type": "LATE_OR_ROLLBACK_OBSERVATION_NON_PIT",
            "state_usable_after_receipt": False,
            "event_signal_eligible": False,
            "pit_eligible_from_pipeline_receipt": False,
            "report_date_gap_days": (current_date - prior_date).days,
            "sequence_gap_detected": False,
        }
    if current_date == prior_date and raw_hash == prior["raw_sha256"]:
        return {
            "event_type": "UNCHANGED",
            "state_usable_after_receipt": True,
            "event_signal_eligible": False,
            "pit_eligible_from_pipeline_receipt": False,
            "report_date_gap_days": 0,
            "sequence_gap_detected": False,
        }
    if current_date == prior_date:
        return {
            "event_type": "NEW_REVISION_FIRST_SCHEDULED_OBSERVATION",
            "state_usable_after_receipt": True,
            "event_signal_eligible": False,
            "pit_eligible_from_pipeline_receipt": False,
            "report_date_gap_days": 0,
            "sequence_gap_detected": False,
        }
    if previously_observed_report_date:
        gap = (current_date - prior_date).days
        return {
            "event_type": "PREVIOUSLY_OBSERVED_REPORT_DATE_STATE_ONLY",
            "state_usable_after_receipt": True,
            "event_signal_eligible": False,
            "pit_eligible_from_pipeline_receipt": False,
            "previously_observed_report_date": True,
            "report_date_gap_days": gap,
            "sequence_gap_detected": gap > 8,
        }
    if raw_hash == prior["raw_sha256"]:
        raise ValueError("report date advanced but raw hash is unchanged")
    gap = (current_date - prior_date).days
    return {
        "event_type": "NEW_REPORT_FIRST_SCHEDULED_OBSERVATION",
        "state_usable_after_receipt": True,
        "event_signal_eligible": True,
        "pit_eligible_from_pipeline_receipt": True,
        "report_date_gap_days": gap,
        "sequence_gap_detected": gap > 8,
    }


def _capture_one(*, root: Path, stream: str, url: str, raw_bytes: bytes,
                 headers: dict, index_sha256: str, receipt_time: datetime,
                 event_name: str, env: dict) -> dict:
    parsed = parse_tff_file(raw_bytes, stream)
    raw_hash = parsed["raw_sha256"]
    prior = _latest_scheduled(root, stream)
    previously_observed_report_date = any(
        item.get("report_date") == parsed["report_date"]
        for item in _metadata_records(root, stream)
    )
    classification = _classify(
        parsed, raw_hash, prior, event_name, receipt_time,
        previously_observed_report_date=previously_observed_report_date,
    )
    if classification["event_type"] == "UNCHANGED":
        return {
            "status": "UNCHANGED",
            **parsed,
            "event_type": "UNCHANGED",
            "new_snapshot": False,
            "pit_eligible_from_pipeline_receipt": False,
        }

    stamp = receipt_time.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_path = Path("data") / "cftc_tff" / "raw" / stream / f'{parsed["report_date"]}__{raw_hash[:16]}.txt.gz'
    meta_path = Path("data") / "cftc_tff" / "metadata" / f'{stream}__{parsed["report_date"]}__{raw_hash[:16]}__{event_name}__{stamp}.json'
    _write_gzip_once(root / raw_path, raw_bytes)
    et = receipt_time.astimezone(ET)
    metadata = {
        "source": "CFTC Traders in Financial Futures",
        "capture_protocol_version": CAPTURE_PROTOCOL_VERSION,
        **parsed,
        "report_url": url,
        "index_url": INDEX_URL,
        "index_html_sha256": index_sha256,
        "observed_at_utc": _iso_z(receipt_time),
        "observed_at_et": et.isoformat(),
        "event_name": event_name,
        "historical_first_publication_time_verified": False,
        "first_observed_by_pipeline_utc": _iso_z(receipt_time),
        "http_date_header_recorded_not_used_as_availability": headers.get("Date"),
        "workflow_run_id": env.get("GITHUB_RUN_ID"),
        "workflow_run_attempt": env.get("GITHUB_RUN_ATTEMPT"),
        "workflow_sha": env.get("GITHUB_SHA"),
        "raw_snapshot_path": raw_path.as_posix(),
        "raw_compression": "gzip; decompression reproduces exact response bytes",
        **classification,
        "earliest_decision_session_policy": "first regular XNYS session strictly after observed_at_utc",
        "earliest_execution_policy": "close of that next XNYS session under the existing EOD discipline",
    }
    _write_json_once(root / meta_path, metadata)
    return {
        "status": classification["event_type"],
        **parsed,
        "new_snapshot": True,
        "metadata_path": meta_path.as_posix(),
        "raw_snapshot_path": raw_path.as_posix(),
        "event_type": classification["event_type"],
        "pit_eligible_from_pipeline_receipt": classification["pit_eligible_from_pipeline_receipt"],
        "state_usable_after_receipt": classification["state_usable_after_receipt"],
        "report_date_gap_days": classification["report_date_gap_days"],
        "sequence_gap_detected": classification["sequence_gap_detected"],
    }


def capture_current_reports(*, root: Path, event_name: str,
                            now: Optional[datetime] = None, fetcher=None,
                            env: Optional[dict] = None) -> dict:
    env = env or os.environ
    if fetcher is None:
        def fetcher(url):
            request = urllib.request.Request(
                url, headers={"User-Agent": "NuevaEstrategia-CFTC-TFF-research/1.0"}
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read(), dict(response.headers.items())

    index_bytes, _index_headers = fetcher(INDEX_URL)
    index_sha = hashlib.sha256(index_bytes).hexdigest()
    urls = extract_tff_urls(index_bytes.decode("utf-8-sig", errors="replace"))
    stamp_time = now or datetime.now(timezone.utc)
    index_path = Path("data") / "cftc_tff" / "index_snapshots" / f"{index_sha[:16]}.html.gz"
    index_meta_path = Path("data") / "cftc_tff" / "index_snapshots" / f"{index_sha[:16]}.json"
    _write_gzip_once(root / index_path, index_bytes)
    _write_json_once(root / index_meta_path, {
        "source": INDEX_URL,
        "capture_protocol_version": CAPTURE_PROTOCOL_VERSION,
        "observed_at_utc": _iso_z(stamp_time),
        "index_html_sha256": index_sha,
        "raw_snapshot_path": index_path.as_posix(),
        "raw_compression": "gzip; decompression reproduces exact response bytes",
        "event_name": event_name,
        "workflow_run_id": env.get("GITHUB_RUN_ID"),
        "workflow_run_attempt": env.get("GITHUB_RUN_ATTEMPT"),
        "workflow_sha": env.get("GITHUB_SHA"),
    })

    captures = []
    for stream, url in sorted(urls.items()):
        raw_bytes, headers = fetcher(url)
        receipt_time = now or datetime.now(timezone.utc)
        captures.append(_capture_one(
            root=root, stream=stream, url=url, raw_bytes=raw_bytes,
            headers=headers, index_sha256=index_sha, receipt_time=receipt_time,
            event_name=event_name, env=env,
        ))
    return {
        "phase": 239,
        "source": "CFTC Traders in Financial Futures",
        "capture_protocol_version": CAPTURE_PROTOCOL_VERSION,
        "index_html_sha256": index_sha,
        "observed_at_utc": _iso_z(stamp_time),
        "event_name": event_name,
        "stream_count": len(captures),
        "new_snapshot_count": sum(x.get("new_snapshot", False) for x in captures),
        "pit_event_count": sum(x.get("pit_eligible_from_pipeline_receipt", False) for x in captures),
        "captures": captures,
        "historical_pit_admission": False,
        "alpha_admission": False,
    }


def main() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="phase239_output/capture_attempt.json")
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", "manual"))
    args = parser.parse_args()
    result = capture_current_reports(
        root=Path(args.root), event_name=args.event_name
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
