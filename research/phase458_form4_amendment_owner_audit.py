#!/usr/bin/env python3
"""Phase 458: audit Form 4 purchase-line owner grain, 10b5-1 flags and amendment corrections."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, zipfile
from collections import Counter, defaultdict
from pathlib import Path

ARTIFACT_ID = 12781850078
RUN_ID = 40606706518
OUTER_SHA256 = "203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66"
INNER_SHA256 = {
    "2012Q1": "0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357",
    "2026Q3": "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3",
}
FORM4_TYPES = {"4", "4/A"}
ORIGINAL_TYPE = "4"
AMENDMENT_TYPE = "4/A"
REQUIRED = {
    "SUBMISSION.tsv": {"ACCESSION_NUMBER", "FILING_DATE", "PERIOD_OF_REPORT", "DATE_OF_ORIG_SUB", "DOCUMENT_TYPE", "ISSUERCIK"},
    "REPORTINGOWNER.tsv": {"ACCESSION_NUMBER", "RPTOWNERCIK"},
    "NONDERIV_TRANS.tsv": {"ACCESSION_NUMBER", "NONDERIV_TRANS_SK", "SECURITY_TITLE", "TRANS_DATE", "TRANS_CODE", "TRANS_FORM_TYPE", "TRANS_SHARES", "TRANS_PRICEPERSHARE", "TRANS_ACQUIRED_DISP_CD", "DIRECT_INDIRECT_OWNERSHIP"},
}
CORE_FIELDS = (
    "SECURITY_TITLE", "TRANS_DATE", "TRANS_CODE", "TRANS_FORM_TYPE", "TRANS_SHARES",
    "TRANS_PRICEPERSHARE", "DIRECT_INDIRECT_OWNERSHIP", "SHRS_OWND_FOLWNG_TRANS", "VALU_OWND_FOLWNG_TRANS",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_tsv(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    with zf.open(name) as handle:
        reader = csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig", newline=""), delimiter="\t")
        if not reader.fieldnames:
            raise ValueError(f"{name}: missing header")
        missing = REQUIRED[name] - set(reader.fieldnames)
        if missing:
            raise ValueError(f"{name}: missing required columns {sorted(missing)}")
        rows = list(reader)
        if any(None in row for row in rows):
            raise ValueError(f"{name}: row with extra columns")
        return rows


def norm_flag(value: str | None) -> str:
    v = str(value or "").strip().lower()
    if v in {"1", "true", "yes", "y"}:
        return "yes"
    if v in {"0", "false", "no", "n"}:
        return "no"
    return "unknown"


def _pct(n: int, d: int) -> float | None:
    return round(100.0 * n / d, 6) if d else None


def _core_key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(str(row.get(k) or "").strip() for k in CORE_FIELDS)


def _amendment_pairs(submissions, owners):
    originals = [r for r in submissions if r.get("DOCUMENT_TYPE") == ORIGINAL_TYPE]
    amendments = [r for r in submissions if r.get("DOCUMENT_TYPE") == AMENDMENT_TYPE]
    unique, ambiguous, no_candidate = [], [], []
    for amendment in amendments:
        acc = amendment["ACCESSION_NUMBER"]
        owner_ids = owners.get(acc, set())
        candidates = [o for o in originals
            if o.get("ISSUERCIK") == amendment.get("ISSUERCIK")
            and o.get("FILING_DATE") == amendment.get("DATE_OF_ORIG_SUB")
            and o.get("PERIOD_OF_REPORT") == amendment.get("PERIOD_OF_REPORT")
            and bool(owner_ids & owners.get(o["ACCESSION_NUMBER"], set()))]
        if len(candidates) == 1:
            unique.append((amendment, candidates[0]))
        elif len(candidates) > 1:
            ambiguous.append(amendment)
        else:
            no_candidate.append(amendment)
    return unique, ambiguous, no_candidate


def _compare_amendment_rows(pairs, transactions):
    changes = Counter()
    p_d_to_a = []
    unresolved_core_collisions = 0
    for amendment, original in pairs:
        old_rows = transactions.get(original["ACCESSION_NUMBER"], [])
        new_rows = transactions.get(amendment["ACCESSION_NUMBER"], [])
        old_by, new_by = defaultdict(list), defaultdict(list)
        for row in old_rows:
            old_by[_core_key(row)].append(row)
        for row in new_rows:
            new_by[_core_key(row)].append(row)
        for key in set(old_by) & set(new_by):
            left, right = old_by[key], new_by[key]
            if len(left) != 1 or len(right) != 1:
                unresolved_core_collisions += 1
                continue
            old_ad = str(left[0].get("TRANS_ACQUIRED_DISP_CD") or "").strip()
            new_ad = str(right[0].get("TRANS_ACQUIRED_DISP_CD") or "").strip()
            if old_ad != new_ad:
                code = str(left[0].get("TRANS_CODE") or "").strip()
                changes[(code, old_ad, new_ad)] += 1
                if code == "P" and old_ad == "D" and new_ad == "A":
                    p_d_to_a.append({
                        "original_accession": original["ACCESSION_NUMBER"],
                        "amendment_accession": amendment["ACCESSION_NUMBER"],
                        "issuer_cik": amendment.get("ISSUERCIK"),
                        "period_of_report": amendment.get("PERIOD_OF_REPORT"),
                        "corrected_transaction_rows": 1,
                    })
    return changes, p_d_to_a, unresolved_core_collisions


def summarize_period(period: str, submissions, owner_rows, transaction_rows) -> dict:
    sub_by_acc = {}
    for row in submissions:
        acc = str(row.get("ACCESSION_NUMBER") or "").strip()
        if not acc or acc in sub_by_acc:
            raise ValueError(f"{period}: blank or duplicate submission accession")
        sub_by_acc[acc] = row
    owners = defaultdict(set)
    owner_keys = set()
    for row in owner_rows:
        acc = str(row.get("ACCESSION_NUMBER") or "").strip()
        cik = str(row.get("RPTOWNERCIK") or "").strip()
        if not acc or not cik:
            raise ValueError(f"{period}: blank reporting-owner key")
        key = (acc, cik)
        if key in owner_keys:
            raise ValueError(f"{period}: duplicate reporting-owner key {key}")
        owner_keys.add(key)
        owners[acc].add(cik)
    transactions = defaultdict(list)
    transaction_keys = set()
    for row in transaction_rows:
        acc = str(row.get("ACCESSION_NUMBER") or "").strip()
        sk = str(row.get("NONDERIV_TRANS_SK") or "").strip()
        if not acc or not sk:
            raise ValueError(f"{period}: blank transaction key")
        key = (acc, sk)
        if key in transaction_keys:
            raise ValueError(f"{period}: duplicate transaction key {key}")
        transaction_keys.add(key)
        if acc in sub_by_acc and sub_by_acc[acc].get("DOCUMENT_TYPE") in FORM4_TYPES:
            transactions[acc].append(row)
    form4 = {a: r for a, r in sub_by_acc.items() if r.get("DOCUMENT_TYPE") in FORM4_TYPES}
    form4_rows = [row for acc in form4 for row in transactions.get(acc, [])]
    p_rows = [row for row in form4_rows if str(row.get("TRANS_CODE") or "").strip() == "P"]
    p_accessions = {row["ACCESSION_NUMBER"] for row in p_rows}
    multi_owner_form4 = {a for a in form4 if len(owners.get(a, set())) > 1}
    multi_owner_p = {a for a in p_accessions if len(owners.get(a, set())) > 1}
    flag_present = bool(submissions and "AFF10B5ONE" in submissions[0])
    all_flag_raw = Counter((str(r.get("AFF10B5ONE") or "").strip().lower() if flag_present else "field_absent") for r in form4.values())
    p_flag_raw = Counter((str(form4[a].get("AFF10B5ONE") or "").strip().lower() if flag_present else "field_absent") for a in p_accessions)
    p_flag_norm = Counter(norm_flag(form4[a].get("AFF10B5ONE")) if flag_present else "unknown" for a in p_accessions)
    p_rows_by_flag = Counter(norm_flag(form4[row["ACCESSION_NUMBER"]].get("AFF10B5ONE")) if flag_present else "unknown" for row in p_rows)
    amendments, ambiguous, no_candidate = _amendment_pairs(submissions, owners)
    changes, p_d_to_a, collisions = _compare_amendment_rows(amendments, transactions)
    p_ad = Counter(str(r.get("TRANS_ACQUIRED_DISP_CD") or "").strip() for r in p_rows)
    return {
        "period": period,
        "form4_and_4a_submissions": len(form4),
        "form4_original_submissions": sum(r.get("DOCUMENT_TYPE") == "4" for r in form4.values()),
        "form4_amendment_submissions": sum(r.get("DOCUMENT_TYPE") == "4/A" for r in form4.values()),
        "form4_accessions_with_multiple_reporting_owners": len(multi_owner_form4),
        "form4_multi_owner_pct": _pct(len(multi_owner_form4), len(form4)),
        "p_coded_nonderivative_rows": len(p_rows),
        "p_coded_accessions": len(p_accessions),
        "p_accessions_with_multiple_reporting_owners": len(multi_owner_p),
        "p_multi_owner_accession_pct": _pct(len(multi_owner_p), len(p_accessions)),
        "p_rows_in_multi_owner_accessions": sum(row["ACCESSION_NUMBER"] in multi_owner_p for row in p_rows),
        "p_multi_owner_row_pct": _pct(sum(row["ACCESSION_NUMBER"] in multi_owner_p for row in p_rows), len(p_rows)),
        "p_acquired_disposed_raw": dict(sorted(p_ad.items())),
        "p_transaction_form_type_raw": dict(sorted(Counter(str(r.get("TRANS_FORM_TYPE") or "").strip() for r in p_rows).items())),
        "aff10b5one_field_present": flag_present,
        "aff10b5one_all_form4_raw": dict(sorted(all_flag_raw.items())),
        "aff10b5one_p_accessions_raw": dict(sorted(p_flag_raw.items())),
        "aff10b5one_p_accessions_normalized": dict(sorted(p_flag_norm.items())),
        "aff10b5one_p_rows_normalized": dict(sorted(p_rows_by_flag.items())),
        "same_quarter_amendment_link": {
            "unique_heuristic_pairs": len(amendments),
            "ambiguous_candidates": len(ambiguous),
            "no_in_quarter_candidate": len(no_candidate),
            "matching_rule": "same issuer CIK + original filing date + period of report + at least one shared reporting-owner CIK",
            "is_authoritative_accession_lineage": False,
            "transaction_ad_changes": {"|".join(k): v for k, v in sorted(changes.items())},
            "unresolved_duplicate_core_keys": collisions,
            "p_disposition_to_acquisition_corrections": len(p_d_to_a),
            "p_disposition_to_acquisition_examples": p_d_to_a,
        },
        "bulk_grain_controls": {
            "transaction_table_has_reporting_owner_cik": False,
            "transaction_to_owner_assignment_from_bulk_alone": False,
            "aff10b5one_is_submission_level": True,
            "amendment_link_uses_date_and_owner_overlap_not_accession_parent_id": True,
        },
    }


def analyze(artifact_path: Path, enforce_hash: bool = True) -> dict:
    raw = artifact_path.read_bytes()
    if enforce_hash and sha(raw) != OUTER_SHA256:
        raise ValueError("Phase 39 archive artifact SHA-256 mismatch")
    periods = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        for period, expected in INNER_SHA256.items():
            member = f"{period.lower()}_form345.zip"
            inner = outer.read(member)
            if enforce_hash and sha(inner) != expected:
                raise ValueError(f"{period} nested archive SHA-256 mismatch")
            with zipfile.ZipFile(io.BytesIO(inner)) as z:
                periods[period] = summarize_period(
                    period, read_tsv(z, "SUBMISSION.tsv"),
                    read_tsv(z, "REPORTINGOWNER.tsv"), read_tsv(z, "NONDERIV_TRANS.tsv"))
    if periods["2012Q1"]["p_coded_nonderivative_rows"] != 7180:
        raise ValueError("2012Q1 P-row count does not match immutable audit expectation")
    if periods["2026Q3"]["p_coded_nonderivative_rows"] != 5183:
        raise ValueError("2026Q3 P-row count does not match immutable audit expectation")
    if periods["2026Q3"]["same_quarter_amendment_link"]["p_disposition_to_acquisition_corrections"] != 2:
        raise ValueError("2026Q3 P/D-to-P/A correction count does not match immutable audit expectation")
    return {
        "phase": 458,
        "audit_date": "2026-11-17",
        "source": {"workflow_run_id": RUN_ID, "artifact_id": ARTIFACT_ID, "outer_sha256": sha(raw),
                   "inner_sha256": INNER_SHA256, "archive_periods": sorted(periods)},
        "periods": periods,
        "official_filing_validation": {
            "original_accession": "0001493152-26-034516",
            "amendment_accession": "0001493152-26-034654",
            "issuer_cik": "0001873093",
            "issuer_symbol": "GDTC",
            "original_edgar_acceptance_et": "2026-07-24 12:33:42",
            "amendment_edgar_acceptance_et": "2026-07-24 21:01:08",
            "correction": "Form 4/A corrected two Table I acquisition/disposition indicators from D to A; its footnote says no other changes were made.",
            "verified_against_original_and_amendment_sec_submission_text": True,
            "original_bulk_rows_with_p_and_d": 2,
            "amended_bulk_rows_with_p_and_a": 2,
            "interpretation": "Amendment changes the information state at amendment availability; it does not create two new economic trades or backdate the corrected A/D state.",
        },
        "disposition": {
            "form4_candidate_remains_conditional": True,
            "bulk_only_owner_breadth_or_cluster_signal_authorized": False,
            "transaction_code_P_alone_sufficient_for_purchase_label": False,
            "amendments_must_update_event_state_at_amendment_availability": True,
            "historical_public_first_seen_reconstructed": False,
            "historical_security_class_universe_gate_passed": False,
            "alpha_authorized": False,
            "frozen_baseline_changed": False,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-noncanonical-hash", action="store_true")
    args = parser.parse_args()
    result = analyze(args.artifact, not args.allow_noncanonical_hash)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
