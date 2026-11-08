#!/usr/bin/env python3
"""Phase 201: SEC MIDAS README/version and derived-ratio semantics audit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import time
import zipfile
from collections import Counter
from datetime import datetime, timezone
from itertools import chain
from pathlib import Path

from research.phase198_sec_midas_archive_inventory import fetch_sec_page, parse_inventory
from research.phase199_sec_midas_disputed_quarter_content_audit import (
    download_archive, detect_delimiter, normalize_header, parse_date, REQUIRED,
)
from research.phase200_sec_midas_duplicate_negative_diagnostics import (
    find_midas_member, parse_number,
)

QUARTERS = ("2014 Q2", "2016 Q1", "2016 Q2", "2016 Q3", "2016 Q4", "2019 Q4")
MAX_README_BYTES = 2_000_000
DOC_KEYWORDS = ("hidden", "volume", "trade", "negative", "correction", "cancel", "rank", "ticker", "date")


def collect_readmes(content: bytes, nesting: int = 0) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    archive_sha = hashlib.sha256(content).hexdigest()
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"zip_crc_failure:{bad}")
        members = [item for item in archive.infolist() if not item.is_dir()]
        layer = {
            "sha256": archive_sha,
            "bytes": len(content),
            "zip_crc_passed": True,
            "members": [item.filename for item in members],
        }
        docs = []
        for item in members:
            if "readme" not in item.filename.lower():
                continue
            if item.file_size > MAX_README_BYTES:
                raise ValueError(f"readme_too_large:{item.filename}:{item.file_size}")
            raw = archive.read(item)
            decoded = raw.decode("utf-8-sig", errors="replace")
            relevant = [
                line.strip() for line in decoded.splitlines()
                if any(word in line.lower() for word in DOC_KEYWORDS)
            ]
            docs.append({
                "member": item.filename,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "text": decoded,
                "relevant_lines": relevant[:80],
                "mentions_negative": "negative" in decoded.lower(),
                "mentions_correction": "correction" in decoded.lower() or "corrected" in decoded.lower(),
            })
        nested = [item for item in members if item.filename.lower().endswith(".zip")]
        layers = [layer]
        if len(nested) == 1 and nesting < 3:
            inner = archive.read(nested[0])
            inner_docs, inner_layers = collect_readmes(inner, nesting + 1)
            docs.extend(inner_docs)
            layers.extend(inner_layers)
        return docs, layers


def ratio_stats():
    return {
        "valid_count": 0, "negative_numerator_count": 0, "denominator_zero_count": 0,
        "denominator_missing_count": 0, "numerator_missing_count": 0,
        "denominator_negative_count": 0, "greater_than_one_count": 0,
        "min": None, "max": None, "negative_examples": [], "greater_than_one_examples": [],
    }


def audit_derived_ratios(csv_bytes: bytes, quarter: str) -> dict[str, object]:
    text = io.TextIOWrapper(io.BytesIO(csv_bytes), encoding="utf-8-sig", errors="replace", newline="")
    first_line = text.readline()
    if not first_line:
        raise ValueError("empty_csv")
    delimiter = detect_delimiter(first_line)
    reader = csv.reader(chain([first_line], text), delimiter=delimiter)
    header = next(reader)
    normalized = [normalize_header(value) for value in header]
    missing = sorted(REQUIRED - set(normalized))
    if missing:
        raise ValueError(f"missing_required_columns:{missing}")
    idx = {name: i for i, name in enumerate(normalized)}
    specs = {
        "hidden_rate": ("hidden", "tradesforhidden"),
        "hidden_volume_share": ("hiddenvol('000)", "tradevolforhidden('000)"),
    }
    stats = {name: ratio_stats() for name in specs}
    rows = 0
    for raw in reader:
        if not raw or not any(value.strip() for value in raw) or len(raw) != len(header):
            continue
        ticker = raw[idx["ticker"]].strip().upper()
        parsed_date = parse_date(raw[idx["date"]])
        if not ticker or parsed_date is None:
            continue
        day = parsed_date.isoformat()
        rows += 1
        for name, (num_field, den_field) in specs.items():
            numerator = parse_number(raw[idx[num_field]])
            denominator = parse_number(raw[idx[den_field]])
            item = stats[name]
            if numerator is None:
                item["numerator_missing_count"] += 1
                continue
            if numerator < 0:
                item["negative_numerator_count"] += 1
                if denominator is None:
                    item["denominator_missing_count"] += 1
                elif denominator == 0:
                    item["denominator_zero_count"] += 1
                elif denominator < 0:
                    item["denominator_negative_count"] += 1
                if len(item["negative_examples"]) < 12:
                    item["negative_examples"].append({
                        "ticker": ticker, "date": day, "numerator": numerator,
                        "denominator": denominator, "denominator_field": den_field,
                    })
                continue
            if denominator is None:
                item["denominator_missing_count"] += 1
                continue
            if denominator < 0:
                item["denominator_negative_count"] += 1
                continue
            if denominator == 0:
                item["denominator_zero_count"] += 1
                continue
            ratio = numerator / denominator
            item["valid_count"] += 1
            item["min"] = ratio if item["min"] is None else min(item["min"], ratio)
            item["max"] = ratio if item["max"] is None else max(item["max"], ratio)
            if ratio > 1 + 1e-12:
                item["greater_than_one_count"] += 1
                if len(item["greater_than_one_examples"]) < 12:
                    item["greater_than_one_examples"].append({
                        "ticker": ticker, "date": day, "numerator": numerator,
                        "denominator": denominator, "ratio": ratio,
                    })
    return {
        "quarter": quarter,
        "csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "valid_rows_parsed": rows,
        "ratios": stats,
    }


def build_result(results: list[dict[str, object]]) -> dict[str, object]:
    complete = {item["quarter"] for item in results} == set(QUARTERS)
    readme_hashes = sorted({
        doc["sha256"] for item in results for doc in item["readmes"]
    })
    return {
        "phase": 201,
        "status": "SIX_QUARTER_README_AND_DERIVED_RATIO_AUDIT_COMPLETED" if complete else "PARTIAL_AUDIT",
        "audit_as_of_utc": datetime.now(timezone.utc).isoformat(),
        "quarters_audited": list(QUARTERS),
        "quarter_results": results,
        "unique_readme_hashes": readme_hashes,
        "interpretation": {
            "embedded_readmes_extracted": True,
            "readme_versions_compared_by_sha256": True,
            "hidden_rate_recomputed_as_hidden_over_tradesforhidden": True,
            "hidden_volume_share_recomputed_as_hiddenvol_over_tradevolforhidden": True,
            "negative_values_assumed_to_be_sentinels": False,
            "strict_pit_admitted": False,
            "alpha_test_authorized": False,
            "holdout_used": False,
            "production_changed": False,
            "data_purchase": False,
            "vendor_contact": False,
            "f80_frozen": True,
        },
        "decision": (
            "Documentation and derived-ratio audit only. README wording is evidence about "
            "field definitions, not a publication timestamp. Negative numerator values remain "
            "unclassified unless the embedded documentation explicitly resolves them."
        ),
    }


def run_audit() -> dict[str, object]:
    inventory = parse_inventory(fetch_sec_page())
    urls = inventory["quarter_urls"]
    missing = [q for q in QUARTERS if q not in urls]
    if missing:
        raise RuntimeError(f"quarters_missing_from_sec_inventory:{missing}")
    results = []
    for i, quarter in enumerate(QUARTERS):
        if i:
            time.sleep(1.0)
        archive_bytes, http = download_archive(urls[quarter])
        csv_bytes, archive_meta = find_midas_member(archive_bytes)
        readmes, readme_layers = collect_readmes(archive_bytes)
        ratios = audit_derived_ratios(csv_bytes, quarter)
        results.append({
            "quarter": quarter,
            "archive_metadata": archive_meta,
            "readme_archive_layers": readme_layers,
            "readmes": readmes,
            "ratio_diagnostics": ratios,
            "http_metadata": http,
        })
    return build_result(results)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase201_output")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result = run_audit()
    target = output / "phase201_sec_midas_readme_ratio_semantics.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
