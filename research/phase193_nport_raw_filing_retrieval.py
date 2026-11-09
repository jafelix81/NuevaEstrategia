#!/usr/bin/env python3
"""Phase 193: SEC N-PORT raw filing, acceptance-time and direct-short reconciliation.

Network access is fail-closed unless SEC_CONTACT_EMAIL is supplied by the
GitHub Actions secret. Raw public filing bytes are staged only as a workflow
artifact; the repository receives metadata, hashes and aggregate row results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

EVIDENCE_PATH = Path(__file__).with_name("phase193_nport_raw_filing_retrieval.json")
ET_ZONE = ZoneInfo("America/New_York")
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024
RETRIES = 3


class RetrievalError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def normalize_accession(value: str) -> str:
    return re.sub(r"[^0-9]", "", str(value))


def local_name(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1].split(":")[-1]


def direct_text(node: ET.Element, name: str) -> str:
    target = name.lower()
    for child in list(node):
        if local_name(child.tag).lower() == target:
            return "".join(child.itertext()).strip()
    return ""


def descendant_text(node: ET.Element, name: str) -> str:
    target = name.lower()
    for child in node.iter():
        if child is not node and local_name(child.tag).lower() == target:
            return "".join(child.itertext()).strip()
    return ""


def field_text(node: ET.Element, name: str) -> str:
    return direct_text(node, name) or descendant_text(node, name)


def parse_decimal(value: str) -> Decimal | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        result = Decimal(raw)
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def parse_submission_header(payload: bytes, expected_accession: str, expected_form: str) -> dict[str, str]:
    text = payload.decode("latin-1", errors="replace")
    fields = {}
    for name in (
        "ACCESSION NUMBER",
        "CONFORMED SUBMISSION TYPE",
        "CONFORMED PERIOD OF REPORT",
        "FILED AS OF DATE",
        "DATE AS OF CHANGE",
        "ACCEPTANCE-DATETIME",
    ):
        match = re.search(r"(?im)^\s*" + re.escape(name) + r"\s*:\s*([^\r\n]+)", text)
        if match:
            fields[name] = match.group(1).strip()

    accession = fields.get("ACCESSION NUMBER", "")
    form = fields.get("CONFORMED SUBMISSION TYPE", "")
    acceptance = fields.get("ACCEPTANCE-DATETIME", "")
    if normalize_accession(accession) != normalize_accession(expected_accession):
        raise ValueError("submission_accession_mismatch")
    if form.upper() != expected_form.upper():
        raise ValueError("submission_form_mismatch")
    if not re.fullmatch(r"\d{14}", acceptance):
        raise ValueError("acceptance_datetime_missing_or_invalid")

    accepted_local = datetime.strptime(acceptance, "%Y%m%d%H%M%S").replace(tzinfo=ET_ZONE)
    fields["acceptance_datetime_et"] = accepted_local.isoformat()
    fields["acceptance_datetime_utc"] = accepted_local.astimezone(timezone.utc).isoformat()
    fields["acceptance_date_matches_filed_date"] = str(fields.get("FILED AS OF DATE", "")) == acceptance[:8]
    fields["header_accession_reconciled"] = "true"
    fields["header_form_reconciled"] = "true"
    return fields


def _identifier_values(node: ET.Element) -> dict[str, str]:
    found: dict[str, str] = {}
    for container in node.iter():
        if local_name(container.tag).lower() != "identifiers":
            continue
        for item in list(container):
            if local_name(item.tag).lower() != "identifier":
                continue
            kind = direct_text(item, "idType").upper()
            value = direct_text(item, "idValue")
            if kind and value:
                found[kind] = value
    return found


def parse_nport_xml(payload: bytes) -> dict[str, object]:
    root = ET.fromstring(payload)
    holdings = [node for node in root.iter() if local_name(node.tag).lower() == "invstorseC".lower()]
    series_ids = sorted({
        "".join(node.itertext()).strip()
        for node in root.iter()
        if local_name(node.tag).lower() == "seriesid" and "".join(node.itertext()).strip()
    })

    counts: Counter[str] = Counter()
    direct_short_rows: list[dict[str, object]] = []
    cusips: set[str] = set()

    for node in holdings:
        payoff = field_text(node, "payoffProfile")
        asset = field_text(node, "assetCat")
        issuer = field_text(node, "issuerCat")
        country = field_text(node, "invCountry")
        units = field_text(node, "units").upper()
        balance_raw = field_text(node, "balance")
        value_raw = field_text(node, "valUSD")
        pct_raw = field_text(node, "pctVal")
        balance = parse_decimal(balance_raw)
        value = parse_decimal(value_raw)
        pct = parse_decimal(pct_raw)

        if payoff.lower() == "short":
            counts["short_payoff_rows"] += 1
        if payoff.lower() == "short" and asset.upper() == "EC":
            counts["short_equity_common_rows"] += 1
        if payoff.lower() == "short" and asset.upper() == "EC" and issuer.upper() == "CORP" and country.upper() == "US":
            counts["short_ec_corp_us_rows"] += 1
            identifiers = _identifier_values(node)
            cusip = field_text(node, "cusip") or identifiers.get("CUSIP", "")
            isin = field_text(node, "isin") or identifiers.get("ISIN", "")
            ticker = field_text(node, "ticker") or field_text(node, "tradingSymbol") or identifiers.get("TICKER", "")
            if cusip:
                cusips.add(cusip)
            sign_ok = (
                units == "NS"
                and balance is not None and balance < 0
                and value is not None and value < 0
                and pct is not None and pct < 0
            )
            counts["direct_short_sign_concordant_rows" if sign_ok else "direct_short_sign_or_unit_mismatch_rows"] += 1
            if len(direct_short_rows) < 250:
                direct_short_rows.append({
                    "cusip": cusip or None,
                    "isin": isin or None,
                    "ticker": ticker or None,
                    "balance": balance_raw or None,
                    "units": units or None,
                    "val_usd": value_raw or None,
                    "pct_net_assets": pct_raw or None,
                    "sign_concordant": sign_ok,
                })

    return {
        "holding_nodes": len(holdings),
        "series_ids": series_ids,
        "distinct_series_id_count": len(series_ids),
        "counts": dict(sorted(counts.items())),
        "direct_short_cusips": sorted(cusips),
        "direct_short_rows_sample": direct_short_rows,
        "direct_short_rows_sample_truncated": counts["short_ec_corp_us_rows"] > len(direct_short_rows),
    }


def parse_index_listing(payload: bytes, accession: str, primary_document: str) -> dict[str, object]:
    data = json.loads(payload.decode("utf-8"))
    directory = data.get("directory", {})
    items = directory.get("item", [])
    if not isinstance(items, list):
        raise ValueError("sec_index_item_list_missing")
    primary = next((x for x in items if str(x.get("name", "")).lower() == primary_document.lower()), None)
    if primary is None:
        raise ValueError("primary_document_not_in_sec_index")
    target = normalize_accession(accession)
    candidates = [
        x for x in items
        if str(x.get("name", "")).lower().endswith(".txt")
        and target in normalize_accession(str(x.get("name", "")))
    ]
    if len(candidates) != 1:
        raise ValueError("complete_submission_text_not_uniquely_resolved")
    return {
        "primary_document_name": primary.get("name"),
        "primary_document_size": primary.get("size"),
        "primary_document_last_modified": primary.get("last-modified"),
        "submission_text_name": candidates[0].get("name"),
        "submission_text_size": candidates[0].get("size"),
        "submission_text_last_modified": candidates[0].get("last-modified"),
        "directory_item_count": len(items),
    }


def _fetch(url: str, user_agent: str) -> tuple[bytes, dict[str, str]]:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "www.sec.gov":
        raise RetrievalError("non_sec_https_url_rejected")
    request = Request(url, headers={
        "User-Agent": user_agent,
        "Accept": "application/json, application/xml, text/xml, text/plain, */*",
        "Accept-Encoding": "identity",
    })
    for attempt in range(RETRIES + 1):
        try:
            with urlopen(request, timeout=45) as response:
                payload = response.read(MAX_FILE_BYTES + 1)
                if len(payload) > MAX_FILE_BYTES:
                    raise RetrievalError("file_size_limit_exceeded")
                headers = {
                    "http_status": str(response.status),
                    "content_type": response.headers.get("Content-Type", ""),
                    "date": response.headers.get("Date", ""),
                    "etag": response.headers.get("ETag", ""),
                    "last_modified": response.headers.get("Last-Modified", ""),
                    "content_length": response.headers.get("Content-Length", ""),
                }
                return payload, headers
        except HTTPError as exc:
            code = f"http_{exc.code}"
            if exc.code in (429, 500, 502, 503, 504) and attempt < RETRIES:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise RetrievalError(code) from None
        except URLError:
            if attempt < RETRIES:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise RetrievalError("url_error") from None
    raise RetrievalError("retry_exhausted")


def _base_url(item: dict[str, str]) -> str:
    accession_path = normalize_accession(item["accession"])
    return f"https://www.sec.gov/Archives/edgar/data/{item['cik']}/{accession_path}/"


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", value)


def blocked_audit(evidence: dict[str, object]) -> dict[str, object]:
    return {
        "phase": 193,
        "audit_as_of_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BLOCKED_MISSING_SEC_CONTACT_EMAIL",
        "source": evidence["source"],
        "accessions_attempted": 0,
        "accessions_total": len(evidence["accessions"]),
        "email_secret_present": False,
        "files_downloaded": 0,
        "raw_xml_sha256_verified": False,
        "submission_sha256_verified": False,
        "acceptance_time_reconciled": False,
        "curated_cusips_reconciled": False,
        "series_ids_present_for_all": False,
        "first_public_receipt_verified": False,
        "strict_pit_admitted": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "production_changed": False,
        "data_purchase": False,
        "vendor_contact": False,
        "f80_frozen": True,
        "decision": "SEC retrieval was not attempted because SEC_CONTACT_EMAIL is not configured. Add an authorized project contact email as a GitHub Actions repository secret, then rerun this workflow. No request was sent and no raw filing bytes were downloaded."
    }


def run_audit(email: str, output_dir: Path, evidence: dict[str, object] | None = None) -> dict[str, object]:
    ev = evidence if evidence is not None else json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    if not email or "@" not in email or any(ch.isspace() for ch in email):
        return blocked_audit(ev)

    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_root = output_dir / "raw"
    results: list[dict[str, object]] = []
    total_bytes = 0
    for item in ev["accessions"]:
        accession = item["accession"]
        base = _base_url(item)
        result: dict[str, object] = {
            "accession": accession,
            "cik": item["cik"],
            "filing_year": item["filing_year"],
            "expected_form": item["form"],
            "files": {},
            "status": "PENDING",
        }
        try:
            index_bytes, index_headers = _fetch(base + "index.json", user_agent)
            total_bytes += len(index_bytes)
            listing = parse_index_listing(index_bytes, accession, item["primary_document"])
            submission_name = str(listing["submission_text_name"])
            primary_name = str(listing["primary_document_name"])
            submission_bytes, submission_headers = _fetch(base + quote(submission_name), user_agent)
            total_bytes += len(submission_bytes)
            primary_bytes, primary_headers = _fetch(base + quote(primary_name), user_agent)
            total_bytes += len(primary_bytes)
            if total_bytes > MAX_TOTAL_BYTES:
                raise RetrievalError("total_download_limit_exceeded")

            header = parse_submission_header(submission_bytes, accession, item["form"])
            parsed = parse_nport_xml(primary_bytes)
            expected_cusips = set(item.get("expected_cusips", []))
            observed_cusips = set(parsed["direct_short_cusips"])
            missing_cusips = sorted(expected_cusips - observed_cusips)
            short_count = int(parsed["counts"].get("short_ec_corp_us_rows", 0))
            min_rows = int(item.get("expected_min_direct_short_rows", 0))
            rows_gate = short_count >= min_rows
            result.update({
                "status": "RAW_RETRIEVED",
                "index_sha256": hashlib.sha256(index_bytes).hexdigest(),
                "submission_sha256": hashlib.sha256(submission_bytes).hexdigest(),
                "primary_xml_sha256": hashlib.sha256(primary_bytes).hexdigest(),
                "index_bytes": len(index_bytes),
                "submission_bytes": len(submission_bytes),
                "primary_xml_bytes": len(primary_bytes),
                "index_response_headers": index_headers,
                "submission_response_headers": submission_headers,
                "primary_xml_response_headers": primary_headers,
                "index_listing": listing,
                "submission_header": header,
                "xml_audit": parsed,
                "expected_min_direct_short_rows": min_rows,
                "expected_row_count_gate_pass": rows_gate,
                "expected_cusips": sorted(expected_cusips),
                "missing_expected_cusips": missing_cusips,
                "expected_cusip_gate_pass": not missing_cusips,
                "series_id_gate_pass": bool(parsed["series_ids"]),
            })
            folder = raw_root / normalize_accession(accession)
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "index.json").write_bytes(index_bytes)
            (folder / _safe_name(submission_name)).write_bytes(submission_bytes)
            (folder / _safe_name(primary_name)).write_bytes(primary_bytes)
            result["raw_files_staged_for_artifact"] = True
        except (RetrievalError, ValueError, ET.ParseError, json.JSONDecodeError) as exc:
            code = exc.code if isinstance(exc, RetrievalError) else str(exc)
            result.update({"status": "RETRIEVAL_OR_PARSE_ERROR", "error_code": code})
        results.append(result)
        time.sleep(0.25)

    complete = [x for x in results if x["status"] == "RAW_RETRIEVED"]
    all_complete = len(complete) == len(ev["accessions"])
    all_acceptance = all(
        x.get("submission_header", {}).get("header_accession_reconciled") == "true"
        and x.get("submission_header", {}).get("header_form_reconciled") == "true"
        and bool(x.get("submission_header", {}).get("acceptance_datetime_utc"))
        for x in complete
    ) and all_complete
    all_cusips = all(x.get("expected_cusip_gate_pass") for x in complete) and all_complete
    all_rows = all(x.get("expected_row_count_gate_pass") for x in complete) and all_complete
    all_series = all(x.get("series_id_gate_pass") for x in complete) and all_complete
    status = (
        "RAW_SAMPLE_RETRIEVED_ACCEPTANCE_RECONCILED"
        if all_complete and all_acceptance and all_cusips and all_rows and all_series
        else "PARTIAL_RETRIEVAL_OR_RECONCILIATION"
        if complete
        else "RETRIEVAL_FAILED"
    )
    return {
        "phase": 193,
        "audit_as_of_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source": ev["source"],
        "accessions_attempted": len(results),
        "accessions_total": len(ev["accessions"]),
        "email_secret_present": True,
        "files_downloaded": len(complete) * 3,
        "complete_accessions": len(complete),
        "total_download_bytes": total_bytes,
        "raw_xml_sha256_verified": all_complete,
        "submission_sha256_verified": all_complete,
        "acceptance_time_reconciled": all_acceptance,
        "curated_cusips_reconciled": all_cusips,
        "expected_row_count_gates_passed": all_rows,
        "series_ids_present_for_all": all_series,
        "first_public_receipt_verified": False,
        "strict_pit_admitted": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "production_changed": False,
        "data_purchase": False,
        "vendor_contact": False,
        "raw_files_staged_for_artifact": any(x.get("raw_files_staged_for_artifact") for x in results),
        "raw_files_persisted_in_repository": False,
        "representative_sample": False,
        "prevalence_estimated": False,
        "amendment_lineage_in_scope": False,
        "f80_frozen": True,
        "accession_results": results,
        "decision": "Full filing bytes, hashes, SEC-HEADER acceptance timestamps and direct-short row counts are audited only for the purposive five-accession sample. Acceptance is not first public receipt; no same-session use is authorized. No amendments, historical listing crosswalk, broad universe or alpha test are admitted."
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase193_output")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    email = os.environ.get("SEC_CONTACT_EMAIL", "").strip()
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    summary = run_audit(email, output_dir, evidence)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase193_nport_raw_filing_audit.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
