#!/usr/bin/env python3
"""Bounded SEC EDGAR Entity Landing Page discovery/transport audit."""
from __future__ import annotations
import argparse, csv, hashlib, json, re, time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests

BASE = "https://www.sec.gov"
USER_AGENT = "NuevaEstrategia research contact jafelix81@gmail.com"
PAGES = [
    {"id": "revance_default", "cik": "0001479290", "owner": "",
     "expected": ["0000019617-25-000296"], "name": "Revance Therapeutics"},
    {"id": "revance_owner_exclude", "cik": "0001479290", "owner": "exclude",
     "expected": ["0000019617-25-000296"], "name": "Revance Therapeutics"},
    {"id": "revance_owner_include", "cik": "0001479290", "owner": "include",
     "expected": ["0000019617-25-000296"], "name": "Revance Therapeutics"},
    {"id": "osisko_default", "cik": "0001431852", "owner": "",
     "expected": ["0001062993-25-015044"], "name": "Osisko Development"},
    {"id": "fox_default", "cik": "0001754301", "owner": "",
     "expected": ["0000950157-25-000788", "0000950170-25-114595"], "name": "Fox Corporation"},
]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts, self.links, self.inline_scripts = [], [], []
        self.title_parts, self.text_parts = [], []
        self._in_title, self._in_script = False, False
        self._script_src, self._script_data = "", []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
        if tag == "script":
            self._in_script = True
            self._script_src = attrs.get("src", "")
            self._script_data = []
            if self._script_src:
                self.scripts.append(self._script_src)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
        if self._in_script:
            self._script_data.append(data)
        else:
            if data.strip():
                self.text_parts.append(data.strip())

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "script":
            if self._script_data and not self._script_src:
                self.inline_scripts.append("".join(self._script_data))
            self._in_script = False
            self._script_src, self._script_data = "", []


def normalize_accession(value):
    digits = re.sub(r"\D", "", str(value or ""))
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}" if len(digits) >= 18 else ""


def accession_present(html, accession):
    dashed = normalize_accession(accession)
    return bool(dashed and (dashed in html or dashed.replace("-", "") in html))


def build_page_url(page):
    url = f"{BASE}/edgar/browse/?CIK={int(page['cik'])}"
    if page.get("owner"):
        url += f"&owner={page['owner']}"
    return url


def extract_candidate_endpoints(text):
    patterns = [
        r"https?://[^\\s\\\"'<>]+",
        r"/(?:api|edgar|browse|submissions|filings|ownership)[^\\s\\\"'<>]*",
    ]
    values = []
    for pattern in patterns:
        values.extend(re.findall(pattern, text, flags=re.I))
    keywords = ("api", "browse", "filing", "ownership", "submission", "search", "data.sec.gov")
    return sorted({v.rstrip(");,") for v in values if any(k in v.lower() for k in keywords)})


class SecClient:
    def __init__(self, sleep_seconds=0.6, timeout=60):
        self.sleep_seconds, self.timeout = sleep_seconds, timeout
        self.last_request, self.request_count = 0.0, 0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate",
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


def run_audit(outdir: Path, sleep_seconds=0.6, max_js=8):
    outdir.mkdir(parents=True, exist_ok=True)
    html_dir, js_dir = outdir / "html", outdir / "js"
    html_dir.mkdir(exist_ok=True); js_dir.mkdir(exist_ok=True)
    client, page_rows, script_urls, endpoint_rows = SecClient(sleep_seconds), [], set(), []
    for page in PAGES:
        url = build_page_url(page)
        row = {"page_id": page["id"], "cik": page["cik"], "owner": page["owner"],
               "company": page["name"], "url": url, "expected_accessions": json.dumps(page["expected"])}
        try:
            response = client.get(url)
            body = response.content
            text = body.decode("utf-8", errors="replace")
            parser = PageParser(); parser.feed(text)
            (html_dir / f"{page['id']}.html").write_text(text, encoding="utf-8")
            row.update({
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "content_length": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "title": " ".join(parser.title_parts),
                "subject_cik_present": page["cik"] in text,
                "company_name_present": page["name"].lower() in text.lower(),
                "expected_accessions_present": json.dumps([a for a in page["expected"] if accession_present(text, a)]),
                "expected_accession_count_present": sum(accession_present(text, a) for a in page["expected"]),
                "script_count": len(parser.scripts),
                "inline_script_count": len(parser.inline_scripts),
                "script_sources": json.dumps(parser.scripts),
                "candidate_endpoints_inline": json.dumps(extract_candidate_endpoints("\\n".join(parser.inline_scripts))),
                "http_error": "" if response.ok else f"HTTP {response.status_code}",
            })
            for src in parser.scripts:
                absolute = urljoin(url, src)
                if urlparse(absolute).netloc.endswith("sec.gov") and absolute.lower().endswith(".js"):
                    script_urls.add(absolute)
        except Exception as exc:
            row.update({"status_code": 0, "content_length": 0, "sha256": "",
                        "expected_accessions_present": "[]", "expected_accession_count_present": 0,
                        "script_count": 0, "inline_script_count": 0, "http_error": repr(exc)})
        page_rows.append(row)

    js_rows = []
    for index, url in enumerate(sorted(script_urls)[:max_js], 1):
        row = {"script_id": f"js{index:02d}", "url": url}
        try:
            response = client.get(url)
            body = response.content
            text = body.decode("utf-8", errors="replace")
            (js_dir / f"js{index:02d}.js").write_text(text, encoding="utf-8")
            endpoints = extract_candidate_endpoints(text)
            row.update({
                "status_code": response.status_code, "content_length": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "candidate_endpoint_count": len(endpoints),
                "candidate_endpoints": json.dumps(endpoints, ensure_ascii=False),
                "contains_ownership": "ownership" in text.lower(),
                "contains_beneficial": "beneficial" in text.lower(),
                "contains_submissions": "submissions" in text.lower(),
                "http_error": "" if response.ok else f"HTTP {response.status_code}",
            })
            for endpoint in endpoints:
                endpoint_rows.append({"script_id": row["script_id"], "source_url": url, "candidate_endpoint": endpoint})
        except Exception as exc:
            row.update({"status_code": 0, "content_length": 0, "sha256": "",
                        "candidate_endpoint_count": 0, "candidate_endpoints": "[]", "http_error": repr(exc)})
        js_rows.append(row)

    successful_pages = [r for r in page_rows if r.get("status_code") == 200]
    expected_total = sum(len(p["expected"]) for p in PAGES)
    expected_found = sum(int(r.get("expected_accession_count_present", 0)) for r in page_rows)
    summary = {
        "phase": "80-sec-entity-landing-page-pit-audit",
        "page_count": len(page_rows),
        "page_200_count": len(successful_pages),
        "expected_accessions_total": expected_total,
        "expected_accessions_found_in_raw_html": expected_found,
        "script_assets_discovered": len(script_urls),
        "script_assets_fetched": len(js_rows),
        "request_count": client.request_count,
        "raw_html_contains_positive_controls": expected_found > 0,
        "decision": (
            "SERVER_RENDERED_SUBJECT_INDEX_CANDIDATE" if expected_found > 0
            else ("CLIENT_SIDE_DATA_ENDPOINT_IDENTIFICATION_REQUIRED" if successful_pages
                  else "ENTITY_LANDING_PAGE_ACCESS_FAILED")
        ),
        "limitations": [
            "Only three subject issuers and four known accessions were probed.",
            "Raw HTML may not contain client-rendered filing rows; a linked JSON endpoint may be required.",
            "This is a current page transport/schema audit, not a historical coverage or PIT-vintage proof.",
            "No forward returns, alpha tests or production changes.",
        ],
    }
    write_csv(outdir / "page_audit.csv", page_rows)
    write_csv(outdir / "script_audit.csv", js_rows)
    write_csv(outdir / "candidate_endpoints.csv", endpoint_rows)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return summary


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8"); return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path("phase80_sec_entity_landing_page_audit"))
    parser.add_argument("--sleep-seconds", type=float, default=0.6)
    parser.add_argument("--max-js", type=int, default=8)
    args = parser.parse_args()
    run_audit(args.outdir, args.sleep_seconds, args.max_js)


if __name__ == "__main__":
    main()
