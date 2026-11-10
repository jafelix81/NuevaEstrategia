#!/usr/bin/env python3
"""Phase 271: conservative SEC Form 4 explicit-open-market purchase screen.

Consumes the immutable Phase 39 SEC Form 3/4/5 artifact. It deliberately does
not make a return test or claim that transaction code P proves a discretionary
public-market purchase. Only aggregate metadata is emitted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

EXPECTED_OUTER_SHA256 = "203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66"
EXPECTED_INNER_SHA256 = {
    "2012q1_form345.zip": "0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357",
    "2026q3_form345.zip": "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3",
}
FOOTNOTE_ID_RE = re.compile(r"F\\d+")
OPEN_MARKET_RE = re.compile(r"\\bopen[- ]market\\b", re.I)
PRIVATE_RE = re.compile(r"\\bprivate\\b", re.I)
PLAN_RE = re.compile(r"\\b(?:10b5[- ]?1|plan|ESPP|employee stock purchase)\\b", re.I)
MECHANICAL_RE = re.compile(
    r"\\b(?:tax|withhold|exercise|grant|vesting|gift|automatic|option|award|"
    r"compensation|employee|match(?:ing)?)\\b",
    re.I,
)
COMMON_RE = re.compile(r"\\bcommon (?:stock|shares)\\b", re.I)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_tsv(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    with zf.open(name) as raw:
        wrapper = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        return list(csv.DictReader(wrapper, delimiter="\\t"))


def normalize_aff(value: str | None) -> str:
    value = (value or "").strip().lower()
    if value in {"1", "true", "yes"}:
        return "true"
    if value in {"0", "false", "no"}:
        return "false"
    return "unknown"


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


def _period_result(inner_bytes: bytes, period: str) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(inner_bytes)) as zf:
        submissions = read_tsv(zf, "SUBMISSION.tsv")
        transactions = read_tsv(zf, "NONDERIV_TRANS.tsv")
        footnotes = read_tsv(zf, "FOOTNOTES.tsv")
        owners = read_tsv(zf, "REPORTINGOWNER.tsv")

    submission_by_acc = {r["ACCESSION_NUMBER"]: r for r in submissions}
    owners_by_acc = Counter(r["ACCESSION_NUMBER"] for r in owners)
    footnotes_by_acc: dict[str, dict[str, str]] = {}
    for row in footnotes:
        footnotes_by_acc.setdefault(row["ACCESSION_NUMBER"], {})[row["FOOTNOTE_ID"]] = row["FOOTNOTE_TXT"]

    require_known_false = date.fromisoformat(period[:4] + "-04-01") >= date(2023, 4, 1)
    stages = [
        "base",
        "explicit_open_market",
        "no_private_disclosure",
        "no_plan_disclosure",
        "no_mechanical_disclosure",
        "direct_ownership",
        "single_reporting_owner",
        "common_stock_title",
    ]
    if require_known_false:
        stages.append("aff_gate")

    counts = Counter()
    accession_sets = {name: set() for name in stages}
    issuer_sets = {name: set() for name in stages}
    base_rows = 0
    missing_footnote_refs = 0
    aff_counts = Counter()
    for tx in transactions:
        acc = tx["ACCESSION_NUMBER"]
        sub = submission_by_acc.get(acc)
        if not sub:
            continue
        row = dict(tx)
        row["DOCUMENT_TYPE"] = sub.get("DOCUMENT_TYPE", "")
        foot_map = footnotes_by_acc.get(acc, {})
        referenced_ids: set[str] = set()
        for key, value in tx.items():
            if key.endswith("_FN"):
                referenced_ids.update(FOOTNOTE_ID_RE.findall(value or ""))
        missing_footnote_refs += sum(1 for ref in referenced_ids if ref not in foot_map)
        footnote_text = " ".join(foot_map[ref] for ref in sorted(referenced_ids) if ref in foot_map)
        aff = sub.get("AFF10B5ONE", "")
        aff_counts[normalize_aff(aff)] += 1

        flags = classify_purchase_row(
            row,
            footnote_text,
            owners_by_acc.get(acc, 0),
            aff,
            require_known_false,
        )
        if not flags["base"]:
            continue
        base_rows += 1
        issuer = sub.get("ISSUERCIK", "")
        for stage in stages:
            if not flags[stage]:
                break
            counts[stage] += 1
            accession_sets[stage].add(acc)
            if issuer:
                issuer_sets[stage].add(issuer)

    waterfall = []
    for stage in stages:
        waterfall.append({
            "stage": stage,
            "rows": counts[stage],
            "unique_accessions": len(accession_sets[stage]),
            "unique_issuer_ciks": len(issuer_sets[stage]),
        })

    final_stage = stages[-1]
    return {
        "period": period,
        "base_original_form4_table_i_purchase_rows": base_rows,
        "aff_status_counts_across_nonderivative_transaction_rows": dict(sorted(aff_counts.items())),
        "missing_referenced_footnote_ids_in_base_sample": missing_footnote_refs,
        "waterfall": waterfall,
        "candidate_rows": counts[final_stage],
        "candidate_accessions": len(accession_sets[final_stage]),
        "candidate_issuer_ciks": len(issuer_sets[final_stage]),
        "aff_gate_required": require_known_false,
        "candidate_plan_status": "known_false" if require_known_false else "unknown_pre_checkbox_era",
    }


def analyze_artifact(path: str | Path) -> dict[str, Any]:
    outer = Path(path).read_bytes()
    outer_sha = sha256_bytes(outer)
    if outer_sha != EXPECTED_OUTER_SHA256:
        raise ValueError("Phase 39 outer artifact SHA-256 mismatch")
    results = {}
    with zipfile.ZipFile(io.BytesIO(outer)) as outer_zip:
        for filename, expected_hash in EXPECTED_INNER_SHA256.items():
            inner = outer_zip.read(filename)
            if sha256_bytes(inner) != expected_hash:
                raise ValueError(f"Inner source SHA-256 mismatch: {filename}")
            period = "2012Q1" if filename.startswith("2012") else "2026Q3"
            results[period] = _period_result(inner, period)

    return {
        "phase": 271,
        "date": "2026-11-10",
        "source_artifact": {
            "workflow_run_id": 40606706518,
            "artifact_id": 12781850078,
            "outer_sha256": outer_sha,
            "inner_sha256": EXPECTED_INNER_SHA256,
        },
        "method": {
            "population": "original Form 4 submissions, Table I NONDERIV_TRANS rows, TRANS_FORM_TYPE=4, code P, acquired/disposed=A",
            "high_precision_screen": [
                "transaction-row footnote explicitly says open market",
                "no explicit private wording",
                "no explicit 10b5-1/plan/ESPP wording",
                "no explicit tax/withholding/exercise/grant/vesting/gift/automatic/option/award/compensation/employee/matching wording",
                "direct ownership",
                "exactly one reporting owner on accession",
                "security title explicitly contains common stock or common shares",
                "for post-2023-04-01 filings, AFF10B5ONE explicitly false",
            ],
            "limitations": [
                "Text screen is deliberately high-precision/low-recall and requires manual semantic adjudication before any event use.",
                "Absence of private/plan/mechanical wording does not prove a discretionary open-market trade.",
                "AFF10B5ONE=false does not prove absence of a non-Rule-10b5-1 plan.",
                "Pre-2023-04-01 AFF10B5ONE is unknown, never false.",
                "FILING_DATE is date-only; this audit does not reconcile acceptance timestamps for every accession.",
                "Only two endpoint quarters are sampled; no continuous history or frozen-universe coverage is measured.",
            ],
        },
        "periods": results,
        "admission": {
            "strict_pit": False,
            "universe_coverage": False,
            "return_test": False,
            "alpha": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "purchase_or_vendor_contact": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = analyze_artifact(args.artifact)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    print("PHASE271_STATUS=EXPLICIT_OPEN_MARKET_PURCHASE_CANDIDATES_ONLY_NO_PIT_NO_ALPHA")
    for period, data in result["periods"].items():
        print(f"{period}: {data['candidate_rows']} rows / {data['candidate_accessions']} accessions / {data['candidate_issuer_ciks']} issuers")
    print("PIT_ADMISSION=false ALPHA_ADMISSION=false F80_FROZEN=true")


if __name__ == "__main__":
    main()
