"""Extract the filed Schedule 13D/13G XML from an EDGAR complete-submission text file.

The SEC complete-submission .txt preserves the original <DOCUMENT>/<TEXT>/<XML>
payload and the SEC-HEADER's separate SUBJECT COMPANY and FILED BY identities.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from zoneinfo import ZoneInfo


def normalize_cik(value: str) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(10) if digits and len(digits) <= 10 else digits


def normalize_acceptance_datetime(value: str, source_timezone: str = "UTC") -> str:
    """Return YYYYMMDDHHMMSS in UTC.

    SEC-HEADER ACCEPTANCE-DATETIME is an Eastern wall-clock timestamp without
    an offset. submissions[].acceptanceDateTime is ISO-8601 UTC. Callers must
    pass America/New_York for the former; ISO timestamps retain their offset.
    """
    raw = str(value or "").strip()
    if not raw:
        return ""
    if re.fullmatch(r"\d{14}", raw):
        local = datetime.strptime(raw, "%Y%m%d%H%M%S").replace(tzinfo=ZoneInfo(source_timezone))
        return local.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(source_timezone))
    return parsed.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")


def _first(pattern: str, text: str) -> str:
    match = re.search(pattern, text or "", flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def _header_identity(header: str, label: str, next_label: str | None) -> tuple[str, str]:
    start = re.search(rf"{re.escape(label)}\s*:", header, flags=re.IGNORECASE)
    if not start:
        return "", ""
    end = len(header)
    if next_label:
        next_match = re.search(rf"{re.escape(next_label)}\s*:", header[start.end():], flags=re.IGNORECASE)
        if next_match:
            end = start.end() + next_match.start()
    block = header[start.end():end]
    cik = normalize_cik(_first(r"CENTRAL INDEX KEY:\s*(\d{1,10})", block))
    name = _first(r"COMPANY CONFORMED NAME:\s*([^\r\n]+)", block)
    return cik, name


def _parse_sec_header(text: str) -> dict[str, str]:
    match = re.search(r"<SEC-HEADER>\s*(.*?)\s*</SEC-HEADER>", text, flags=re.IGNORECASE | re.DOTALL)
    header = match.group(1) if match else ""
    subject_cik, subject_name = _header_identity(header, "SUBJECT COMPANY", "FILED BY")
    filer_cik, filer_name = _header_identity(header, "FILED BY", None)
    acceptance = _first(r"<ACCEPTANCE-DATETIME>\s*(\d{14})", text)
    filed_raw = _first(r"FILED AS OF DATE:\s*(\d{8})", header)
    filed_date = f"{filed_raw[:4]}-{filed_raw[4:6]}-{filed_raw[6:8]}" if len(filed_raw) == 8 else ""
    return {
        "subject_cik": subject_cik,
        "subject_name": subject_name,
        "filer_cik": filer_cik,
        "filer_name": filer_name,
        "form": _first(r"CONFORMED SUBMISSION TYPE:\s*([^\r\n]+)", header).upper(),
        "filing_date": filed_date,
        "acceptance_datetime": acceptance,
        "accession": _first(r"ACCESSION NUMBER:\s*([0-9-]+)", header),
        "header_present": "true" if header else "false",
    }


def extract_primary_doc_xml(raw: bytes | str) -> dict:
    """Return the primary_doc.xml payload and SEC header identity from a .txt filing."""
    if isinstance(raw, bytes):
        text = raw.decode("utf-8-sig", errors="replace")
    else:
        text = str(raw or "").lstrip("\ufeff")

    header = _parse_sec_header(text)
    documents = re.finditer(r"<DOCUMENT>\s*(.*?)\s*</DOCUMENT>", text, flags=re.IGNORECASE | re.DOTALL)
    for document_match in documents:
        block = document_match.group(1)
        filename = _first(r"<FILENAME>\s*([^\r\n<]+)", block)
        if PurePosixPath(filename.replace("\\", "/")).name.lower() != "primary_doc.xml":
            continue

        text_match = re.search(r"<TEXT>\s*(.*?)\s*</TEXT>", block, flags=re.IGNORECASE | re.DOTALL)
        if not text_match:
            continue
        text_block = text_match.group(1)
        xml_match = re.search(r"<XML>\s*(.*?)\s*</XML>", text_block, flags=re.IGNORECASE | re.DOTALL)
        if xml_match:
            xml_text = xml_match.group(1).strip()
        else:
            candidate = text_block.strip()
            if not (candidate.startswith("<?xml") or "<edgarSubmission" in candidate):
                continue
            xml_text = candidate

        if not xml_text:
            continue
        return {
            **header,
            "xml_bytes": xml_text.encode("utf-8"),
            "document_filename": filename.strip(),
            "extraction_method": "complete_submission_txt_primary_doc_xml",
        }

    raise ValueError("complete submission text contains no primary_doc.xml XML payload")
