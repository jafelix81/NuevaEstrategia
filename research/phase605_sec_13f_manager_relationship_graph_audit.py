#!/usr/bin/env python3
"""Phase 605 — role-aware SEC Form 13F manager relationship graph audit.

Pure parsing and identity-resolution helpers. No network requests, holdings
returns, alpha calculations, or trading signals are performed here.

The two SEC tables are deliberately kept as different directed edge types:
- OTHERMANAGER: managers reporting holdings FOR the filing manager.
- OTHERMANAGER2: managers INCLUDED IN the filing manager's report.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any


class ManagerGraphError(ValueError):
    """Raised when table structure or identity cannot be interpreted safely."""


def _norm_header(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _index(header: list[str], *names: str) -> int | None:
    positions = {_norm_header(value): i for i, value in enumerate(header)}
    return next((positions[_norm_header(name)] for name in names
                 if _norm_header(name) in positions), None)


def _cell(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return str(row[index] or "").strip()


def normalize_cik(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if not digits or len(digits) > 10:
        raise ManagerGraphError("invalid_cik")
    return digits.zfill(10)


def normalize_file_number(value: Any) -> str | None:
    """Normalize SEC 13F file numbers without using names as identity.

    Accepts common filed variants such as 028-04545, 28-4545 and
    028 - 4545. A missing value remains None; malformed nonblank values
    are rejected rather than fuzzily repaired.
    """
    raw = re.sub(r"\s+", "", str(value or "").strip())
    if not raw:
        return None
    match = re.fullmatch(r"0*28-0*(\d{1,8})", raw)
    if not match:
        raise ManagerGraphError("invalid_form13f_file_number")
    return "028-" + match.group(1).zfill(5)


def _build_filer_index(
    submission_header: list[str],
    submission_rows: list[list[str]],
    coverpage_header: list[str],
    coverpage_rows: list[list[str]],
) -> tuple[dict[str, dict], dict[str, set[str]], dict]:
    si = {
        "accession": _index(submission_header, "ACCESSION_NUMBER"),
        "cik": _index(submission_header, "CIK"),
        "form": _index(submission_header, "SUBMISSIONTYPE", "SUBMISSION_TYPE"),
        "filing_date": _index(submission_header, "FILING_DATE"),
        "report_period": _index(submission_header, "PERIODOFREPORT", "PERIOD_OF_REPORT"),
    }
    ci = {
        "accession": _index(coverpage_header, "ACCESSION_NUMBER"),
        "file_number": _index(coverpage_header, "FORM13FFILENUMBER", "FORM_13F_FILE_NUMBER"),
        "report_type": _index(coverpage_header, "REPORTTYPE", "REPORT_TYPE"),
        "filer_name": _index(coverpage_header, "FILINGMANAGER_NAME", "FILING_MANAGER_NAME"),
    }
    missing_submission = [key for key, value in si.items() if value is None]
    missing_cover = [key for key, value in ci.items() if value is None]
    if missing_submission or missing_cover:
        raise ManagerGraphError(
            "missing_required_schema_fields:"
            + ",".join("submission." + x for x in missing_submission)
            + ","
            + ",".join("coverpage." + x for x in missing_cover)
        )

    submissions: dict[str, dict] = {}
    duplicate_submission_accessions = 0
    for row in submission_rows:
        accession = _cell(row, si["accession"])
        if not accession:
            continue
        if accession in submissions:
            duplicate_submission_accessions += 1
            continue
        cik = normalize_cik(_cell(row, si["cik"]))
        if not cik:
            raise ManagerGraphError("submission_missing_filer_cik:" + accession)
        submissions[accession] = {
            "accession": accession,
            "filer_cik": cik,
            "submission_type": _cell(row, si["form"]).upper(),
            "filing_date": _cell(row, si["filing_date"]),
            "report_period": _cell(row, si["report_period"]),
        }

    coverpages: dict[str, dict] = {}
    duplicate_cover_accessions = 0
    for row in coverpage_rows:
        accession = _cell(row, ci["accession"])
        if not accession:
            continue
        if accession in coverpages:
            duplicate_cover_accessions += 1
            continue
        coverpages[accession] = {
            "form13f_file_number_raw": _cell(row, ci["file_number"]),
            "report_type": _cell(row, ci["report_type"]).upper(),
            "filer_name": _cell(row, ci["filer_name"]),
        }

    missing_cover_accessions = sorted(set(submissions) - set(coverpages))
    extra_cover_accessions = sorted(set(coverpages) - set(submissions))
    filers: dict[str, dict] = {}
    file_number_to_ciks: dict[str, set[str]] = defaultdict(set)
    invalid_filer_file_numbers = 0

    for accession, submission in submissions.items():
        cover = coverpages.get(accession)
        if cover is None:
            continue
        file_number = None
        try:
            file_number = normalize_file_number(cover["form13f_file_number_raw"])
        except ManagerGraphError:
            invalid_filer_file_numbers += 1
        filer = {**submission, **cover, "form13f_file_number": file_number}
        filers[accession] = filer
        if file_number:
            file_number_to_ciks[file_number].add(submission["filer_cik"])

    meta = {
        "submission_rows": len(submission_rows),
        "submission_accessions": len(submissions),
        "coverpage_rows": len(coverpage_rows),
        "coverpage_accessions": len(coverpages),
        "duplicate_submission_accessions": duplicate_submission_accessions,
        "duplicate_coverpage_accessions": duplicate_cover_accessions,
        "missing_coverpage_accessions": len(missing_cover_accessions),
        "extra_coverpage_accessions": len(extra_cover_accessions),
        "invalid_filer_file_numbers": invalid_filer_file_numbers,
        "file_numbers_with_multiple_ciks": sum(
            1 for values in file_number_to_ciks.values() if len(values) > 1
        ),
    }
    return filers, file_number_to_ciks, meta


def _resolve_manager(
    cik_raw: Any,
    file_number_raw: Any,
    file_number_to_ciks: dict[str, set[str]],
) -> dict:
    explicit_cik = None
    file_number = None
    invalid = []
    try:
        explicit_cik = normalize_cik(cik_raw)
    except ManagerGraphError:
        invalid.append("invalid_cik")
    try:
        file_number = normalize_file_number(file_number_raw)
    except ManagerGraphError:
        invalid.append("invalid_form13f_file_number")

    mapped = file_number_to_ciks.get(file_number, set()) if file_number else set()
    if invalid:
        status = "INVALID_IDENTIFIER"
        resolved_cik = None
    elif explicit_cik:
        if len(mapped) == 1 and explicit_cik not in mapped:
            resolved_cik = None
            status = "IDENTITY_CONFLICT"
        else:
            resolved_cik = explicit_cik
            if len(mapped) > 1:
                status = "EXPLICIT_CIK_FILE_NUMBER_AMBIGUOUS"
            else:
                status = "EXPLICIT_CIK"
    elif file_number and len(mapped) == 1:
        resolved_cik = next(iter(mapped))
        status = "RESOLVED_BY_FILE_NUMBER"
    elif file_number and len(mapped) > 1:
        resolved_cik = None
        status = "AMBIGUOUS_FILE_NUMBER"
    elif file_number:
        resolved_cik = None
        status = "UNRESOLVED_FILE_NUMBER"
    else:
        resolved_cik = None
        status = "UNRESOLVED_NO_IDENTIFIER"

    return {
        "resolved_cik": resolved_cik,
        "explicit_cik": explicit_cik,
        "file_number": file_number,
        "file_number_candidates": sorted(mapped),
        "resolution_status": status,
        "name_used_for_identity": False,
    }


def _parse_othermanager(
    header: list[str],
    rows: list[list[str]],
    filers: dict[str, dict],
    file_number_to_ciks: dict[str, set[str]],
) -> tuple[list[dict], dict]:
    ix = {
        "accession": _index(header, "ACCESSION_NUMBER"),
        "key": _index(header, "OTHERMANAGER_SK", "OTHER_MANAGER_SK"),
        "cik": _index(header, "CIK"),
        "file_number": _index(header, "FORM13FFILENUMBER", "FORM_13F_FILE_NUMBER"),
        "name": _index(header, "NAME"),
    }
    missing = [key for key in ("accession", "key", "name") if ix[key] is None]
    if missing:
        raise ManagerGraphError("othermanager_missing_fields:" + ",".join(missing))

    edges = []
    seen = set()
    duplicates = 0
    invalid_keys = 0
    orphans = 0
    missing_names = 0
    for row in rows:
        accession = _cell(row, ix["accession"])
        key = _cell(row, ix["key"])
        name = _cell(row, ix["name"])
        if not accession:
            continue
        if not key.isdigit():
            invalid_keys += 1
            continue
        identity = (accession, key)
        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        if accession not in filers:
            orphans += 1
            continue
        if not name:
            missing_names += 1
        filer = filers[accession]
        target = _resolve_manager(
            _cell(row, ix["cik"]), _cell(row, ix["file_number"]), file_number_to_ciks
        )
        edges.append({
            "accession": accession,
            "report_period": filer["report_period"],
            "filing_date": filer["filing_date"],
            "report_type": filer["report_type"],
            "submission_type": filer["submission_type"],
            "from_filer_cik": filer["filer_cik"],
            "to_reporting_manager_cik": target["resolved_cik"],
            "relationship_type": "FILER_TO_REPORTING_MANAGER",
            "other_manager_sk": key,
            "other_manager_name_as_filed": name,
            **target,
        })
    return edges, {
        "rows": len(rows),
        "edges": len(edges),
        "duplicate_accession_key_rows": duplicates,
        "invalid_key_rows": invalid_keys,
        "orphan_accession_rows": orphans,
        "missing_name_rows": missing_names,
        "schema_ok": True,
    }


def _parse_othermanager2(
    header: list[str],
    rows: list[list[str]],
    filers: dict[str, dict],
    file_number_to_ciks: dict[str, set[str]],
) -> tuple[dict[str, dict[str, dict]], list[dict], dict]:
    ix = {
        "accession": _index(header, "ACCESSION_NUMBER"),
        "sequence": _index(header, "SEQUENCENUMBER", "SEQUENCE_NUMBER"),
        "cik": _index(header, "CIK"),
        "file_number": _index(header, "FORM13FFILENUMBER", "FORM_13F_FILE_NUMBER"),
        "name": _index(header, "NAME"),
    }
    missing = [key for key in ("accession", "sequence", "name") if ix[key] is None]
    if missing:
        raise ManagerGraphError("othermanager2_missing_fields:" + ",".join(missing))

    by_accession: dict[str, dict[str, dict]] = defaultdict(dict)
    edges = []
    seen = set()
    duplicates = 0
    invalid_sequences = 0
    orphans = 0
    missing_names = 0
    for row in rows:
        accession = _cell(row, ix["accession"])
        raw_sequence = _cell(row, ix["sequence"])
        name = _cell(row, ix["name"])
        if not accession:
            continue
        try:
            sequence = int(raw_sequence)
            if sequence < 1:
                raise ValueError
        except ValueError:
            invalid_sequences += 1
            continue
        identity = (accession, sequence)
        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        if accession not in filers:
            orphans += 1
            continue
        if not name:
            missing_names += 1
        filer = filers[accession]
        target = _resolve_manager(
            _cell(row, ix["cik"]), _cell(row, ix["file_number"]), file_number_to_ciks
        )
        record = {
            "accession": accession,
            "sequence_number": sequence,
            "report_period": filer["report_period"],
            "filing_date": filer["filing_date"],
            "report_type": filer["report_type"],
            "submission_type": filer["submission_type"],
            "from_reporting_filer_cik": filer["filer_cik"],
            "to_included_manager_cik": target["resolved_cik"],
            "relationship_type": "REPORTING_FILER_TO_INCLUDED_MANAGER",
            "other_manager_name_as_filed": name,
            **target,
        }
        by_accession[accession][str(sequence)] = record
        edges.append(record)
    return by_accession, edges, {
        "rows": len(rows),
        "edges": len(edges),
        "duplicate_accession_sequence_rows": duplicates,
        "invalid_sequence_rows": invalid_sequences,
        "orphan_accession_rows": orphans,
        "missing_name_rows": missing_names,
        "schema_ok": True,
    }


def _audit_infotable_references(
    header: list[str],
    rows: list[list[str]],
    filers: dict[str, dict],
    included_by_accession: dict[str, dict[str, dict]],
) -> dict:
    accession_ix = _index(header, "ACCESSION_NUMBER")
    sequence_ix = _index(header, "INFOTABLE_SK", "INFOTABLE_SEQUENCE", "SEQUENCE")
    manager_ix = _index(header, "OTHERMANAGER", "OTHER_MANAGER")
    if accession_ix is None or sequence_ix is None or manager_ix is None:
        raise ManagerGraphError("infotable_missing_accession_key_or_othermanager")
    seen_rows = set()
    orphan_rows = 0
    duplicate_rows = 0
    referenced_tokens = 0
    dangling = []
    malformed = []
    resolved = 0
    for row in rows:
        accession = _cell(row, accession_ix)
        if not accession:
            continue
        line_key = _cell(row, sequence_ix)
        if not line_key:
            malformed.append({"accession": accession, "line": None, "token": "<missing INFOTABLE_SK>"})
            continue
        row_key = (accession, line_key)
        if row_key in seen_rows:
            duplicate_rows += 1
        seen_rows.add(row_key)
        if accession not in filers:
            orphan_rows += 1
            continue
        raw = _cell(row, manager_ix).strip()
        if not raw or raw.upper() in {"N/A", "NA", "NONE"}:
            continue
        tokens = [token.strip() for token in raw.split(",")]
        for token in tokens:
            if not token.isdigit() or int(token) < 1:
                malformed.append({"accession": accession, "line": line_key, "token": token})
                continue
            referenced_tokens += 1
            if token in included_by_accession.get(accession, {}):
                resolved += 1
            else:
                dangling.append({"accession": accession, "line": line_key, "sequence": int(token)})
    return {
        "rows": len(rows),
        "duplicate_accession_line_rows": duplicate_rows,
        "orphan_accession_rows": orphan_rows,
        "referenced_sequence_tokens": referenced_tokens,
        "resolved_sequence_tokens": resolved,
        "dangling_sequence_tokens": len(dangling),
        "malformed_sequence_tokens": len(malformed),
        "sample_dangling": dangling[:10],
        "sample_malformed": malformed[:10],
        "schema_ok": True,
    }


def audit_manager_relationship_graph(
    submission_header: list[str],
    submission_rows: list[list[str]],
    coverpage_header: list[str],
    coverpage_rows: list[list[str]],
    othermanager_header: list[str],
    othermanager_rows: list[list[str]],
    othermanager2_header: list[str],
    othermanager2_rows: list[list[str]],
    infotable_header: list[str],
    infotable_rows: list[list[str]],
) -> dict:
    """Build role-specific edges and validate line-to-included-manager links.

    No name-based identity inference is allowed. File-number resolution is
    accepted only when the same bounded sample maps that file number to one
    unique filer CIK. Explicit CIK/file-number conflicts remain visible.
    """
    filers, file_number_to_ciks, filer_meta = _build_filer_index(
        submission_header, submission_rows, coverpage_header, coverpage_rows
    )
    othermanager_edges, othermanager_meta = _parse_othermanager(
        othermanager_header, othermanager_rows, filers, file_number_to_ciks
    )
    included_by_accession, othermanager2_edges, othermanager2_meta = _parse_othermanager2(
        othermanager2_header, othermanager2_rows, filers, file_number_to_ciks
    )
    info_meta = _audit_infotable_references(
        infotable_header, infotable_rows, filers, included_by_accession
    )

    notice_accessions = {
        accession for accession, filer in filers.items()
        if filer["submission_type"] in {"13F-NT", "13F-NT/A"}
        or filer["report_type"] == "13F NOTICE"
    }
    notice_roster_accessions = {
        edge["accession"] for edge in othermanager_edges
        if edge["accession"] in notice_accessions
    }
    notice_without_roster = sorted(notice_accessions - notice_roster_accessions)
    notice_with_holdings_rows = sum(
        1 for row in infotable_rows
        if _cell(row, _index(infotable_header, "ACCESSION_NUMBER")) in notice_accessions
    )

    all_edges = othermanager_edges + othermanager2_edges
    resolution_counts = Counter(edge["resolution_status"] for edge in all_edges)
    identity_conflicts = resolution_counts["IDENTITY_CONFLICT"]
    unresolved = sum(
        resolution_counts[key] for key in (
            "UNRESOLVED_FILE_NUMBER", "UNRESOLVED_NO_IDENTIFIER",
            "AMBIGUOUS_FILE_NUMBER", "EXPLICIT_CIK_FILE_NUMBER_AMBIGUOUS",
            "INVALID_IDENTIFIER",
        )
    )
    report_type_discordance = []
    for accession, filer in filers.items():
        form = filer["submission_type"]
        report_type = filer["report_type"]
        if form in {"13F-NT", "13F-NT/A"} and report_type != "13F NOTICE":
            report_type_discordance.append(accession)
        if form in {"13F-HR", "13F-HR/A"} and report_type == "13F NOTICE":
            report_type_discordance.append(accession)

    duplicate_or_orphan = (
        filer_meta["duplicate_submission_accessions"]
        + filer_meta["duplicate_coverpage_accessions"]
        + othermanager_meta["duplicate_accession_key_rows"]
        + othermanager_meta["invalid_key_rows"]
        + othermanager_meta["orphan_accession_rows"]
        + othermanager_meta["missing_name_rows"]
        + othermanager2_meta["duplicate_accession_sequence_rows"]
        + othermanager2_meta["orphan_accession_rows"]
        + othermanager2_meta["missing_name_rows"]
        + info_meta["duplicate_accession_line_rows"]
        + info_meta["orphan_accession_rows"]
    )
    reference_errors = info_meta["dangling_sequence_tokens"] + info_meta["malformed_sequence_tokens"]
    identity_format_errors = filer_meta["invalid_filer_file_numbers"]
    integrity_ok = (
        duplicate_or_orphan == 0
        and reference_errors == 0
        and identity_conflicts == 0
        and identity_format_errors == 0
        and not report_type_discordance
        and not notice_without_roster
        and notice_with_holdings_rows == 0
    )
    return {
        "phase": 605,
        "status": "PASS_ROLE_AWARE_RELATIONSHIP_INTEGRITY" if integrity_ok
                  else "BLOCKED_RELATIONSHIP_OR_IDENTITY_EXCEPTIONS",
        "signal_eligible": False,
        "schema": {
            "submission_required": ["ACCESSION_NUMBER", "CIK", "SUBMISSIONTYPE", "FILING_DATE", "PERIODOFREPORT"],
            "coverpage_required": ["ACCESSION_NUMBER", "FORM13FFILENUMBER", "REPORTTYPE", "FILINGMANAGER_NAME"],
            "othermanager_required": ["ACCESSION_NUMBER", "OTHERMANAGER_SK", "NAME"],
            "othermanager2_required": ["ACCESSION_NUMBER", "SEQUENCENUMBER", "NAME"],
            "infotable_required": ["ACCESSION_NUMBER", "INFOTABLE_SK", "OTHERMANAGER"],
        },
        "filer_index": filer_meta,
        "othermanager_reporting_for_filer": {
            **othermanager_meta,
            "edges": othermanager_edges,
        },
        "othermanager2_included_in_filing": {
            **othermanager2_meta,
            "edges": othermanager2_edges,
        },
        "infotable_sequence_references": info_meta,
        "notice_controls": {
            "notice_accessions": len(notice_accessions),
            "notice_accessions_with_roster": len(notice_roster_accessions),
            "notice_accessions_without_roster": len(notice_without_roster),
            "sample_notice_without_roster": notice_without_roster[:10],
            "notice_accessions_with_infotable_rows": notice_with_holdings_rows,
        },
        "identity_resolution": {
            "edge_count": len(all_edges),
            "resolution_status_counts": dict(sorted(resolution_counts.items())),
            "unresolved_or_ambiguous_edges": unresolved,
            "identity_complete": unresolved == 0 and identity_conflicts == 0 and filer_meta["file_numbers_with_multiple_ciks"] == 0,
            "identity_conflicts": identity_conflicts,
            "name_based_resolution_used": False,
            "file_number_to_cik_conflict_count": filer_meta["file_numbers_with_multiple_ciks"],
        },
        "report_type_submission_type_discordance_accessions": sorted(set(report_type_discordance)),
        "integrity_controls": {
            "duplicate_or_orphan_rows": duplicate_or_orphan,
            "relationship_reference_errors": reference_errors,
            "identity_format_errors": identity_format_errors,
            "integrity_ok": integrity_ok,
        },
        "interpretation": (
            "Role-aware manager relationship parsing only. OTHERMANAGER and OTHERMANAGER2 "
            "are distinct directed relationships; unresolved identities are not guessed. "
            "13F notices are not zero-holdings signals. No holdings state, alpha, OOS, "
            "bootstrap, LOO, or production eligibility is established."
        ),
    }
