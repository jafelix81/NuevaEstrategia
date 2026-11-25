#!/usr/bin/env python3
"""Bounded SEC EDGAR global-index pilot for Schedule 13D/G subject discovery.

The SEC master index CIK, archive path CIK and accession-prefix filer CIK are
kept as separate fields. The exact master-index filename points to the complete
submission text; the SEC-HEADER is parsed to adjudicate SUBJECT COMPANY vs FILED BY.

This is a data-feasibility audit only: no historical F80 membership, exact public
availability, return test, signal, or production change is inferred.
"""
from __future__ import annotations

import argparse
import ast
import csv
import gzip
import hashlib
import json
import os
import random
import re
import time
import zlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from research import phase401_form144a_full_parent_identity_census as p401
from research.phase485_sec_13dg_subject_filer_header_parser import parse_subject_filer_identity

PHASE = 603
QUARTER = "2026/QTR3"
MASTER_INDEX_URL = f"https://www.sec.gov/Archives/edgar/full-index/{QUARTER}/master.idx"
TICKER_SOURCES = {
    "company_tickers.json": "https://www.sec.gov/files/company_tickers.json",
    "company_tickers_exchange.json": "https://www.sec.gov/files/company_tickers_exchange.json",
    "company_tickers_mf.json": "https://www.sec.gov/files/company_tickers_mf.json",
}
BASE_SOURCE = Path("Nueva_Estrategia_Fase0_Descubrimiento.py")
FORMS = {"SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"}
MAX_PER_STRATUM = 20
SEC_INTERVAL_SECONDS = 0.25
OUTPUT_FIELDS = [
    "accession", "form", "filing_date", "index_row_count",
    "index_ciks", "index_company_names", "archive_path_ciks",
    "submission_path_count", "submission_url", "accession_filer_cik",
    "header_accession", "accession_submitter_cik", "header_subject_cik",
    "header_subject_name", "header_filer_cik", "header_filer_name",
    "header_identity_status", "header_accession_matches_expected",
    "accession_submitter_matches_filed_by", "header_subject_in_index_ciks",
    "header_filer_in_index_ciks", "archive_path_matches_subject",
    "index_contains_both_header_roles", "subject_current_f80_tickers",
    "filer_current_f80_tickers", "subject_current_f80_from_non_f80_filer",
    "acceptance_datetime_raw", "http_status", "submission_sha256", "error",
]
_last_request = 0.0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_cik(value: object) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(10) if digits and len(digits) <= 10 else None


def normalize_index_path(path: str) -> str:
    value = str(path or "").strip()
    match = re.search(r"(?:^|/)edgar/data/.*$", value, re.I)
    return match.group(0).lstrip("/") if match else value.lstrip("/")


def archive_path_format(path: str) -> str:
    parts = normalize_index_path(path).split("/")
    if len(parts) == 4:
        return "flat_accession_file"
    if len(parts) >= 5:
        return "accession_directory"
    return "unknown"


def format_accession(digits: str) -> str | None:
    digits = re.sub(r"\D", "", str(digits or ""))
    if len(digits) != 18:
        return None
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"


def parse_index_path(path: str) -> tuple[str | None, str | None]:
    """Return archive-path CIK and accession from flat or accession-directory paths."""
    parts = normalize_index_path(path).split("/")
    if len(parts) < 4 or parts[0:2] != ["edgar", "data"]:
        return None, None
    archive_cik = normalize_cik(parts[2])
    accession = None
    if len(parts) >= 5:
        accession = format_accession(parts[3])
    if not accession:
        match = re.search(r"(?<!\d)(\d{10}-\d{2}-\d{6})(?!\d)", normalize_index_path(path))
        if match:
            accession = match.group(1)
        else:
            match = re.search(r"(?<!\d)(\d{18})(?!\d)", normalize_index_path(path))
            accession = format_accession(match.group(1)) if match else None
    return archive_cik, accession


def build_submission_url(path: str, accession: str) -> str:
    normalized = normalize_index_path(path)
    if not normalized.startswith("edgar/data/"):
        raise ValueError("invalid_master_index_submission_path")
    if parse_index_path(normalized)[1] != accession:
        raise ValueError("master_index_path_accession_mismatch")
    return f"https://www.sec.gov/Archives/{normalized}"


def normalize_form(value: str) -> str:
    token = " ".join(str(value or "").upper().split())
    return token.replace("SCHEDULE 13D", "SC 13D").replace("SCHEDULE 13G", "SC 13G")


def parse_master_index(raw: bytes | str) -> tuple[list[dict], dict]:
    text = raw.decode("utf-8-sig", "replace") if isinstance(raw, bytes) else str(raw)
    records = []
    invalid = Counter()
    header_seen = False
    for line in text.splitlines():
        if not header_seen:
            if line.strip().lower().startswith("cik|company name|form type|date filed|filename"):
                header_seen = True
            continue
        parts = line.split("|", 4)
        if len(parts) != 5:
            continue
        index_cik_raw, company, form_raw, filing_date, path = [x.strip() for x in parts]
        form = normalize_form(form_raw)
        if form not in FORMS:
            continue
        index_cik = normalize_cik(index_cik_raw)
        archive_cik, accession = parse_index_path(path)
        if not index_cik:
            invalid["invalid_index_cik"] += 1
        if not archive_cik:
            invalid["invalid_archive_path_cik"] += 1
        if not accession:
            invalid["invalid_accession_path"] += 1
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", filing_date):
            invalid["invalid_filing_date"] += 1
        if index_cik and archive_cik and index_cik != archive_cik:
            invalid["index_cik_archive_path_mismatch"] += 1
        if not all((index_cik, archive_cik, accession, filing_date)):
            continue
        records.append({
            "index_cik": index_cik,
            "index_company_name": company,
            "form": form,
            "filing_date": filing_date,
            "filename_path": normalize_index_path(path),
            "archive_path_cik": archive_cik,
            "archive_path_format": archive_path_format(path),
            "accession": accession,
            "accession_filer_cik": accession[:10],
        })
    if not header_seen:
        raise ValueError("master_index_header_not_found")
    return records, dict(invalid)


def group_index_rows(records: list[dict], f80_ciks: set[str]) -> tuple[list[dict], int]:
    groups = {}
    exact_seen = set()
    exact_duplicate_rows = 0
    for row in records:
        exact_key = (row["accession"], row["index_cik"], row["form"],
                     row["filing_date"], row["filename_path"], row["index_company_name"])
        if exact_key in exact_seen:
            exact_duplicate_rows += 1
            continue
        exact_seen.add(exact_key)
        group = groups.setdefault(row["accession"], {
            "accession": row["accession"],
            "accession_filer_cik": row["accession_filer_cik"],
            "index_rows": [],
        })
        group["index_rows"].append(row)
    result = []
    for group in groups.values():
        rows = group["index_rows"]
        forms = sorted({row["form"] for row in rows})
        dates = sorted({row["filing_date"] for row in rows})
        group.update({
            "form": forms[0] if forms else "",
            "form_conflict": len(forms) > 1,
            "filing_date": dates[0] if dates else "",
            "filing_date_conflict": len(dates) > 1,
            "index_ciks": sorted({row["index_cik"] for row in rows}),
            "archive_path_ciks": sorted({row["archive_path_cik"] for row in rows}),
            "filename_paths": sorted({row["filename_path"] for row in rows}),
            "index_company_names": sorted({row["index_company_name"] for row in rows}),
            "archive_path_formats": sorted({row["archive_path_format"] for row in rows}),
        })
        group["any_index_cik_in_f80"] = bool(set(group["index_ciks"]) & f80_ciks)
        group["accession_filer_in_f80"] = group["accession_filer_cik"] in f80_ciks
        result.append(group)
    return sorted(result, key=lambda row: row["accession"]), exact_duplicate_rows


def load_f80_universe(path: Path = BASE_SOURCE) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "DEFAULT_UNIVERSE" for target in node.targets):
                values = sorted({str(x).strip().upper() for x in ast.literal_eval(node.value)})
                if len(values) != 335:
                    raise ValueError(f"expected_335_f80_names_got_{len(values)}")
                return values
    raise ValueError("DEFAULT_UNIVERSE_not_found")


def _row_value(row: dict, aliases: tuple[str, ...]):
    normalized = {re.sub(r"[^a-z0-9]", "", str(k).lower()): v for k, v in row.items()}
    for alias in aliases:
        key = re.sub(r"[^a-z0-9]", "", alias.lower())
        if key in normalized:
            return normalized[key]
    return None


def extract_ticker_pairs(obj: object, source_name: str) -> list[tuple[str, str]]:
    pairs = []
    if isinstance(obj, dict) and isinstance(obj.get("data"), list):
        fields = obj.get("fields") or []
        normalized_fields = [re.sub(r"[^a-z0-9]", "", str(x).lower()) for x in fields]
        for values in obj["data"]:
            if isinstance(values, dict):
                cik = _row_value(values, ("cik", "cik_str"))
                ticker = _row_value(values, ("ticker", "class_ticker"))
            elif isinstance(values, (list, tuple)) and normalized_fields:
                row = {normalized_fields[i]: values[i] for i in range(min(len(values), len(normalized_fields)))}
                cik = row.get("cik") or row.get("cikstr")
                ticker = row.get("ticker") or row.get("classticker")
            elif isinstance(values, (list, tuple)) and len(values) >= 3:
                cik = values[0]
                ticker_index = 3 if "mf" in source_name.lower() and len(values) >= 4 else 2
                ticker = values[ticker_index]
            else:
                continue
            norm_cik = normalize_cik(cik)
            norm_ticker = str(ticker or "").strip().upper()
            if norm_cik and norm_ticker:
                pairs.append((norm_ticker, norm_cik))
    elif isinstance(obj, dict):
        for row in obj.values():
            if not isinstance(row, dict):
                continue
            cik = _row_value(row, ("cik", "cik_str"))
            ticker = _row_value(row, ("ticker", "class_ticker"))
            norm_cik = normalize_cik(cik)
            norm_ticker = str(ticker or "").strip().upper()
            if norm_cik and norm_ticker:
                pairs.append((norm_ticker, norm_cik))
    elif isinstance(obj, list):
        for row in obj:
            if isinstance(row, dict):
                cik = _row_value(row, ("cik", "cik_str"))
                ticker = _row_value(row, ("ticker", "class_ticker"))
                norm_cik = normalize_cik(cik)
                norm_ticker = str(ticker or "").strip().upper()
                if norm_cik and norm_ticker:
                    pairs.append((norm_ticker, norm_cik))
    return pairs


def current_f80_cik_map(universe: list[str], mapping_sources: dict[str, dict]) -> tuple[dict, list[str], list[str], dict]:
    ticker_to_ciks = defaultdict(set)
    source_counts = Counter()
    for source_name, obj in mapping_sources.items():
        for ticker, cik in extract_ticker_pairs(obj, source_name):
            if ticker in universe:
                ticker_to_ciks[ticker].add(cik)
                source_counts[source_name] += 1
    unmapped = sorted(ticker for ticker in universe if not ticker_to_ciks.get(ticker))
    conflicts = sorted(ticker for ticker in universe if len(ticker_to_ciks.get(ticker, set())) > 1)
    resolved = {
        ticker: next(iter(ciks))
        for ticker, ciks in ticker_to_ciks.items()
        if len(ciks) == 1
    }
    cik_to_tickers = defaultdict(list)
    for ticker, cik in resolved.items():
        cik_to_tickers[cik].append(ticker)
    cik_to_tickers = {cik: "|".join(sorted(tickers)) for cik, tickers in cik_to_tickers.items()}
    return cik_to_tickers, unmapped, conflicts, {
        "tickers_mapped": len(resolved),
        "unique_ciks_mapped": len(cik_to_tickers),
        "source_row_counts": dict(source_counts),
    }


def deterministic_stratified_sample(groups: list[dict], f80_ciks: set[str],
                                    max_per_stratum: int = MAX_PER_STRATUM) -> list[dict]:
    strata = defaultdict(list)
    for group in groups:
        if group["form_conflict"] or group["filing_date_conflict"]:
            continue
        key = (group["form"], group["any_index_cik_in_f80"])
        strata[key].append(group)
    selected = []
    for key in sorted(strata):
        ordered = sorted(strata[key], key=lambda row: hashlib.sha256(
            (QUARTER + "|" + row["accession"]).encode("utf-8")
        ).hexdigest())
        selected.extend(ordered[:max_per_stratum])
    return selected


def choose_submission_path(group: dict, f80_ciks: set[str]) -> str:
    rows = sorted(
        group["index_rows"],
        key=lambda row: (
            row["index_cik"] not in f80_ciks,
            row["index_cik"] != row["archive_path_cik"],
            row["filename_path"],
        ),
    )
    if not rows:
        raise ValueError("accession_group_has_no_index_rows")
    return rows[0]["filename_path"]


def resolve_user_agent(secret_value: str | None = None, fallback: str | None = None) -> tuple[str, str, bool, bool]:
    secret = str(secret_value if secret_value is not None else os.environ.get("SEC_USER_AGENT", "")).strip()
    secret_present = bool(secret)
    secret_valid = bool(secret and "@" in secret and "example.com" not in secret.lower()
                        and "<sample" not in secret.lower())
    if secret_valid:
        return secret, "repository_secret", secret_present, True
    shared = str(fallback if fallback is not None else getattr(p401, "SEC_UA", "")).strip()
    if not shared or "@" not in shared or "example.com" in shared.lower():
        raise RuntimeError("no_valid_sec_user_agent_or_shared_contact")
    return shared, "shared_phase401_contact_fallback", secret_present, False


def fetch_sec_bytes(url: str, user_agent: str, timeout: int = 60, retries: int = 5,
                    allow_404: bool = False) -> tuple[bytes, int]:
    global _last_request
    last_error = None
    for attempt in range(retries):
        wait = SEC_INTERVAL_SECONDS - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
        request = Request(url, headers={
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "text/plain,text/html,application/json,*/*",
        })
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
                encoding = str(response.headers.get("Content-Encoding", "")).lower()
                if encoding == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                elif encoding == "deflate":
                    try:
                        raw = zlib.decompress(raw)
                    except zlib.error:
                        raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                return raw, int(getattr(response, "status", 200))
        except HTTPError as error:
            if error.code == 404 and allow_404:
                return b"", 404
            last_error = error
            if error.code not in (408, 429, 500, 502, 503, 504):
                raise
            retry_after = error.headers.get("Retry-After") if error.headers else None
            try:
                delay = float(retry_after) if retry_after else min(45, 2 ** attempt)
            except (TypeError, ValueError):
                delay = min(45, 2 ** attempt)
            time.sleep(delay + random.uniform(0.1, 0.5))
        except (URLError, TimeoutError, OSError, zlib.error) as error:
            last_error = error
            time.sleep(min(30, 2 ** attempt) + random.uniform(0.1, 0.5))
    raise RuntimeError(f"sec_get_failed:{type(last_error).__name__}:{url}")


def acceptance_datetime(raw: bytes) -> str | None:
    text = raw.decode("utf-8", "replace")
    match = re.search(r"<ACCEPTANCE-DATETIME>\s*(\d{14})", text, re.I)
    return match.group(1) if match else None


def fetch_submission_sample(sample: list[dict], cik_to_tickers: dict,
                            f80_ciks: set[str], user_agent: str) -> list[dict]:
    output = []
    for group in sample:
        path = choose_submission_path(group, f80_ciks)
        url = build_submission_url(path, group["accession"])
        index_ciks = set(group["index_ciks"])
        archive_ciks = set(group["archive_path_ciks"])
        base = {
            "accession": group["accession"],
            "form": group["form"],
            "filing_date": group["filing_date"],
            "index_row_count": len(group["index_rows"]),
            "index_ciks": ";".join(group["index_ciks"]),
            "index_company_names": ";".join(group["index_company_names"]),
            "archive_path_ciks": ";".join(group["archive_path_ciks"]),
            "submission_path_count": len(group["filename_paths"]),
            "submission_url": url,
            "accession_filer_cik": group["accession_filer_cik"],
            "accession_submitter_cik": group["accession_filer_cik"],
            "http_status": 0,
            "submission_sha256": "",
            "error": "",
        }
        try:
            raw, status = fetch_sec_bytes(url, user_agent, allow_404=True)
            base["http_status"] = status
            if status != 200:
                base["error"] = f"http_{status}"
                output.append(base)
                continue
            base["submission_sha256"] = hashlib.sha256(raw).hexdigest()
            base["acceptance_datetime_raw"] = acceptance_datetime(raw) or ""
            parsed = parse_subject_filer_identity(raw.decode("utf-8", "replace"), group["accession"])
            subject_cik = parsed.get("subject_issuer_cik")
            filed_by_cik = parsed.get("filed_by_cik") or parsed.get("filing_cik")
            submitter_cik = parsed.get("accession_submitter_cik")
            subject_in_index = bool(subject_cik and subject_cik in index_ciks)
            filed_by_in_index = bool(filed_by_cik and filed_by_cik in index_ciks)
            archive_subject_match = bool(subject_cik and subject_cik in archive_ciks)
            subject_ticker = cik_to_tickers.get(subject_cik, "") if subject_cik else ""
            filed_by_ticker = cik_to_tickers.get(filed_by_cik, "") if filed_by_cik else ""
            base.update({
                "header_accession": parsed.get("header_accession") or "",
                "accession_submitter_cik": submitter_cik or group["accession_filer_cik"],
                "header_subject_cik": subject_cik or "",
                "header_subject_name": parsed.get("subject_issuer_name") or "",
                "header_filer_cik": filed_by_cik or "",
                "header_filer_name": parsed.get("filed_by_entity_name") or parsed.get("filing_entity_name") or "",
                "header_identity_status": parsed.get("identity_status", ""),
                "header_accession_matches_expected": str(bool(parsed.get("accession_matches_header"))).lower(),
                "accession_submitter_matches_filed_by": str(bool(parsed.get("accession_submitter_matches_filed_by"))).lower(),
                "header_subject_in_index_ciks": str(subject_in_index).lower(),
                "header_filer_in_index_ciks": str(filed_by_in_index).lower(),
                "archive_path_matches_subject": str(archive_subject_match).lower(),
                "index_contains_both_header_roles": str(subject_in_index and filed_by_in_index).lower(),
                "subject_current_f80_tickers": subject_ticker,
                "filer_current_f80_tickers": filed_by_ticker,
                "subject_current_f80_from_non_f80_filer": str(bool(subject_ticker and not filed_by_ticker)).lower(),
            })
        except Exception as error:
            base["error"] = f"{type(error).__name__}:{str(error)[:240]}"
        output.append(base)
    return output


def summarize(records: list[dict], groups: list[dict], exact_duplicate_rows: int,
              invalid: dict, sample: list[dict], rows: list[dict],
              universe: list[str], cik_to_tickers: dict, unmapped: list[str],
              conflicts: list[str], mapping_meta: dict, source_status: dict,
              source_hashes: dict, index_hash: str, ua_source: str,
              secret_present: bool, secret_accepted: bool) -> dict:
    candidate_row_forms = Counter(row["form"] for row in records)
    candidate_accession_forms = Counter(group["form"] for group in groups if not group["form_conflict"])
    multiplicity = Counter(str(len(group["index_rows"])) for group in groups)
    sample_forms = Counter(group["form"] for group in sample)
    sample_strata = Counter(
        f'{group["form"]}|{"F80_INDEX_CIK_PRESENT" if group["any_index_cik_in_f80"] else "NO_F80_INDEX_CIK"}'
        for group in sample
    )
    status_counts = Counter(str(row.get("http_status", 0)) for row in rows)
    successful = [row for row in rows if row.get("http_status") == 200]
    verified = [row for row in successful if row.get("header_identity_status") == "VERIFIED_SUBJECT_AND_FILED_BY_CIKS"]
    accession_header_matches = [row for row in verified if row.get("header_accession_matches_expected") == "true"]
    submitter_filed_by_matches = [row for row in verified if row.get("accession_submitter_matches_filed_by") == "true"]
    subject_index = [row for row in verified if row.get("header_subject_in_index_ciks") == "true"]
    filed_by_index = [row for row in verified if row.get("header_filer_in_index_ciks") == "true"]
    archive_subject = [row for row in verified if row.get("archive_path_matches_subject") == "true"]
    subject_f80 = [row for row in verified if row.get("subject_current_f80_tickers")]
    subject_f80_external_filer = [row for row in subject_f80 if not row.get("filer_current_f80_tickers")]
    filed_by_f80 = [row for row in verified if row.get("filer_current_f80_tickers")]
    index_path_mismatches = sum(row["index_cik"] != row["archive_path_cik"] for row in records)
    index_vs_accession_filer_differences = sum(row["index_cik"] != row["accession_filer_cik"] for row in records)
    candidate_f80_index = sum(group["any_index_cik_in_f80"] for group in groups)
    candidate_f80_accession_prefix = sum(group["accession_filer_in_f80"] for group in groups)
    if not sample:
        disposition = "NO_13DG_CANDIDATES_IN_QUARTER"
    elif index_path_mismatches:
        disposition = "QUARANTINE_INDEX_PATH_CIK_MISMATCH"
    elif len(successful) / len(sample) < 0.95:
        disposition = "INCONCLUSIVE_SUBMISSION_FETCH_COVERAGE"
    elif len(verified) / len(successful) < 0.95:
        disposition = "INCONCLUSIVE_SUBJECT_FILED_BY_HEADER_PARSE"
    elif len(accession_header_matches) / len(verified) < 0.95:
        disposition = "QUARANTINE_HEADER_ACCESSION_MISMATCH"
    elif len(subject_index) / len(verified) < 0.95 or len(archive_subject) / len(verified) < 0.95:
        disposition = "QUARANTINE_INDEX_SUBJECT_IDENTITY_COVERAGE"
    else:
        disposition = "GLOBAL_INDEX_SUBJECT_DISCOVERY_PILOT_PASS_CURRENT_CIK_ONLY"
    return {
        "phase": PHASE,
        "audit": "SEC_13DG_GLOBAL_INDEX_SUBJECT_DISCOVERY_PILOT",
        "audit_timestamp_utc": utc_now(),
        "disposition": disposition,
        "quarter": QUARTER,
        "master_index_url": MASTER_INDEX_URL,
        "master_index_sha256": index_hash,
        "ticker_mapping_source_hashes": source_hashes,
        "ticker_mapping_source_status": source_status,
        "frozen_universe_size": len(universe),
        "current_f80_tickers_mapped": mapping_meta["tickers_mapped"],
        "current_f80_unique_ciks_mapped": mapping_meta["unique_ciks_mapped"],
        "current_f80_unmapped_tickers": unmapped,
        "current_f80_mapping_conflict_tickers": conflicts,
        "ticker_mapping_source_row_counts": mapping_meta["source_row_counts"],
        "historical_f80_membership_verified": False,
        "candidate_index_rows": len(records),
        "candidate_accessions": len(groups),
        "candidate_index_row_form_counts": dict(candidate_row_forms),
        "candidate_accession_form_counts": dict(candidate_accession_forms),
        "candidate_accessions_with_multiple_index_rows": sum(len(g["index_rows"]) > 1 for g in groups),
        "candidate_accessions_with_multiple_index_ciks": sum(len(g["index_ciks"]) > 1 for g in groups),
        "candidate_accessions_with_multiple_submission_paths": sum(len(g["filename_paths"]) > 1 for g in groups),
        "candidate_index_row_multiplicity_distribution": dict(multiplicity),
        "candidate_exact_duplicate_index_rows_removed": exact_duplicate_rows,
        "candidate_index_cik_archive_path_mismatch_rows": index_path_mismatches,
        "candidate_index_cik_vs_accession_filer_prefix_difference_rows": index_vs_accession_filer_differences,
        "candidate_accessions_with_any_current_f80_index_cik": candidate_f80_index,
        "candidate_accessions_with_accession_prefix_in_current_f80": candidate_f80_accession_prefix,
        "invalid_master_index_rows": invalid,
        "sample_size_unique_accessions": len(sample),
        "sample_form_counts": dict(sample_forms),
        "sample_strata_counts": dict(sample_strata),
        "submission_http_status_counts": dict(status_counts),
        "submission_http_200": len(successful),
        "header_identity_verified": len(verified),
        "header_accession_matches_expected": len(accession_header_matches),
        "accession_submitter_matches_filed_by": len(submitter_filed_by_matches),
        "header_subject_in_index_ciks": len(subject_index),
        "header_filer_in_index_ciks": len(filed_by_index),
        "archive_path_matches_subject": len(archive_subject),
        "current_f80_subject_matches": len(subject_f80),
        "current_f80_subject_matches_with_non_f80_filer": len(subject_f80_external_filer),
        "current_f80_filed_by_matches": len(filed_by_f80),
        "sec_user_agent_secret_present": secret_present,
        "sec_user_agent_secret_accepted": secret_accepted,
        "sec_user_agent_source": ua_source,
        "public_availability_certified": False,
        "acceptance_datetime_is_public_availability": False,
        "filing_date_used_only_as_coarse_historical_boundary": True,
        "signal_eligible_rows": 0,
        "forward_return_test_performed": False,
        "oos_bootstrap_loo_performed": False,
        "f80_baseline_changed": False,
        "production_changed": False,
        "notes": [
            "The index CIK, archive-path CIK and accession-prefix CIK are not assumed to be the same role.",
            "The accession prefix identifies the EDGAR submitting entity and can be a third-party filing agent; it is not required to equal the FILED BY reporting-owner CIK.",
            "The SEC-HEADER ACCESSION NUMBER is checked against the expected accession; FILED BY CIK is validated independently.",
            "All index rows for an accession are preserved and grouped; repeated accessions are not discarded as conflicts.",
            "The exact master-index filename is fetched as the complete submission text; SEC-HEADER SUBJECT COMPANY and FILED BY blocks are parsed separately.",
            "Current SEC ticker files are a discovery aid only and are not an effective-dated historical F80 security master.",
            "The quarterly index is a retrospective/corrected snapshot, not a prospective first-seen or exact public-dissemination record.",
            "No raw SEC submission payloads are persisted; only hashes, public accession metadata and parsed identity fields are retained in the temporary artifact.",
        ],
        "sample_error_count": sum(bool(row.get("error")) for row in rows),
        "sample_error_examples": [row["error"] for row in rows if row.get("error")][:10],
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run(output: Path) -> dict:
    user_agent, ua_source, secret_present, secret_accepted = resolve_user_agent()
    universe = load_f80_universe()
    index_raw, index_status = fetch_sec_bytes(MASTER_INDEX_URL, user_agent)
    if index_status != 200:
        raise RuntimeError(f"master_index_http_{index_status}")
    mapping_sources = {}
    source_status = {}
    source_hashes = {}
    for source_name, url in TICKER_SOURCES.items():
        try:
            raw, status = fetch_sec_bytes(url, user_agent, allow_404=True)
            source_status[source_name] = f"http_{status}"
            if status == 200:
                mapping_sources[source_name] = json.loads(raw.decode("utf-8"))
                source_hashes[source_name] = hashlib.sha256(raw).hexdigest()
        except Exception as error:
            source_status[source_name] = f"{type(error).__name__}:{str(error)[:160]}"
    cik_to_tickers, unmapped, conflicts, mapping_meta = current_f80_cik_map(universe, mapping_sources)
    f80_ciks = set(cik_to_tickers)
    records, invalid = parse_master_index(index_raw)
    groups, exact_duplicate_rows = group_index_rows(records, f80_ciks)
    sample = deterministic_stratified_sample(groups, f80_ciks)
    rows = fetch_submission_sample(sample, cik_to_tickers, f80_ciks, user_agent)
    summary = summarize(records, groups, exact_duplicate_rows, invalid, sample, rows,
                        universe, cik_to_tickers, unmapped, conflicts, mapping_meta,
                        source_status, source_hashes, hashlib.sha256(index_raw).hexdigest(),
                        ua_source, secret_present, secret_accepted)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "sample.csv", rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase603_output")
    args = parser.parse_args()
    run(Path(args.output))


if __name__ == "__main__":
    main()
