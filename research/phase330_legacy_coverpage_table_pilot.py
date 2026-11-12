#!/usr/bin/env python3
"""Phase 330: visible legacy cover-page table feasibility audit.

The sample is the 25 Phase 328 primary HTML documents where inline-XBRL target
facts were absent. Each fetched byte stream must match its Phase 328 SHA-256.
Visible text is kept separate from structured XBRL facts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import re
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PHASE = 330
EXPECTED_ROWS = 25
MANIFEST_SHA256 = "fb069328bad9e648a85d25264f26cc2a31146d10e14003d004f9725184d30cc7"
PHASE328_ARTIFACT_ID = 13943024635
PHASE328_ARTIFACT_SHA256 = "ed33844f2b9ec435a6ee7eaacbe86fc7001a167efdc2300b65fb6f18f1c24dd8"
EXCLUDED_SYMBOL_TOKENS = {
    "THE", "OF", "EACH", "TITLE", "CLASS", "COMMON", "STOCK", "PREFERRED",
    "SERIES", "WARRANT", "WARRANTS", "SECURITIES", "SECURITY", "TRADING",
    "SYMBOL", "SYMBOLS", "EXCHANGE", "EXCHANGES", "REGISTERED", "NASDAQ",
    "NYSE", "AMEX", "OTC", "MARKET", "ACT", "SECTION", "NONE", "NA", "N/A",
    "NOT", "APPLICABLE", "INC", "CORP", "CORPORATION", "COMPANY", "LIMITED",
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(str(value or "")).replace("\xa0", " ")).strip()


def normalize_symbol_cell(value: str) -> list[str]:
    text = normalize_text(value).upper()
    if not text or text in {"-", "--", "N/A", "NONE", "NOT APPLICABLE"}:
        return []
    tokens = re.findall(r"(?<![A-Z0-9])([A-Z][A-Z0-9.\-]{0,11})(?![A-Z0-9])", text)
    out = []
    for token in tokens:
        token = token.strip(".-")
        if token and token not in EXCLUDED_SYMBOL_TOKENS and token not in out:
            out.append(token)
    return out


class TableParser(HTMLParser):
    """Collect table rows/cells while isolating nested tables."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.table_stack = []
        self.row_stack = []
        self.cell_stack = []
        self.tables = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "table":
            self.table_stack.append({"rows": []})
        elif tag == "tr" and self.table_stack:
            row = []
            self.table_stack[-1]["rows"].append(row)
            self.row_stack.append(row)
        elif tag in {"td", "th"} and self.row_stack:
            cell = []
            self.row_stack[-1].append(cell)
            self.cell_stack.append(cell)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        if self.cell_stack:
            self.cell_stack[-1].append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"td", "th"} and self.cell_stack:
            self.cell_stack.pop()
        elif tag == "tr" and self.row_stack:
            self.row_stack.pop()
        elif tag == "table" and self.table_stack:
            table = self.table_stack.pop()
            if not self.table_stack:
                self.tables.append(table)


def parse_tables(raw: bytes) -> list[list[list[str]]]:
    parser = TableParser()
    parser.feed(raw.decode("utf-8", errors="replace"))
    parser.close()
    return [
        [[normalize_text("".join(cell)) for cell in row] for row in table["rows"]]
        for table in parser.tables
    ]


def find_symbol_column(header: list[str]):
    norm = [normalize_text(x).lower().replace("(", " ").replace(")", " ") for x in header]
    symbol_idx = next((i for i, cell in enumerate(norm) if "trading symbol" in cell), None)
    if symbol_idx is None:
        return None
    title_idx = next((i for i, cell in enumerate(norm) if "title of each class" in cell), None)
    exchange_idx = next((i for i, cell in enumerate(norm) if "exchange" in cell), None)
    return {"symbol": symbol_idx, "title": title_idx, "exchange": exchange_idx}


def extract_coverpage_symbols(tables: list[list[list[str]]]) -> dict:
    found = []
    headers_found = 0
    rows_scanned = 0
    for table_index, table in enumerate(tables):
        for row_index, row in enumerate(table):
            mapping = find_symbol_column(row)
            if mapping is None:
                continue
            headers_found += 1
            symbol_idx = mapping["symbol"]
            for data_row in table[row_index + 1:]:
                if find_symbol_column(data_row) is not None:
                    break
                if symbol_idx >= len(data_row):
                    continue
                rows_scanned += 1
                for symbol in normalize_symbol_cell(data_row[symbol_idx]):
                    found.append({
                        "symbol": symbol,
                        "table_index": table_index,
                        "header_row_index": row_index,
                        "data_row": data_row,
                    })
    unique = sorted({x["symbol"] for x in found})
    return {
        "header_tables_found": headers_found,
        "data_rows_scanned": rows_scanned,
        "visible_symbols": unique,
        "symbol_evidence_rows": found,
    }


def load_manifest(path: Path) -> list[dict]:
    raw = path.read_bytes()
    digest = sha256(raw)
    if digest != MANIFEST_SHA256:
        raise ValueError(f"phase330_manifest_sha256_mismatch:{digest}")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"phase330_manifest_row_count_mismatch:{len(rows)}")
    seen = set()
    for row in rows:
        key = (row["pair_id"], row["side"])
        if key in seen:
            raise ValueError("duplicate_pair_side")
        seen.add(key)
        if not row["selected_filing_date"] < row["event_date"]:
            raise ValueError("manifest_filing_not_before_event")
        if not re.fullmatch(r"[0-9a-f]{64}", row["expected_document_sha256"]):
            raise ValueError("invalid_expected_source_sha256")
    return rows


class SECClient:
    def __init__(self, email: str, min_interval: float = 0.15):
        if not email or "@" not in email:
            raise ValueError("SEC_CONTACT_EMAIL_secret_required")
        self.ua = f"NuevaEstrategia Smart Money Research (contact: {email})"
        self.min_interval = min_interval
        self.last_request = 0.0
        self.cache = {}

    def get(self, url: str, max_bytes: int = 15_000_000):
        if url in self.cache:
            return self.cache[url]
        for attempt in range(4):
            wait = self.min_interval - (time.monotonic() - self.last_request)
            if wait > 0:
                time.sleep(wait)
            req = Request(url, headers={
                "User-Agent": self.ua,
                "Accept": "text/html, text/plain, */*",
                "Accept-Encoding": "identity",
            })
            self.last_request = time.monotonic()
            try:
                with urlopen(req, timeout=35) as response:
                    raw = response.read(max_bytes + 1)
                    if len(raw) > max_bytes:
                        result = (None, response.status, "RESPONSE_TOO_LARGE")
                    else:
                        result = (raw, response.status, "")
                    self.cache[url] = result
                    return result
            except HTTPError as exc:
                if exc.code in {429, 500, 502, 503, 504} and attempt < 3:
                    time.sleep(0.5 * (2 ** attempt))
                    continue
                result = (None, exc.code, f"HTTP_{exc.code}")
                self.cache[url] = result
                return result
            except (URLError, TimeoutError, OSError) as exc:
                if attempt < 3:
                    time.sleep(0.5 * (2 ** attempt))
                    continue
                return (None, 0, f"{type(exc).__name__}:{str(exc)[:160]}")
        return (None, 0, "RETRY_EXHAUSTED")


def audit_row(client: SECClient, row: dict) -> dict:
    cik_path = str(int(row["issuer_cik"]))
    accession_path = row["selected_filing_accession"].replace("-", "")
    url = (
        f"https://www.sec.gov/Archives/edgar/data/{cik_path}/"
        f"{accession_path}/{row['document_name']}"
    )
    raw, status, error = client.get(url)
    base = {
        **row,
        "source_url": url,
        "http_status": status,
        "retrieval_status": "RETRIEVED" if raw else (error or "UNAVAILABLE"),
        "observed_document_bytes": len(raw) if raw else 0,
        "observed_document_sha256": sha256(raw) if raw else "",
        "source_hash_match": bool(raw and sha256(raw) == row["expected_document_sha256"]),
    }
    if not raw:
        return {**base, "parse_status": "NOT_RETRIEVED", "header_tables_found": 0,
                "visible_symbols": [], "candidate_match_status": "NOT_TESTED"}
    if sha256(raw) != row["expected_document_sha256"]:
        return {**base, "parse_status": "SOURCE_HASH_MISMATCH", "header_tables_found": 0,
                "visible_symbols": [], "candidate_match_status": "QUARANTINE_HASH_MISMATCH"}
    tables = parse_tables(raw)
    parsed = extract_coverpage_symbols(tables)
    symbols = parsed["visible_symbols"]
    candidate = row["ticker_candidate"].strip().upper()
    if not parsed["header_tables_found"]:
        match = "NO_TRADING_SYMBOL_COVERPAGE_TABLE"
    elif not symbols:
        match = "HEADER_FOUND_NO_SYMBOL_VALUE"
    elif candidate in symbols and len(symbols) == 1:
        match = "MATCH_SINGLE_VISIBLE_SYMBOL"
    elif candidate in symbols:
        match = "MATCH_AMONG_MULTIPLE_VISIBLE_SYMBOLS"
    else:
        match = "MISMATCH_VISIBLE_SYMBOLS"
    age = (date.fromisoformat(row["event_date"]) - date.fromisoformat(row["selected_filing_date"])).days
    return {
        **base,
        "parse_status": "PARSED",
        "table_count": len(tables),
        **parsed,
        "candidate_match_status": match,
        "filing_age_calendar_days": age,
        "visible_html_is_structured_xbrl_fact": False,
        "security_identity_adjudicated": False,
    }


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                if isinstance(v, (dict, list)) else v
                for k, v in row.items()
            })


def run(manifest_path: Path, outdir: Path, email: str) -> dict:
    rows = load_manifest(manifest_path)
    client = SECClient(email)
    results = []
    for i, row in enumerate(rows, 1):
        results.append(audit_row(client, row))
        if i % 5 == 0:
            print(f"PHASE330_PROGRESS={i}/{len(rows)}")
    counts = Counter(r.get("candidate_match_status", "UNKNOWN") for r in results)
    verified = [r for r in results if r.get("source_hash_match")]
    by_year = defaultdict(Counter)
    for r in results:
        year = r["event_date"][:4]
        by_year[year][r.get("candidate_match_status", "UNKNOWN")] += 1
    summary = {
        "manifest_rows": len(rows),
        "retrieved_documents": sum(r["retrieval_status"] == "RETRIEVED" for r in results),
        "source_hash_verified": len(verified),
        "coverpage_table_found": sum(r.get("header_tables_found", 0) > 0 for r in results),
        "visible_symbols_extracted": sum(bool(r.get("visible_symbols")) for r in results),
        "candidate_exact_single_match": counts["MATCH_SINGLE_VISIBLE_SYMBOL"],
        "candidate_match_multiple": counts["MATCH_AMONG_MULTIPLE_VISIBLE_SYMBOLS"],
        "candidate_mismatch": counts["MISMATCH_VISIBLE_SYMBOLS"],
        "no_trading_symbol_table": counts["NO_TRADING_SYMBOL_COVERPAGE_TABLE"],
        "header_without_symbol_value": counts["HEADER_FOUND_NO_SYMBOL_VALUE"],
        "source_hash_mismatch": counts["QUARANTINE_HASH_MISMATCH"],
        "status_counts": dict(sorted(counts.items())),
        "year_status_counts": {k: dict(sorted(v.items())) for k, v in sorted(by_year.items())},
    }
    controls = {
        "f80_frozen": True, "legacy_coverpage_identity_admitted": False,
        "strict_pit_admitted": False, "security_master_admitted": False,
        "universe_coverage_admitted": False, "alpha_test_authorized": False,
        "return_test_run": False, "bootstrap_loo_run": False,
        "chronological_oos_run": False, "holdout_used": False,
        "production_changed": False, "universe_changed": False,
        "capital_changed": False, "parameters_changed": False,
        "raw_sec_bytes_uploaded": False, "vendor_contacted": False,
        "data_purchased": False, "email_sent": False,
    }
    result = {
        "phase": PHASE,
        "status": "COMPLETED_LEGACY_COVERPAGE_FEASIBILITY_PILOT",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "provider": "U.S. Securities and Exchange Commission",
            "phase328_artifact_id": PHASE328_ARTIFACT_ID,
            "phase328_artifact_sha256": PHASE328_ARTIFACT_SHA256,
            "manifest_sha256": MANIFEST_SHA256,
            "selection": "all 25 Phase 328 primary HTML documents with no target inline-XBRL facts",
        },
        "summary": summary,
        "results": results,
        "controls": controls,
        "interpretation": {
            "sample_is_purposive_not_universe_prevalence": True,
            "visible_text_is_not_structured_xbrl": True,
            "missing_table_means_unknown_not_no_security": True,
            "ticker_match_does_not_prove_share_class": True,
            "identity_crosswalk_admitted": False,
        },
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "phase330_coverpage_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(outdir / "phase330_coverpage_results.csv", results)
    write_csv(outdir / "phase330_quarantine.csv", [r for r in results if not r.get("source_hash_match") or r.get("candidate_match_status") not in {"MATCH_SINGLE_VISIBLE_SYMBOL", "MATCH_AMONG_MULTIPLE_VISIBLE_SYMBOLS"}])
    print("PHASE330_SUMMARY=" + json.dumps(summary, sort_keys=True))
    print("PHASE330_CONTROLS=" + json.dumps(controls, sort_keys=True))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--email", default="")
    a = p.parse_args()
    run(a.manifest, a.output_dir, a.email)


if __name__ == "__main__":
    main()
