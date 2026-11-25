#!/usr/bin/env python3
"""Phase 611 — stratified SEC 13F acceptance-timestamp coverage audit.

Uses the two already-audited public SEC quarterly datasets (2018 Q1 and
2026 Jun-Aug), selects a deterministic filing-date/form/report-type sample,
and checks each EDGAR filing-detail page for accession, filer CIK, form,
filing date, period and exact Accepted time. No signal or return calculation.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
import io
from collections import Counter, defaultdict
from datetime import date, datetime, time as dt_time, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.sec_user_agent import resolve_sec_user_agent
from research.phase606_sec_13f_manager_table_live_audit import (
    DATASETS, download, find_member, read_table, build_filer_context,
)

ALLOWED_FORMS = {"13F-HR", "13F-HR/A", "13F-NT", "13F-NT/A"}
PER_STRATUM = 4
MAX_SAMPLE_PER_DATASET = 32
ET = ZoneInfo("America/New_York")


class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = re.sub(r"\s+", " ", data or "").strip()
        if value:
            self.parts.append(value)


def extract_labeled_value(parts: list[str], label: str, pattern: str) -> str | None:
    compiled = re.compile(pattern)
    for i, part in enumerate(parts):
        if part.strip().lower().rstrip(":") == label.lower():
            for candidate in parts[i + 1:i + 5]:
                match = compiled.search(candidate)
                if match:
                    return match.group(1)
    joined = " ".join(parts)
    match = re.search(rf"{re.escape(label)}\s*:?\s*{pattern}", joined, re.IGNORECASE)
    return match.group(1) if match else None


def observed_federal_holiday(day: date) -> date:
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        first_next = date(year + 1, 1, 1)
    else:
        first_next = date(year, month + 1, 1)
    last = first_next - timedelta(days=1)
    return last - timedelta(days=(last.weekday() - weekday) % 7)


def federal_holidays(year: int) -> set[date]:
    fixed = [
        date(year, 1, 1),
        date(year, 7, 4),
        date(year, 11, 11),
        date(year, 12, 25),
    ]
    if year >= 2021:
        fixed.append(date(year, 6, 19))
    observed = {observed_federal_holiday(day) for day in fixed}
    variable = {
        nth_weekday(year, 1, 0, 3),   # Birthday of Martin Luther King, Jr.
        nth_weekday(year, 2, 0, 3),   # Washington's Birthday
        last_weekday(year, 5, 0),     # Memorial Day
        nth_weekday(year, 9, 0, 1),   # Labor Day
        nth_weekday(year, 10, 0, 2),  # Columbus Day
        nth_weekday(year, 11, 3, 4),  # Thanksgiving Day
    }
    return observed | variable


def is_federal_holiday(day: date) -> bool:
    return any(day in federal_holidays(year) for year in (day.year - 1, day.year, day.year + 1))


def next_sec_business_day(day: date) -> date:
    candidate = day + timedelta(days=1)
    for _ in range(15):
        if candidate.weekday() < 5 and not is_federal_holiday(candidate):
            return candidate
        candidate += timedelta(days=1)
    raise RuntimeError("unable_to_resolve_next_sec_business_day")


def reconcile_filing_date(accepted_at_et: str | None, filing_date: str | None) -> str | None:
    if not accepted_at_et or not filing_date:
        return None
    try:
        accepted = datetime.strptime(accepted_at_et, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ET)
        filed = date.fromisoformat(filing_date)
    except ValueError:
        return "INVALID_DATE"
    accepted_day = accepted.date()
    if accepted_day.weekday() >= 5 or is_federal_holiday(accepted_day):
        return "INVALID_NON_BUSINESS_DAY_ACCEPTANCE"
    if accepted.time() > dt_time(17, 30):
        return (
            "AFTER_1730_NEXT_SEC_BUSINESS_DAY"
            if next_sec_business_day(accepted_day) == filed
            else "MISMATCH"
        )
    return "SAME_DAY" if accepted_day == filed else "MISMATCH"


def parse_filing_detail_html(payload: bytes) -> dict:
    parser = TextCollector()
    parser.feed(payload.decode("utf-8", errors="replace"))
    joined = " ".join(parser.parts)
    accepted = extract_labeled_value(
        parser.parts, "Accepted", r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})"
    )
    filing_date = extract_labeled_value(parser.parts, "Filing Date", r"(\d{4}-\d{2}-\d{2})")
    period = extract_labeled_value(parser.parts, "Period of Report", r"(\d{4}-\d{2}-\d{2})")
    accession_match = re.search(r"SEC Accession No\.\s*(\d{10}-\d{2}-\d{6})", joined, re.IGNORECASE)
    filer_match = re.search(r"\(?Filer\)?\s*CIK:\s*0*(\d{1,10})", joined, re.IGNORECASE)
    filer_cik_value = filer_match.group(1) if filer_match else None
    if not filer_cik_value:
        cik_candidates = re.findall(r"\bCIK:\s*0*(\d{1,10})", joined, re.IGNORECASE)
        if len(cik_candidates) == 1:
            filer_cik_value = cik_candidates[0]
    form_match = re.search(r"Form\s+(13F-HR/A|13F-HR|13F-NT/A|13F-NT)\b", joined, re.IGNORECASE)

    accepted_utc = None
    clock_bucket = None
    weekend = None
    accepted_after_1730 = None
    if accepted:
        try:
            accepted_dt = datetime.strptime(accepted, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ET)
            accepted_utc = accepted_dt.astimezone(timezone.utc).isoformat()
            weekend = accepted_dt.weekday() >= 5
            accepted_after_1730 = accepted_dt.time() > dt_time(17, 30)
            if weekend:
                clock_bucket = "WEEKEND"
            elif accepted_dt.time() < dt_time(9, 30):
                clock_bucket = "PRE_MARKET_WEEKDAY"
            elif accepted_dt.time() >= dt_time(16, 0):
                clock_bucket = "AFTER_CLOSE_WEEKDAY"
            else:
                clock_bucket = "REGULAR_SESSION_CLOCK_WEEKDAY"
        except ValueError:
            accepted_utc = None

    return {
        "accession_from_page": accession_match.group(1) if accession_match else None,
        "filer_cik_from_page": filer_cik_value.zfill(10) if filer_cik_value else None,
        "form_type": form_match.group(1).upper() if form_match else None,
        "accepted_at_et": accepted,
        "accepted_at_utc": accepted_utc,
        "filing_date": filing_date,
        "period_of_report": period,
        "accepted_date_matches_filing_date": (
            accepted[:10] == filing_date if accepted and filing_date else None
        ),
        "filing_date_clock_reconciliation": reconcile_filing_date(accepted, filing_date),
        "accepted_after_1730_et": accepted_after_1730,
        "accepted_clock_bucket": clock_bucket,
        "accepted_on_weekend": weekend,
    }


def normalize_dataset_date(value: object) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y"):
        try:
            return datetime.strptime(raw.upper(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def select_stratified_samples(dataset: str, filers: dict, per_stratum: int = PER_STRATUM) -> list[dict]:
    strata: dict[tuple[str, str], list[tuple[str, dict]]] = defaultdict(list)
    for accession, filer in filers.items():
        form = str(filer.get("submission_type") or "").upper()
        report_type = str(filer.get("report_type") or "").upper()
        if form in ALLOWED_FORMS and filer.get("cik") and filer.get("filing_date"):
            strata[(form, report_type)].append((accession, filer))

    selected: list[dict] = []
    for (form, report_type), rows in sorted(strata.items()):
        rows.sort(key=lambda item: (item[1].get("filing_date") or "", item[0]))
        bins = min(per_stratum, len(rows))
        used_ciks: set[str] = set()
        for bin_ix in range(bins):
            start_ix = bin_ix * len(rows) // bins
            end_ix = (bin_ix + 1) * len(rows) // bins
            candidates = rows[start_ix:end_ix]
            candidates = sorted(
                candidates,
                key=lambda item: hashlib.sha256(
                    f"{dataset}|{form}|{report_type}|{bin_ix}|{item[0]}".encode()
                ).hexdigest(),
            )
            chosen = next(
                (item for item in candidates if item[1].get("cik") not in used_ciks),
                candidates[0],
            )
            accession, filer = chosen
            cik = str(filer["cik"]).zfill(10)
            used_ciks.add(cik)
            selected.append({
                "dataset": dataset,
                "accession": accession,
                "filer_cik_from_dataset": cik,
                "submission_type": form,
                "report_type": report_type,
                "filing_date_raw_from_dataset": filer.get("filing_date"),
                "filing_date_from_dataset": normalize_dataset_date(filer.get("filing_date")),
                "period_of_report_raw_from_dataset": filer.get("report_period"),
                "period_of_report_from_dataset": normalize_dataset_date(filer.get("report_period")),
                "stratum": f"{form}|{report_type or 'UNKNOWN'}",
                "date_bin": f"{bin_ix + 1}/{bins}",
            })
    return selected[:MAX_SAMPLE_PER_DATASET]


def build_index_url(sample: dict) -> str:
    accession = sample["accession"]
    compact = accession.replace("-", "")
    # The archive path uses the filing CIK from SUBMISSION, not the first
    # ten digits of accession; filing agents can make those differ.
    filer_cik_path = str(int(sample["filer_cik_from_dataset"]))
    return (
        f"https://www.sec.gov/Archives/edgar/data/{filer_cik_path}/"
        f"{compact}/{accession}-index.htm"
    )


def fetch_page(url: str, user_agent: str) -> tuple[bytes, str, int]:
    request = urllib.request.Request(url, headers={
        "User-Agent": user_agent,
        "Accept-Encoding": "identity",
        "Accept": "text/html,application/xhtml+xml,*/*",
    })
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = response.read()
                return payload, response.geturl(), int(response.status)
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {403, 408, 429, 500, 502, 503, 504} or attempt == 2:
                raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == 2:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError(f"SEC page fetch failed: {last_error}")


def audit_sample(sample: dict, user_agent: str) -> dict:
    url = build_index_url(sample)
    try:
        payload, final_url, http_status = fetch_page(url, user_agent)
        parsed = parse_filing_detail_html(payload)
        checks = {
            "accession_matches": parsed.get("accession_from_page") == sample["accession"],
            # The SEC 13F SUBMISSION table supplies the filer CIK. The detail
            # page does not expose a consistently parseable CIK label across
            # older EDGAR layouts, so verify the canonical archive path used.
            "filer_cik_path_matches": f"/data/{int(sample['filer_cik_from_dataset'])}/" in final_url,
            "form_matches": parsed.get("form_type") == sample["submission_type"],
            "filing_date_matches": parsed.get("filing_date") == sample["filing_date_from_dataset"],
            "period_of_report_matches": parsed.get("period_of_report") == sample["period_of_report_from_dataset"],
            "accepted_timestamp_present": bool(parsed.get("accepted_at_et")),
            "filing_date_clock_reconciles": parsed.get("filing_date_clock_reconciliation") in {
                "SAME_DAY", "AFTER_1730_NEXT_SEC_BUSINESS_DAY"
            },
        }
        mismatch = any(value is False for key, value in checks.items() if key != "accepted_timestamp_present")
        missing = any(value is None or value is False for value in checks.values())
        status = "PASS" if not missing else ("REVIEW_MISMATCH" if mismatch else "REVIEW_MISSING_FIELD")
        return {
            **sample,
            "status": status,
            "source_url": url,
            "final_url": final_url,
            "http_status": http_status,
            "html_bytes": len(payload),
            "html_sha256": hashlib.sha256(payload).hexdigest(),
            "checks": checks,
            **parsed,
        }
    except Exception as exc:
        return {
            **sample,
            "status": "FETCH_ERROR",
            "source_url": url,
            "error_type": type(exc).__name__,
            "error": str(exc)[:300],
        }


def audit_dataset(label: str, url: str, user_agent: str) -> dict:
    payload = download(url, user_agent)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = archive.namelist()
        submission_member = find_member(names, "SUBMISSION")
        cover_member = find_member(names, "COVERPAGE")
        submission_header, submission_rows = read_table(archive, submission_member)
        cover_header, cover_rows = read_table(archive, cover_member)
    context = build_filer_context(
        submission_header, submission_rows, cover_header, cover_rows
    )
    if not context.get("schema_ok"):
        return {
            "status": "BLOCKED_FILER_SCHEMA",
            "zip_bytes": len(payload),
            "zip_sha256": hashlib.sha256(payload).hexdigest(),
            "filer_context": context,
        }

    filers = context["filers"]
    selected = select_stratified_samples(label, filers)
    population_strata = Counter(
        f"{f.get('submission_type','')}|{f.get('report_type') or 'UNKNOWN'}"
        for f in filers.values()
        if f.get("submission_type") in ALLOWED_FORMS
    )
    results = []
    for sample in selected:
        # The exact collector's first-seen timestamp is not available historically.
        results.append(audit_sample(sample, user_agent))
        time.sleep(0.15)  # stay comfortably below SEC's published request-rate ceiling

    counts = Counter(x["status"] for x in results)
    clocks = Counter(
        x.get("accepted_clock_bucket") or "MISSING"
        for x in results
        if x.get("accepted_at_et")
    )
    weekend_count = sum(x.get("accepted_on_weekend") is True for x in results)
    filing_clock_reconciliation_counts = Counter(
        x.get("filing_date_clock_reconciliation") or "MISSING"
        for x in results
    )
    return {
        "status": "PASS_STRATIFIED_TIMESTAMP_SAMPLE" if results and counts["PASS"] == len(results) else "REVIEW_STRATIFIED_TIMESTAMP_SAMPLE",
        "source_url": url,
        "zip_bytes": len(payload),
        "zip_sha256": hashlib.sha256(payload).hexdigest(),
        "population_accessions_with_coverpage": len(filers),
        "population_submission_type_counts": context.get("submission_type_counts"),
        "population_report_type_counts": context.get("report_type_counts"),
        "population_strata_counts": dict(sorted(population_strata.items())),
        "sample_size": len(results),
        "sample_status_counts": dict(sorted(counts.items())),
        "accepted_clock_bucket_counts": dict(sorted(clocks.items())),
        "weekend_acceptances": weekend_count,
        "filing_date_clock_reconciliation_counts": dict(sorted(filing_clock_reconciliation_counts.items())),
        "sample": results,
        "calendar_limit": "Weekend classification only. No XNYS holiday/session claim is made in this phase.",
        "availability_limit": "Historical EDGAR Accepted time is not historical collector first-seen time. Use max(accepted_at, collector_first_seen) when available; until then, do not backdate to period_of_report.",
        "signal_eligible": False,
    }


def main() -> None:
    user_agent, source = resolve_sec_user_agent()
    out = {
        "phase": 611,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "user_agent_source": source,
        "status": "UNKNOWN",
        "datasets": {},
    }
    for label, url in DATASETS.items():
        try:
            out["datasets"][label] = audit_dataset(label, url, user_agent)
        except Exception as exc:
            out["datasets"][label] = {
                "status": "DOWNLOAD_OR_PARSE_ERROR",
                "error_type": type(exc).__name__,
                "error": str(exc)[:400],
                "source_url": url,
            }
    statuses = [x.get("status") for x in out["datasets"].values()]
    out["status"] = (
        "PASS_BOTH_STRATIFIED_SAMPLES"
        if len(statuses) == len(DATASETS) and all(x == "PASS_STRATIFIED_TIMESTAMP_SAMPLE" for x in statuses)
        else "REVIEW_OR_BLOCKED"
    )
    out["interpretation"] = (
        "Timestamp coverage feasibility only. Stratified sample spans filing type, report type and filing-date bins. "
        "No complete-population coverage, collector first-seen history, XNYS session mapping, alpha, OOS or production eligibility."
    )
    out["next_gate"] = (
        "If the stratified sample passes, expand only strata with missing/mismatched metadata; then validate XNYS sessions "
        "and prospective collector first-seen timestamps before constructing point-in-time 13F features."
    )
    Path("phase611_sec_13f_acceptance_timestamp_stratified_audit.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
