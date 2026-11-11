"""Phase 283: offline SEC daily form-index parser and accession ledger."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

HEADER = ["CIK", "Company Name", "Form Type", "Date Filed", "Filename"]
INDEX_NAME_RE = re.compile(r"(?:^|/)form\.(\d{8})\.idx$", re.IGNORECASE)
FILING_PATH_RE = re.compile(
    r"(?:^|/)edgar/data/(?P<path_cik>\d+)/(?P<accession>\d{18})\.txt$",
    re.IGNORECASE,
)
FULL_SESSION_SECONDS = 6 * 60 * 60 + 30 * 60


def _iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"invalid ISO date: {value!r}") from exc


def _aware_datetime(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid ISO datetime: {value!r}") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("session open/close must include an explicit UTC offset")
    return result


def _accession_from_path(path: str) -> tuple[str, str] | None:
    match = FILING_PATH_RE.search(path.strip())
    if not match:
        return None
    digits = match.group("accession")
    accession = f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"
    return accession, match.group("path_cik")


def parse_daily_form_index(raw: bytes, index_filename: str) -> dict[str, Any]:
    """Parse Form 4/4-A rows; quarantine invalid rows without retaining raw text."""
    name_match = INDEX_NAME_RE.search(index_filename.replace("\\", "/"))
    if not name_match:
        raise ValueError("index filename must be form.YYYYMMDD.idx")
    index_date = datetime.strptime(name_match.group(1), "%Y%m%d").date()
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("daily index is not valid UTF-8/ASCII") from exc

    lines = decoded.splitlines()
    header_line = None
    for i, line in enumerate(lines):
        if [part.strip() for part in line.split("|")] == HEADER:
            header_line = i
            break
    if header_line is None:
        raise ValueError("expected SEC pipe-delimited daily index header not found")

    seen: dict[str, dict[str, Any]] = {}
    conflicts: set[str] = set()
    quarantine: list[dict[str, Any]] = []
    counts = {
        "rows_seen_after_header": 0,
        "form4_rows_seen": 0,
        "non_form4_rows_ignored": 0,
        "malformed_rows": 0,
        "exact_duplicate_rows": 0,
        "conflicting_duplicate_accessions": 0,
        "index_date_before_filing_date": 0,
        "index_date_after_filing_date": 0,
    }

    for line_number, line in enumerate(lines[header_line + 1 :], start=header_line + 2):
        if not line.strip() or set(line.strip()) == {"-"}:
            continue
        counts["rows_seen_after_header"] += 1
        try:
            row = next(csv.reader([line], delimiter="|", quotechar='"'))
        except csv.Error:
            counts["malformed_rows"] += 1
            quarantine.append({"line_number": line_number, "reason": "csv_parse_error"})
            continue
        row = [field.strip() for field in row]
        if len(row) != 5:
            counts["malformed_rows"] += 1
            quarantine.append({"line_number": line_number, "reason": "wrong_column_count"})
            continue

        cik, company_name, form_type, filing_date_text, filing_path = row
        form_type = form_type.upper()
        if form_type not in {"4", "4/A"}:
            counts["non_form4_rows_ignored"] += 1
            continue
        counts["form4_rows_seen"] += 1

        if not cik.isdigit() or not company_name or not filing_path:
            counts["malformed_rows"] += 1
            quarantine.append({"line_number": line_number, "reason": "missing_required_field"})
            continue
        try:
            filing_date = _iso_date(filing_date_text)
        except ValueError:
            counts["malformed_rows"] += 1
            quarantine.append({"line_number": line_number, "reason": "invalid_filing_date"})
            continue

        path_identity = _accession_from_path(filing_path)
        if path_identity is None:
            counts["malformed_rows"] += 1
            quarantine.append({"line_number": line_number, "reason": "unrecognized_accession_path"})
            continue
        accession, path_cik = path_identity
        if int(cik) != int(path_cik):
            quarantine.append({"line_number": line_number, "accession": accession,
                               "reason": "row_cik_path_cik_mismatch"})
            continue
        if accession[:10] != str(int(cik)).zfill(10):
            quarantine.append({"line_number": line_number, "accession": accession,
                               "reason": "accession_cik_prefix_mismatch"})
            continue
        index_lag_days = (index_date - filing_date).days
        if index_lag_days < 0:
            counts["index_date_before_filing_date"] += 1
            quarantine.append({"line_number": line_number, "accession": accession,
                               "reason": "index_date_precedes_filing_date"})
            continue
        if index_lag_days > 0:
            counts["index_date_after_filing_date"] += 1

        record = {
            "accession": accession,
            "cik": str(int(cik)),
            "company_name": company_name,
            "form_type": form_type,
            "filing_date": filing_date.isoformat(),
            "index_date": index_date.isoformat(),
            "index_date_lag_days": index_lag_days,
            "filename": filing_path,
        }
        existing = seen.get(accession)
        if existing is None:
            record["same_file_exact_duplicate_rows"] = 0
            seen[accession] = record
            continue
        comparable = {k: v for k, v in existing.items() if k != "same_file_exact_duplicate_rows"}
        if comparable == record:
            existing["same_file_exact_duplicate_rows"] += 1
            counts["exact_duplicate_rows"] += 1
        else:
            conflicts.add(accession)
            counts["conflicting_duplicate_accessions"] += 1
            quarantine.append({"line_number": line_number, "accession": accession,
                               "reason": "conflicting_duplicate_accession_within_index"})

    for accession in conflicts:
        seen.pop(accession, None)
    return {
        "index_filename": Path(index_filename).name,
        "index_date": index_date.isoformat(),
        "index_sha256": hashlib.sha256(raw).hexdigest(),
        "records": list(seen.values()),
        "quarantine": quarantine,
        "counts": counts,
    }


def build_accession_ledger(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Collapse sightings to one accession while preserving all observed dates."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["accession"])].append(record)

    ledger: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    identity_fields = ("cik", "company_name", "form_type", "filing_date", "filename")
    for accession in sorted(grouped):
        sightings = grouped[accession]
        identities = {
            tuple(str(row.get(field, "")) for field in identity_fields)
            for row in sightings
        }
        if len(identities) != 1:
            quarantine.append({"accession": accession,
                               "reason": "cross_index_identity_conflict",
                               "sighting_count": len(sightings)})
            continue
        identity = sightings[0]
        dates = sorted({str(row["index_date"]) for row in sightings})
        filing_date = date.fromisoformat(str(identity["filing_date"]))
        lag_days = [(date.fromisoformat(value) - filing_date).days for value in dates]
        ledger.append({
            "accession": accession,
            "cik": identity["cik"],
            "company_name": identity["company_name"],
            "form_type": identity["form_type"],
            "filing_date": identity["filing_date"],
            "filename": identity["filename"],
            "first_daily_index_date": dates[0],
            "first_index_lag_days": lag_days[0],
            "max_index_lag_days": max(lag_days),
            "all_daily_index_dates": dates,
            "index_sightings": len(sightings),
            "same_file_exact_duplicate_rows": sum(
                int(row.get("same_file_exact_duplicate_rows", 0)) for row in sightings
            ),
        })
    return {"ledger": ledger, "quarantine": quarantine}


def next_full_xnys_session_close(
    index_date: str, sessions: Sequence[dict[str, str]]
) -> str:
    """Return the next full 6.5-hour XNYS close; skip early closes."""
    knowledge_date = _iso_date(index_date)
    candidates: list[tuple[date, datetime]] = []
    for session in sessions:
        session_date = _iso_date(session["session_date"])
        if session_date <= knowledge_date:
            continue
        market_open = _aware_datetime(session["open_utc"])
        market_close = _aware_datetime(session["close_utc"])
        duration = (market_close - market_open).total_seconds()
        if duration <= 0:
            raise ValueError("session close must be after session open")
        if duration == FULL_SESSION_SECONDS:
            candidates.append((session_date, market_close))
    if not candidates:
        raise LookupError("no subsequent full XNYS session in supplied calendar")
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1].isoformat()


def build_contract_result() -> dict[str, Any]:
    return {
        "phase": 283,
        "status": "PARSER_CONTRACT_IMPLEMENTED_NO_SEC_BYTES_OR_ALPHA",
        "source": "SEC historical daily form.YYYYMMDD.idx",
        "scope": "offline parser and synthetic regression fixtures only",
        "raw_sec_requests": 0,
        "raw_index_bytes_downloaded": 0,
        "gates": {
            "parser_contract_tested": False,
            "raw_index_format_verified": False,
            "six_quarter_accession_join_verified": False,
            "same_day_pac_rate_measured": False,
            "first_public_timestamp_observed": False,
            "strict_pit_admitted": False,
            "alpha_test_authorized": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
        },
    }


def validate_contract_result(result: dict[str, Any]) -> None:
    gates = result["gates"]
    if gates["strict_pit_admitted"] or gates["alpha_test_authorized"]:
        raise ValueError("offline parser contract cannot admit PIT or alpha")
    if gates["holdout_used"] or not gates["f80_frozen"]:
        raise ValueError("research controls violated")
    if result["raw_sec_requests"] != 0 or result["raw_index_bytes_downloaded"] != 0:
        raise ValueError("offline contract unexpectedly accessed SEC data")


def main(argv: Sequence[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-file", action="append", required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    parsed_files: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []
    all_quarantine: list[dict[str, Any]] = []
    totals: dict[str, int] = defaultdict(int)

    for filename in args.index_file:
        raw = Path(filename).read_bytes()
        parsed = parse_daily_form_index(raw, filename)
        parsed_files.append({
            "index_filename": parsed["index_filename"],
            "index_date": parsed["index_date"],
            "index_sha256": parsed["index_sha256"],
            "counts": parsed["counts"],
        })
        all_records.extend(parsed["records"])
        all_quarantine.extend(parsed["quarantine"])
        for key, value in parsed["counts"].items():
            totals[key] += int(value)

    built = build_accession_ledger(all_records)
    result = {
        "phase": 283,
        "status": "DAILY_INDEX_ACCESSION_LEDGER_BUILT_NOT_PIT_ADMITTED",
        "input_files": parsed_files,
        "counts": dict(totals),
        "unique_accessions": len(built["ledger"]),
        "ledger": built["ledger"],
        "quarantine": all_quarantine + built["quarantine"],
        "controls": {
            "fallback_to_filing_date": False,
            "fallback_to_acceptance_time": False,
            "strict_pit_admitted": False,
            "alpha_test_authorized": False,
            "holdout_used": False,
            "f80_frozen": True,
        },
    }
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return result


if __name__ == "__main__":
    main()
