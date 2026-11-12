#!/usr/bin/env python3
"""Phase 312: retrieve and reconcile the deterministic 56-filing N-PORT QA sample.

Raw complete-submission bytes are written and SHA-256 hashed before semantic
parsing. This is a parser/coverage gate, not a representative prevalence sample
or a return/alpha test.
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
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import requests

SEC_ARCHIVES = "https://www.sec.gov/Archives"
DATA_FORMS = {"NPORT-P", "NPORT-P/A"}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def all_text(root: ET.Element, name: str) -> list[str]:
    return [
        (element.text or "").strip()
        for element in root.iter()
        if local_name(element.tag) == name and (element.text or "").strip()
    ]


def first_text(root: ET.Element, name: str) -> str | None:
    values = all_text(root, name)
    return values[0] if values else None


def decimal_value(value: str | None) -> Decimal | None:
    if value is None or not str(value).strip():
        return None
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def unique_ordered(values: list[str]) -> list[str]:
    out = []
    seen = set()
    for value in values:
        value = value.strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def extract_primary_xml(submission_text: str, expected_form: str) -> str:
    blocks = re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>", submission_text, flags=re.I | re.S)
    for block in blocks:
        type_match = re.search(r"<TYPE>\s*([^\r\n<]+)", block, flags=re.I)
        if not type_match or type_match.group(1).strip().upper() != expected_form.upper():
            continue
        xml_match = re.search(r"<XML>\s*(.*?)\s*</XML>", block, flags=re.I | re.S)
        if xml_match:
            return xml_match.group(1).strip()
        text_match = re.search(r"<TEXT>\s*(.*?)\s*</TEXT>", block, flags=re.I | re.S)
        if text_match:
            payload = text_match.group(1).strip()
            if payload.startswith("<XML>"):
                payload = re.sub(r"^<XML>\s*|\s*</XML>$", "", payload, flags=re.I | re.S)
            return payload
    raise ValueError("primary_nport_xml_document_not_found")


def _direct_children(element: ET.Element) -> dict[str, str]:
    result = {}
    for child in list(element):
        name = local_name(child.tag)
        if name == "identifiers":
            continue
        result[name] = (child.text or "").strip()
    return result


def _identifier_children(element: ET.Element) -> dict[str, str]:
    result = {}
    for child in list(element):
        if local_name(child.tag) == "identifiers":
            for identifier in list(child):
                result[local_name(identifier.tag)] = (identifier.text or "").strip()
    return result


def parse_holding_rows(root: ET.Element) -> tuple[list[dict[str, Any]], int]:
    candidates: list[dict[str, Any]] = []
    total_rows = 0
    for element in root.iter():
        if local_name(element.tag) != "invstOrSec":
            continue
        total_rows += 1
        fields = _direct_children(element)
        identifiers = _identifier_children(element)
        row = {
            "issuer_name": fields.get("name", ""),
            "issue_title": fields.get("title", ""),
            "cusip": fields.get("cusip", ""),
            "isin": identifiers.get("isin", ""),
            "ticker": identifiers.get("ticker", ""),
            "balance": fields.get("balance", ""),
            "units": fields.get("units", ""),
            "currency_value_usd": fields.get("valUSD", ""),
            "percentage_nav": fields.get("pctVal", ""),
            "payoff_profile": fields.get("payoffProfile", ""),
            "asset_category": fields.get("assetCat", ""),
            "issuer_type": fields.get("issuerCat", ""),
            "investment_country": fields.get("invCountry", ""),
        }
        category_match = (
            row["payoff_profile"].strip().lower() == "short"
            and row["asset_category"].strip().upper() == "EC"
            and row["issuer_type"].strip().upper() == "CORP"
            and row["investment_country"].strip().upper() == "US"
            and row["units"].strip().upper() == "NS"
        )
        if not category_match:
            continue
        balance = decimal_value(row["balance"])
        value = decimal_value(row["currency_value_usd"])
        pct = decimal_value(row["percentage_nav"])
        sign_concordant = (
            balance is not None and value is not None and pct is not None
            and balance < 0 and value < 0 and pct < 0
        )
        row["category_match"] = True
        row["sign_concordant"] = sign_concordant
        candidates.append(row)
    return candidates, total_rows


def _series_state(header_ids: list[str], xml_ids: list[str]) -> str:
    h, x = set(header_ids), set(xml_ids)
    if not h and not x:
        return "MISSING_BOTH"
    if h and not x:
        return "HEADER_ONLY"
    if x and not h:
        return "XML_ONLY"
    if h == x:
        return "MATCH"
    return "MISMATCH"


def parse_submission(raw_bytes: bytes, expected: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    text = raw_bytes.decode("utf-8", errors="replace")
    accession_match = re.search(r"ACCESSION NUMBER:\s*(\d{10}-\d{2}-\d{6})", text, flags=re.I)
    form_match = re.search(r"CONFORMED SUBMISSION TYPE:\s*([A-Z0-9/-]+)", text, flags=re.I)
    cik_match = re.search(r"CENTRAL INDEX KEY:\s*(\d{1,10})", text, flags=re.I)
    filed_match = re.search(r"FILED AS OF DATE:\s*(\d{8})", text, flags=re.I)
    period_match = re.search(r"CONFORMED PERIOD OF REPORT:\s*(\d{8})", text, flags=re.I)
    acceptance_match = re.search(r"<ACCEPTANCE-DATETIME>\s*(\d{14})", text, flags=re.I)

    required = {
        "accession": accession_match,
        "form": form_match,
        "registrant_cik": cik_match,
        "filed_as_of_date": filed_match,
        "acceptance_datetime": acceptance_match,
    }
    missing = [key for key, match in required.items() if match is None]
    if missing:
        raise ValueError("submission_header_fields_missing:" + ",".join(missing))

    header_accession = accession_match.group(1)
    header_form = form_match.group(1).strip().upper()
    header_cik = cik_match.group(1).zfill(10)
    filed_as_of = filed_match.group(1)
    acceptance = acceptance_match.group(1)
    expected_accession = expected["accession"]
    expected_cik = expected["cik"].zfill(10)
    expected_form = expected["form_type"].upper()
    expected_filing_date = expected["filing_date"].replace("-", "")

    xml_text = extract_primary_xml(text, expected_form)
    root = ET.fromstring(xml_text)
    xml_submission_type = (first_text(root, "submissionType") or "").upper()
    xml_reg_cik = (first_text(root, "regCik") or "").zfill(10)
    xml_report_date = first_text(root, "repPdDate")
    xml_period_end = first_text(root, "repPdEnd")

    series_header = unique_ordered(re.findall(r"<SERIES-ID>\s*([^<\s]+)\s*</SERIES-ID>", text, flags=re.I))
    class_header = unique_ordered(re.findall(r"<CLASS-CONTRACT-ID>\s*([^<\s]+)\s*</CLASS-CONTRACT-ID>", text, flags=re.I))
    series_xml = unique_ordered(all_text(root, "seriesId"))
    class_xml = unique_ordered(all_text(root, "classId"))
    series_ids = unique_ordered(series_header + series_xml)
    class_ids = unique_ordered(class_header + class_xml)
    series_names = unique_ordered(re.findall(r"<SERIES-NAME>\s*([^<]+?)\s*</SERIES-NAME>", text, flags=re.I) + all_text(root, "seriesName"))

    short_rows, holding_rows = parse_holding_rows(root)
    series_state = _series_state(series_header, series_xml)
    class_state = _series_state(class_header, class_xml)

    meta = {
        "accession": expected_accession,
        "registrant_cik": expected_cik,
        "company_name": expected.get("company_name", ""),
        "form_type": expected_form,
        "master_index_filing_date": expected["filing_date"],
        "master_index_filename": expected["filename"],
        "raw_bytes": len(raw_bytes),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "xml_bytes": len(xml_text.encode("utf-8")),
        "xml_sha256": hashlib.sha256(xml_text.encode("utf-8")).hexdigest(),
        "header_accession": header_accession,
        "header_accession_match": header_accession == expected_accession,
        "header_form": header_form,
        "header_form_match": header_form == expected_form,
        "header_registrant_cik": header_cik,
        "header_cik_match": header_cik == expected_cik,
        "filed_as_of_date": filed_as_of,
        "filed_date_match": filed_as_of == expected_filing_date,
        "acceptance_datetime_et": acceptance,
        "acceptance_date_matches_filed_date": acceptance[:8] == filed_as_of,
        "conformed_period_of_report": period_match.group(1) if period_match else None,
        "xml_submission_type": xml_submission_type,
        "xml_submission_type_match": xml_submission_type == expected_form,
        "xml_reg_cik": xml_reg_cik,
        "xml_reg_cik_match": xml_reg_cik == expected_cik,
        "xml_report_date": xml_report_date,
        "report_date_matches_header_period": bool(
            xml_report_date and period_match and xml_report_date.replace("-", "") == period_match.group(1)
        ),
        "xml_period_end": xml_period_end,
        "series_ids_header": series_header,
        "series_ids_xml": series_xml,
        "series_ids": series_ids,
        "series_identity_state": series_state,
        "class_ids_header": class_header,
        "class_ids_xml": class_xml,
        "class_ids": class_ids,
        "class_identity_state": class_state,
        "series_names": series_names,
        "total_assets": first_text(root, "totAssets"),
        "net_assets": first_text(root, "netAssets"),
        "holding_rows_total": holding_rows,
        "short_category_rows": len(short_rows),
        "short_sign_concordant_rows": sum(1 for row in short_rows if row["sign_concordant"]),
        "short_sign_nonconcordant_rows": sum(1 for row in short_rows if not row["sign_concordant"]),
        "short_rows_with_cusip": sum(1 for row in short_rows if row["cusip"]),
        "short_rows_with_isin": sum(1 for row in short_rows if row["isin"]),
        "short_rows_with_ticker": sum(1 for row in short_rows if row["ticker"]),
        "core_reconciliation_pass": all([
            header_accession == expected_accession,
            header_form == expected_form,
            header_cik == expected_cik,
            filed_as_of == expected_filing_date,
            xml_submission_type == expected_form,
            xml_reg_cik == expected_cik,
        ]),
        "parse_status": "PARSED",
    }
    return meta, short_rows


def read_sample(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 56:
        raise ValueError(f"phase311_sample_must_contain_56_rows:{len(rows)}")
    if any(row["form_type"] not in DATA_FORMS for row in rows):
        raise ValueError("phase311_sample_contains_non_data_form")
    if len({row["accession"] for row in rows}) != 56:
        raise ValueError("phase311_sample_accessions_not_unique")
    return rows


def download_submission(session: requests.Session, candidate: dict[str, str]) -> tuple[bytes, str, int, str]:
    url = f"{SEC_ARCHIVES}/{candidate['filename'].lstrip('/')}"
    last_error = None
    for attempt in range(5):
        try:
            response = session.get(url, timeout=(20, 120))
            response.raise_for_status()
            payload = response.content
            if len(payload) < 1000:
                raise RuntimeError(f"submission_too_small:{len(payload)}")
            return payload, url, response.status_code, response.headers.get("Content-Type", "")
        except Exception as exc:
            last_error = f"{type(exc).__name__}:{exc}"
            if attempt < 4:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"download_failed:{candidate['accession']}:{last_error}")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_audit(input_dir: Path, output_dir: Path, contact_email: str) -> dict[str, Any]:
    if not contact_email or "@" not in contact_email:
        raise RuntimeError("SEC_CONTACT_EMAIL_secret_missing_or_invalid")
    candidates = read_sample(input_dir / "nport_stratified_sample_candidates.csv")
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": f"NuevaEstrategia quantitative research contact {contact_email}",
        "Accept": "text/plain,application/octet-stream,*/*",
        "Accept-Encoding": "gzip, deflate",
    })

    filings: list[dict[str, Any]] = []
    short_rows_all: list[dict[str, Any]] = []
    download_failures = []
    parse_failures = []

    for index, candidate in enumerate(candidates):
        accession_compact = candidate["accession"].replace("-", "")
        raw_path = raw_dir / f"{accession_compact}.txt"
        try:
            payload, url, status, content_type = download_submission(session, candidate)
        except Exception as exc:
            download_failures.append({"accession": candidate["accession"], "error": str(exc)})
            filings.append({
                "accession": candidate["accession"],
                "form_type": candidate["form_type"],
                "master_index_filing_date": candidate["filing_date"],
                "parse_status": "DOWNLOAD_FAILED",
                "error": str(exc),
            })
            continue

        # Persist and hash the complete submission before parsing any SGML/XML.
        raw_path.write_bytes(payload)
        raw_sha256 = hashlib.sha256(payload).hexdigest()
        try:
            meta, short_rows = parse_submission(payload, candidate)
            meta.update({
                "source_url": url,
                "http_status": status,
                "content_type": content_type,
                "raw_file": str(raw_path.relative_to(output_dir)),
                "raw_sha256": raw_sha256,
            })
            for row_index, row in enumerate(short_rows, start=1):
                short_rows_all.append({
                    "accession": candidate["accession"],
                    "registrant_cik": candidate["cik"],
                    "form_type": candidate["form_type"],
                    "filing_date": candidate["filing_date"],
                    "acceptance_datetime_et": meta["acceptance_datetime_et"],
                    "report_date": meta["xml_report_date"],
                    "series_ids": ";".join(meta["series_ids"]),
                    "series_identity_state": meta["series_identity_state"],
                    "row_number_within_short_candidates": row_index,
                    **row,
                })
            filings.append(meta)
        except Exception as exc:
            parse_failures.append({"accession": candidate["accession"], "error": str(exc), "raw_sha256": raw_sha256})
            filings.append({
                "accession": candidate["accession"],
                "registrant_cik": candidate["cik"],
                "form_type": candidate["form_type"],
                "master_index_filing_date": candidate["filing_date"],
                "raw_bytes": len(payload),
                "raw_sha256": raw_sha256,
                "raw_file": str(raw_path.relative_to(output_dir)),
                "source_url": url,
                "http_status": status,
                "content_type": content_type,
                "parse_status": "PARSE_FAILED",
                "error": str(exc),
            })
        print(
            f"{index + 1}/{len(candidates)} {candidate['accession']} "
            f"{candidate['form_type']} status={filings[-1].get('parse_status','PARSED')} "
            f"short={filings[-1].get('short_sign_concordant_rows','NA')}",
            flush=True,
        )
        if index + 1 < len(candidates):
            time.sleep(0.25)

    parsed = [x for x in filings if x.get("parse_status") == "PARSED"]
    core_pass = [x for x in parsed if x.get("core_reconciliation_pass")]
    series_states = Counter(x.get("series_identity_state", "UNKNOWN") for x in parsed)
    form_counts = Counter(x.get("form_type") for x in filings)
    sign_rows = [x for x in short_rows_all if x.get("sign_concordant")]
    unique_cusips = sorted({x["cusip"] for x in sign_rows if x.get("cusip")})
    unique_isins = sorted({x["isin"] for x in sign_rows if x.get("isin")})
    unique_tickers = sorted({x["ticker"] for x in sign_rows if x.get("ticker")})

    status = (
        "PASS_RAW_SAMPLE_CORE_RECONCILIATION"
        if len(parsed) == 56 and len(core_pass) == 56 and not download_failures
        else "PARTIAL_QUARANTINED"
    )
    result = {
        "phase": 312,
        "audit_started_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "sample": {
            "expected_candidates": 56,
            "nport_p_candidates": sum(1 for x in candidates if x["form_type"] == "NPORT-P"),
            "nport_p_a_candidates": sum(1 for x in candidates if x["form_type"] == "NPORT-P/A"),
            "distinct_registrant_ciks": len({x["cik"] for x in candidates}),
            "selection_design": "Phase 311 deterministic SHA-256 minimum per quarter and data-bearing form; not representative",
        },
        "retrieval": {
            "raw_files_downloaded": len(filings) - len(download_failures),
            "raw_files_expected": 56,
            "download_failures": download_failures,
            "parse_failures": parse_failures,
            "all_raw_bytes_hashed_before_parse": True,
        },
        "reconciliation": {
            "parsed_filings": len(parsed),
            "core_reconciled_filings": len(core_pass),
            "header_accession_matches": sum(1 for x in parsed if x.get("header_accession_match")),
            "header_form_matches": sum(1 for x in parsed if x.get("header_form_match")),
            "header_cik_matches": sum(1 for x in parsed if x.get("header_cik_match")),
            "filed_date_matches": sum(1 for x in parsed if x.get("filed_date_match")),
            "xml_submission_type_matches": sum(1 for x in parsed if x.get("xml_submission_type_match")),
            "xml_reg_cik_matches": sum(1 for x in parsed if x.get("xml_reg_cik_match")),
            "acceptance_date_matches_filed_date": sum(1 for x in parsed if x.get("acceptance_date_matches_filed_date")),
            "report_date_matches_header_period": sum(1 for x in parsed if x.get("report_date_matches_header_period")),
            "series_identity_states": dict(series_states),
            "series_ids_present": sum(1 for x in parsed if x.get("series_ids")),
            "class_ids_present": sum(1 for x in parsed if x.get("class_ids")),
        },
        "holdings": {
            "total_investment_rows": sum(int(x.get("holding_rows_total", 0)) for x in parsed),
            "narrow_short_category_rows": sum(int(x.get("short_category_rows", 0)) for x in parsed),
            "sign_concordant_short_rows": len(sign_rows),
            "nonconcordant_short_category_rows": sum(int(x.get("short_sign_nonconcordant_rows", 0)) for x in parsed),
            "sign_concordant_rows_with_cusip": sum(1 for x in sign_rows if x.get("cusip")),
            "sign_concordant_rows_with_isin": sum(1 for x in sign_rows if x.get("isin")),
            "sign_concordant_rows_with_ticker": sum(1 for x in sign_rows if x.get("ticker")),
            "unique_cusips": len(unique_cusips),
            "unique_isins": len(unique_isins),
            "unique_tickers": len(unique_tickers),
            "short_filter": {
                "payoff_profile": "Short",
                "asset_category": "EC",
                "issuer_type": "CORP",
                "investment_country": "US",
                "units": "NS",
                "sign_concordance": "balance < 0, currency value < 0, percentage of NAV < 0",
                "title_text_is_not_a_filter": True,
            },
        },
        "filing_form_counts": dict(form_counts),
        "filings": filings,
        "controls": {
            "nt_nport_p_not_sampled_as_holdings": True,
            "amendments_kept_as_separate_accessions": True,
            "amendment_parent_linking_attempted": False,
            "fund_position_interpreted_as_trade": False,
            "acceptance_treated_as_first_public_timestamp": False,
            "first_public_timestamp_admitted": False,
            "effective_dated_security_master_complete": False,
            "f80_universe_coverage_measured": False,
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
            "data_purchase": False,
            "vendor_contact": False,
            "email_sent": False,
        },
        "decision": (
            "Raw sample and schema reconciliation only. Preserve each NPORT-P/A as a separate "
            "vintage. Do not treat a reported short position as an executed trade or informed "
            "signal. Next gates: amendment lineage, effective-dated CUSIP/ISIN security identity, "
            "fund/series continuity, F80 universe coverage and conservative public-availability "
            "clock. No returns or alpha tests are authorized."
        ),
    }

    filing_fields = [
        "accession", "registrant_cik", "company_name", "form_type", "master_index_filing_date",
        "header_accession", "header_accession_match", "header_form", "header_form_match",
        "header_registrant_cik", "header_cik_match", "filed_as_of_date", "filed_date_match",
        "acceptance_datetime_et", "acceptance_date_matches_filed_date", "conformed_period_of_report",
        "xml_submission_type", "xml_submission_type_match", "xml_reg_cik", "xml_reg_cik_match",
        "xml_report_date", "report_date_matches_header_period", "xml_period_end", "series_ids_header",
        "series_ids_xml", "series_ids", "series_identity_state", "class_ids_header", "class_ids_xml",
        "class_ids", "class_identity_state", "series_names", "total_assets", "net_assets",
        "holding_rows_total", "short_category_rows", "short_sign_concordant_rows",
        "short_sign_nonconcordant_rows", "short_rows_with_cusip", "short_rows_with_isin",
        "short_rows_with_ticker", "core_reconciliation_pass", "raw_bytes", "raw_sha256",
        "xml_bytes", "xml_sha256", "raw_file", "source_url", "http_status", "content_type",
        "parse_status", "error",
    ]
    short_fields = [
        "accession", "registrant_cik", "form_type", "filing_date", "acceptance_datetime_et",
        "report_date", "series_ids", "series_identity_state", "row_number_within_short_candidates",
        "issuer_name", "issue_title", "cusip", "isin", "ticker", "balance", "units",
        "currency_value_usd", "percentage_nav", "payoff_profile", "asset_category", "issuer_type",
        "investment_country", "category_match", "sign_concordant",
    ]
    write_csv(output_dir / "nport_sample_filing_reconciliation.csv", filings, filing_fields)
    write_csv(output_dir / "nport_short_candidate_rows.csv", short_rows_all, short_fields)
    (output_dir / "phase312_nport_raw_sample_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("phase311_input"))
    parser.add_argument("--output-dir", type=Path, default=Path("phase312_output"))
    args = parser.parse_args()
    result = run_audit(args.input_dir, args.output_dir, os.environ.get("SEC_CONTACT_EMAIL", ""))
    print(json.dumps({
        "phase": 312,
        "status": result["status"],
        "raw_files_downloaded": result["retrieval"]["raw_files_downloaded"],
        "parsed_filings": result["reconciliation"]["parsed_filings"],
        "core_reconciled_filings": result["reconciliation"]["core_reconciled_filings"],
        "sign_concordant_short_rows": result["holdings"]["sign_concordant_short_rows"],
        "output_dir": str(args.output_dir),
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
