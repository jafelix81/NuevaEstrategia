#!/usr/bin/env python3
"""Phase 198: SEC MIDAS quarterly archive inventory and disputed-gap probe.

Only fetches the SEC landing page and the first four bytes of six ZIP assets
using HTTP Range requests. It does not download or persist full archives.
No release date, PIT eligibility, participant identity or alpha is inferred.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

SEC_PAGE = "https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security"
SEC_USER_AGENT = "Felix and Sarmiento Abogados S.C. research jose.felix@felixsarmiento.com"
DISPUTED_QUARTERS = [
    "2014 Q2", "2016 Q1", "2016 Q2", "2016 Q3", "2016 Q4", "2019 Q4",
]
KNOWN_RELEASE_ANCHORS = [
    {"quarter": "2021 Q3", "public_bulletin_date": "2021-11-02",
     "url": "https://content.govdelivery.com/accounts/USSEC/bulletins/2fa5ec1"},
    {"quarter": "2023 Q1", "public_bulletin_date": "2023-05-02",
     "url": "https://content.govdelivery.com/accounts/USSEC/bulletins/3583f8b"},
    {"quarter": "2023 Q4", "public_bulletin_date": "2024-01-31",
     "url": "https://content.govdelivery.com/accounts/USSEC/bulletins/387f950"},
]


def expected_quarters() -> list[str]:
    result: list[str] = []
    year, quarter = 2012, 1
    while (year, quarter) <= (2026, 2):
        result.append(f"{year} Q{quarter}")
        quarter += 1
        if quarter == 5:
            year += 1
            quarter = 1
    return result


class QuarterLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.href: str | None = None
        self.text_parts: list[str] = []
        self.links: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self.href = dict(attrs).get("href")
            self.text_parts = []

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self.href is None:
            return
        label = re.sub(r"\s+", " ", "".join(self.text_parts)).strip()
        match = re.fullmatch(r"(\d{4}) Q([1-4])", label)
        if match:
            quarter = label
            url = urljoin(SEC_PAGE, self.href)
            parsed = urlparse(url)
            if parsed.hostname not in {"www.sec.gov", "sec.gov"} or not parsed.path.lower().endswith(".zip"):
                raise ValueError(f"non_SEC_zip_link:{quarter}")
            if quarter in self.links:
                raise ValueError(f"duplicate_quarter_link:{quarter}")
            self.links[quarter] = url
        self.href = None
        self.text_parts = []


def parse_inventory(html: str) -> dict[str, object]:
    parser = QuarterLinkParser()
    parser.feed(html)
    expected = expected_quarters()
    actual = sorted(parser.links, key=lambda x: (int(x[:4]), int(x[-1])))
    missing = [q for q in expected if q not in parser.links]
    unexpected = [q for q in actual if q not in expected]
    reviewed = re.search(
        r"Last Reviewed or Updated:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        html, re.IGNORECASE,
    )
    return {
        "quarter_count": len(parser.links),
        "expected_quarter_count": len(expected),
        "quarter_labels": actual,
        "missing_quarters": missing,
        "unexpected_quarters": unexpected,
        "consecutive_2012q1_to_2026q2": actual == expected,
        "page_last_reviewed_or_updated": reviewed.group(1) if reviewed else None,
        "quarter_urls": parser.links,
    }


def summarize_zip_probe(status: int, headers: dict[str, str], prefix: bytes, final_url: str) -> dict[str, object]:
    magic_ok = prefix.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))
    return {
        "http_status": status,
        "final_url": final_url,
        "zip_signature_valid": magic_ok,
        "first_four_bytes_hex": prefix.hex(),
        "range_bytes_read": len(prefix),
        "content_length": headers.get("Content-Length"),
        "content_range": headers.get("Content-Range"),
        "content_type": headers.get("Content-Type"),
        "last_modified": headers.get("Last-Modified"),
        "http_date": headers.get("Date"),
        "etag": headers.get("ETag"),
    }


def fetch_sec_page() -> str:
    request = Request(
        SEC_PAGE,
        headers={"User-Agent": SEC_USER_AGENT, "Accept": "text/html,*/*"},
    )
    with urlopen(request, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")


def probe_zip_url(url: str) -> dict[str, object]:
    request = Request(
        url,
        headers={
            "User-Agent": SEC_USER_AGENT,
            "Accept": "application/zip,application/octet-stream,*/*",
            "Range": "bytes=0-3",
        },
    )
    try:
        with urlopen(request, timeout=45) as response:
            prefix = response.read(4)
            headers = {key: value for key, value in response.headers.items()}
            return summarize_zip_probe(response.status, headers, prefix, response.geturl())
    except HTTPError as exc:
        headers = {key: value for key, value in exc.headers.items()}
        return summarize_zip_probe(exc.code, headers, b"", exc.geturl())
    except (URLError, TimeoutError) as exc:
        return {
            "http_status": None,
            "final_url": url,
            "zip_signature_valid": False,
            "range_bytes_read": 0,
            "error": type(exc).__name__,
        }


def build_result(inventory: dict[str, object], probes: dict[str, dict[str, object]]) -> dict[str, object]:
    quarter_urls = inventory["quarter_urls"]
    disputed_present = all(q in quarter_urls for q in DISPUTED_QUARTERS)
    probes_complete = set(probes) == set(DISPUTED_QUARTERS)
    all_zip_signatures = probes_complete and all(
        bool(item.get("zip_signature_valid")) for item in probes.values()
    )
    archive_index_complete = (
        inventory["quarter_count"] == 58
        and inventory["consecutive_2012q1_to_2026q2"] is True
        and not inventory["missing_quarters"]
        and not inventory["unexpected_quarters"]
    )
    status = (
        "SEC_ARCHIVE_INDEX_COMPLETE_AND_DISPUTED_ZIPS_REACHABLE"
        if archive_index_complete and disputed_present and all_zip_signatures
        else "PARTIAL_OR_FAILED_ARCHIVE_PROBE"
    )
    return {
        "phase": 198,
        "status": status,
        "audit_as_of_utc": datetime.now(timezone.utc).isoformat(),
        "source": "SEC Metrics by Individual Security quarterly public archive",
        "source_page": SEC_PAGE,
        "archive_inventory": {
            key: value for key, value in inventory.items() if key != "quarter_urls"
        },
        "disputed_quarters": DISPUTED_QUARTERS,
        "disputed_quarter_probes": probes,
        "release_anchors": KNOWN_RELEASE_ANCHORS,
        "release_anchor_count": len(KNOWN_RELEASE_ANCHORS),
        "archive_quarter_count": inventory["quarter_count"],
        "release_anchor_coverage_ratio": "0.05172414",
        "release_anchors_without_verified_bulletin_date": 55,
        "interpretation": {
            "range_probe_only": True,
            "full_zip_downloaded": False,
            "full_quarter_content_verified": False,
            "quarter_daily_row_coverage_verified": False,
            "first_publication_time_verified_for_all_quarters": False,
            "release_anchor_is_not_first_receipt_for_all_users": True,
            "strict_pit_admitted": False,
            "off_exchange_flow_measure": False,
            "participant_identity_available": False,
            "buyer_seller_aggressor_side_available": False,
            "alpha_test_authorized": False,
            "holdout_used": False,
            "production_changed": False,
            "data_purchase": False,
            "vendor_contact": False,
            "f80_frozen": True,
        },
        "decision": (
            "The SEC landing page is the authoritative current archive inventory. "
            "A ZIP signature probe establishes only that the six disputed public assets "
            "are reachable, not that every daily row is complete. The three known SEC "
            "bulletin anchors cover only 3 of 58 quarter releases; the page's current "
            "last-reviewed date is not a per-quarter publication timestamp. MIDAS public "
            "security metrics are daily on-exchange market-structure aggregates, not "
            "off-exchange flow, aggressor-side flow or participant identity. Strict PIT "
            "and alpha admission remain false."
        ),
    }


def run_audit() -> dict[str, object]:
    inventory = parse_inventory(fetch_sec_page())
    quarter_urls = inventory["quarter_urls"]
    missing_disputed = [q for q in DISPUTED_QUARTERS if q not in quarter_urls]
    if missing_disputed:
        raise RuntimeError(f"disputed_quarters_missing_from_sec_page:{missing_disputed}")
    probes = {quarter: probe_zip_url(quarter_urls[quarter]) for quarter in DISPUTED_QUARTERS}
    return build_result(inventory, probes)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase198_output")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = run_audit()
    path = output_dir / "phase198_sec_midas_archive_inventory.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
