#!/usr/bin/env python3
"""Audit SEC Form 4/4-A as-filed issuer-symbol labels; CIK remains primary."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, re, zipfile
from collections import Counter, defaultdict
from pathlib import Path

ARTIFACT_RUN_ID = 40606706518
ARTIFACT_ID = 12781850078
ARTIFACT_SHA256 = "203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66"
INNER = {
    "2012Q1": ("2012q1_form345.zip", "0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357"),
    "2026Q3": ("2026q3_form345.zip", "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3"),
}
PLACEHOLDERS = {"", "NONE", "(NONE)", "[NONE]", "NO SYMBOL", "N/A", "NA", "NULL", "NAN", "NONE]"}
SINGLE = re.compile(r"^[A-Z0-9][A-Z0-9.-]{0,9}$")
EXCHANGE = re.compile(r"^([A-Z0-9.-]{1,8}):\s*([A-Z0-9.-]{1,10})$")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify_symbol(raw: str | None) -> tuple[str, str | None]:
    value = (raw or "").strip().upper()
    if value in PLACEHOLDERS:
        return "MISSING_OR_PLACEHOLDER", None
    m = EXCHANGE.fullmatch(value)
    if m:
        return "EXCHANGE_PREFIXED_SINGLE", m.group(2)
    if SINGLE.fullmatch(value):
        return "SINGLE_TOKEN", value
    if any(c in value for c in (",", ";", "/", " ", "\t")):
        return "MULTI_OR_FREEFORM", None
    return "OTHER_NONCANONICAL", None


def parse_period_zip(raw: bytes, period: str) -> dict:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        sub = [n for n in names if n.lower().endswith("submission.tsv")]
        meta = [n for n in names if n.lower().endswith("metadata.json")]
        if len(sub) != 1 or len(meta) != 1:
            raise ValueError("Expected one SUBMISSION.tsv and one metadata.json")
        md = json.loads(z.read(meta[0]).decode("utf-8"))
        table = next((t for t in md.get("tables", []) if t.get("url") == "SUBMISSION.tsv"), None)
        if table is None:
            raise ValueError("SUBMISSION.tsv metadata schema missing")
        desc = {c.get("name"): " ".join((c.get("dc:description") or "").split()).casefold()
                for c in table["tableSchema"]["columns"]}
        expected = {
            "ISSUERCIK": "central index key of issuer",
            "ISSUERNAME": "name of issuer",
            "ISSUERTRADINGSYMBOL": "issuer trading symbol",
            "ACCESSION_NUMBER": "unique identifier assigned by the sec to each edgar submission",
        }
        if any(desc.get(k) != v for k, v in expected.items()):
            raise ValueError("SEC SUBMISSION metadata field definitions changed")
        rows = list(csv.DictReader(io.StringIO(z.read(sub[0]).decode("utf-8-sig")), delimiter="\t"))
    if not rows:
        raise ValueError("SUBMISSION.tsv is empty")
    f4 = [r for r in rows if (r.get("DOCUMENT_TYPE") or "").strip().upper() in {"4", "4/A"}]
    if not f4:
        raise ValueError("No Form 4 or 4/A rows found")
    ciks, raw_by_cik, candidates_by_cik, candidate_to_ciks = set(), defaultdict(set), defaultdict(set), defaultdict(set)
    classes, forms = Counter(), Counter()
    missing_filing = missing_event = 0
    for r in f4:
        cik = (r.get("ISSUERCIK") or "").strip()
        accession = (r.get("ACCESSION_NUMBER") or "").strip()
        if not re.fullmatch(r"\d{10}", cik):
            raise ValueError(f"Invalid issuer CIK: {cik!r}")
        if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
            raise ValueError(f"Invalid accession: {accession!r}")
        ciks.add(cik)
        forms[(r.get("DOCUMENT_TYPE") or "").strip().upper()] += 1
        missing_filing += not bool((r.get("FILING_DATE") or "").strip())
        missing_event += not bool((r.get("PERIOD_OF_REPORT") or "").strip())
        raw = (r.get("ISSUERTRADINGSYMBOL") or "").strip()
        cls, candidate = classify_symbol(raw)
        classes[cls] += 1
        if raw:
            raw_by_cik[cik].add(raw.upper())
        if candidate:
            candidates_by_cik[cik].add(candidate)
            candidate_to_ciks[candidate].add(cik)
    raw_ciks = {k: v for k, v in raw_by_cik.items() if v}
    candidate_ciks = {k: v for k, v in candidates_by_cik.items() if v}
    collisions = {k: len(v) for k, v in candidate_to_ciks.items() if len(v) > 1}
    n = len(f4)
    canonical_rows = classes["SINGLE_TOKEN"] + classes["EXCHANGE_PREFIXED_SINGLE"]
    return {
        "period": period, "all_submission_rows": len(rows), "form4_rows": n,
        "form4_original_rows": forms["4"], "form4_amendment_rows": forms["4/A"],
        "unique_issuer_ciks": len(ciks), "symbol_class_counts": dict(sorted(classes.items())),
        "canonical_symbol_rows": canonical_rows,
        "canonical_symbol_coverage_pct": round(100 * canonical_rows / n, 4),
        "issuer_ciks_with_one_raw_symbol_value": sum(len(v) == 1 for v in raw_ciks.values()),
        "issuer_ciks_with_multiple_raw_symbol_values": sum(len(v) > 1 for v in raw_ciks.values()),
        "issuer_ciks_with_one_canonical_symbol_candidate": sum(len(v) == 1 for v in candidate_ciks.values()),
        "issuer_ciks_with_multiple_canonical_symbol_candidates": sum(len(v) > 1 for v in candidate_ciks.values()),
        "issuer_ciks_without_canonical_symbol_candidate": len(ciks - set(candidate_ciks)),
        "issuer_ciks_with_no_nonblank_symbol_value": len(ciks - set(raw_ciks)),
        "issuer_ciks_with_only_noncanonical_or_placeholder_values": len(ciks - set(candidate_ciks)) - len(ciks - set(raw_ciks)),
        "ticker_candidates_reused_across_ciks": collisions,
        "max_ciks_per_ticker_candidate": max((len(v) for v in candidate_to_ciks.values()), default=0),
        "missing_filing_date_rows": missing_filing, "missing_period_of_report_rows": missing_event,
    }


def result(periods: dict, verification_mode: str, verified_hash: str) -> dict:
    return {
        "phase": 150, "status": "COMPLETED_AS_FILED_ISSUER_SYMBOL_FIELD_AUDIT",
        "source": {
            "provider": "U.S. Securities and Exchange Commission",
            "page": "https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets",
            "schema_documentation": "https://www.sec.gov/files/insider_transactions_readme.pdf",
            "artifact_run_id": ARTIFACT_RUN_ID, "artifact_id": ARTIFACT_ID,
            "artifact_sha256": ARTIFACT_SHA256,
            "inner_zip_sha256": {k: v[1] for k, v in INNER.items()},
            "verification_mode": verification_mode, "verified_input_sha256": verified_hash,
            "periods": list(INNER),
        },
        "periods": periods,
        "pit_and_identity_rules": [
            "ISSUERCIK is the primary issuer identity; the symbol is a label, not a permanent security key.",
            "Preserve raw symbols; do not split multi-class/free-form values.",
            "Join ACCESSION_NUMBER to EDGAR acceptance time; FILING_DATE is date-only and PERIOD_OF_REPORT is event date.",
            "Do not backdate the quarterly bulk dataset or a later ticker value into an earlier decision.",
        ],
    }


def audit_dir(directory: Path) -> dict:
    periods, verified = {}, {}
    for period, (filename, expected) in INNER.items():
        path = directory / filename
        if not path.is_file():
            raise ValueError(f"Missing artifact member: {filename}")
        raw = path.read_bytes()
        digest = sha256(raw)
        if digest != expected:
            raise ValueError(f"{period} ZIP SHA-256 mismatch: {digest}")
        verified[period] = digest
        periods[period] = parse_period_zip(raw, period)
    combined = sha256(json.dumps(verified, sort_keys=True).encode())
    return result(periods, "verified_inner_zip_hashes", combined)


def audit_outer(path: Path) -> dict:
    raw = path.read_bytes()
    if sha256(raw) != ARTIFACT_SHA256:
        raise ValueError("Phase 39 outer artifact SHA-256 mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        periods, verified = {}, {}
        for period, (filename, expected) in INNER.items():
            data = z.read(next(n for n in z.namelist() if n.lower().endswith(filename.lower())))
            if sha256(data) != expected:
                raise ValueError(f"{period} inner ZIP SHA-256 mismatch")
            verified[period] = expected
            periods[period] = parse_period_zip(data, period)
    return result(periods, "outer_and_inner_artifact_hashes", sha256(raw))


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--input-dir", type=Path)
    g.add_argument("--input-zip", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    out = audit_dir(a.input_dir) if a.input_dir else audit_outer(a.input_zip)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {"form4_rows": v["form4_rows"], "issuer_ciks": v["unique_issuer_ciks"],
                          "canonical_symbol_coverage_pct": v["canonical_symbol_coverage_pct"]}
                      for k, v in out["periods"].items()}, indent=2))

if __name__ == "__main__":
    main()
