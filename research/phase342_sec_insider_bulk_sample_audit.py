#!/usr/bin/env python3
"""Phase 342: acquire and audit six official SEC Insider Transactions archives.

This is a source/schema/coverage audit only. It does not infer discretionary
intent from transaction code P, admit strict PIT, or test returns/alpha.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

ARCHIVES = {
    "2006Q1": {
        "filename": "2006q1_form345.zip",
        "url": "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/2006q1_form345.zip",
        "phase39_inner_sha256": None,
    },
    "2012Q1": {
        "filename": "2012q1_form345.zip",
        "url": "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/2012q1_form345.zip",
        "phase39_inner_sha256": "0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357",
        "phase271_expected": {"candidate_rows": 102, "candidate_accessions": 47, "candidate_issuer_ciks": 16},
    },
    "2023Q1": {
        "filename": "2023q1_form345.zip",
        "url": "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/2023q1_form345.zip",
        "phase39_inner_sha256": None,
    },
    "2023Q2": {
        "filename": "2023q2_form345.zip",
        "url": "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/2023q2_form345.zip",
        "phase39_inner_sha256": None,
    },
    "2025Q3": {
        "filename": "2025q3_form345.zip",
        "url": "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/2025q3_form345.zip",
        "phase39_inner_sha256": None,
    },
    "2026Q3": {
        "filename": "2026q3_form345.zip",
        "url": "https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/2026q3_form345.zip",
        "phase39_inner_sha256": "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3",
        "phase271_expected": {"candidate_rows": 85, "candidate_accessions": 59, "candidate_issuer_ciks": 31},
    },
}

TABLE_KEYS = {
    "SUBMISSION.tsv": ["ACCESSION_NUMBER"],
    "REPORTINGOWNER.tsv": ["ACCESSION_NUMBER", "RPTOWNERCIK"],
    "NONDERIV_TRANS.tsv": ["ACCESSION_NUMBER", "NONDERIV_TRANS_SK"],
    "NONDERIV_HOLDING.tsv": ["ACCESSION_NUMBER", "NONDERIV_HOLDING_SK"],
    "DERIV_TRANS.tsv": ["ACCESSION_NUMBER", "DERIV_TRANS_SK"],
    "DERIV_HOLDING.tsv": ["ACCESSION_NUMBER", "DERIV_HOLDING_SK"],
    "FOOTNOTES.tsv": ["ACCESSION_NUMBER", "FOOTNOTE_ID"],
    "OWNER_SIGNATURE.tsv": ["ACCESSION_NUMBER", "OWNERSIGNATURENAME"],
}
FOOTNOTE_ID_RE = re.compile(r"F\d+")
OPEN_MARKET_RE = re.compile(r"\bopen[- ]market\b", re.I)
PRIVATE_RE = re.compile(r"\bprivate\b", re.I)
PLAN_RE = re.compile(r"\b(?:10b5[- ]?1|plan|ESPP|employee stock purchase)\b", re.I)
MECHANICAL_RE = re.compile(
    r"\b(?:tax|withhold|exercise|grant|vesting|gift|automatic|option|award|"
    r"compensation|employee|match(?:ing)?)\b", re.I
)
COMMON_RE = re.compile(r"\bcommon (?:stock|shares)\b", re.I)
CHECKBOX_EFFECTIVE = date(2023, 4, 1)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_aff(value: str | None) -> str:
    value = (value or "").strip().lower()
    if value in {"1", "true", "yes"}:
        return "true"
    if value in {"0", "false", "no"}:
        return "false"
    return "unknown"


def parse_sec_date(value: str | None) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d-%B-%Y"):
        try:
            return datetime.strptime(value.upper(), fmt).date()
        except ValueError:
            pass
    return None


def aff_gate_required(filing_date: str | None) -> bool:
    parsed = parse_sec_date(filing_date)
    return bool(parsed and parsed >= CHECKBOX_EFFECTIVE)


def referenced_footnote_ids(row: dict[str, str]) -> set[str]:
    refs: set[str] = set()
    for key, value in row.items():
        if key.endswith("_FN"):
            refs.update(FOOTNOTE_ID_RE.findall(value or ""))
    return refs


def classify_purchase_row(
    row: dict[str, str],
    footnote_text: str,
    owner_count: int,
    aff_value: str | None,
    require_known_false: bool,
) -> dict[str, bool | str]:
    aff = normalize_aff(aff_value)
    return {
        "base": (
            row.get("DOCUMENT_TYPE") == "4"
            and row.get("TRANS_FORM_TYPE") == "4"
            and row.get("TRANS_CODE") == "P"
            and row.get("TRANS_ACQUIRED_DISP_CD") == "A"
        ),
        "explicit_open_market": bool(OPEN_MARKET_RE.search(footnote_text)),
        "no_private_disclosure": not bool(PRIVATE_RE.search(footnote_text)),
        "no_plan_disclosure": not bool(PLAN_RE.search(footnote_text)),
        "no_mechanical_disclosure": not bool(MECHANICAL_RE.search(footnote_text)),
        "direct_ownership": row.get("DIRECT_INDIRECT_OWNERSHIP") == "D",
        "single_reporting_owner": owner_count == 1,
        "common_stock_title": bool(COMMON_RE.search(row.get("SECURITY_TITLE", ""))),
        "aff_status": aff,
        "aff_gate": (aff == "false") if require_known_false else True,
    }


def read_tsv(zf: zipfile.ZipFile, member: str) -> tuple[list[str], list[dict[str, str]]]:
    with zf.open(member) as raw:
        wrapper = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        reader = csv.DictReader(wrapper, delimiter="\t")
        if not reader.fieldnames:
            raise ValueError(f"Missing header in {member}")
        return list(reader.fieldnames), list(reader)


def find_member(zf: zipfile.ZipFile, basename: str) -> str:
    matches = [n for n in zf.namelist() if Path(n).name.upper() == basename.upper()]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {basename}; found {matches}")
    return matches[0]


def key_audit(rows: list[dict[str, str]], key_fields: list[str]) -> dict[str, Any]:
    counts: Counter[tuple[str, ...]] = Counter()
    signatures: dict[tuple[str, ...], set[str]] = defaultdict(set)
    missing_key_rows = 0
    for row in rows:
        key = tuple((row.get(k) or "").strip() for k in key_fields)
        if any(not v for v in key):
            missing_key_rows += 1
            continue
        counts[key] += 1
        signatures[key].add(json.dumps(row, sort_keys=True, ensure_ascii=False))
    duplicate_keys = [k for k, n in counts.items() if n > 1]
    conflicting = [k for k in duplicate_keys if len(signatures[k]) > 1]
    return {
        "row_count": len(rows),
        "unique_key_count": len(counts),
        "missing_key_rows": missing_key_rows,
        "duplicate_key_count": len(duplicate_keys),
        "conflicting_duplicate_key_count": len(conflicting),
        "key_fields": key_fields,
    }


def audit_archive(path: Path, period: str, response_headers: str = "") -> dict[str, Any]:
    raw = path.read_bytes()
    archive_sha = sha256_bytes(raw)
    tables: dict[str, list[dict[str, str]]] = {}
    schemas: dict[str, list[str]] = {}
    table_audits: dict[str, dict[str, Any]] = {}
    members: list[str]
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        bad_member = zf.testzip()
        if bad_member:
            raise ValueError(f"Corrupt ZIP member: {bad_member}")
        members = zf.namelist()
        for table, key_fields in TABLE_KEYS.items():
            member = find_member(zf, table)
            fields, rows = read_tsv(zf, member)
            schemas[table] = fields
            tables[table] = rows
            table_audits[table] = key_audit(rows, key_fields)

    required_fields = {
        "SUBMISSION.tsv": [
            "ACCESSION_NUMBER", "DOCUMENT_TYPE", "FILING_DATE", "ISSUERCIK",
            "ISSUERNAME", "ISSUERTRADINGSYMBOL", "PERIOD_OF_REPORT", "DATE_OF_ORIG_SUB",
        ],
        "REPORTINGOWNER.tsv": ["ACCESSION_NUMBER", "RPTOWNERCIK"],
        "NONDERIV_TRANS.tsv": [
            "ACCESSION_NUMBER", "NONDERIV_TRANS_SK", "SECURITY_TITLE", "TRANS_DATE",
            "TRANS_FORM_TYPE", "TRANS_CODE", "TRANS_ACQUIRED_DISP_CD",
            "DIRECT_INDIRECT_OWNERSHIP",
        ],
        "FOOTNOTES.tsv": ["ACCESSION_NUMBER", "FOOTNOTE_ID", "FOOTNOTE_TXT"],
    }
    missing_fields = {
        table: sorted(set(fields) - set(schemas.get(table, [])))
        for table, fields in required_fields.items()
        if set(fields) - set(schemas.get(table, []))
    }

    submissions = tables["SUBMISSION.tsv"]
    submission_by_acc: dict[str, dict[str, str]] = {}
    submission_counts = Counter((r.get("ACCESSION_NUMBER") or "").strip() for r in submissions)
    duplicate_submission_accessions = sorted(k for k, n in submission_counts.items() if k and n > 1)
    for row in submissions:
        acc = (row.get("ACCESSION_NUMBER") or "").strip()
        if acc and submission_counts[acc] == 1:
            submission_by_acc[acc] = row

    accession_set = set(submission_by_acc)
    orphan_rows = {}
    for table, rows in tables.items():
        if table == "SUBMISSION.tsv":
            continue
        orphan_rows[table] = sum(
            1 for r in rows
            if (r.get("ACCESSION_NUMBER") or "").strip() not in accession_set
        )

    owners_by_acc: dict[str, set[str]] = defaultdict(set)
    for row in tables["REPORTINGOWNER.tsv"]:
        acc = (row.get("ACCESSION_NUMBER") or "").strip()
        owner = (row.get("RPTOWNERCIK") or "").strip()
        if acc and owner:
            owners_by_acc[acc].add(owner)

    footnotes_by_acc: dict[str, dict[str, str]] = defaultdict(dict)
    conflicting_footnotes: set[tuple[str, str]] = set()
    for row in tables["FOOTNOTES.tsv"]:
        acc = (row.get("ACCESSION_NUMBER") or "").strip()
        fid = (row.get("FOOTNOTE_ID") or "").strip()
        txt = row.get("FOOTNOTE_TXT") or ""
        if not acc or not fid:
            continue
        prior = footnotes_by_acc[acc].get(fid)
        if prior is not None and prior != txt:
            conflicting_footnotes.add((acc, fid))
        else:
            footnotes_by_acc[acc][fid] = txt

    stage_names = [
        "base", "explicit_open_market", "no_private_disclosure",
        "no_plan_disclosure", "no_mechanical_disclosure", "direct_ownership",
        "single_reporting_owner", "common_stock_title", "aff_gate",
    ]
    stage_counts = Counter()
    stage_accessions = {k: set() for k in stage_names}
    stage_issuers = {k: set() for k in stage_names}
    aff_counts = Counter()
    aff_by_regime = {"pre_effective_date": Counter(), "post_effective_date": Counter()}
    base_rows = 0
    missing_footnote_refs = 0
    conflicted_footnote_rows = 0
    candidate_rows: list[dict[str, Any]] = []
    transaction_rows = tables["NONDERIV_TRANS.tsv"]
    for tx in transaction_rows:
        acc = (tx.get("ACCESSION_NUMBER") or "").strip()
        sub = submission_by_acc.get(acc)
        if not sub:
            continue
        row = dict(tx)
        row["DOCUMENT_TYPE"] = (sub.get("DOCUMENT_TYPE") or "").strip()
        filing_date = sub.get("FILING_DATE") or ""
        require_aff_false = aff_gate_required(filing_date)
        aff = sub.get("AFF10B5ONE", "") if "AFF10B5ONE" in schemas["SUBMISSION.tsv"] else ""
        aff_status = normalize_aff(aff)
        aff_counts[aff_status] += 1
        regime = "post_effective_date" if require_aff_false else "pre_effective_date"
        aff_by_regime[regime][aff_status] += 1

        if not (
            row["DOCUMENT_TYPE"] == "4"
            and row.get("TRANS_FORM_TYPE") == "4"
            and row.get("TRANS_CODE") == "P"
            and row.get("TRANS_ACQUIRED_DISP_CD") == "A"
        ):
            continue
        base_rows += 1

        refs = referenced_footnote_ids(tx)
        foot_map = footnotes_by_acc.get(acc, {})
        missing = sorted(ref for ref in refs if ref not in foot_map)
        missing_footnote_refs += len(missing)
        conflict_refs = sorted(ref for ref in refs if (acc, ref) in conflicting_footnotes)
        if conflict_refs:
            conflicted_footnote_rows += 1
        footnote_text = " ".join(foot_map[ref] for ref in sorted(refs) if ref in foot_map)
        flags = classify_purchase_row(
            row, footnote_text, len(owners_by_acc.get(acc, set())), aff, require_aff_false
        )
        # Fail closed: a missing or conflicting referenced footnote cannot qualify.
        if missing or conflict_refs:
            flags["explicit_open_market"] = False

        issuer = (sub.get("ISSUERCIK") or "").strip()
        for stage in stage_names:
            if not flags[stage]:
                break
            stage_counts[stage] += 1
            stage_accessions[stage].add(acc)
            if issuer:
                stage_issuers[stage].add(issuer)
        if all(flags[k] for k in stage_names) and not missing and not conflict_refs:
            candidate_rows.append({
                "accession": acc,
                "issuer_cik": issuer,
                "issuer_symbol_as_filed": (sub.get("ISSUERTRADINGSYMBOL") or "").strip(),
                "filing_date": filing_date,
                "transaction_date": tx.get("TRANS_DATE", ""),
                "security_title": tx.get("SECURITY_TITLE", ""),
                "transaction_shares": tx.get("TRANS_SHARES", ""),
                "transaction_price_per_share": tx.get("TRANS_PRICEPERSHARE", ""),
                "aff10b5one": aff_status,
                "aff_gate_required": require_aff_false,
            })

    waterfall = []
    for stage in stage_names:
        waterfall.append({
            "stage": stage,
            "rows": stage_counts[stage],
            "unique_accessions": len(stage_accessions[stage]),
            "unique_issuer_ciks": len(stage_issuers[stage]),
        })

    duplicate_key_total = sum(x["duplicate_key_count"] for x in table_audits.values())
    conflicting_duplicate_total = sum(x["conflicting_duplicate_key_count"] for x in table_audits.values())
    orphan_total = sum(orphan_rows.values())
    return {
        "period": period,
        "source_url": ARCHIVES[period]["url"],
        "filename": path.name,
        "zip_bytes": len(raw),
        "zip_sha256": archive_sha,
        "zip_integrity": "PASS",
        "zip_members": members,
        "response_headers": response_headers,
        "table_schemas": schemas,
        "table_audits": table_audits,
        "submission_rows": len(submissions),
        "submission_document_type_counts": dict(sorted(Counter((r.get("DOCUMENT_TYPE") or "").strip() for r in submissions).items())),
        "submission_unique_accessions": len(submission_by_acc),
        "duplicate_submission_accessions": len(duplicate_submission_accessions),
        "reporting_owner_rows": len(tables["REPORTINGOWNER.tsv"]),
        "unique_reporting_owner_ciks": len({(r.get("RPTOWNERCIK") or "").strip() for r in tables["REPORTINGOWNER.tsv"] if (r.get("RPTOWNERCIK") or "").strip()}),
        "transaction_rows": len(transaction_rows),
        "footnote_rows": len(tables["FOOTNOTES.tsv"]),
        "aff10b5one_field_present": "AFF10B5ONE" in schemas["SUBMISSION.tsv"],
        "aff10b5one_transaction_row_counts": dict(sorted(aff_counts.items())),
        "aff10b5one_by_filing_date_regime": {
            k: dict(sorted(v.items())) for k, v in aff_by_regime.items()
        },
        "missing_required_fields": missing_fields,
        "orphan_rows_by_table": orphan_rows,
        "orphan_rows_total": orphan_total,
        "missing_referenced_footnote_ids_in_base_rows": missing_footnote_refs,
        "base_rows_with_conflicting_footnote_ids": conflicted_footnote_rows,
        "candidate_waterfall": waterfall,
        "candidate_rows": len(candidate_rows),
        "candidate_accessions": len({r["accession"] for r in candidate_rows}),
        "candidate_issuer_ciks": len({r["issuer_cik"] for r in candidate_rows if r["issuer_cik"]}),
        "candidate_events": candidate_rows,
        "key_duplicate_count_total": duplicate_key_total,
        "key_conflicting_duplicate_count_total": conflicting_duplicate_total,
    }


def parse_headers(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="latin-1", errors="replace").splitlines():
        if ":" not in line or line.startswith("HTTP/"):
            continue
        k, v = line.split(":", 1)
        out[k.strip().lower()] = v.strip()
    return out


def verify_phase39_artifact(path: Path) -> dict[str, Any]:
    outer = path.read_bytes()
    outer_sha = sha256_bytes(outer)
    expected_outer = "203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66"
    expected_inner = {
        "2012q1_form345.zip": "0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357",
        "2026q3_form345.zip": "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3",
    }
    if outer_sha != expected_outer:
        raise ValueError("Phase 39 artifact outer SHA-256 mismatch")
    with zipfile.ZipFile(io.BytesIO(outer)) as zf:
        result = {}
        for name, expected in expected_inner.items():
            data = zf.read(name)
            actual = sha256_bytes(data)
            if actual != expected:
                raise ValueError(f"Phase 39 inner SHA-256 mismatch: {name}")
            result[name] = {"sha256": actual, "bytes": len(data)}
    return {"artifact_id": 12781850078, "outer_sha256": outer_sha, "inner_archives": result}


def run(input_dir: Path, phase39_artifact: Path, output_dir: Path) -> dict[str, Any]:
    results = {}
    phase39 = verify_phase39_artifact(phase39_artifact)
    for period, spec in ARCHIVES.items():
        path = input_dir / spec["filename"]
        if not path.is_file():
            raise FileNotFoundError(path)
        headers = parse_headers(input_dir / f"{period}.headers")
        audit = audit_archive(path, period, headers)
        prior_hash = spec.get("phase39_inner_sha256")
        audit["phase39_hash_comparison"] = (
            "NOT_APPLICABLE" if not prior_hash else
            "MATCH" if audit["zip_sha256"] == prior_hash else "DIFFERENT_VINTAGE_OR_REPACKED"
        )
        expected = spec.get("phase271_expected")
        if expected and audit["zip_sha256"] == prior_hash:
            for key, value in expected.items():
                if audit[key] != value:
                    raise AssertionError(f"{period} Phase271 reproducibility mismatch: {key}")
            audit["phase271_reproduction"] = "PASS_EXACT_SOURCE_BYTES"
        elif expected:
            audit["phase271_reproduction"] = "NOT_COMPARABLE_SOURCE_BYTES_DIFFER"
        else:
            audit["phase271_reproduction"] = "NOT_PREVIOUSLY_SCREENED"
        results[period] = audit

    schema_gaps = {p: r["missing_required_fields"] for p, r in results.items() if r["missing_required_fields"]}
    invalid_zips = [p for p, r in results.items() if r["zip_integrity"] != "PASS"]
    duplicate_keys = {p: r["key_duplicate_count_total"] for p, r in results.items() if r["key_duplicate_count_total"]}
    orphan_rows = {p: r["orphan_rows_total"] for p, r in results.items() if r["orphan_rows_total"]}
    result = {
        "phase": 342,
        "status": "COMPLETED_SIX_ARCHIVE_SCHEMA_AND_HIGH_PRECISION_SCREEN_AUDIT",
        "source": {
            "name": "SEC Insider Transactions Data Sets",
            "official_page": "https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets",
            "coverage_sample": list(ARCHIVES),
            "downloaded_archive_count": len(results),
            "downloaded_total_bytes": sum(r["zip_bytes"] for r in results.values()),
            "retrieved_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "phase39_artifact": phase39,
        },
        "archives": results,
        "summary": {
            "periods": len(results),
            "all_zip_integrity_pass": not invalid_zips,
            "schema_gap_periods": schema_gaps,
            "duplicate_key_periods": duplicate_keys,
            "orphan_row_periods": orphan_rows,
            "phase39_crosschecks": {
                p: results[p]["phase39_hash_comparison"] for p in ("2012Q1", "2026Q3")
            },
            "candidate_rows_by_period": {p: r["candidate_rows"] for p, r in results.items()},
            "candidate_accessions_by_period": {p: r["candidate_accessions"] for p, r in results.items()},
            "candidate_issuers_by_period": {p: r["candidate_issuer_ciks"] for p, r in results.items()},
            "aff10b5one_field_presence_by_period": {p: r["aff10b5one_field_present"] for p, r in results.items()},
        },
        "decisions": {
            "phase271_screen_reproduced_only_when_exact_source_bytes_match": True,
            "aff10b5one_gate_applied_by_actual_filing_date_not_quarter_label": True,
            "pre_2023_04_01_missing_checkbox_means_unknown_not_false": True,
            "form4a_treated_as_separate_as_filed_vintage_not_new_trade": True,
            "transaction_code_p_alone_proves_open_market": False,
            "bulk_submission_date_is_exact_first_public_receipt": False,
            "owner_transaction_attribution_admitted": False,
            "effective_dated_security_identity_admitted": False,
            "strict_pit_admitted": False,
            "alpha_test_run": False,
            "return_test_run": False,
            "bootstrap_loo_run": False,
            "chronological_oos_run": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "parameters_changed": False,
            "data_purchased": False,
            "vendor_contacted": False,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase342_sec_insider_bulk_sample_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (output_dir / "phase342_candidate_summary.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["period", "submission_rows", "transaction_rows", "candidate_rows",
                  "candidate_accessions", "candidate_issuer_ciks", "aff10b5one_field_present",
                  "zip_sha256", "phase39_hash_comparison", "phase271_reproduction"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for period, audit in results.items():
            writer.writerow({
                "period": period,
                "submission_rows": audit["submission_rows"],
                "transaction_rows": audit["transaction_rows"],
                "candidate_rows": audit["candidate_rows"],
                "candidate_accessions": audit["candidate_accessions"],
                "candidate_issuer_ciks": audit["candidate_issuer_ciks"],
                "aff10b5one_field_present": audit["aff10b5one_field_present"],
                "zip_sha256": audit["zip_sha256"],
                "phase39_hash_comparison": audit["phase39_hash_comparison"],
                "phase271_reproduction": audit["phase271_reproduction"],
            })
    print("PHASE342_STATUS=" + result["status"])
    print("PHASE342_SUMMARY=" + json.dumps(result["summary"], sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--phase39-artifact", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.input_dir, args.phase39_artifact, args.output_dir)


if __name__ == "__main__":
    main()
