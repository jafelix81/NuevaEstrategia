#!/usr/bin/env python3
"""Fail-closed parser for SEC EDGAR Schedule 13D/G complete-submission identity blocks.

SUBJECT COMPANY and FILED BY identify different roles. The accession prefix
identifies the EDGAR submitting entity and can be a third-party filing agent;
it must not be equated with the FILED BY CIK. The SEC-HEADER ACCESSION NUMBER
is validated separately against the expected accession.
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
    accession_submitter_cik = accession_match.group(1) if accession_match else None

    header = _header_payload(str(header_text or ""))
    blocks = _identity_blocks(header)
    subject_block = blocks.get("SUBJECT COMPANY")
    filed_by_block = blocks.get("FILED BY")

    header_accession = _field(header, "ACCESSION NUMBER")
    subject_name = _field(subject_block, "COMPANY CONFORMED NAME") if subject_block else None
    subject_cik = _normalize_cik(_field(subject_block, "CENTRAL INDEX KEY")) if subject_block else None
    filed_by_name = _field(filed_by_block, "COMPANY CONFORMED NAME") if filed_by_block else None
    filed_by_cik = _normalize_cik(_field(filed_by_block, "CENTRAL INDEX KEY")) if filed_by_block else None
    header_accession_valid = bool(header_accession and ACCESSION_RE.fullmatch(header_accession))

    if subject_block is None:
        status = "NO_SUBJECT_COMPANY_BLOCK"
    elif filed_by_block is None:
        status = "NO_FILED_BY_BLOCK"
    elif not subject_cik:
        status = "MISSING_OR_INVALID_SUBJECT_CIK"
    elif not filed_by_cik:
        status = "MISSING_OR_INVALID_FILED_BY_CIK"
    elif not accession_match:
        status = "INVALID_OR_MISSING_ACCESSION"
    elif not header_accession_valid:
        status = "MISSING_OR_INVALID_HEADER_ACCESSION"
    elif header_accession != accession:
        status = "HEADER_ACCESSION_MISMATCH"
    else:
        status = "VERIFIED_SUBJECT_AND_FILED_BY_CIKS"

    verified = status == "VERIFIED_SUBJECT_AND_FILED_BY_CIKS"
    submitter_matches_filed_by = bool(
        accession_submitter_cik and filed_by_cik and accession_submitter_cik == filed_by_cik
    )
    return {
        "accession": accession or None,
        "header_accession": header_accession,
        "accession_submitter_cik": accession_submitter_cik,
        "accession_matches_header": bool(header_accession_valid and header_accession == accession),
        "accession_submitter_matches_filed_by": submitter_matches_filed_by,
        "subject_issuer_cik": subject_cik,
        "subject_issuer_name": subject_name,
        "filed_by_cik": filed_by_cik,
        "filed_by_entity_name": filed_by_name,
        # Backward-compatible aliases: these identify the FILED BY block, not the EDGAR submitter.
        "filing_cik": filed_by_cik,
        "filing_entity_name": filed_by_name,
        "identity_status": status,
        "subject_issuer_identity_verified": verified,
        "filed_by_identity_verified": verified,
        "ticker": None,
        "ticker_mapping_status": "NOT_ATTEMPTED",
        "signal_eligible": False,
    }
