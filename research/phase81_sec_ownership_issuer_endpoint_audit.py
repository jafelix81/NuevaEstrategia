#!/usr/bin/env python3
"""Bounded audit of SEC EDGAR ownership-disposition issuer/reporter endpoints.

This is a transport and positive-control feasibility check only. It is not a
historical-coverage proof, a PIT-vintage proof, or an alpha test.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode

import requests

BASE = "https://www.sec.gov"
USER_AGENT = "NuevaEstrategia research contact jafelix81@gmail.com"

CONTROLS = [
    {"name": "Revance", "subject_cik": "0001479290", "filer_cik": "0000019617",
     "accession": "0000019617-25-000296", "form": "SC 13G/A", "filed": "2025-03-06"},
    {"name": "Osisko", "subject_cik": "0001431852", "filer_cik": "0002083861",
     "accession": "0001062993-25-015044", "form": "SC 13D", "filed": "2025-08-28"},
    {"name": "Fox", "subject_cik": "0001754301", "filer_cik": "0002080603",
     "accession": "0000950157-25-000788", "form": "SC 13D", "filed": "2025-09-12"},
    {"name": "Fox", "subject_cik": "0001754301", "filer_cik": "0002084288",
     "accession": "0000950170-25-114595", "form": "SC 13D", "filed": "2025-09-12"},
]


class FilingPageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts: list[str] = []
        self.hrefs: list[str] = []
        self.row_count = 0
        self.title_parts: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "tr":
            self.row_count += 1
        if tag.lower() == "a" and attrs.get("href"):
            self.hrefs.append(attrs["href"])
        if tag.lower() == "title":
            self.in_title = True

    def handle_data(self, data):
        if data.strip():
            self.text_parts.append(data.strip())
        if self.in_title:
            self.title_parts.append(data.strip())

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False


def normalize_cik(value: str) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(10) if digits else ""


def cik_url_value(value: str) -> str:
    normalized = normalize_cik(value)
    return str(int(normalized)) if normalized else ""


def normalize_accession(value: str) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) != 18:
        return ""
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"


def extract_accessions(*values: str) -> list[str]:
    found: set[str] = set()
    for value in values:
        text = str(value or "")
        for match in re.findall(r"(?<!\d)\d{10}-\d{2}-\d{6}(?!\d)", text):
            found.add(normalize_accession(match))
        for match in re.findall(r"(?<!\d)\d{18}(?!\d)", text):
            found.add(normalize_accession(match))
    return sorted(x for x in found if x)


def build_endpoint(kind: str, cik: str) -> str:
    if kind not in {"issuer", "reporter"}:
        raise ValueError(f"Unsupported endpoint kind: {kind}")
    action = "getissuer" if kind == "issuer" else "getowner"
    query = urlencode({"action": action, "CIK": cik_url_value(cik)})
    return f"{BASE}/cgi-bin/own-disp?{query}"


def build_query_plan(controls=CONTROLS):
    by_subject: dict[str, list[dict]] = {}
    by_filer: dict[str, list[dict]] = {}
    for control in controls:
        by_subject.setdefault(control["subject_cik"], []).append(control)
        by_filer.setdefault(control["filer_cik"], []).append(control)
    plan = []
    for cik, items in sorted(by_subject.items()):
        plan.append({
            "query_id": f"issuer_{cik}",
            "endpoint_kind": "issuer",
            "cik": normalize_cik(cik),
            "company_names": sorted({x["name"] for x in items}),
            "expected_accessions": sorted({normalize_accession(x["accession"]) for x in items}),
            "expected_forms": sorted({x["form"] for x in items}),
        })
    for cik, items in sorted(by_filer.items()):
        plan.append({
            "query_id": f"reporter_{cik}",
            "endpoint_kind": "reporter",
            "cik": normalize_cik(cik),
            "company_names": sorted({x["name"] for x in items}),
            "expected_accessions": sorted({normalize_accession(x["accession"]) for x in items}),
            "expected_forms": sorted({x["form"] for x in items}),
        })
    return plan


class SecClient:
    def __init__(self, sleep_seconds=0.8, timeout=45):
        self.sleep_seconds = sleep_seconds
        self.timeout = timeout
        self.last_request = 0.0
        self.request_count = 0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "text/html,application/xhtml+xml,application/json,*/*",
        })

    def get(self, url):
        delay = self.sleep_seconds - (time.monotonic() - self.last_request)
        if delay > 0:
            time.sleep(delay)
        self.last_request = time.monotonic()
        response = self.session.get(url, timeout=self.timeout)
        self.request_count += 1
        return response


def run_audit(outdir: Path, sleep_seconds=0.8):
    outdir.mkdir(parents=True, exist_ok=True)
    raw_dir = outdir / "raw"
    raw_dir.mkdir(exist_ok=True)
    client = SecClient(sleep_seconds=sleep_seconds)
    rows = []

    for query in build_query_plan():
        url = build_endpoint(query["endpoint_kind"], query["cik"])
        row = {
            "query_id": query["query_id"],
            "endpoint_kind": query["endpoint_kind"],
            "cik": query["cik"],
            "company_names": json.dumps(query["company_names"]),
            "expected_accessions": json.dumps(query["expected_accessions"]),
            "expected_count": len(query["expected_accessions"]),
            "url": url,
        }
        try:
            response = client.get(url)
            body = response.content
            html = body.decode("utf-8", errors="replace")
            parser = FilingPageParser()
            parser.feed(html)
            accessions = extract_accessions(html, " ".join(parser.hrefs))
            expected = set(query["expected_accessions"])
            found = sorted(expected & set(accessions))
            missing = sorted(expected - set(accessions))
            raw_name = f"{query['query_id']}.html"
            (raw_dir / raw_name).write_text(html, encoding="utf-8")
            row.update({
                "status_code": response.status_code,
                "final_url": response.url,
                "content_type": response.headers.get("Content-Type", ""),
                "content_length": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "title": " ".join(parser.title_parts),
                "table_row_count": parser.row_count,
                "unique_accession_count": len(accessions),
                "expected_found": json.dumps(found),
                "expected_found_count": len(found),
                "missing_expected": json.dumps(missing),
                "http_error": "" if response.ok else f"HTTP {response.status_code}",
                "body_excerpt": " ".join(parser.text_parts)[:1200],
                "raw_file": raw_name,
            })
        except Exception as exc:
            row.update({
                "status_code": 0,
                "content_length": 0,
                "sha256": "",
                "table_row_count": 0,
                "unique_accession_count": 0,
                "expected_found": "[]",
                "expected_found_count": 0,
                "missing_expected": json.dumps(query["expected_accessions"]),
                "http_error": repr(exc),
                "body_excerpt": "",
                "raw_file": "",
            })
        rows.append(row)

    issuer_rows = [r for r in rows if r["endpoint_kind"] == "issuer"]
    reporter_rows = [r for r in rows if r["endpoint_kind"] == "reporter"]
    expected_all = {normalize_accession(x["accession"]) for x in CONTROLS}
    issuer_found = {a for r in issuer_rows for a in json.loads(r["expected_found"])}
    reporter_found = {a for r in reporter_rows for a in json.loads(r["expected_found"])}
    all_http_ok = all(r["status_code"] == 200 and not r["http_error"] for r in rows)
    summary = {
        "phase": "81-sec-ownership-issuer-endpoint-audit",
        "query_count": len(rows),
        "request_count": client.request_count,
        "issuer_query_count": len(issuer_rows),
        "reporter_query_count": len(reporter_rows),
        "positive_control_count": len(expected_all),
        "issuer_controls_found": sorted(issuer_found),
        "issuer_controls_found_count": len(issuer_found),
        "reporter_controls_found": sorted(reporter_found),
        "reporter_controls_found_count": len(reporter_found),
        "all_http_200": all_http_ok,
        "all_issuer_controls_found": expected_all.issubset(issuer_found),
        "all_reporter_controls_found": expected_all.issubset(reporter_found),
        "decision": (
            "ISSUER_AND_REPORTER_ENDPOINTS_POSITIVE_CONTROLS_PASS"
            if all_http_ok and expected_all.issubset(issuer_found) and expected_all.issubset(reporter_found)
            else (
                "ISSUER_ENDPOINT_POSITIVE_CONTROLS_PASS"
                if all_http_ok and expected_all.issubset(issuer_found)
                else (
                    "REPORTER_ENDPOINT_ONLY"
                    if all_http_ok and expected_all.issubset(reporter_found)
                    else "ENDPOINT_POSITIVE_CONTROLS_FAIL_OR_PARTIAL"
                )
            )
        ),
        "limitations": [
            "Four known cross-filer accessions across three subject issuers are positive controls, not a recall/precision sample.",
            "Current endpoint behavior does not establish historical endpoint stability or PIT-vintage availability.",
            "A successful issuer lookup is not proof of complete 13D/13G coverage or historical F80 security identity.",
            "No broad universe crawl, forward returns, alpha tests, or production changes.",
        ],
    }
    write_csv(outdir / "endpoint_audit.csv", rows)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return summary


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path("phase81_sec_ownership_issuer_endpoint_audit"))
    parser.add_argument("--sleep-seconds", type=float, default=0.8)
    args = parser.parse_args()
    run_audit(args.outdir, args.sleep_seconds)


if __name__ == "__main__":
    main()
