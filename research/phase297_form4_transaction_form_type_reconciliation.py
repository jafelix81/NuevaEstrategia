"""Phase 297: reconcile Form 4 bulk transaction-form type and owner/footnote gates.

Offline-only audit of the immutable Phase 294 SEC Form 345 sample artifact.
No SEC requests, return tests, or alpha claims are made here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

EXPECTED_OUTER_SHA256 = "8b256375a68ffc581134e3fb05dd96ca3a02f6acd47925a003aa3f4b3d1680f4"
EXPECTED_INNER_SHA256 = {
    "2006q1_form345.zip": "62becdadbe5eaff68f03edefe2ba2357c8bb498a1f825b697003e087cf98e6ce",
    "2012q1_form345.zip": "0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357",
    "2023q1_form345.zip": "0b476188f52a0862e71886eb31a81f6345fc6616403b52188484aef0438cfcfb",
    "2023q2_form345.zip": "7e636787231ae0f00accf5c3627298402dedd1aefffd7c50fb48292e5d3a8fbb",
    "2025q3_form345.zip": "9c57f272b7230500771f661bc1fe181527ed6b76a6f45d23a910c7fc7e9fcfa4",
    "2026q3_form345.zip": "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3",
}
EXPECTED_QUARTERS = {
    "2006q1_form345.zip": "2006Q1",
    "2012q1_form345.zip": "2012Q1",
    "2023q1_form345.zip": "2023Q1",
    "2023q2_form345.zip": "2023Q2",
    "2025q3_form345.zip": "2025Q3",
    "2026q3_form345.zip": "2026Q3",
}
FOOTNOTE_ID_RE = re.compile(r"F\d+")
OPEN_MARKET_RE = re.compile(r"\bopen[- ]market\b", re.I)
PRIVATE_RE = re.compile(r"\bprivate\b", re.I)
PLAN_RE = re.compile(r"\b(?:10b5[- ]?1|plan|ESPP|employee stock purchase)\b", re.I)
MECHANICAL_RE = re.compile(
    r"\b(?:tax|withhold|exercise|grant|vesting|gift|automatic|option|award|"
    r"compensation|employee|match(?:ing)?)\b",
    re.I,
)
COMMON_RE = re.compile(r"\bcommon (?:stock|shares)\b", re.I)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_tsv(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    with zf.open(name, "r") as raw:
        wrapper = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        return list(csv.DictReader(wrapper, delimiter="\t", quotechar='"'))


def parse_date(value: str | None) -> date | None:
    raw = (value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    return None


def parse_number(value: str | None) -> float | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        result = float(raw.replace(",", ""))
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def normalize_aff(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if raw in {"1", "true", "yes"}:
        return "true"
    if raw in {"0", "false", "no"}:
        return "false"
    return "unknown"


def build_owner_sets(rows: list[dict[str, str]]) -> tuple[dict[str, set[str]], int]:
    owners: dict[str, set[str]] = defaultdict(set)
    row_counts: Counter[str] = Counter()
    for row in rows:
        accession = (row.get("ACCESSION_NUMBER") or "").strip()
        cik = (row.get("RPTOWNERCIK") or "").strip()
        if accession and cik:
            owners[accession].add(cik)
            row_counts[accession] += 1
    duplicate_owner_rows = sum(
        row_counts[acc] - len(ciks) for acc, ciks in owners.items()
    )
    return dict(owners), duplicate_owner_rows


def build_footnote_map(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = defaultdict(dict)
    for row in rows:
        accession = (row.get("ACCESSION_NUMBER") or "").strip()
        footnote_id = (row.get("FOOTNOTE_ID") or "").strip()
        if accession and footnote_id:
            result[accession][footnote_id] = row.get("FOOTNOTE_TXT") or ""
    return dict(result)


def referenced_footnote_text(
    transaction: dict[str, str],
    accession: str,
    footnotes_by_acc: dict[str, dict[str, str]],
) -> tuple[str, list[str], list[str]]:
    refs: set[str] = set()
    for key, value in transaction.items():
        if key.endswith("_FN"):
            refs.update(FOOTNOTE_ID_RE.findall(value or ""))
    foot_map = footnotes_by_acc.get(accession, {})
    missing = sorted(ref for ref in refs if ref not in foot_map)
    text = " ".join(foot_map[ref] for ref in sorted(refs) if ref in foot_map)
    return text, sorted(refs), missing


def phase296_candidate(
    transaction: dict[str, str],
    submission: dict[str, str],
    owner_count: int,
) -> tuple[bool, bool, int | None]:
    """Return (Phase296 broad candidate, corrected Table-I candidate, lag days)."""
    filing = parse_date(submission.get("FILING_DATE"))
    trans = parse_date(transaction.get("TRANS_DATE"))
    lag = (filing - trans).days if filing and trans else None
    shares = parse_number(transaction.get("TRANS_SHARES"))
    price = parse_number(transaction.get("TRANS_PRICEPERSHARE"))
    broad = (
        transaction.get("TRANS_CODE") == "P"
        and transaction.get("TRANS_ACQUIRED_DISP_CD") == "A"
        and transaction.get("DIRECT_INDIRECT_OWNERSHIP") == "D"
        and shares is not None and shares > 0
        and price is not None and price > 0
        and submission.get("DOCUMENT_TYPE") == "4"
        and owner_count == 1
        and lag is not None and 0 <= lag <= 2
    )
    corrected = broad and transaction.get("TRANS_FORM_TYPE") == "4"
    return broad, corrected, lag


def high_precision_flags(
    transaction: dict[str, str],
    submission: dict[str, str],
    footnote_text: str,
    owner_count: int,
) -> dict[str, bool]:
    filing = parse_date(submission.get("FILING_DATE"))
    aff_applies = filing is not None and filing >= date(2023, 4, 1)
    shares = parse_number(transaction.get("TRANS_SHARES"))
    price = parse_number(transaction.get("TRANS_PRICEPERSHARE"))
    return {
        "base": (
            submission.get("DOCUMENT_TYPE") == "4"
            and transaction.get("TRANS_FORM_TYPE") == "4"
            and transaction.get("TRANS_CODE") == "P"
            and transaction.get("TRANS_ACQUIRED_DISP_CD") == "A"
        ),
        "explicit_open_market": bool(OPEN_MARKET_RE.search(footnote_text)),
        "no_private_disclosure": not bool(PRIVATE_RE.search(footnote_text)),
        "no_plan_disclosure": not bool(PLAN_RE.search(footnote_text)),
        "no_mechanical_disclosure": not bool(MECHANICAL_RE.search(footnote_text)),
        "direct_ownership": transaction.get("DIRECT_INDIRECT_OWNERSHIP") == "D",
        "single_reporting_owner": owner_count == 1,
        "common_stock_title": bool(COMMON_RE.search(transaction.get("SECURITY_TITLE", ""))),
        "aff_gate_applicable": aff_applies,
        "aff_gate_pass": (normalize_aff(submission.get("AFF10B5ONE")) == "false") if aff_applies else True,
        "positive_price_and_shares": shares is not None and shares > 0 and price is not None and price > 0,
    }


def analyze_period(inner_bytes: bytes, period: str) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(inner_bytes)) as zf:
        submissions = read_tsv(zf, "SUBMISSION.tsv")
        transactions = read_tsv(zf, "NONDERIV_TRANS.tsv")
        footnotes = read_tsv(zf, "FOOTNOTES.tsv")
        reporting_owners = read_tsv(zf, "REPORTINGOWNER.tsv")

    submission_by_acc: dict[str, dict[str, str]] = {}
    duplicate_submission_accessions = 0
    for row in submissions:
        accession = (row.get("ACCESSION_NUMBER") or "").strip()
        if not accession:
            continue
        if accession in submission_by_acc:
            duplicate_submission_accessions += 1
            continue
        if (row.get("DOCUMENT_TYPE") or "").strip().upper() in {"4", "4/A"}:
            submission_by_acc[accession] = row

    owner_sets, duplicate_owner_rows = build_owner_sets(reporting_owners)
    footnotes_by_acc = build_footnote_map(footnotes)
    counts = Counter()
    broad_form_type_counts: Counter[str] = Counter()
    phase296_aff_counts: Counter[str] = Counter()
    corrected_aff_counts: Counter[str] = Counter()
    lag_counts: Counter[str] = Counter()
    high_precision_counts = Counter()
    high_precision_sets: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"accessions": set(), "issuers": set()}
    )
    missing_footnote_refs = 0
    total_matched_transaction_rows = 0
    broad_footnote_rows = 0
    phase296_rows = 0
    corrected_rows = 0
    phase296_accs: set[str] = set()
    phase296_issuers: set[str] = set()
    phase296_owners: set[str] = set()
    corrected_accs: set[str] = set()
    corrected_issuers: set[str] = set()
    corrected_owners: set[str] = set()
    excluded_type5_accs: set[str] = set()
    excluded_type5_issuers: set[str] = set()
    excluded_type5_owners: set[str] = set()
    excluded_type5_rows = 0

    for tx in transactions:
        accession = (tx.get("ACCESSION_NUMBER") or "").strip()
        submission = submission_by_acc.get(accession)
        if not submission:
            continue
        total_matched_transaction_rows += 1
        owner_ciks = owner_sets.get(accession, set())
        owner_count = len(owner_ciks)
        issuer = (submission.get("ISSUERCIK") or "").strip()
        footnote_text, refs, missing = referenced_footnote_text(tx, accession, footnotes_by_acc)
        missing_footnote_refs += len(missing)

        is_broad_p_a_d = (
            tx.get("TRANS_CODE") == "P"
            and tx.get("TRANS_ACQUIRED_DISP_CD") == "A"
            and tx.get("DIRECT_INDIRECT_OWNERSHIP") == "D"
        )
        if is_broad_p_a_d:
            counts["broad_p_a_d_rows"] += 1
            broad_form_type_counts[tx.get("TRANS_FORM_TYPE") or "UNKNOWN"] += 1
            if refs:
                broad_footnote_rows += 1
            shares = parse_number(tx.get("TRANS_SHARES"))
            price = parse_number(tx.get("TRANS_PRICEPERSHARE"))
            if shares is not None and shares > 0 and price is not None and price > 0:
                counts["positive_price_share_rows_all_types"] += 1
                if tx.get("TRANS_FORM_TYPE") == "4":
                    counts["positive_price_share_rows_type4"] += 1
                    if owner_count == 1:
                        counts["positive_price_share_rows_type4_single_owner"] += 1

        broad_candidate, corrected_candidate, lag = phase296_candidate(tx, submission, owner_count)
        if broad_candidate:
            phase296_rows += 1
            phase296_accs.add(accession)
            if issuer:
                phase296_issuers.add(issuer)
            phase296_owners.update(owner_ciks)
            phase296_aff_counts[normalize_aff(submission.get("AFF10B5ONE"))] += 1
            if lag is not None:
                lag_counts[str(lag)] += 1
            if tx.get("TRANS_FORM_TYPE") == "5":
                excluded_type5_rows += 1
                excluded_type5_accs.add(accession)
                if issuer:
                    excluded_type5_issuers.add(issuer)
                excluded_type5_owners.update(owner_ciks)

        if corrected_candidate:
            corrected_rows += 1
            corrected_accs.add(accession)
            if issuer:
                corrected_issuers.add(issuer)
            corrected_owners.update(owner_ciks)
            corrected_aff_counts[normalize_aff(submission.get("AFF10B5ONE"))] += 1

        flags = high_precision_flags(tx, submission, footnote_text, owner_count)
        if not flags["base"]:
            continue
        stages = [
            "base", "explicit_open_market", "no_private_disclosure",
            "no_plan_disclosure", "no_mechanical_disclosure", "direct_ownership",
            "single_reporting_owner", "common_stock_title",
        ]
        if flags["aff_gate_applicable"]:
            stages.append("aff_gate_pass")
        stages.append("positive_price_and_shares")
        passed = True
        for stage in stages:
            if passed and flags[stage]:
                high_precision_counts[stage] += 1
                high_precision_sets[stage]["accessions"].add(accession)
                if issuer:
                    high_precision_sets[stage]["issuers"].add(issuer)
            else:
                passed = False

    stage_names = [
        "base", "explicit_open_market", "no_private_disclosure",
        "no_plan_disclosure", "no_mechanical_disclosure", "direct_ownership",
        "single_reporting_owner", "common_stock_title",
    ]
    filing_cutoff_applies = any(
        parse_date(row.get("FILING_DATE")) is not None
        and parse_date(row.get("FILING_DATE")) >= date(2023, 4, 1)
        for row in submission_by_acc.values()
    )
    if filing_cutoff_applies:
        stage_names.append("aff_gate_pass")
    stage_names.append("positive_price_and_shares")
    waterfall = []
    for stage in stage_names:
        waterfall.append({
            "stage": stage,
            "rows": high_precision_counts[stage],
            "unique_accessions": len(high_precision_sets[stage]["accessions"]),
            "unique_issuer_ciks": len(high_precision_sets[stage]["issuers"]),
        })
    final_screen_stage = "aff_gate_pass" if filing_cutoff_applies else "common_stock_title"

    return {
        "period": period,
        "source_rows": {
            "all_submission_rows": len(submissions),
            "form4_and_4a_accessions": len(submission_by_acc),
            "matched_nonderivative_transaction_rows": total_matched_transaction_rows,
            "reporting_owner_accessions": len(owner_sets),
            "duplicate_submission_accessions": duplicate_submission_accessions,
            "duplicate_reporting_owner_rows": duplicate_owner_rows,
            "missing_referenced_footnote_ids": missing_footnote_refs,
        },
        "owner_attribution": {
            "single_owner_accessions": sum(1 for acc in submission_by_acc if len(owner_sets.get(acc, set())) == 1),
            "multiple_owner_accessions": sum(1 for acc in submission_by_acc if len(owner_sets.get(acc, set())) > 1),
            "no_owner_accessions": sum(1 for acc in submission_by_acc if len(owner_sets.get(acc, set())) == 0),
        },
        "phase296_reconciliation": {
            "broad_p_a_d_rows": counts["broad_p_a_d_rows"],
            "broad_p_a_d_transaction_form_type_counts": dict(sorted(broad_form_type_counts.items())),
            "broad_p_a_d_rows_with_any_footnote_reference": broad_footnote_rows,
            "positive_price_share_rows_all_transaction_form_types": counts["positive_price_share_rows_all_types"],
            "positive_price_share_rows_transaction_form_type_4": counts["positive_price_share_rows_type4"],
            "positive_price_share_rows_type4_single_owner": counts["positive_price_share_rows_type4_single_owner"],
            "phase296_original_conservative_rows_without_transaction_form_type_gate": phase296_rows,
            "phase296_original_conservative_accessions": len(phase296_accs),
            "phase296_original_conservative_issuer_ciks": len(phase296_issuers),
            "phase296_original_conservative_owner_ciks": len(phase296_owners),
            "phase296_original_aff10b5one_status_counts": dict(sorted(phase296_aff_counts.items())),
            "phase296_lag_days": dict(sorted(lag_counts.items(), key=lambda x: int(x[0]))),
            "corrected_table_i_type4_conservative_rows": corrected_rows,
            "corrected_table_i_type4_conservative_accessions": len(corrected_accs),
            "corrected_table_i_type4_conservative_issuer_ciks": len(corrected_issuers),
            "corrected_table_i_type4_conservative_owner_ciks": len(corrected_owners),
            "corrected_aff10b5one_status_counts": dict(sorted(corrected_aff_counts.items())),
            "excluded_transaction_form_type_5_rows": excluded_type5_rows,
            "excluded_transaction_form_type_5_accessions": len(excluded_type5_accs),
            "excluded_transaction_form_type_5_issuer_ciks": len(excluded_type5_issuers),
            "excluded_transaction_form_type_5_owner_ciks": len(excluded_type5_owners),
        },
        "_internal_identities": {
            "phase296_accessions": sorted(phase296_accs),
            "phase296_issuers": sorted(phase296_issuers),
            "phase296_owners": sorted(phase296_owners),
            "corrected_accessions": sorted(corrected_accs),
            "corrected_issuers": sorted(corrected_issuers),
            "corrected_owners": sorted(corrected_owners),
            "excluded_type5_accessions": sorted(excluded_type5_accs),
            "excluded_type5_issuers": sorted(excluded_type5_issuers),
            "excluded_type5_owners": sorted(excluded_type5_owners),
        },
        "high_precision_footnote_screen": {
            "waterfall": waterfall,
            "high_precision_rows_before_positive_price_share_gate": high_precision_counts[final_screen_stage],
            "high_precision_accessions_before_positive_price_share_gate": len(high_precision_sets[final_screen_stage]["accessions"]),
            "high_precision_issuer_ciks_before_positive_price_share_gate": len(high_precision_sets[final_screen_stage]["issuers"]),
            "positive_price_share_rows_after_all_high_precision_gates": high_precision_counts["positive_price_and_shares"],
            "positive_price_share_accessions_after_all_high_precision_gates": len(high_precision_sets["positive_price_and_shares"]["accessions"]),
            "positive_price_share_issuer_ciks_after_all_high_precision_gates": len(high_precision_sets["positive_price_and_shares"]["issuers"]),
            "aff10b5one_gate_applied_by_actual_filing_date": filing_cutoff_applies,
        },
    }


def analyze_artifact(path: str | Path) -> dict[str, Any]:
    outer = Path(path).read_bytes()
    outer_sha = sha256_bytes(outer)
    if outer_sha != EXPECTED_OUTER_SHA256:
        raise ValueError("Phase 294 outer artifact SHA-256 mismatch")
    results = {}
    global_data = {
        "phase296_accessions": set(), "phase296_issuers": set(), "phase296_owners": set(),
        "corrected_accessions": set(), "corrected_issuers": set(), "corrected_owners": set(),
        "excluded_accessions": set(), "excluded_issuers": set(), "excluded_owners": set(),
        "aff_original": Counter(), "aff_corrected": Counter(),
    }
    with zipfile.ZipFile(io.BytesIO(outer)) as outer_zip:
        for filename, expected_hash in EXPECTED_INNER_SHA256.items():
            inner = outer_zip.read(f"raw/{filename}")
            if sha256_bytes(inner) != expected_hash:
                raise ValueError(f"Phase 294 inner archive SHA-256 mismatch: {filename}")
            result = analyze_period(inner, EXPECTED_QUARTERS[filename])
            results[EXPECTED_QUARTERS[filename]] = result
            rec = result["phase296_reconciliation"]
            ids = result["_internal_identities"]
            for key in ("phase296_accessions", "phase296_issuers", "phase296_owners",
                        "corrected_accessions", "corrected_issuers", "corrected_owners"):
                global_data[key].update(ids[key])
            for source_key, target_key in (
                ("excluded_type5_accessions", "excluded_accessions"),
                ("excluded_type5_issuers", "excluded_issuers"),
                ("excluded_type5_owners", "excluded_owners"),
            ):
                global_data[target_key].update(ids[source_key])
            global_data["aff_original"].update(rec["phase296_original_aff10b5one_status_counts"])
            global_data["aff_corrected"].update(rec["corrected_aff10b5one_status_counts"])

    for result in results.values():
        result.pop("_internal_identities", None)

    return {
        "phase": 297,
        "date": "2026-11-11",
        "source": {
            "phase294_workflow_run_id": 43083625013,
            "phase294_artifact_id": 13884014630,
            "outer_sha256": outer_sha,
            "inner_sha256": EXPECTED_INNER_SHA256,
            "sample_design": "six purposive quarter archives: 2006Q1, 2012Q1, 2023Q1, 2023Q2, 2025Q3, 2026Q3",
        },
        "aggregate": {
            "form4_and_4a_accessions": sum(r["source_rows"]["form4_and_4a_accessions"] for r in results.values()),
            "single_owner_accessions": sum(r["owner_attribution"]["single_owner_accessions"] for r in results.values()),
            "multiple_owner_accessions": sum(r["owner_attribution"]["multiple_owner_accessions"] for r in results.values()),
            "no_owner_accessions": sum(r["owner_attribution"]["no_owner_accessions"] for r in results.values()),
            "phase296_original_conservative_rows": sum(r["phase296_reconciliation"]["phase296_original_conservative_rows_without_transaction_form_type_gate"] for r in results.values()),
            "corrected_table_i_type4_conservative_rows": sum(r["phase296_reconciliation"]["corrected_table_i_type4_conservative_rows"] for r in results.values()),
            "excluded_transaction_form_type_5_rows": sum(r["phase296_reconciliation"]["excluded_transaction_form_type_5_rows"] for r in results.values()),
            "phase296_original_unique_accessions": len(global_data["phase296_accessions"]),
            "corrected_unique_accessions": len(global_data["corrected_accessions"]),
            "excluded_type5_unique_accessions": len(global_data["excluded_accessions"]),
            "phase296_original_unique_issuer_ciks": len(global_data["phase296_issuers"]),
            "corrected_unique_issuer_ciks": len(global_data["corrected_issuers"]),
            "excluded_type5_unique_issuer_ciks": len(global_data["excluded_issuers"]),
            "phase296_original_unique_owner_ciks": len(global_data["phase296_owners"]),
            "corrected_unique_owner_ciks": len(global_data["corrected_owners"]),
            "excluded_type5_unique_owner_ciks": len(global_data["excluded_owners"]),
            "phase296_original_aff10b5one_status_counts": dict(sorted(global_data["aff_original"].items())),
            "corrected_aff10b5one_status_counts": dict(sorted(global_data["aff_corrected"].items())),
            "high_precision_rows_before_positive_price_share_gate": sum(r["high_precision_footnote_screen"]["high_precision_rows_before_positive_price_share_gate"] for r in results.values()),
            "positive_price_share_rows_after_all_high_precision_gates": sum(r["high_precision_footnote_screen"]["positive_price_share_rows_after_all_high_precision_gates"] for r in results.values()),
        },
        "periods": results,
        "decision": {
            "phase296_candidate_definition_corrected": True,
            "transaction_form_type_4_required_for_form4_table_i_screen": True,
            "high_precision_footnote_screen_remains_low_recall_text_evidence_only": True,
            "strict_pit_admitted": False,
            "return_test_run": False,
            "alpha_test_run": False,
            "bootstrap_loo_run": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "data_purchase_or_vendor_contact": False,
            "sec_requests_made": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = analyze_artifact(args.artifact)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PHASE297_STATUS=PHASE296_FORM4_TRANSACTION_FORM_TYPE_GATE_CORRECTED")
    print("PHASE296_ROWS=" + str(result["aggregate"]["phase296_original_conservative_rows"]))
    print("CORRECTED_TABLE_I_ROWS=" + str(result["aggregate"]["corrected_table_i_type4_conservative_rows"]))
    print("EXCLUDED_FORM_TYPE_5_ROWS=" + str(result["aggregate"]["excluded_transaction_form_type_5_rows"]))
    print("STRICT_PIT=false ALPHA=false F80_FROZEN=true")


if __name__ == "__main__":
    main()
