"""Prospective, append-only CFTC BPR futures page capture.

This workflow records when this repository's capture pipeline first observes a
new report version. It does not claim to know the CFTC's exact first-publication
second. Manual dispatches are always marked non-PIT.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

INDEX_URL = "https://www.cftc.gov/MarketReports/BankParticipationReports/index.htm"
BASE_URL = "https://www.cftc.gov"
BPR_FUTURES_PATH = re.compile(r"/MarketReports/BankParticipation/dea[a-z]{3}\d{2}f$", re.I)
ET = ZoneInfo("America/New_York")

class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current_href = None
        self.current_text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            attrs = dict(attrs)
            self.current_href = attrs.get("href")
            self.current_text = []

    def handle_data(self, data):
        if self.current_href is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.current_href is not None:
            self.links.append((self.current_href, " ".join(self.current_text).strip()))
            self.current_href = None
            self.current_text = []

class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

    def text(self):
        return " ".join(self.parts)

def select_latest_futures_url(index_html: str) -> str:
    parser = LinkCollector()
    parser.feed(index_html)
    for href, label in parser.links:
        absolute = urljoin(BASE_URL, href)
        path = absolute.split("?", 1)[0]
        if BPR_FUTURES_PATH.search(path) and label.strip().lower() == "futures":
            return absolute
    raise ValueError("latest CFTC BPR futures link not found")

def extract_report_date(report_html: str) -> str:
    parser = TextCollector()
    parser.feed(report_html)
    text = parser.text()
    match = re.search(r"REPORT\s+DATE\s*:\s*(\d{1,2}/\d{1,2}/\d{4})", text, re.I)
    if not match:
        raise ValueError("CFTC BPR REPORT DATE not found")
    parsed = datetime.strptime(match.group(1), "%m/%d/%Y").date()
    return parsed.isoformat()

def _iso_z(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("receipt timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def build_capture_metadata(
    *,
    report_date: str,
    report_url: str,
    report_sha256: str,
    receipt_time: datetime,
    event_name: str,
    http_date_header: Optional[str] = None,
    index_sha256: Optional[str] = None,
    workflow_run_id: Optional[str] = None,
    workflow_run_attempt: Optional[str] = None,
    workflow_sha: Optional[str] = None,
) -> dict:
    receipt_et = receipt_time.astimezone(ET)
    scheduled_window = (
        event_name == "schedule"
        and receipt_et.weekday() == 4
        and (receipt_et.hour, receipt_et.minute) >= (15, 30)
    )
    return {
        "source": "CFTC Bank Participation Report — Futures IN CONTRACT",
        "report_date": report_date,
        "report_url": report_url,
        "report_sha256": report_sha256,
        "first_observed_by_capture_pipeline_utc": _iso_z(receipt_time),
        "first_observed_by_capture_pipeline_et": receipt_et.isoformat(),
        "event_name": event_name,
        "pit_eligible_from_pipeline_receipt": bool(scheduled_window),
        "pit_rule": (
            "Use only after this pipeline's recorded receipt; earliest modeled "
            "trade is the next regular XNYS session after receipt."
            if scheduled_window else
            "Not PIT-admitted; manual or outside scheduled Friday release window."
        ),
        "http_date_header_recorded_not_used_as_availability": http_date_header,
        "index_sha256": index_sha256,
        "workflow_run_id": workflow_run_id,
        "workflow_run_attempt": workflow_run_attempt,
        "workflow_sha": workflow_sha,
    }

def _existing_metadata(root: Path, report_date: str) -> list[dict]:
    folder = root / "data" / "cftc_bpr" / "metadata"
    if not folder.exists():
        return []
    records = []
    for path in sorted(folder.glob(f"{report_date}__*.json")):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            raise ValueError(f"malformed existing metadata: {path}")
    return records

def capture_latest(
    *,
    root: Path,
    event_name: str,
    now: Optional[datetime] = None,
    fetcher=None,
    env: Optional[dict] = None,
) -> dict:
    """Fetch latest BPR futures page and append a raw/version receipt."""
    env = env or os.environ
    if fetcher is None:
        def fetcher(url):
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "NuevaEstrategia-CFTC-BPR-research/1.0"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read(), dict(response.headers.items())

    index_bytes, _ = fetcher(INDEX_URL)
    index_html = index_bytes.decode("utf-8", errors="replace")
    report_url = select_latest_futures_url(index_html)
    report_bytes, report_headers = fetcher(report_url)
    receipt_time = now or datetime.now(timezone.utc)
    report_html = report_bytes.decode("utf-8", errors="replace")
    report_date = extract_report_date(report_html)
    digest = hashlib.sha256(report_bytes).hexdigest()
    existing = _existing_metadata(root, report_date)

    same_hash = [x for x in existing if x.get("report_sha256") == digest]
    scheduled_same_hash = [
        x for x in same_hash if x.get("pit_eligible_from_pipeline_receipt") is True
    ]
    if scheduled_same_hash:
        return {
            "status": "UNCHANGED_ALREADY_CAPTURED",
            "report_date": report_date,
            "report_sha256": digest,
            "new_snapshot": False,
            "pit_eligible_from_pipeline_receipt": False,
        }

    revision = bool(existing and not same_hash)
    raw_dir = root / "data" / "cftc_bpr" / "raw"
    meta_dir = root / "data" / "cftc_bpr" / "metadata"
    raw_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / f"{report_date}__{digest[:12]}.html"
    if not raw_path.exists():
        raw_path.write_bytes(report_bytes)

    metadata = build_capture_metadata(
        report_date=report_date,
        report_url=report_url,
        report_sha256=digest,
        receipt_time=receipt_time,
        event_name=event_name,
        http_date_header=report_headers.get("Date"),
        index_sha256=hashlib.sha256(index_bytes).hexdigest(),
        workflow_run_id=env.get("GITHUB_RUN_ID"),
        workflow_run_attempt=env.get("GITHUB_RUN_ATTEMPT"),
        workflow_sha=env.get("GITHUB_SHA"),
    )
    metadata["receipt_kind"] = "NEW_REVISION" if revision else "FIRST_PIPELINE_OBSERVATION"
    metadata["raw_snapshot_path"] = str(raw_path.relative_to(root))
    stamp = receipt_time.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    meta_path = meta_dir / f"{report_date}__{digest[:12]}__{event_name}__{stamp}.json"
    meta_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "status": "NEW_REVISION_CAPTURED" if revision else "NEW_REPORT_VERSION_CAPTURED",
        "report_date": report_date,
        "report_sha256": digest,
        "new_snapshot": True,
        "pit_eligible_from_pipeline_receipt": metadata["pit_eligible_from_pipeline_receipt"],
        "raw_snapshot_path": str(raw_path.relative_to(root)),
        "metadata_path": str(meta_path.relative_to(root)),
    }

def main() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="phase234_output/capture_attempt.json")
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", "manual"))
    args = parser.parse_args()
    result = capture_latest(root=Path(args.root), event_name=args.event_name)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result

if __name__ == "__main__":
    main()
