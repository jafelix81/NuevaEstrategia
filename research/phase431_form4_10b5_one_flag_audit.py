#!/usr/bin/env python3
"""Audit SEC Form 345 AFF10B5ONE schema and filing-level semantics."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_aff10b5one(value: str | None) -> str:
    """Normalize source variants without treating blank/unrecognized as false."""
    if value is None or not str(value).strip():
        return "unknown"
    token = str(value).strip().lower()
    if token in {"1", "true", "t", "yes", "y"}:
        return "checked"
    if token in {"0", "false", "f", "no", "n"}:
        return "unchecked"
    return "unrecognized"


def _read_tsv(zf: zipfile.ZipFile, member: str) -> tuple[list[str], list[dict[str, str]]]:
    with zf.open(member) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        reader = csv.DictReader(text, delimiter="\t")
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def _flag_counts(rows: list[dict[str, str]], field_present: bool) -> dict[str, int]:
    if not field_present:
        return {"checked": 0, "unchecked": 0, "unknown": len(rows), "unrecognized": 0}
    counts = Counter(normalize_aff10b5one(row.get("AFF10B5ONE")) for row in rows)
    return {key: int(counts.get(key, 0)) for key in ("checked", "unchecked", "unknown", "unrecognized")}


def summarize_period(inner_zip_bytes: bytes, period_name: str) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(inner_zip_bytes)) as zf:
        members = set(zf.namelist())
        missing = sorted({"SUBMISSION.tsv", "NONDERIV_TRANS.tsv"} - members)
        if missing:
            raise ValueError(f"{period_name}: missing members {missing}")
        submission_header, submissions = _read_tsv(zf, "SUBMISSION.tsv")
        transaction_header, transactions = _read_tsv(zf, "NONDERIV_TRANS.tsv")
        flag_present = "AFF10B5ONE" in submission_header
        doc_type_counts = Counter(row.get("DOCUMENT_TYPE", "") for row in submissions)
        form4 = [row for row in submissions if row.get("DOCUMENT_TYPE") in {"4", "4/A"}]
        by_accession: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in transactions:
            by_accession[row.get("ACCESSION_NUMBER", "")].append(row)
        form4_flag_by_type = {}
        for doc_type in ("4", "4/A"):
            subset = [row for row in form4 if row.get("DOCUMENT_TYPE") == doc_type]
            form4_flag_by_type[doc_type] = {"filings": len(subset), "flag_counts": _flag_counts(subset, flag_present)}
        flag_by_accession = {
            row.get("ACCESSION_NUMBER", ""): normalize_aff10b5one(row.get("AFF10B5ONE")) if flag_present else "unknown"
            for row in form4
        }
        code_sets = {
            accession: {tx.get("TRANS_CODE", "") for tx in by_accession.get(accession, []) if tx.get("TRANS_CODE", "").strip()}
            for accession in flag_by_accession
        }
        checked_with_transactions = [
            accession for accession, flag in flag_by_accession.items()
            if flag == "checked" and by_accession.get(accession)
        ]
        checked_mixed = [a for a in checked_with_transactions if len(code_sets.get(a, set())) > 1]
        checked_p_mixed = [a for a in checked_with_transactions if "P" in code_sets.get(a, set()) and len(code_sets[a]) > 1]
        checked_s_mixed = [a for a in checked_with_transactions if "S" in code_sets.get(a, set()) and len(code_sets[a]) > 1]
        form4_transactions = [row for row in transactions if row.get("ACCESSION_NUMBER", "") in flag_by_accession]
        non_form4_transactions = [row for row in transactions if row.get("ACCESSION_NUMBER", "") not in flag_by_accession]
        transaction_code_stats = {}
        non_form4_code_rows = {}
        for code in ("P", "S"):
            code_rows = [row for row in form4_transactions if row.get("TRANS_CODE") == code]
            accessions = sorted({row.get("ACCESSION_NUMBER", "") for row in code_rows})
            filing_counts = Counter(flag_by_accession.get(acc, "unknown") for acc in accessions)
            row_counts = Counter(flag_by_accession.get(row.get("ACCESSION_NUMBER", ""), "unknown") for row in code_rows)
            transaction_code_stats[code] = {
                "transaction_rows": len(code_rows),
                "distinct_form4_accessions": len(accessions),
                "filing_flag_counts": {key: int(filing_counts.get(key, 0)) for key in ("checked", "unchecked", "unknown", "unrecognized")},
                "transaction_row_flag_counts_by_parent_filing": {key: int(row_counts.get(key, 0)) for key in ("checked", "unchecked", "unknown", "unrecognized")},
            }
            non_form4_code_rows[code] = sum(1 for row in non_form4_transactions if row.get("TRANS_CODE") == code)
        metadata_has_flag = False
        html_readme_has_flag = False
        for member in ("FORM_345_metadata.json", "insider_transactions_metadata.json"):
            if member in members and "AFF10B5ONE" in zf.read(member).decode("utf-8", "replace"):
                metadata_has_flag = True
                break
        for member in ("FORM_345_readme.htm", "insider_transactions_readme.htm"):
            if member in members and "AFF10B5ONE" in zf.read(member).decode("utf-8", "replace"):
                html_readme_has_flag = True
                break
        raw_flag_values = Counter(
            (row.get("AFF10B5ONE") or "").strip().lower() if flag_present else "<field_absent>"
            for row in form4
        )
        return {
            "period": period_name,
            "inner_zip_bytes": len(inner_zip_bytes),
            "inner_zip_sha256": sha256(inner_zip_bytes),
            "submission_rows": len(submissions),
            "document_type_counts": dict(sorted(doc_type_counts.items())),
            "submission_has_AFF10B5ONE": flag_present,
            "submission_header": submission_header,
            "transaction_header_has_AFF10B5ONE": "AFF10B5ONE" in transaction_header,
            "metadata_has_AFF10B5ONE": metadata_has_flag,
            "html_readme_has_AFF10B5ONE": html_readme_has_flag,
            "form4_and_4a_filings": len(form4),
            "form4_and_4a_flag_counts": _flag_counts(form4, flag_present),
            "form4_and_4a_raw_flag_value_counts": dict(sorted(raw_flag_values.items())),
            "form4_flag_counts_by_document_type": form4_flag_by_type,
            "checked_form4_with_transaction_rows": len(checked_with_transactions),
            "checked_form4_with_multiple_transaction_codes": len(checked_mixed),
            "checked_form4_with_P_and_other_codes": len(checked_p_mixed),
            "checked_form4_with_S_and_other_codes": len(checked_s_mixed),
            "transaction_code_stats": transaction_code_stats,
            "non_form4_P_or_S_transaction_rows_excluded": non_form4_code_rows,
        }


def audit_artifact(artifact_path: str | Path) -> dict[str, Any]:
    artifact_path = Path(artifact_path)
    outer_bytes = artifact_path.read_bytes()
    result: dict[str, Any] = {
        "source_artifact_file": artifact_path.name,
        "source_artifact_bytes": len(outer_bytes),
        "source_artifact_sha256": sha256(outer_bytes),
        "source_run_id": 40606706518,
        "source_artifact_id": 12781850078,
        "periods": {},
    }
    with zipfile.ZipFile(io.BytesIO(outer_bytes)) as outer:
        for period, member in (("2012Q1", "2012q1_form345.zip"), ("2026Q3", "2026q3_form345.zip")):
            if member not in outer.namelist():
                raise ValueError(f"Outer artifact missing {member}")
            result["periods"][period] = summarize_period(outer.read(member), period)
    result["interpretation"] = {
        "flag_grain": "submission/accession-level; not transaction-row-level",
        "unchecked_semantics": "not evidence that a transaction was discretionary or not under a grandfathered/other plan",
        "checked_semantics": "reported as intended to satisfy amended Rule 10b5-1(c); not a legal validation of the affirmative defense",
        "P_code_semantics": "open-market OR private purchase; footnotes are required to separate them",
        "pit_semantics": "quarterly flat-file publication is not the filing acceptance timestamp; join accession to EDGAR acceptance metadata",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-zip", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    summary = audit_artifact(args.artifact_zip)
    Path(args.output).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
