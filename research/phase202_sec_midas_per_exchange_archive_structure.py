#!/usr/bin/env python3
"""Phase 202: SEC MIDAS per-security/per-exchange archive structure audit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from zipfile import ZipFile

from research.phase198_sec_midas_archive_inventory import SEC_USER_AGENT
from research.phase199_sec_midas_disputed_quarter_content_audit import download_archive, detect_delimiter

PAGE_URL = "https://www.sec.gov/data-research/sec-markets-data/market-structure-data-security-exchange"
SAMPLE_QUARTERS = ("2016 Q2", "2017 Q2", "2019 Q4")
EXCHANGE_REQUIRED = {
    "ticker", "date", "security", "mcaprank", "turnrank", "volatilityrank", "pricerank",
    "cancels", "trades", "littrades", "oddlots", "hidden", "tradesforhidden",
    "ordervol", "tradevol", "litvol", "oddlotvol", "hiddenvol", "tradevolforhidden",
}
MAX_NESTING = 3
MAX_README_BYTES = 2_000_000


def normalize_column(value: str) -> str:
    value = re.sub(r"\s+", "", value.strip().lower())
    return value.replace("('000)", "")


class QuarterAnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.parts = []
        self.links = {}

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self.href = dict(attrs).get("href")
            self.parts = []

    def handle_data(self, data):
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() != "a" or self.href is None:
            return
        label = " ".join("".join(self.parts).split())
        match = re.search(r"(\d{4})\s*Q([1-4])", label, re.I)
        if match and self.href.lower().split("?", 1)[0].endswith(".zip"):
            quarter = f"{match.group(1)} Q{match.group(2)}"
            self.links[quarter] = urljoin(PAGE_URL, self.href)
        self.href = None
        self.parts = []


def fetch_exchange_inventory() -> dict[str, object]:
    request = Request(PAGE_URL, headers={"User-Agent": SEC_USER_AGENT, "Accept": "text/html"})
    with urlopen(request, timeout=60) as response:
        html = response.read().decode("utf-8", errors="replace")
        status = response.status
        last_modified = response.headers.get("Last-Modified")
        page_date = response.headers.get("Date")
    parser = QuarterAnchorParser()
    parser.feed(html)
    return {
        "page_url": PAGE_URL,
        "http_status": status,
        "last_modified": last_modified,
        "http_date": page_date,
        "quarter_urls": parser.links,
        "quarter_count": len(parser.links),
        "min_quarter": min(parser.links) if parser.links else None,
        "max_quarter": max(parser.links) if parser.links else None,
        "html_sha256": hashlib.sha256(html.encode()).hexdigest(),
    }


def filename_exchange_hints(name: str) -> list[str]:
    base = name.lower()
    tokens = (
        "nyse", "amex", "nasdaq", "arca", "bats", "byx", "bzx", "edga", "edgx",
        "boston", "phlx", "chx", "nsx", "iex", "memx", "ltse",
    )
    return [token for token in tokens if re.search(rf"(^|[^a-z]){re.escape(token)}([^a-z]|$)", base)]


def has_data_member(inspection: dict[str, object]) -> bool:
    if inspection["data_member_count"] > 0:
        return True
    return any(has_data_member(item["inspection"]) for item in inspection["nested_archives"])


def inspect_zip_bytes(content: bytes, nesting: int = 0) -> dict[str, object]:
    archive_sha = hashlib.sha256(content).hexdigest()
    with ZipFile(io.BytesIO(content)) as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        data_members = []
        readmes = []
        nested = []
        extension_counts = {}
        for item in members:
            suffix = Path(item.filename).suffix.lower() or "[none]"
            extension_counts[suffix] = extension_counts.get(suffix, 0) + 1
            with archive.open(item, "r") as stream:
                prefix = stream.read(16384)
            if prefix.startswith(b"PK\x03\x04") or item.filename.lower().endswith(".zip"):
                nested.append(item)
                continue
            if "readme" in item.filename.lower() and item.file_size <= MAX_README_BYTES:
                raw = archive.read(item)
                decoded = raw.decode("utf-8-sig", errors="replace")
                readmes.append({
                    "member": item.filename,
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "text": decoded,
                })
            decoded_prefix = prefix.decode("utf-8-sig", errors="replace")
            first_line = decoded_prefix.splitlines()[0] if decoded_prefix.splitlines() else ""
            delimiter = detect_delimiter(first_line)
            try:
                header = next(csv.reader([first_line], delimiter=delimiter))
            except (StopIteration, csv.Error):
                continue
            normalized = {normalize_column(value) for value in header}
            if EXCHANGE_REQUIRED.issubset(normalized):
                sample_reader = csv.reader(io.StringIO(decoded_prefix), delimiter=delimiter)
                sample_rows = []
                for _ in range(4):
                    try:
                        sample_rows.append(next(sample_reader))
                    except StopIteration:
                        break
                data_members.append({
                    "member": item.filename,
                    "compressed_bytes": item.compress_size,
                    "uncompressed_bytes": item.file_size,
                    "crc32_from_central_directory": f"{item.CRC:08x}",
                    "header": header,
                    "normalized_header": sorted(normalized),
                    "header_sha256": hashlib.sha256("\x1f".join(header).encode()).hexdigest(),
                    "exchange_column_present": "exchange" in normalized,
                    "filename_exchange_hints": filename_exchange_hints(item.filename),
                    "sample_rows": sample_rows[1:],
                })
        nested_results = []
        for item in nested:
            if nesting >= MAX_NESTING:
                raise ValueError("max_nested_zip_depth_exceeded")
            nested_bytes = archive.read(item)
            nested_results.append({
                "container_member": item.filename,
                "container_bytes": len(nested_bytes),
                "inspection": inspect_zip_bytes(nested_bytes, nesting + 1),
            })
        return {
            "archive_sha256": archive_sha,
            "archive_bytes": len(content),
            "nesting_depth": nesting,
            "member_count": len(members),
            "total_uncompressed_member_bytes": sum(item.file_size for item in members),
            "extension_counts": dict(sorted(extension_counts.items())),
            "data_member_count": len(data_members),
            "data_members": data_members,
            "readme_count": len(readmes),
            "readmes": readmes,
            "nested_zip_count": len(nested),
            "nested_archives": nested_results,
            "full_crc_validation_performed": False,
        }


def build_result(inventory: dict[str, object], quarter_results: list[dict[str, object]]) -> dict[str, object]:
    links_complete = all(q in inventory["quarter_urls"] for q in SAMPLE_QUARTERS)
    archives_ok = len(quarter_results) == len(SAMPLE_QUARTERS) and all(
        has_data_member(item["archive_inspection"]) for item in quarter_results
    )
    return {
        "phase": 202,
        "status": "THREE_QUARTER_PER_EXCHANGE_ARCHIVE_STRUCTURE_AUDITED" if links_complete and archives_ok else "PARTIAL_OR_FAILED_STRUCTURE_AUDIT",
        "audit_as_of_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "inventory": inventory,
        "sample_quarters": list(SAMPLE_QUARTERS),
        "quarter_results": quarter_results,
        "interpretation": {
            "official_archive_page_lists_58_quarters": inventory["quarter_count"] == 58,
            "per_exchange_dimension_structure_identified": archives_ok,
            "full_archive_crc_verified": False,
            "full_row_reconciliation_performed": False,
            "first_publication_time_verified": False,
            "strict_pit_admitted": False,
            "alpha_test_authorized": False,
            "holdout_used": False,
            "production_changed": False,
            "data_purchase": False,
            "vendor_contact": False,
            "f80_frozen": True,
        },
        "decision": (
            "Structure/feasibility audit only. The official SEC page describes per-security "
            "metrics partitioned by exchange and lists 58 quarterly archives from January 2012 "
            "through June 2026. This phase inspects three ZIP layouts and schemas; it does not "
            "fully CRC-validate, reconcile all rows or establish publication-time PIT."
        ),
    }


def run_audit() -> dict[str, object]:
    inventory = fetch_exchange_inventory()
    missing = [q for q in SAMPLE_QUARTERS if q not in inventory["quarter_urls"]]
    if missing:
        raise RuntimeError(f"sample_quarters_missing_from_exchange_page:{missing}")
    results = []
    for i, quarter in enumerate(SAMPLE_QUARTERS):
        if i:
            time.sleep(1.0)
        data, http = download_archive(inventory["quarter_urls"][quarter])
        results.append({
            "quarter": quarter,
            "url": inventory["quarter_urls"][quarter],
            "http_metadata": http,
            "archive_inspection": inspect_zip_bytes(data),
        })
    return build_result(inventory, results)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase202_output")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result = run_audit()
    target = output / "phase202_sec_midas_per_exchange_archive_structure.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
