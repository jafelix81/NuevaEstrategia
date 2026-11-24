#!/usr/bin/env python3
"""Fail-closed parser for SEC EDGAR Schedule 13D/G index-header identity blocks.

The SEC index header separates SUBJECT COMPANY from FILED BY. Never infer the
subject issuer from the accession prefix, the queried submissions CIK, or a
ticker mapping.
"""
from __future__ import annotations

import re
from typing import Any

ACCESSION_RE = re.compile(r"^(\d{10})-\d{2}-\d{6}$")
# Header block markers and field values are single-line records. Do not use
# \s here: it includes newlines and can consume the next field when a value is blank.
BLOCK_RE = re.compile(r"^[ \t]*(SUBJECT COMPANY|FILED BY)[ \t]*:[ \t]*\r?$", re.I | re.M)


def _normalize_cik(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value.isdigit() or len(value) > 10:
        return None
    return value.zfill(10)


def _header_payload(text: str) -> str:
    match = re.search(r"<SEC-HEADER>(.*?)</SEC-HEADER>", text, re.I | re.S)
    return match.group(1) if match else text


def _identity_blocks(header: str) -> dict[str, str]:
    markers = list(BLOCK_RE.finditer(header))
    blocks: dict[str, str] = {}
    for index, marker in enumerate(markers):
        label = marker.group(1).upper()
        if label in blocks:
            # Duplicate identity blocks are ambiguous; do not silently choose one.
            blocks[label] = ""
            continue
        end = markers[index + 1].start() if index + 1 < len(markers) else len(header)
        blocks[label] = header[marker.end():end]
    return blocks


def _field(block: str, field_name: str) -> str | None:
    # A blank value must remain blank; never consume the next header line.
    pattern = rf"^[ \t]*{re.escape(field_name)}[ \t]*:[ \t]*([^\r\n]*?)[ \t]*\r?$"
    match = re.search(pattern, block, re.I | re.M)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def parse_subject_filer_identity(header_text: str, accession: str) -> dict[str, Any]:
    accession = str(accession or "").strip()
    accession_match = ACCESSION_RE.fullmatch(accession)
    accession_filer_cik = accession_match.group(1) if accession_match else None

    header = _header_payload(str(header_text or ""))
    blocks = _identity_blocks(header)
    subject_block = blocks.get("SUBJECT COMPANY")
    filer_block = blocks.get("FILED BY")

    subject_name = _field(subject_block, "COMPANY CONFORMED NAME") if subject_block else None
    subject_cik = _normalize_cik(_field(subject_block, "CENTRAL INDEX KEY")) if subject_block else None
    filer_name = _field(filer_block, "COMPANY CONFORMED NAME") if filer_block else None
    filer_cik = _normalize_cik(_field(filer_block, "CENTRAL INDEX KEY")) if filer_block else None

    if subject_block is None:
        status = "NO_SUBJECT_COMPANY_BLOCK"
    elif filer_block is None:
        status = "NO_FILED_BY_BLOCK"
    elif not subject_cik:
        status = "MISSING_OR_INVALID_SUBJECT_CIK"
    elif not filer_cik:
        status = "MISSING_OR_INVALID_FILER_CIK"
    elif not accession_filer_cik:
        status = "INVALID_OR_MISSING_ACCESSION"
    elif filer_cik != accession_filer_cik:
        status = "ACCESSION_HEADER_FILER_MISMATCH"
    else:
        status = "VERIFIED_SUBJECT_AND_FILER_CIKS"

    verified = status == "VERIFIED_SUBJECT_AND_FILER_CIKS"
    return {
        "accession": accession or None,
        "accession_filer_cik": accession_filer_cik,
        "subject_issuer_cik": subject_cik,
        "subject_issuer_name": subject_name,
        "filing_cik": filer_cik,
        "filing_entity_name": filer_name,
        "identity_status": status,
        "subject_issuer_identity_verified": verified,
        "ticker": None,
        "ticker_mapping_status": "NOT_ATTEMPTED",
        "signal_eligible": False,
    }
