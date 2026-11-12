#!/usr/bin/env python3
"""Phase 314: identify the original N-PORT filing for an Otter Creek NPORT-P/A.

Downloads only the 2022Q3 NPORT-P candidates for registrant CIK 811030, then
matches report date and series ID against the Phase 312 amendment. It preserves
all candidate hashes and compares short-position vintages without treating
holdings as trades or an amendment as a new position event.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

try:
    from research.phase313_nport_sgml_header_reconciliation import (
        extract_primary_xml,
        identity_state,
        local_name,
        parse_header_identity,
        xml_values,
    )
except ModuleNotFoundError:
    from phase313_nport_sgml_header_reconciliation import (
        extract_primary_xml,
        identity_state,
        local_name,
        parse_header_identity,
        xml_values,
    )

TARGET_CIK = "0000811030"
TARGET_REPORT_DATE = "2022-07-31"
TARGET_SERIES_ID = "S000043717"
TARGET_AMENDMENT = "0001145549-22-060851"
TARGET_2023 = "0001145549-23-060491"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def accession_raw_filename(accession: str) -> str:
    return accession.replace("-", "") + ".txt"


def dec(value: str | None) -> Decimal | None:
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError):
        return None


def direct_child_text(parent: ET.Element, name: str) -> str:
    for child in list(parent):
        if local_name(child.tag) == name:
            return (child.text or "").strip()
    return ""


def parse_header_fields(text: str) -> dict[str, str]:
    header = text.split("<DOCUMENT>", 1)[0]

    def one(pattern: str) -> str:
        match = re.search(pattern, header, flags=re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else ""

    return {
        "accession": one(r"ACCESSION NUMBER:\s*([0-9-]+)"),
        "form_type": one(r"CONFORMED SUBMISSION TYPE:\s*([A-Z0-9/-]+)"),
        "registrant_cik": one(r"CENTRAL INDEX KEY:\s*([0-9]+)").zfill(10),
        "filed_as_of_date": one(r"FILED AS OF DATE:\s*([0-9]{8})"),
        "period_of_report": one(r"CONFORMED PERIOD OF REPORT:\s*([0-9]{8})"),
        "acceptance_datetime_et": one(r"ACCEPTANCE-DATETIME:\s*([0-9]{14})"),
    }


def parse_short_positions(root: ET.Element) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for node in root.iter():
        if local_name(node.tag) != "invstOrSec":
            continue
        payoff = direct_child_text(node, "payoffProfile")
        asset_cat = direct_child_text(node, "assetCat")
        issuer_cat = direct_child_text(node, "issuerCat")
        country = direct_child_text(node, "invCountry")
        units = direct_child_text(node, "units")
        balance = direct_child_text(node, "balance")
        value = direct_child_text(node, "valUSD")
        pct = direct_child_text(node, "pctVal")
        b, v, p = dec(balance), dec(value), dec(pct)
        if not (
            payoff == "Short"
            and asset_cat == "EC"
            and issuer_cat == "CORP"
            and country == "US"
            and units == "NS"
            and b is not None and b < 0
            and v is not None and v < 0
            and p is not None and p < 0
        ):
            continue
        identifiers = next((child for child in list(node) if local_name(child.tag) == "identifiers"), None)
        isin = direct_child_text(identifiers, "isin") if identifiers is not None else ""
        ticker = direct_child_text(identifiers, "ticker") if identifiers is not None else ""
        out.append({
            "issuer_name": direct_child_text(node, "name"),
            "issue_title": direct_child_text(node, "title"),
            "cusip": direct_child_text(node, "cusip"),
            "isin": isin,
            "ticker": ticker,
            "balance": balance,
            "value_usd": value,
            "percentage_nav": pct,
            "payoff_profile": payoff,
            "asset_category": asset_cat,
            "issuer_type": issuer_cat,
            "investment_country": country,
            "units": units,
        })
    return out


def parse_submission(raw: bytes, expected_form: str) -> dict[str, Any]:
    text = raw.decode("utf-8", errors="replace")
    header = parse_header_fields(text)
    header_identity = parse_header_identity(text)
    xml_text = extract_primary_xml(text, expected_form)
    root = ET.fromstring(xml_text)
    xml_series = xml_values(root, "seriesId")
    xml_classes = xml_values(root, "classId")
    xml_names = xml_values(root, "seriesName")
    report_dates = xml_values(root, "repPdDate")
    submission_types = xml_values(root, "submissionType")
    return {
        **header,
        "series_ids_header": header_identity["series_ids"],
        "series_ids_xml": xml_series,
        "series_ids": list(dict.fromkeys(header_identity["series_ids"] + xml_series)),
        "series_identity_state": identity_state(header_identity["series_ids"], xml_series),
        "class_ids_header": header_identity["class_ids"],
        "class_ids_xml": xml_classes,
        "class_ids": list(dict.fromkeys(header_identity["class_ids"] + xml_classes)),
        "class_identity_state": identity_state(header_identity["class_ids"], xml_classes),
        "series_names": list(dict.fromkeys(header_identity["series_names"] + xml_names)),
        "report_dates": report_dates,
        "report_date": report_dates[0] if len(report_dates) == 1 else "",
        "xml_submission_types": submission_types,
        "short_positions": parse_short_positions(root),
        "holding_nodes": sum(1 for node in root.iter() if local_name(node.tag) == "invstOrSec"),
    }


def position_key(row: dict[str, str]) -> str:
    if row.get("cusip"):
        security = "CUSIP:" + row["cusip"]
    elif row.get("isin"):
        security = "ISIN:" + row["isin"]
    else:
        security = "NAME:" + row.get("issuer_name", "") + "|" + row.get("issue_title", "")
    return "|".join([
        security,
        row.get("payoff_profile", ""),
        row.get("asset_category", ""),
        row.get("issuer_type", ""),
        row.get("investment_country", ""),
        row.get("units", ""),
    ])


def position_values(row: dict[str, str]) -> tuple[str, str, str]:
    return (row.get("balance", ""), row.get("value_usd", ""), row.get("percentage_nav", ""))


def compare_positions(left: list[dict[str, str]], right: list[dict[str, str]]) -> dict[str, Any]:
    left_map: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    right_map: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for row in left:
        left_map[position_key(row)].append(position_values(row))
    for row in right:
        right_map[position_key(row)].append(position_values(row))

    added = removed = unchanged = modified = 0
    examples: list[dict[str, Any]] = []
    for key in sorted(set(left_map) | set(right_map)):
        a = sorted(left_map.get(key, []))
        b = sorted(right_map.get(key, []))
        if not a:
            added += len(b)
            if len(examples) < 10:
                examples.append({"key": key, "state": "ADDED", "right": b})
        elif not b:
            removed += len(a)
            if len(examples) < 10:
                examples.append({"key": key, "state": "REMOVED", "left": a})
        elif a == b:
            unchanged += len(a)
        else:
            shared = min(len(a), len(b))
            modified += shared
            if len(b) > len(a):
                added += len(b) - len(a)
            elif len(a) > len(b):
                removed += len(a) - len(b)
            if len(examples) < 10:
                examples.append({"key": key, "state": "MODIFIED", "left": a, "right": b})
    return {
        "left_rows": len(left),
        "right_rows": len(right),
        "unchanged_rows": unchanged,
        "modified_rows": modified,
        "added_rows": added,
        "removed_rows": removed,
        "examples_max_10": examples,
    }


def select_candidates(census: list[dict[str, str]], amendment_filing_date: str) -> list[dict[str, str]]:
    rows = [
        row for row in census
        if row.get("cik", "").zfill(10) == TARGET_CIK
        and row.get("quarter") == "2022Q3"
        and row.get("form_type") == "NPORT-P"
        and row.get("filing_date", "") < amendment_filing_date
    ]
    return sorted(rows, key=lambda row: (row.get("filing_date", ""), row.get("accession", "")))


def classify_parent_matches(candidates: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    matches = [
        row for row in candidates
        if row.get("report_date") == TARGET_REPORT_DATE
        and TARGET_SERIES_ID in row.get("series_ids", [])
        and row.get("registrant_cik") == TARGET_CIK
        and row.get("form_type") == "NPORT-P"
    ]
    if len(matches) == 1:
        return "UNIQUE_METADATA_PARENT_CANDIDATE_NOT_AUTHORITATIVE", matches
    if len(matches) == 0:
        return "NO_METADATA_PARENT_CANDIDATE", matches
    return "AMBIGUOUS_METADATA_PARENT_CANDIDATES", matches


def download_sec_file(url: str, user_agent: str, max_attempts: int = 6) -> bytes:
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": user_agent,
                "Accept": "text/plain, application/xml, */*",
                "Accept-Encoding": "identity",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
                if response.status != 200 or not data:
                    raise RuntimeError(f"unexpected_http_response:{response.status}:{len(data)}")
                return data
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            retry_after = 0
            if isinstance(exc, urllib.error.HTTPError):
                try:
                    retry_after = int(exc.headers.get("Retry-After", "0"))
                except (TypeError, ValueError):
                    retry_after = 0
            delay = max(retry_after, min(2 ** attempt, 30))
            if attempt + 1 < max_attempts:
                time.sleep(delay)
    raise RuntimeError(f"sec_download_failed:{url}:{last_error}")


def load_amendment(phase312_dir: Path) -> tuple[bytes, str, str]:
    raw_path = phase312_dir / "raw" / accession_raw_filename(TARGET_AMENDMENT)
    ledger = read_csv(phase312_dir / "nport_sample_filing_reconciliation.csv")
    row = next((x for x in ledger if x.get("accession") == TARGET_AMENDMENT), None)
    if row is None or not raw_path.is_file():
        raise FileNotFoundError("phase312_otter_creek_amendment_or_ledger_missing")
    raw = raw_path.read_bytes()
    actual = sha256(raw)
    if actual != row.get("raw_sha256"):
        raise ValueError("phase312_amendment_sha256_mismatch")
    expected_filed_date = row.get("master_index_filing_date", "").replace("-", "")
    return raw, actual, expected_filed_date


def load_2023_control(phase310_dir: Path) -> tuple[bytes, str]:
    raw_path = phase310_dir / "phase193_output/raw/000114554923060491/0001145549-23-060491.txt"
    result_path = phase310_dir / "phase310_output/phase310_nport_raw_vintage_validation.json"
    if not raw_path.is_file() or not result_path.is_file():
        raise FileNotFoundError("phase310_2023_otter_creek_control_missing")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    item = next((x for x in result.get("accessions", []) if x.get("accession") == TARGET_2023), None)
    if item is None:
        raise ValueError("phase310_2023_otter_creek_control_not_in_result")
    raw = raw_path.read_bytes()
    expected = item.get("sha256", {}).get("submission")
    if sha256(raw) != expected:
        raise ValueError("phase310_2023_submission_sha256_mismatch")
    return raw, expected


def run_audit(phase311_dir: Path, phase312_dir: Path, phase310_dir: Path, output_dir: Path, contact_email: str) -> dict[str, Any]:
    if not contact_email or "@" not in contact_email:
        raise ValueError("SEC_CONTACT_EMAIL_missing_or_invalid")
    census_path = phase311_dir / "nport_accession_census.csv"
    if not census_path.is_file():
        raise FileNotFoundError("phase311_nport_accession_census_missing")
    census = read_csv(census_path)
    census_sha = sha256(census_path.read_bytes())

    amendment_raw, amendment_sha, amendment_expected_filed_date = load_amendment(phase312_dir)
    amendment = parse_submission(amendment_raw, "NPORT-P/A")
    if amendment["accession"] != TARGET_AMENDMENT or amendment["form_type"] != "NPORT-P/A":
        raise ValueError("target_amendment_header_identity_failed")
    if amendment["registrant_cik"] != TARGET_CIK or amendment["report_date"] != TARGET_REPORT_DATE:
        raise ValueError("target_amendment_cik_or_report_date_mismatch")
    if amendment["period_of_report"] != amendment["report_date"].replace("-", ""):
        raise ValueError("target_amendment_header_xml_report_date_mismatch")
    if amendment["filed_as_of_date"] != amendment_expected_filed_date or amendment["acceptance_datetime_et"][:8] != amendment["filed_as_of_date"]:
        raise ValueError("target_amendment_filed_or_acceptance_date_mismatch")
    if amendment["series_identity_state"] != "MATCH" or amendment["class_identity_state"] != "MATCH" or TARGET_SERIES_ID not in amendment["series_ids"]:
        raise ValueError("target_amendment_series_or_class_identity_not_confirmed")

    amendment_filing_date = amendment["filed_as_of_date"][:4] + "-" + amendment["filed_as_of_date"][4:6] + "-" + amendment["filed_as_of_date"][6:8]
    candidates = select_candidates(census, amendment_filing_date)
    if len(candidates) != 25:
        raise ValueError(f"candidate_count_expected_25:{len(candidates)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw_candidates"
    raw_dir.mkdir(exist_ok=True)
    user_agent = f"SmartMoneyResearch/1.0 ({contact_email})"
    candidate_results: list[dict[str, Any]] = []

    for candidate in candidates:
        accession = candidate["accession"]
        filename = candidate.get("filename") or f"edgar/data/{TARGET_CIK.lstrip('0')}/{accession.replace('-', '')}.txt"
        url = "https://www.sec.gov/Archives/" + filename
        raw = download_sec_file(url, user_agent)
        raw_path = raw_dir / f"{accession}.txt"
        raw_path.write_bytes(raw)
        parsed = parse_submission(raw, "NPORT-P")
        if parsed["accession"] != accession:
            raise ValueError(f"candidate_accession_mismatch:{accession}:{parsed['accession']}")
        if parsed["form_type"] != "NPORT-P" or parsed["registrant_cik"] != TARGET_CIK:
            raise ValueError(f"candidate_form_or_cik_mismatch:{accession}")
        if parsed["filed_as_of_date"] != candidate.get("filing_date", "").replace("-", ""):
            raise ValueError(f"candidate_filed_date_mismatch:{accession}")
        if parsed["acceptance_datetime_et"][:8] != parsed["filed_as_of_date"]:
            raise ValueError(f"candidate_acceptance_date_mismatch:{accession}")
        if parsed["period_of_report"] and parsed["report_date"] and parsed["period_of_report"] != parsed["report_date"].replace("-", ""):
            raise ValueError(f"candidate_period_of_report_mismatch:{accession}")
        if parsed["series_identity_state"] not in {"MATCH", "MISSING_BOTH"} or parsed["class_identity_state"] not in {"MATCH", "MISSING_BOTH"}:
            raise ValueError(f"candidate_header_xml_identity_mismatch:{accession}")
        candidate_results.append({
            "accession": accession,
            "filing_date": candidate.get("filing_date", ""),
            "filed_as_of_date": parsed["filed_as_of_date"],
            "period_of_report": parsed["period_of_report"],
            "report_date": parsed["report_date"],
            "registrant_cik": parsed["registrant_cik"],
            "form_type": parsed["form_type"],
            "series_ids": parsed["series_ids"],
            "class_ids": parsed["class_ids"],
            "series_names": parsed["series_names"],
            "series_identity_state": parsed["series_identity_state"],
            "class_identity_state": parsed["class_identity_state"],
            "acceptance_datetime_et": parsed["acceptance_datetime_et"],
            "short_rows": len(parsed["short_positions"]),
            "raw_size_bytes": len(raw),
            "raw_sha256": sha256(raw),
            "raw_file": f"raw_candidates/{accession}.txt",
        })
        time.sleep(0.25)

    parent_status, parent_matches = classify_parent_matches(candidate_results)
    for match in parent_matches:
        match["class_ids_exact_match_to_amendment"] = set(match.get("class_ids", [])) == set(amendment["class_ids"])
        match["series_name_exact_match_to_amendment"] = set(match.get("series_names", [])) == set(amendment["series_names"])
    parent_raw = None
    parent_meta = None
    original_vs_amendment = None
    if len(parent_matches) == 1:
        parent_accession = parent_matches[0]["accession"]
        parent_raw = (raw_dir / f"{parent_accession}.txt").read_bytes()
        parent_meta = parse_submission(parent_raw, "NPORT-P")
        original_vs_amendment = compare_positions(parent_meta["short_positions"], amendment["short_positions"])

    control_raw, control_sha = load_2023_control(phase310_dir)
    control = parse_submission(control_raw, "NPORT-P")
    if control["accession"] != TARGET_2023 or control["registrant_cik"] != TARGET_CIK:
        raise ValueError("2023_control_accession_or_cik_mismatch")
    if control["report_date"] != "2023-07-31" or control["series_identity_state"] != "MATCH" or control["class_identity_state"] != "MATCH":
        raise ValueError("2023_control_report_date_or_series_class_identity_mismatch")
    if control["period_of_report"] != control["report_date"].replace("-", ""):
        raise ValueError("2023_control_header_xml_report_date_mismatch")
    if control["filed_as_of_date"] != "20230929" or control["acceptance_datetime_et"][:8] != control["filed_as_of_date"]:
        raise ValueError("2023_control_filed_or_acceptance_date_mismatch")
    if TARGET_SERIES_ID not in control["series_ids"]:
        raise ValueError("2023_control_series_id_mismatch")

    amendment_vs_2023 = compare_positions(amendment["short_positions"], control["short_positions"])
    candidate_fields = [
        "accession", "filing_date", "filed_as_of_date", "period_of_report", "report_date", "registrant_cik", "form_type",
        "series_ids", "class_ids", "series_names", "series_identity_state",
        "class_identity_state", "acceptance_datetime_et", "short_rows",
        "raw_size_bytes", "raw_sha256", "raw_file",
    ]
    write_csv(output_dir / "candidate_originals_reconciliation.csv", candidate_results, candidate_fields)

    result = {
        "phase": 314,
        "status": "PASS_OTTER_CREEK_PARENT_CANDIDATE_AUDIT",
        "source_artifacts": {
            "phase311_run_id": 43156706936,
            "phase311_artifact_id": 13916331861,
            "phase311_artifact_sha256": "b03abc72c5ed9d59005ccca9a1285169c6bac7b7a607e9f415ec4c0fe1a342be",
            "phase311_census_sha256": census_sha,
            "phase312_run_id": 43157888685,
            "phase312_artifact_id": 13915839847,
            "phase312_artifact_sha256": "78586bd1dbbbd12473ce6d0f75cdee360991541e99a9e2eb45641005f81a4287",
            "phase310_run_id": 43154326395,
            "phase310_artifact_id": 13915126393,
            "phase310_artifact_sha256": "f4827e6065b76bb2f8d4c6287e2026cf1b6eb06f136a407d6295ab530e47ef98"
        },
        "candidate_count": len(candidate_results),
        "candidate_downloads": len(candidate_results),
        "candidate_hashes_recorded": len(candidate_results),
        "target_amendment": {
            "accession": TARGET_AMENDMENT,
            "sha256": amendment_sha,
            "form_type": amendment["form_type"],
            "report_date": amendment["report_date"],
            "filing_date": amendment["filed_as_of_date"],
            "series_ids": amendment["series_ids"],
            "class_ids": amendment["class_ids"],
            "series_identity_state": amendment["series_identity_state"],
            "short_rows": len(amendment["short_positions"]),
        },
        "parent_linkage": {
            "status": parent_status,
            "match_count": len(parent_matches),
            "matches": parent_matches,
            "is_authoritative_accession_link": False,
            "method": "same registrant CIK + exact report date + exact series ID + original NPORT-P form + earlier filing date",
        },
        "original_vs_amendment": original_vs_amendment,
        "2023_same_series_control": {
            "accession": TARGET_2023,
            "sha256": control_sha,
            "report_date": control["report_date"],
            "filing_date": control["filed_as_of_date"],
            "series_ids": control["series_ids"],
            "short_rows": len(control["short_positions"]),
        },
        "amendment_vs_2023_cross_period": amendment_vs_2023,
        "candidate_summary": {
            "series_identity_states": dict(Counter(x["series_identity_state"] for x in candidate_results)),
            "class_identity_states": dict(Counter(x["class_identity_state"] for x in candidate_results)),
            "report_dates": dict(Counter(x["report_date"] for x in candidate_results)),
        },
        "controls": {
            "amendment_is_trade": False,
            "positions_are_trades": False,
            "parent_link_is_authoritative": False,
            "report_date_is_knowledge_date": False,
            "acceptance_is_first_public_timestamp": False,
            "effective_dated_security_master_complete": False,
            "universe_coverage_measured": False,
            "prevalence_estimated": False,
            "return_test": False,
            "alpha_test": False,
            "bootstrap": False,
            "loo": False,
            "chronological_oos": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "parameters_changed": False,
            "vendor_contact": False,
            "data_purchase": False,
            "email_sent": False,
        },
    }
    (output_dir / "phase314_otter_creek_parent_audit_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "target_amendment_raw.txt").write_bytes(amendment_raw)
    (output_dir / "same_series_2023_raw.txt").write_bytes(control_raw)
    if parent_raw is not None and parent_matches:
        (output_dir / "unique_parent_candidate_raw.txt").write_bytes(parent_raw)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase311-dir", type=Path, default=Path("phase311_input"))
    parser.add_argument("--phase312-dir", type=Path, default=Path("phase312_input"))
    parser.add_argument("--phase310-dir", type=Path, default=Path("phase310_input"))
    parser.add_argument("--output-dir", type=Path, default=Path("phase314_output"))
    args = parser.parse_args()
    result = run_audit(
        args.phase311_dir,
        args.phase312_dir,
        args.phase310_dir,
        args.output_dir,
        os.environ.get("SEC_CONTACT_EMAIL", ""),
    )
    print(json.dumps({
        "phase": 314,
        "status": result["status"],
        "candidate_count": result["candidate_count"],
        "parent_linkage": result["parent_linkage"]["status"],
        "parent_matches": result["parent_linkage"]["match_count"],
        "original_vs_amendment": result["original_vs_amendment"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
