#!/usr/bin/env python3
"""Phase 102: SEC FTD multi-period archive continuity and threshold audit.

Source feasibility only. No forward returns, signal construction, or alpha test.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import time
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import requests

SEC_PAGE = "https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data"
OUT = Path("phase102_sec_ftd_multiperiod")
USER_AGENT = "Felix and Sarmiento Abogados S.C. jose.felix@felixsarmiento.com"
EXPECTED_HEADER = [
    "SETTLEMENT DATE", "CUSIP", "SYMBOL", "QUANTITY (FAILS)", "DESCRIPTION", "PRICE"
]
SAMPLES = [
    {"key": "2004q1", "filename": "cnsfails2004q1.zip", "label": "2004, first quarter",
     "start": "2004-02-01", "end": "2004-03-31", "regime": "pre_threshold"},
    {"key": "2008q3", "filename": "cnsfails2008q3.zip", "label": "2008, third quarter",
     "start": "2008-07-01", "end": "2008-09-30", "regime": "threshold_transition"},
    {"key": "2008q4", "filename": "cnsfails2008q4.zip", "label": "2008, fourth quarter",
     "start": "2008-10-01", "end": "2008-12-31", "regime": "post_threshold_quarterly"},
    {"key": "2009q2", "filename": "cnsfails2009q2.zip", "label": "2009, second quarter",
     "start": "2009-04-01", "end": "2009-06-30", "regime": "last_quarterly_archive"},
    {"key": "200907a", "filename": "cnsfails200907a.zip", "label": "July 2009, first half",
     "start": "2009-07-01", "end": "2009-07-15", "regime": "first_half_monthly_archive"},
    {"key": "201801a", "filename": "cnsfails201801a.zip", "label": "January 2018, first half",
     "start": "2018-01-01", "end": "2018-01-15", "regime": "modern_half_monthly"},
    {"key": "202609b", "filename": "cnsfails202609b.zip", "label": "September 2026, second half",
     "start": "2026-09-16", "end": "2026-09-30", "regime": "current_half_monthly"},
]
BREAK = date(2008, 9, 16)


class ZipLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = dict(attrs).get("href", "")
            if href.lower().endswith(".zip"):
                self.links.append(href)


def parse_page_links(html: str, base_url: str = SEC_PAGE) -> dict[str, str]:
    parser = ZipLinkParser()
    parser.feed(html)
    return {href.rsplit("/", 1)[-1].lower(): urljoin(base_url, href) for href in parser.links}


def normalize_row(original: list[str]) -> list[str] | None:
    row = list(original)
    while len(row) > 6 and not row[-1].strip():
        row.pop()
    if len(row) > 6:
        row = row[:4] + ["|".join(row[4:-1])] + [row[-1]]
    elif len(row) == 5:
        row = row + ["."]
    return row if len(row) == 6 else None


def parse_text_member(raw: bytes, member_name: str) -> dict:
    text = raw.decode("latin-1")
    parsed = list(csv.reader(io.StringIO(text), delimiter="|"))
    parsed = [r for r in parsed if any(str(x).strip() for x in r)]
    if not parsed:
        raise ValueError(f"{member_name}: empty text member")
    header = [x.strip().upper().lstrip("\\ufeff") for x in parsed[0]]
    if header != EXPECTED_HEADER:
        raise ValueError(f"{member_name}: unexpected header {header!r}")
    records, malformed = [], []
    trailer_count = trailer_quantity = None
    trailer_lines = 0
    for line_no, original in enumerate(parsed[1:], start=2):
        if len(original) == 1:
            footer = original[0].strip()
            if footer.startswith("Trailer record count "):
                trailer_count = int(footer.rsplit(" ", 1)[1])
                trailer_lines += 1
                continue
            if footer.startswith("Trailer total quantity of shares "):
                trailer_quantity = int(footer.rsplit(" ", 1)[1])
                trailer_lines += 1
                continue
        row = normalize_row(original)
        if row is None:
            malformed.append({"line": line_no, "field_count": len(original), "sample": original[:8]})
            continue
        records.append(row)

    valid, bad = [], Counter()
    for row in records:
        d, cusip, symbol, qty_raw, description, price_raw = [x.strip() for x in row]
        try:
            dt = datetime.strptime(d, "%Y%m%d").date()
        except ValueError:
            bad["date"] += 1
            continue
        try:
            qty = int(qty_raw.replace(",", ""))
            if qty <= 0:
                raise ValueError("non-positive")
        except ValueError:
            bad["quantity"] += 1
            continue
        price = None
        if price_raw not in ("", "."):
            try:
                price = float(price_raw.replace(",", ""))
                if price < 0:
                    raise ValueError("negative")
            except ValueError:
                bad["price"] += 1
                continue
        valid.append({
            "settlement_date": dt.isoformat(),
            "cusip": cusip,
            "symbol": symbol.upper(),
            "quantity": qty,
            "description": description,
            "price": price,
        })

    qty_sum = sum(x["quantity"] for x in valid)
    trailer_count_match = None if trailer_count is None else trailer_count == len(valid)
    trailer_quantity_match = None if trailer_quantity is None else trailer_quantity == qty_sum
    return {
        "member": member_name,
        "raw_nonblank_rows": len(parsed) - 1,
        "valid_records": len(valid),
        "records": valid,
        "malformed": malformed,
        "bad_fields": dict(bad),
        "trailer_lines": trailer_lines,
        "trailer_record_count": trailer_count,
        "trailer_count_match": trailer_count_match,
        "trailer_total_quantity": trailer_quantity,
        "calculated_quantity_sum": qty_sum,
        "trailer_quantity_match": trailer_quantity_match,
    }


def summarize_sample(spec: dict, downloaded: dict, members: list[dict]) -> dict:
    rows = [r for m in members for r in m["records"]]
    dates = [date.fromisoformat(r["settlement_date"]) for r in rows]
    pre = [r for r in rows if date.fromisoformat(r["settlement_date"]) < BREAK]
    post = [r for r in rows if date.fromisoformat(r["settlement_date"]) >= BREAK]
    cusip_symbols = defaultdict(set)
    symbol_cusips = defaultdict(set)
    keys = Counter()
    for r in rows:
        if r["cusip"]:
            cusip_symbols[r["cusip"]].add(r["symbol"])
        if r["symbol"] and r["cusip"]:
            symbol_cusips[r["symbol"]].add(r["cusip"])
        keys[(r["settlement_date"], r["cusip"], r["symbol"])] += 1
    duplicate_groups = {k: n for k, n in keys.items() if n > 1}
    malformed_count = sum(len(m["malformed"]) for m in members)
    bad_counts = Counter()
    for m in members:
        bad_counts.update(m["bad_fields"])
    trailer_failures = sum(
        1 for m in members
        if m["trailer_count_match"] is False or m["trailer_quantity_match"] is False
    )
    start, end = date.fromisoformat(spec["start"]), date.fromisoformat(spec["end"])
    out_of_range = sum(1 for d in dates if d < start or d > end)
    pre_small = sum(1 for r in pre if r["quantity"] < 10000)
    post_small = sum(1 for r in post if r["quantity"] < 10000)
    cusip_nonblank = sum(bool(r["cusip"]) for r in rows)
    symbol_nonblank = sum(bool(r["symbol"]) for r in rows)
    return {
        "key": spec["key"],
        "label": spec["label"],
        "regime": spec["regime"],
        "url": downloaded["url"],
        "download_bytes": downloaded["bytes"],
        "download_sha256": downloaded["sha256"],
        "zip_members": [m["member"] for m in members],
        "records": len(rows),
        "unique_settlement_dates": len(set(dates)),
        "min_settlement_date": min(dates).isoformat() if dates else None,
        "max_settlement_date": max(dates).isoformat() if dates else None,
        "out_of_expected_range_records": out_of_range,
        "unique_cusips": len(cusip_symbols),
        "unique_symbols": len({r["symbol"] for r in rows if r["symbol"]}),
        "cusip_nonblank_pct": round(100 * cusip_nonblank / len(rows), 4) if rows else 0.0,
        "symbol_nonblank_pct": round(100 * symbol_nonblank / len(rows), 4) if rows else 0.0,
        "cusips_with_multiple_symbols": sum(1 for v in cusip_symbols.values() if len(v) > 1),
        "symbols_with_multiple_cusips": sum(1 for v in symbol_cusips.values() if len(v) > 1),
        "duplicate_key_groups": len(duplicate_groups),
        "duplicate_rows_beyond_first": sum(n - 1 for n in duplicate_groups.values()),
        "malformed_records": malformed_count,
        "bad_field_counts": dict(bad_counts),
        "trailer_lines": sum(m["trailer_lines"] for m in members),
        "trailer_validation_failures": trailer_failures,
        "pre_2008_09_16_records": len(pre),
        "pre_break_below_10000": pre_small,
        "post_2008_09_16_records": len(post),
        "post_break_below_10000": post_small,
        "pre_break_min_quantity": min((r["quantity"] for r in pre), default=None),
        "post_break_min_quantity": min((r["quantity"] for r in post), default=None),
        "schema_status": "PASS" if rows and not out_of_range and not malformed_count and not bad_counts and not trailer_failures else "FAIL",
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/zip,*/*"})
    page = session.get(SEC_PAGE, timeout=60)
    page.raise_for_status()
    links = parse_page_links(page.text)
    results, downloads, member_summaries, errors = [], [], [], []
    all_rows = []
    for spec in SAMPLES:
        try:
            url = links.get(spec["filename"].lower())
            if not url:
                raise RuntimeError(f"Official SEC page did not expose {spec['filename']}")
            response = session.get(url, timeout=120)
            response.raise_for_status()
            payload = response.content
            downloads.append({
                "filename": spec["filename"], "url": url, "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            })
            with zipfile.ZipFile(io.BytesIO(payload)) as zf:
                names = [n for n in zf.namelist() if n.lower().endswith(".txt")]
                if not names:
                    raise RuntimeError(f"{spec['filename']}: no TXT member; members={zf.namelist()}")
                parsed_members = [parse_text_member(zf.read(n), n) for n in names]
            summary = summarize_sample(spec, downloads[-1], parsed_members)
            results.append(summary)
            for m in parsed_members:
                member_summaries.append({
                    "sample": spec["key"],
                    "member": m["member"],
                    "raw_nonblank_rows": m["raw_nonblank_rows"],
                    "valid_records": m["valid_records"],
                    "trailer_lines": m["trailer_lines"],
                    "trailer_record_count": m["trailer_record_count"],
                    "trailer_count_match": m["trailer_count_match"],
                    "trailer_total_quantity": m["trailer_total_quantity"],
                    "calculated_quantity_sum": m["calculated_quantity_sum"],
                    "trailer_quantity_match": m["trailer_quantity_match"],
                    "malformed": m["malformed"][:10],
                    "bad_fields": m["bad_fields"],
                })
                all_rows.extend(m["records"])
            time.sleep(0.2)
        except Exception as exc:
            errors.append({"sample": spec["key"], "label": spec["label"], "error": repr(exc)})

    transition = next((x for x in results if x["key"] == "2008q3"), None)
    transition_gate = None if transition is None else (
        transition["pre_break_below_10000"] == 0
        and transition["post_break_below_10000"] > 0
    )
    summary = {
        "phase": 102,
        "source": "SEC official Fails-to-Deliver Data",
        "audit_timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "samples_expected": len(SAMPLES),
        "samples_completed": len(results),
        "samples": results,
        "member_integrity": member_summaries,
        "download_hashes": downloads,
        "errors": errors,
        "gates": {
            "all_representative_archive_regimes_downloaded": len(results) == len(SAMPLES) and not errors,
            "all_sample_schemas_valid": len(results) == len(SAMPLES) and all(x["schema_status"] == "PASS" for x in results),
            "2008_threshold_break_observed_in_transition_archive": transition_gate,
            "cusip_symbol_lifecycle_audit_available": False,
            "historical_publication_vintage_verified": False,
            "inactive_security_return_linkage_verified": False,
        },
        "source_history_status": "SAMPLE_ARCHIVE_CONTINUITY_ONLY",
        "pit_status": "NOT_PASSED; use conservative file-availability dates only after independent validation; SEC does not guarantee exact posting dates",
        "interpretation": "FTD is an aggregate net fail balance at settlement date, not a daily flow or direct short-sale/informed-trading measure.",
        "forward_returns_used": False,
        "alpha_test_authorized": False,
        "f80_changed": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "member_integrity.json").write_text(json.dumps(member_summaries, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if not summary["gates"]["all_representative_archive_regimes_downloaded"] or not summary["gates"]["all_sample_schemas_valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
