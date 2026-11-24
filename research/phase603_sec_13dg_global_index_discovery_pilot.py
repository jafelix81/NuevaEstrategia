#!/usr/bin/env python3
"""Bounded SEC EDGAR global-index pilot for Schedule 13D/G subject-issuer discovery.

This is a data-feasibility audit only. It does not infer historical F80 membership,
public dissemination time, trades, or signals.
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
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
BASE_SOURCE = Path("Nueva_Estrategia_Fase0_Descubrimiento.py")
FORMS = {"SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"}
MAX_PER_STRATUM = 25
SEC_INTERVAL_SECONDS = 0.25
OUTPUT_FIELDS = [
    "accession", "form", "filing_date", "index_company_name",
    "index_filer_cik", "accession_filer_cik", "archive_path_cik", "archive_path_format",
    "header_subject_cik", "header_subject_name", "header_filer_cik",
    "header_filer_name", "identity_status", "header_filer_matches_index",
    "header_filer_matches_accession", "archive_path_matches_subject",
    "filer_current_f80_ticker", "subject_current_f80_ticker",
    "subject_current_f80_from_external_filer", "acceptance_datetime_raw",
    "http_status", "header_sha256", "index_headers_url", "error",
]
_last_request = 0.0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_cik(value: object) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(10) if digits and len(digits) <= 10 else None


def normalize_form(value: str) -> str:
    token = " ".join(str(value or "").upper().split())
    token = token.replace("SCHEDULE 13D", "SC 13D").replace("SCHEDULE 13G", "SC 13G")
    return token


def format_accession(digits: str) -> str | None:
    digits = re.sub(r"\D", "", str(digits or ""))
    if len(digits) != 18:
        return None
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"


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


def parse_index_path(path: str) -> tuple[str | None, str | None]:
    """Return archive-path CIK and accession from flat or directory EDGAR index paths."""
    normalized = normalize_index_path(path)
    parts = normalized.split("/")
    if len(parts) < 4 or parts[0:2] != ["edgar", "data"]:
        return None, None
    archive_cik = normalize_cik(parts[2])
    accession = None
    if len(parts) >= 5:
        accession = format_accession(parts[3])
    if not accession:
        match = re.search(r"(?<!\d)(\d{10}-\d{2}-\d{6})(?!\d)", normalized)
        if match:
            accession = match.group(1)
        else:
            match = re.search(r"(?<!\d)(\d{18})(?!\d)", normalized)
            accession = format_accession(match.group(1)) if match else None
    return archive_cik, accession


def build_index_headers_url(path: str, accession: str) -> str:
    """Resolve the canonical accession-directory header URL from either index path form."""
    normalized = normalize_index_path(path)
    parts = normalized.split("/")
    if len(parts) < 4 or parts[0:2] != ["edgar", "data"]:
        raise ValueError("invalid_master_index_archive_path")
    if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", str(accession or "")):
        raise ValueError("invalid_accession")
    if parse_index_path(path)[1] != accession:
        raise ValueError("master_index_path_accession_mismatch")
    archive_cik = normalize_cik(parts[2])
    if not archive_cik:
        raise ValueError("invalid_archive_path_cik")
    accession_directory = accession.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(archive_cik)}/"
        f"{accession_directory}/{accession}-index-headers.html"
    )


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
        if not all((index_cik, archive_cik, accession, filing_date)):
            continue
        records.append({
            "index_filer_cik": index_cik,
            "index_company_name": company,
            "form": form,
            "filing_date": filing_date,
            "filename_path": path,
            "archive_path_cik": archive_cik,
            "archive_path_format": archive_path_format(path),
            "accession": accession,
            "accession_filer_cik": accession[:10],
        })
    if not header_seen:
        raise ValueError("master_index_header_not_found")
    return records, dict(invalid)


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


def current_f80_cik_map(universe: list[str], company_tickers: dict) -> tuple[dict, list[str]]:
    ticker_to_cik = {}
    for row in company_tickers.values():
        ticker = str(row.get("ticker", "")).strip().upper()
        cik = normalize_cik(row.get("cik_str"))
        if ticker in universe and cik:
            ticker_to_cik[ticker] = cik
    cik_to_ticker = {}
    for ticker, cik in ticker_to_cik.items():
        if cik in cik_to_ticker and cik_to_ticker[cik] != ticker:
            cik_to_ticker[cik] = "|".join(sorted(set(cik_to_ticker[cik].split("|") + [ticker])))
        else:
            cik_to_ticker[cik] = ticker
    return cik_to_ticker, [ticker for ticker in universe if ticker not in ticker_to_cik]


def deterministic_stratified_sample(records: list[dict], max_per_stratum: int = MAX_PER_STRATUM) -> list[dict]:
    groups = defaultdict(list)
    for row in records:
        key = (row["form"], row["index_filer_cik"] in row.get("_f80_ciks", set()))
        groups[key].append(row)
    selected = []
    for key in sorted(groups):
        ordered = sorted(groups[key], key=lambda row: hashlib.sha256(
            (QUARTER + "|" + row["accession"]).encode("utf-8")
        ).hexdigest())
        selected.extend(ordered[:max_per_stratum])
    return selected


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
            if error.code not in (403, 408, 429, 500, 502, 503, 504):
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


def fetch_header_sample(sample: list[dict], cik_to_ticker: dict, user_agent: str) -> list[dict]:
    output = []
    for row in sample:
        url = build_index_headers_url(row["filename_path"], row["accession"])
        base = {
            "accession": row["accession"],
            "form": row["form"],
            "filing_date": row["filing_date"],
            "index_company_name": row["index_company_name"],
            "index_filer_cik": row["index_filer_cik"],
            "accession_filer_cik": row["accession_filer_cik"],
            "archive_path_cik": row["archive_path_cik"],
            "archive_path_format": row.get("archive_path_format", ""),
            "index_headers_url": url,
            "http_status": 0,
            "header_sha256": "",
            "error": "",
        }
        try:
            raw, status = fetch_sec_bytes(url, user_agent, allow_404=True)
            base["http_status"] = status
            if status != 200:
                base["error"] = f"http_{status}"
                output.append(base)
                continue
            base["header_sha256"] = hashlib.sha256(raw).hexdigest()
            base["acceptance_datetime_raw"] = acceptance_datetime(raw) or ""
            parsed = parse_subject_filer_identity(raw.decode("utf-8", "replace"), row["accession"])
            subject_cik = parsed.get("subject_issuer_cik")
            header_filer_cik = parsed.get("filing_cik")
            header_filer_matches_index = bool(header_filer_cik and header_filer_cik == row["index_filer_cik"])
            header_filer_matches_accession = bool(header_filer_cik and header_filer_cik == row["accession_filer_cik"])
            archive_path_matches_subject = bool(subject_cik and subject_cik == row["archive_path_cik"])
            filer_ticker = cik_to_ticker.get(row["index_filer_cik"], "")
            subject_ticker = cik_to_ticker.get(subject_cik, "") if subject_cik else ""
            identity_status = parsed.get("identity_status", "")
            if parsed.get("subject_issuer_identity_verified") and not header_filer_matches_index:
                identity_status = "INDEX_FILER_CIK_MISMATCH"
            base.update({
                "header_subject_cik": subject_cik or "",
                "header_subject_name": parsed.get("subject_issuer_name") or "",
                "header_filer_cik": header_filer_cik or "",
                "header_filer_name": parsed.get("filing_entity_name") or "",
                "identity_status": identity_status,
                "header_filer_matches_index": str(header_filer_matches_index).lower(),
                "header_filer_matches_accession": str(header_filer_matches_accession).lower(),
                "archive_path_matches_subject": str(archive_path_matches_subject).lower(),
                "filer_current_f80_ticker": filer_ticker,
                "subject_current_f80_ticker": subject_ticker,
                "subject_current_f80_from_external_filer": str(bool(subject_ticker and not filer_ticker)).lower(),
            })
        except Exception as error:
            base["error"] = f"{type(error).__name__}:{str(error)[:240]}"
        output.append(base)
    return output


def summarize(records: list[dict], invalid: dict, sample: list[dict], rows: list[dict],
              universe: list[str], cik_to_ticker: dict, unmapped: list[str],
              index_hash: str, tickers_hash: str, ua_source: str,
              secret_present: bool, secret_accepted: bool) -> dict:
    candidate_forms = Counter(row["form"] for row in records)
    candidate_path_formats = Counter(row.get("archive_path_format", "unknown") for row in records)
    index_accession_mismatches = sum(row["index_filer_cik"] != row["accession_filer_cik"] for row in records)
    candidate_f80_filers = sum(row["index_filer_cik"] in set(cik_to_ticker) for row in records)
    sample_forms = Counter(row["form"] for row in sample)
    sample_strata = Counter(f'{row["form"]}|{"F80_FILER" if row["index_filer_cik"] in set(cik_to_ticker) else "NON_F80_FILER"}'
                            for row in sample)
    status_counts = Counter(str(row.get("http_status", 0)) for row in rows)
    successful = [row for row in rows if row.get("http_status") == 200]
    identity_verified = [row for row in successful if row.get("identity_status") == "VERIFIED_SUBJECT_AND_FILER_CIKS"]
    filer_index_matches = [row for row in identity_verified if row.get("header_filer_matches_index") == "true"]
    filer_accession_matches = [row for row in identity_verified if row.get("header_filer_matches_accession") == "true"]
    archive_subject_matches = [row for row in identity_verified if row.get("archive_path_matches_subject") == "true"]
    subject_f80 = [row for row in identity_verified if row.get("subject_current_f80_ticker")]
    external_filer_subject_f80 = [row for row in subject_f80 if not row.get("filer_current_f80_ticker")]
    filer_f80 = [row for row in identity_verified if row.get("filer_current_f80_ticker")]
    if not sample:
        disposition = "NO_13DG_CANDIDATES_IN_QUARTER"
    elif index_accession_mismatches:
        disposition = "QUARANTINE_MASTER_INDEX_FILER_CIK_MISMATCH"
    elif len(successful) / len(sample) < 0.95:
        disposition = "INCONCLUSIVE_HEADER_FETCH_COVERAGE"
    elif len(identity_verified) / len(successful) < 0.95:
        disposition = "INCONCLUSIVE_SUBJECT_FILER_HEADER_COVERAGE"
    elif len(filer_index_matches) != len(identity_verified) or len(filer_accession_matches) != len(identity_verified):
        disposition = "QUARANTINE_INDEX_OR_ACCESSION_FILER_MISMATCH"
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
        "company_tickers_sha256": tickers_hash,
        "frozen_universe_size": len(universe),
        "current_f80_ticker_to_cik_mapped": len(cik_to_ticker),
        "current_f80_unmapped_tickers": unmapped,
        "historical_f80_membership_verified": False,
        "candidate_accessions": len(records),
        "candidate_form_counts": dict(candidate_forms),
        "candidate_archive_path_formats": dict(candidate_path_formats),
        "candidate_index_filer_accession_prefix_mismatches": index_accession_mismatches,
        "candidate_filer_current_f80_accessions": candidate_f80_filers,
        "invalid_master_index_rows": invalid,
        "sample_size": len(sample),
        "sample_form_counts": dict(sample_forms),
        "sample_strata_counts": dict(sample_strata),
        "header_http_status_counts": dict(status_counts),
        "header_http_200": len(successful),
        "header_identity_verified": len(identity_verified),
        "header_filer_matches_index": len(filer_index_matches),
        "header_filer_matches_accession": len(filer_accession_matches),
        "archive_path_matches_subject": len(archive_subject_matches),
        "current_f80_subject_matches": len(subject_f80),
        "current_f80_filer_matches": len(filer_f80),
        "current_f80_subject_matches_with_non_f80_filer": len(external_filer_subject_f80),
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
            "Global quarterly index discovery enumerates all filers; it does not restrict discovery to the frozen universe's filer CIKs.",
            "SUBJECT COMPANY and FILED BY are parsed separately; no accession-prefix or queried-filer fallback is allowed for subject identity.",
            "Current SEC company_tickers mapping is a discovery aid only, not historical F80 membership or an effective-dated security master.",
            "The SEC quarterly index is a retrospective/corrected index snapshot, not a prospective first-seen or exact public-dissemination record.",
            "No raw SEC header payloads are persisted; only accession metadata, response hashes and parser outputs are retained in the temporary artifact.",
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
    tickers_raw, tickers_status = fetch_sec_bytes(COMPANY_TICKERS_URL, user_agent)
    if tickers_status != 200:
        raise RuntimeError(f"company_tickers_http_{tickers_status}")
    company_tickers = json.loads(tickers_raw.decode("utf-8"))
    cik_to_ticker, unmapped = current_f80_cik_map(universe, company_tickers)
    records, invalid = parse_master_index(index_raw)
    by_accession = {}
    conflicting_accessions = []
    for row in records:
        previous = by_accession.get(row["accession"])
        if previous is None:
            by_accession[row["accession"]] = row
        elif previous != row:
            conflicting_accessions.append(row["accession"])
    records = list(by_accession.values())
    f80_ciks = set(cik_to_ticker)
    for row in records:
        row["_f80_ciks"] = f80_ciks
    sample = deterministic_stratified_sample(records)
    rows = fetch_header_sample(sample, cik_to_ticker, user_agent)
    index_hash = hashlib.sha256(index_raw).hexdigest()
    tickers_hash = hashlib.sha256(tickers_raw).hexdigest()
    summary = summarize(records, invalid, sample, rows, universe, cik_to_ticker,
                        unmapped, index_hash, tickers_hash, ua_source,
                        secret_present, secret_accepted)
    summary["conflicting_duplicate_accessions"] = sorted(set(conflicting_accessions))
    summary["conflicting_duplicate_accession_count"] = len(set(conflicting_accessions))
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
