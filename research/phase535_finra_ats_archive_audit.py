#!/usr/bin/env python3
"""Phase 535: safe feasibility audit of FINRA's public ATS historical download index.

The audit never accepts FINRA terms, posts a certification form, logs in, or
stores raw ATS files. It performs GET-only checks and stores metadata only.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import re
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests

INDEX_URL = "https://ats.finra.org/TradingDetailFileArchive/TradingDetailFilesDownloadGrid"
UNIVERSE_SOURCE = Path("Nueva_Estrategia_Fase11_Real1000_LTM_v4.py")
OUT = Path("phase535_output")
MAX_SAMPLE_REPORTS = 6
MAX_SAMPLE_BYTES = 25 * 1024 * 1024
REQUIRED_COLUMNS = {
    "Report_Type", "Symbol", "Issue_Description", "ATS_Description",
    "ATS_MPID", "Shares", "Shares_Last_Updated", "Trades", "Trades_Last_Updated",
}


class GridParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        tag = tag.lower()
        if tag == "table" and self.table is None:
            self.table = {"id": attrs.get("id", ""), "rows": []}
        elif self.table is not None and tag == "tr":
            self.row = []
        elif self.table is not None and self.row is not None and tag in {"td", "th"}:
            self.cell = {"text": "", "links": []}
        elif self.cell is not None and tag == "a":
            self.cell["links"].append({
                "href": attrs.get("href", ""),
                "onclick": attrs.get("onclick", ""),
                "title": attrs.get("title", ""),
            })

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"] += data

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"td", "th"} and self.cell is not None:
            self.cell["text"] = " ".join(self.cell["text"].split())
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.table["rows"].append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None
            self.row = None
            self.cell = None


def load_f80_universe() -> set[str]:
    tree = ast.parse(UNIVERSE_SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DEFAULT_UNIVERSE":
                    values = {str(x).strip().upper() for x in ast.literal_eval(node.value)}
                    if len(values) != 335:
                        raise RuntimeError(f"Expected 335 legacy F80 names, got {len(values)}")
                    return values
    raise RuntimeError("DEFAULT_UNIVERSE not found")


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    value = str(value).strip()
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y", "%d-%B-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def has_certification_gate(html: str) -> bool:
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).lower()
    markers = (
        "user certification",
        "i agree",
        "i disagree",
        "you must agree to the terms",
        "solely for your personal",
        "terms of use",
    )
    return any(marker in text for marker in markers)


def extract_direct_url(link: dict) -> str | None:
    href = (link.get("href") or "").strip()
    if href and not href.lower().startswith(("javascript:", "#", "mailto:")):
        return href
    onclick = link.get("onclick") or ""
    match = re.search(r"""(?:window\.open|location(?:\.href)?)\s*\(?\s*['"]([^'"]+)['"]""", onclick, re.I)
    if match:
        return match.group(1)
    return None


def parse_grid(html: str, base_url: str = INDEX_URL) -> dict:
    parser = GridParser()
    parser.feed(html)
    chosen = None
    for table in parser.tables:
        if table["id"].lower() == "tbltrading":
            chosen = table
            break
    if chosen is None:
        for table in parser.tables:
            header_text = " ".join(cell["text"].lower() for cell in (table["rows"][0] if table["rows"] else []))
            if "week" in header_text and "report" in header_text and "last updated" in header_text:
                chosen = table
                break
    if chosen is None or not chosen["rows"]:
        return {"table_found": False, "reports": [], "table_id": None}

    header = [normalize_header(cell["text"]) for cell in chosen["rows"][0]]
    indices = {}
    for name in ("week", "report_type", "last_updated", "year", "download"):
        if name in header:
            indices[name] = header.index(name)

    reports = []
    for row in chosen["rows"][1:]:
        texts = [cell["text"] for cell in row]
        if len(texts) < 3:
            continue
        def get(name):
            idx = indices.get(name)
            return texts[idx] if idx is not None and idx < len(texts) else ""
        week_raw = get("week")
        week_date = parse_date(week_raw)
        report_type = get("report_type").strip()
        if not report_type and not week_raw:
            continue
        links = [link for cell in row for link in cell.get("links", [])]
        direct = next((extract_direct_url(link) for link in links if extract_direct_url(link)), None)
        onclicks = [link.get("onclick", "") for link in links if link.get("onclick")]
        reports.append({
            "week_raw": week_raw,
            "week_date": week_date.isoformat() if week_date else None,
            "report_type": report_type,
            "last_updated_raw": get("last_updated"),
            "last_updated": parse_date(get("last_updated")).isoformat() if parse_date(get("last_updated")) else None,
            "download_url": urljoin(base_url, direct) if direct else None,
            "download_path": urlsplit(urljoin(base_url, direct)).path if direct else None,
            "has_onclick": bool(onclicks),
        })
    return {"table_found": True, "table_id": chosen["id"], "header": header, "reports": reports}


def select_samples(reports: list[dict], max_samples: int = MAX_SAMPLE_REPORTS) -> list[dict]:
    by_type = {}
    for report in reports:
        if report.get("week_date"):
            by_type.setdefault(report.get("report_type") or "UNKNOWN", []).append(report)
    candidates = []
    for report_type, items in sorted(by_type.items()):
        ordered = sorted(items, key=lambda x: x["week_date"])
        candidates.append(ordered[0])
        if len(ordered) > 1:
            candidates.append(ordered[-1])
    unique = {}
    for item in candidates:
        key = (item.get("report_type"), item.get("week_date"), item.get("download_path"))
        unique[key] = item
    return sorted(unique.values(), key=lambda x: (x.get("week_date") or "", x.get("report_type") or ""))[:max_samples]


def parse_report_text(text: str, f80_universe: set[str], report_type: str, week_date: str) -> dict:
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")), delimiter="|")
    fields = set(reader.fieldnames or [])
    if not REQUIRED_COLUMNS.issubset(fields):
        return {
            "status": "SCHEMA_MISMATCH",
            "columns": sorted(fields),
            "missing_columns": sorted(REQUIRED_COLUMNS - fields),
        }
    row_count = 0
    symbols = set()
    mpids = set()
    missing_symbols = 0
    invalid_quantities = 0
    invalid_update_dates = 0
    duplicate_keys = set()
    seen_keys = set()
    f80_symbols = set()
    max_row_update = None
    for row in reader:
        if not row or not any((value or "").strip() for value in row.values()):
            continue
        row_count += 1
        symbol = (row.get("Symbol") or "").strip().upper()
        mpid = (row.get("ATS_MPID") or "").strip().upper()
        if not symbol:
            missing_symbols += 1
        else:
            symbols.add(symbol)
            if symbol in f80_universe:
                f80_symbols.add(symbol)
        if mpid:
            mpids.add(mpid)
        key = ((row.get("Report_Type") or report_type).strip(), symbol, mpid)
        if key in seen_keys:
            duplicate_keys.add(key)
        seen_keys.add(key)
        for field in ("Shares", "Trades"):
            raw = (row.get(field) or "").replace(",", "").strip()
            try:
                if raw and float(raw) < 0:
                    invalid_quantities += 1
            except ValueError:
                invalid_quantities += 1
        for field in ("Shares_Last_Updated", "Trades_Last_Updated"):
            raw = row.get(field)
            parsed = parse_date(raw)
            if raw and not parsed:
                invalid_update_dates += 1
            if parsed and (max_row_update is None or parsed > max_row_update):
                max_row_update = parsed
    return {
        "status": "PARSED",
        "report_type": report_type,
        "report_week": week_date,
        "rows": row_count,
        "unique_symbols": len(symbols),
        "unique_ats_mpids": len(mpids),
        "missing_symbol_rows": missing_symbols,
        "negative_or_invalid_quantity_fields": invalid_quantities,
        "invalid_update_date_fields": invalid_update_dates,
        "duplicate_report_symbol_mpid_keys": len(duplicate_keys),
        "max_row_update_date": max_row_update.isoformat() if max_row_update else None,
        "f80_335_overlap_count_diagnostic_only": len(f80_symbols),
        "f80_335_overlap_pct_diagnostic_only": round(100 * len(f80_symbols) / len(f80_universe), 2) if f80_universe else None,
        "raw_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "phase": 535,
        "source": "FINRA ATS Transparency historical download archive",
        "audit_started_utc": datetime.now(timezone.utc).isoformat(),
        "index_url": INDEX_URL,
        "method": "GET only; no login, no form submission, no cookie-based certification, no terms acceptance",
        "f80_universe_size": None,
        "f80_overlap_role": "diagnostic_only; F80 is manually selected and not a representative broad-market universe",
        "status": "NOT_RUN",
        "index": {},
        "report_type_summary": [],
        "sample_downloads": [],
        "pit_assessment": {
            "official_delay_rule": "NMS Tier 1: two-week delay; other NMS/OTC: four-week delay",
            "archive_row_fields": ["Shares_Last_Updated", "Trades_Last_Updated"],
            "initial_publication_timestamp_in_download_file": False,
            "pit_status": "NOT_ESTABLISHED",
            "rule": "Do not backdate a final revised snapshot to report week. Use exact first publication/vintage data where available; otherwise keep this source signal-ineligible until publication/update timestamps are validated against the API and first-seen captures."
        },
        "limitations": [
            "FINRA ATS reports are self-reported ATS volume and trade counts, not aggressor direction, beneficial owner, or proof of informed trading.",
            "ATS activity is not all off-exchange activity; non-ATS OTC/TRF activity is a separate category.",
            "The 335-name F80 list is diagnostic only and is not a representative market universe."
        ],
    }
    f80 = load_f80_universe()
    result["f80_universe_size"] = len(f80)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; ResearchFeasibilityAudit/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    try:
        response = session.get(INDEX_URL, timeout=(20, 60), allow_redirects=True)
        result["index"] = {
            "http_status": response.status_code,
            "content_type": response.headers.get("Content-Type"),
            "bytes": len(response.content),
            "final_path": urlsplit(response.url).path,
            "sha256": hashlib.sha256(response.content).hexdigest(),
        }
        if response.status_code != 200:
            result["status"] = "HTTP_BLOCKED_OR_UNAVAILABLE"
        elif "text/html" not in (response.headers.get("Content-Type") or "").lower():
            result["status"] = "UNEXPECTED_CONTENT_TYPE"
        elif has_certification_gate(response.text):
            result["status"] = "CERTIFICATION_GATE_PRESENT"
            result["index"]["certification_gate_detected"] = True
            # Do not click/submit the certification control or attempt downloads.
        else:
            grid = parse_grid(response.text, response.url)
            result["index"]["table_found"] = grid["table_found"]
            result["index"]["table_id"] = grid.get("table_id")
            result["index"]["header"] = grid.get("header", [])
            reports = grid["reports"]
            result["index"]["report_rows"] = len(reports)
            dated = [r for r in reports if r.get("week_date")]
            result["index"]["first_report_week"] = min((r["week_date"] for r in dated), default=None)
            result["index"]["last_report_week"] = max((r["week_date"] for r in dated), default=None)
            by_type = {}
            for report in dated:
                by_type.setdefault(report.get("report_type") or "UNKNOWN", []).append(report)
            for report_type, items in sorted(by_type.items()):
                result["report_type_summary"].append({
                    "report_type": report_type,
                    "report_count": len(items),
                    "first_week": min(x["week_date"] for x in items),
                    "last_week": max(x["week_date"] for x in items),
                    "direct_download_links": sum(bool(x.get("download_url")) for x in items),
                    "rows_with_postback_only": sum(bool(x.get("has_onclick")) and not x.get("download_url") for x in items),
                })
            if not grid["table_found"]:
                result["status"] = "TABLE_NOT_FOUND"
            elif not dated:
                result["status"] = "TABLE_FOUND_NO_DATED_REPORTS"
            else:
                samples = select_samples(reports)
                for item in samples:
                    sample = {
                        "report_type": item.get("report_type"),
                        "report_week": item.get("week_date"),
                        "last_updated": item.get("last_updated"),
                        "download_path": item.get("download_path"),
                        "status": "NO_DIRECT_DOWNLOAD_URL",
                    }
                    if item.get("download_url"):
                        try:
                            download = session.get(item["download_url"], timeout=(20, 120), stream=True)
                            sample["http_status"] = download.status_code
                            sample["content_type"] = download.headers.get("Content-Type")
                            if download.status_code == 200:
                                chunks = bytearray()
                                too_large = False
                                for chunk in download.iter_content(chunk_size=1024 * 1024):
                                    if not chunk:
                                        continue
                                    chunks.extend(chunk)
                                    if len(chunks) > MAX_SAMPLE_BYTES:
                                        too_large = True
                                        break
                                if too_large:
                                    sample["status"] = "SAMPLE_EXCEEDS_SIZE_CAP"
                                    sample["bytes_observed_at_cap"] = len(chunks)
                                elif "text/html" in (sample["content_type"] or "").lower():
                                    sample["status"] = "HTML_RESPONSE_NOT_DATA"
                                else:
                                    text = bytes(chunks).decode("utf-8-sig", errors="replace")
                                    sample.update(parse_report_text(text, f80, item.get("report_type") or "", item.get("week_date") or ""))
                                    sample["bytes"] = len(chunks)
                            else:
                                sample["status"] = "DOWNLOAD_HTTP_ERROR"
                            download.close()
                        except Exception as exc:
                            sample["status"] = "DOWNLOAD_ERROR"
                            sample["error"] = repr(exc)[:500]
                    result["sample_downloads"].append(sample)
                direct_count = sum(bool(x.get("download_url")) for x in dated)
                parsed_count = sum(x.get("status") == "PARSED" for x in result["sample_downloads"])
                if parsed_count and parsed_count == len(result["sample_downloads"]):
                    result["status"] = "SAMPLED_DOWNLOADS_PARSED"
                elif direct_count == 0:
                    result["status"] = "ARCHIVE_INDEX_FOUND_BUT_DOWNLOADS_REQUIRE_POSTBACK"
                elif parsed_count:
                    result["status"] = "SAMPLED_DOWNLOADS_PARTIAL"
                else:
                    result["status"] = "ARCHIVE_INDEX_FOUND_DOWNLOAD_SCHEMA_UNRESOLVED"
    except Exception as exc:
        result["status"] = "REQUEST_OR_PARSE_ERROR"
        result["error"] = repr(exc)[:1000]

    result["audit_completed_utc"] = datetime.now(timezone.utc).isoformat()
    (OUT / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
