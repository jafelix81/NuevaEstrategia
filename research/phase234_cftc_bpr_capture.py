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
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

INDEX_URL = "https://www.cftc.gov/MarketReports/BankParticipationReports/index.htm"
BASE_URL = "https://www.cftc.gov"
BPR_FUTURES_PATH = re.compile(r"/MarketReports/BankParticipation/dea([a-z]{3})(\d{2})f$", re.I)
CAPTURE_PROTOCOL_VERSION = 3
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

def report_month_from_url(url: str) -> tuple[int, int]:
    parsed = urlparse(url)
    match = BPR_FUTURES_PATH.search(parsed.path)
    if not match:
        raise ValueError(f"not a CFTC BPR futures URL: {url!r}")
    month_abbr, yy = match.groups()
    try:
        month = datetime.strptime(month_abbr.title(), "%b").month
    except ValueError as exc:
        raise ValueError(f"invalid month in CFTC BPR URL: {url!r}") from exc
    return 2000 + int(yy), month


def list_futures_links(index_html: str) -> list[str]:
    """Return all distinct Futures URLs sorted by report month."""
    parser = LinkCollector()
    parser.feed(index_html)
    by_month = {}
    for href, label in parser.links:
        if label.strip().lower() != "futures":
            continue
        absolute = urljoin(BASE_URL, href)
        parsed = urlparse(absolute)
        if parsed.scheme != "https" or parsed.hostname not in {"www.cftc.gov", "cftc.gov"}:
            continue
        clean = parsed._replace(query="", fragment="").geturl()
        try:
            month_key = report_month_from_url(clean)
        except ValueError:
            continue
        prior = by_month.get(month_key)
        if prior is not None and prior != clean:
            raise ValueError(f"multiple CFTC BPR futures links for {month_key}: {prior}, {clean}")
        by_month[month_key] = clean
    if not by_month:
        raise ValueError("CFTC BPR futures links not found")
    return [by_month[key] for key in sorted(by_month)]


def select_latest_futures_url(index_html: str) -> str:
    """Select by encoded report month, never by HTML row order."""
    return list_futures_links(index_html)[-1]


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
    initial_baseline: bool = False,
    revision: bool = False,
    previously_observed: bool = False,
) -> dict:
    receipt_et = receipt_time.astimezone(ET)
    scheduled_after_release = (
        event_name == "schedule"
        and receipt_et.weekday() < 5
        and (receipt_et.hour, receipt_et.minute) >= (15, 30)
    )
    state_usable = scheduled_after_release
    revision_state_only = scheduled_after_release and revision and not initial_baseline
    previously_observed_state_only = (
        scheduled_after_release and previously_observed
        and not initial_baseline and not revision
    )
    event_signal_eligible = (
        scheduled_after_release and not initial_baseline
        and not revision and not previously_observed
    )
    if initial_baseline and state_usable:
        pit_rule = (
            "Initial report is a pre-existing baseline state, not a new release event. "
            "It may be used only as a state snapshot after this pipeline receipt; do "
            "not backdate to the report date or count it as an event signal."
        )
        event_type = "INITIAL_BASELINE_STATE_ONLY"
    elif revision_state_only:
        pit_rule = (
            "A changed hash for an already-seen report date is a correction/revision. "
            "Preserve this version as a state update from this pipeline receipt, but "
            "do not treat it as a new report event or directional signal."
        )
        event_type = "NEW_REVISION_STATE_ONLY"
    elif previously_observed_state_only:
        pit_rule = (
            "This exact report date was already observed in an earlier non-PIT or "
            "prior-protocol capture. The scheduled receipt may establish a usable "
            "current state, but must not promote it into a new release event."
        )
        event_type = "PREVIOUSLY_OBSERVED_VERSION_STATE_ONLY"
    elif event_signal_eligible:
        pit_rule = (
            "A newly indexed report date is usable only after this pipeline's recorded "
            "report-page receipt; earliest modeled trade is the next regular XNYS "
            "session after receipt."
        )
        event_type = "NEW_REPORT_FIRST_SCHEDULED_OBSERVATION"
    else:
        pit_rule = "Not PIT-admitted; manual or outside scheduled weekday release window."
        event_type = "MANUAL_OR_NONQUALIFYING_OBSERVATION"
    return {
        "source": "CFTC Bank Participation Report — Futures IN CONTRACT",
        "capture_protocol_version": CAPTURE_PROTOCOL_VERSION,
        "report_date": report_date,
        "report_url": report_url,
        "report_sha256": report_sha256,
        "observed_at_utc": _iso_z(receipt_time),
        "observed_at_et": receipt_et.isoformat(),
        "event_name": event_name,
        "initial_baseline": bool(initial_baseline),
        "previously_observed": bool(previously_observed),
        "historical_publication_time_verified": False,
        "prospective_state_usable_after_receipt": bool(state_usable),
        "event_signal_eligible": bool(event_signal_eligible),
        "pit_eligible_from_pipeline_receipt": bool(event_signal_eligible),
        "event_type": event_type,
        "pit_rule": pit_rule,
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

def _latest_scheduled_index_snapshot(root: Path) -> Optional[dict]:
    folder = root / "data" / "cftc_bpr" / "index_snapshots"
    if not folder.exists():
        return None
    records = []
    for path in sorted(folder.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"malformed CFTC index snapshot: {path}") from exc
        if (record.get("event_name") == "schedule"
                and record.get("capture_protocol_version") == CAPTURE_PROTOCOL_VERSION):
            records.append(record)
    return max(records, key=lambda x: x.get("observed_at_utc", "")) if records else None


def _write_scheduled_index_snapshot(*, root: Path, index_bytes: bytes,
                                    futures_urls: list[str], receipt_time: datetime,
                                    env: dict) -> bool:
    canonical = json.dumps(sorted(futures_urls), separators=(",", ":")).encode("utf-8")
    links_hash = hashlib.sha256(canonical).hexdigest()
    previous = _latest_scheduled_index_snapshot(root)
    if previous and previous.get("futures_links_sha256") == links_hash:
        return False
    folder = root / "data" / "cftc_bpr" / "index_snapshots"
    raw_folder = folder / "raw"
    raw_folder.mkdir(parents=True, exist_ok=True)
    stamp = receipt_time.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    index_digest = hashlib.sha256(index_bytes).hexdigest()
    raw_path = raw_folder / f"{stamp}__{index_digest[:12]}.html"
    if not raw_path.exists():
        raw_path.write_bytes(index_bytes)
    record = {
        "source": INDEX_URL,
        "capture_protocol_version": CAPTURE_PROTOCOL_VERSION,
        "event_name": "schedule",
        "observed_at_utc": _iso_z(receipt_time),
        "index_html_sha256": index_digest,
        "raw_index_snapshot_path": str(raw_path.relative_to(root)),
        "futures_links_sha256": links_hash,
        "futures_urls": sorted(futures_urls),
        "workflow_run_id": env.get("GITHUB_RUN_ID"),
        "workflow_run_attempt": env.get("GITHUB_RUN_ATTEMPT"),
        "workflow_sha": env.get("GITHUB_SHA"),
    }
    path = folder / f"{stamp}__{links_hash[:12]}.json"
    if not path.exists():
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


def _capture_one(*, root: Path, report_url: str, report_bytes: bytes,
                 report_headers: dict, receipt_time: datetime, event_name: str,
                 index_sha256: str, env: dict, initial_baseline: bool) -> dict:
    report_html = report_bytes.decode("utf-8", errors="replace")
    report_date = extract_report_date(report_html)
    report_year_month = tuple(int(x) for x in report_date[:7].split("-"))
    if report_month_from_url(report_url) != report_year_month:
        raise ValueError(
            f"CFTC link month {report_month_from_url(report_url)} does not match report date {report_date}"
        )
    digest = hashlib.sha256(report_bytes).hexdigest()
    existing = _existing_metadata(root, report_date)
    same_hash = [x for x in existing if x.get("report_sha256") == digest]
    scheduled_current_protocol_same_hash = [
        x for x in same_hash
        if x.get("event_name") == "schedule"
        and x.get("capture_protocol_version") == CAPTURE_PROTOCOL_VERSION
    ]
    if event_name == "schedule" and scheduled_current_protocol_same_hash:
        return {
            "status": "UNCHANGED_ALREADY_CAPTURED",
            "report_date": report_date,
            "report_sha256": digest,
            "new_snapshot": False,
            "pit_eligible_from_pipeline_receipt": any(
                x.get("pit_eligible_from_pipeline_receipt") is True for x in scheduled_current_protocol_same_hash
            ),
            "prospective_state_usable_after_receipt": any(
                x.get("prospective_state_usable_after_receipt") is True for x in scheduled_current_protocol_same_hash
            ),
        }
    if event_name != "schedule" and same_hash:
        return {
            "status": "UNCHANGED_NON_PIT_VERSION",
            "report_date": report_date,
            "report_sha256": digest,
            "new_snapshot": False,
            "pit_eligible_from_pipeline_receipt": False,
            "prospective_state_usable_after_receipt": False,
        }

    revision = bool(existing and not same_hash)
    previously_observed = bool(existing)
    raw_dir = root / "data" / "cftc_bpr" / "raw"
    meta_dir = root / "data" / "cftc_bpr" / "metadata"
    raw_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{report_date}__{digest[:12]}.html"
    if not raw_path.exists():
        raw_path.write_bytes(report_bytes)

    metadata = build_capture_metadata(
        report_date=report_date, report_url=report_url, report_sha256=digest,
        receipt_time=receipt_time, event_name=event_name,
        http_date_header=report_headers.get("Date"), index_sha256=index_sha256,
        workflow_run_id=env.get("GITHUB_RUN_ID"),
        workflow_run_attempt=env.get("GITHUB_RUN_ATTEMPT"),
        workflow_sha=env.get("GITHUB_SHA"), initial_baseline=initial_baseline,
        revision=revision, previously_observed=previously_observed,
    )
    if initial_baseline:
        metadata["receipt_kind"] = "INITIAL_BASELINE_STATE_ONLY"
    elif revision:
        metadata["receipt_kind"] = (
            "NEW_REVISION_STATE_ONLY" if event_name == "schedule"
            else "MANUAL_REVISION_NON_PIT"
        )
    elif previously_observed:
        metadata["receipt_kind"] = "PREVIOUSLY_OBSERVED_VERSION_FIRST_SCHEDULED_RECEIPT_STATE_ONLY"
    elif event_name == "schedule":
        metadata["receipt_kind"] = "NEW_REPORT_FIRST_SCHEDULED_OBSERVATION"
    else:
        metadata["receipt_kind"] = "MANUAL_NON_PIT"
    metadata["raw_snapshot_path"] = str(raw_path.relative_to(root))
    stamp = receipt_time.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    meta_path = meta_dir / f"{report_date}__{digest[:12]}__{event_name}__{stamp}.json"
    if not meta_path.exists():
        meta_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "status": metadata["receipt_kind"],
        "report_date": report_date,
        "report_sha256": digest,
        "new_snapshot": True,
        "pit_eligible_from_pipeline_receipt": metadata["pit_eligible_from_pipeline_receipt"],
        "prospective_state_usable_after_receipt": metadata["prospective_state_usable_after_receipt"],
        "raw_snapshot_path": str(raw_path.relative_to(root)),
        "metadata_path": str(meta_path.relative_to(root)),
    }


def capture_latest(*, root: Path, event_name: str, now: Optional[datetime] = None,
                   fetcher=None, env: Optional[dict] = None) -> dict:
    """Capture the full retained BPR archive and preserve every observed vintage.

    The first scheduled run bootstraps every currently retained report as
    state-only. Later scheduled runs poll every retained report page so a
    correction to an older, non-latest report is not silently missed. New URLs
    are event candidates only when they have never been observed before.
    Manual runs capture only the latest page and never advance the schedule baseline.
    """
    env = env or os.environ
    if fetcher is None:
        def fetcher(url):
            request = urllib.request.Request(
                url, headers={"User-Agent": "NuevaEstrategia-CFTC-BPR-research/2.0"}
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read(), dict(response.headers.items())

    index_bytes, _ = fetcher(INDEX_URL)
    index_html = index_bytes.decode("utf-8", errors="replace")
    futures_urls = list_futures_links(index_html)
    latest_url = futures_urls[-1]
    index_digest = hashlib.sha256(index_bytes).hexdigest()
    initial_baseline = False
    if event_name == "schedule":
        previous = _latest_scheduled_index_snapshot(root)
        initial_baseline = previous is None
        # Poll every retained URL on every scheduled run. The archive is small
        # (about 25 monthly reports); this detects revisions to non-latest pages.
        candidate_urls = list(futures_urls)
    else:
        candidate_urls = [latest_url]

    captures = []
    for report_url in candidate_urls:
        report_bytes, report_headers = fetcher(report_url)
        receipt_time = now or datetime.now(timezone.utc)
        captures.append(_capture_one(
            root=root, report_url=report_url, report_bytes=report_bytes,
            report_headers=report_headers, receipt_time=receipt_time,
            event_name=event_name, index_sha256=index_digest, env=env,
            initial_baseline=initial_baseline,
        ))

    index_snapshot_written = False
    if event_name == "schedule":
        index_receipt = now or datetime.now(timezone.utc)
        index_snapshot_written = _write_scheduled_index_snapshot(
            root=root, index_bytes=index_bytes, futures_urls=futures_urls,
            receipt_time=index_receipt, env=env,
        )
    new_captures = [x for x in captures if x.get("new_snapshot")]
    pit_any = any(x.get("pit_eligible_from_pipeline_receipt") for x in new_captures)
    state_any = any(x.get("prospective_state_usable_after_receipt") for x in captures)
    if not new_captures:
        status = "UNCHANGED_ALREADY_CAPTURED" if event_name == "schedule" else "UNCHANGED_NON_PIT_VERSION"
    elif initial_baseline:
        status = "INITIAL_BASELINE_CAPTURED_STATE_ONLY"
    elif len(new_captures) == 1:
        status = new_captures[0]["status"]
    else:
        status = "MULTIPLE_NEW_REPORT_VERSIONS_CAPTURED"
    result = {
        "status": status,
        "capture_protocol_version": CAPTURE_PROTOCOL_VERSION,
        "initial_baseline": initial_baseline,
        "latest_report_url": latest_url,
        "latest_report_date": next((x.get("report_date") for x in reversed(captures)
                                    if x.get("report_date")), None),
        "new_snapshot": bool(new_captures),
        "pit_eligible_from_pipeline_receipt": pit_any,
        "prospective_state_usable_after_receipt": state_any,
        "index_snapshot_written": index_snapshot_written,
        "captures": captures,
    }
    if len(new_captures) == 1:
        result.update({k: v for k, v in new_captures[0].items()
                       if k in {"report_date", "report_sha256", "raw_snapshot_path", "metadata_path"}})
    return result


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
