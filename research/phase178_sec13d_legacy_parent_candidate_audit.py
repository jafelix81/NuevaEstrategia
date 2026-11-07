#!/usr/bin/env python3
"""Phase 178: conservative in-sample predecessor-candidate screen for legacy 13D."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, re
from datetime import date
from pathlib import Path
from typing import Any

PHASE = 178
INPUT_NAME = "phase178_sec13d_legacy_parent_input.csv.gz"
INPUT_GZIP_SHA256 = "4d14030c8b176065f40f10537d34d4de9491c71183200ab3480f27469085cb05"
INPUT_CSV_SHA256 = "4370ba9645d8184101fd8230cdcf274c99c68cd9561387aee898fc4cb7063d07"
SOURCE_PHASE159_CSV_SHA256 = "bb6411e78fc3eca1ca8c7aae6c76a1b26e6ef03138bb5eb622d8747cf330cfa4"
SOURCE_PHASE157_CSV_SHA256 = "154b628436d6c438e54bb953f7d77b0a82f89b5c19373e9f1b642a5140f20072"
REQUIRED_FIELDS = {"acc", "dt", "role", "filer", "cusip", "issuer_h96", "owner_h96", "i4", "prev"}
ROLE_CODES = {"A", "N", "C"}

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def cusip_is_valid(value: str) -> bool:
    """Validate the standard 9-character CUSIP check digit."""
    c = (value or "").strip().upper()
    if len(c) != 9 or not c[-1].isdigit():
        return False
    values = []
    for ch in c[:8]:
        if ch.isdigit(): value_int = int(ch)
        elif "A" <= ch <= "Z": value_int = ord(ch) - 55
        elif ch == "*": value_int = 36
        elif ch == "@": value_int = 37
        elif ch == "#": value_int = 38
        else: return False
        values.append(value_int)
    total = 0
    for index, value_int in enumerate(values):
        product = value_int * (2 if index % 2 else 1)
        total += product // 10 + product % 10
    return (10 - total % 10) % 10 == int(c[8])

def parse_rows(csv_bytes: bytes) -> list[dict[str, str]]:
    if sha256(csv_bytes) != INPUT_CSV_SHA256:
        raise ValueError("compact_csv_sha256_mismatch")
    rows = list(csv.DictReader(csv_bytes.decode("utf-8").splitlines()))
    if not rows or set(rows[0]) != REQUIRED_FIELDS:
        raise ValueError("compact_input_schema_mismatch")
    if len(rows) != 180:
        raise ValueError("compact_input_row_count_mismatch")
    seen = set()
    for row in rows:
        if row["acc"] in seen: raise ValueError("duplicate_accession")
        seen.add(row["acc"])
        if row["role"] not in ROLE_CODES: raise ValueError("unknown_role_code")
        try: date.fromisoformat(row["dt"])
        except ValueError as exc: raise ValueError("invalid_filing_date") from exc
        if row["i4"] not in {"0", "1"} or row["prev"] not in {"0", "1"}:
            raise ValueError("invalid_binary_flag")
        for key in ("issuer_h96", "owner_h96"):
            if row[key] and not re.fullmatch(r"[0-9a-f]{24}", row[key]):
                raise ValueError("invalid_name_hash")
        if row["filer"] and not row["filer"].isdigit():
            raise ValueError("invalid_filer_cik")
    return rows

def prior_candidates(rows: list[dict[str, str]], child: dict[str, str], *, require_owner: bool) -> list[dict[str, str]]:
    # Missing values are never wildcards; CUSIP must pass its check digit.
    if not child["issuer_h96"] or not child["filer"] or not cusip_is_valid(child["cusip"]):
        return []
    if require_owner and not child["owner_h96"]: return []
    child_date = date.fromisoformat(child["dt"])
    matches = []
    for candidate in rows:
        if candidate["acc"] == child["acc"] or date.fromisoformat(candidate["dt"]) >= child_date:
            continue
        if not candidate["issuer_h96"] or candidate["issuer_h96"] != child["issuer_h96"]:
            continue
        if not cusip_is_valid(candidate["cusip"]) or candidate["cusip"] != child["cusip"]:
            continue
        if not candidate["filer"] or candidate["filer"] != child["filer"]:
            continue
        if require_owner and (not candidate["owner_h96"] or candidate["owner_h96"] != child["owner_h96"]):
            continue
        matches.append(candidate)
    return matches

def audit_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    role_counts = {role: sum(row["role"] == role for row in rows) for role in sorted(ROLE_CODES)}
    item4_initial = [r for r in rows if r["role"] == "N" and r["i4"] == "1"]
    amendments = [r for r in rows if r["role"] in {"A", "C"}]
    complete_initial = [r for r in item4_initial if r["issuer_h96"] and r["filer"] and cusip_is_valid(r["cusip"])]
    initial_counts = [len(prior_candidates(rows, r, require_owner=True)) for r in item4_initial]
    amendment_counts, pairs = [], []
    for child in amendments:
        matches = prior_candidates(rows, child, require_owner=True)
        amendment_counts.append(len(matches))
        if len(matches) == 1:
            parent = matches[0]
            pairs.append({
                "candidate_predecessor_accession": parent["acc"],
                "candidate_predecessor_filing_date": parent["dt"],
                "candidate_predecessor_role": parent["role"],
                "candidate_predecessor_item4": parent["i4"] == "1",
                "later_amendment_accession": child["acc"],
                "later_amendment_filing_date": child["dt"],
                "later_amendment_role": child["role"],
                "later_amendment_item4": child["i4"] == "1",
                "same_issuer_hash": True, "same_valid_cusip": True,
                "same_filer_cik": True, "same_first_owner_hash": True,
                "verified_parent_edge": False,
            })
    for pair in pairs:
        parent = next(r for r in rows if r["acc"] == pair["candidate_predecessor_accession"])
        if parent["role"] != "A": raise ValueError("candidate_predecessor_not_amendment_control_failed")
        if prior_candidates(rows, parent, require_owner=True):
            raise ValueError("candidate_predecessor_has_earlier_in_sample_anchor")
    return {
        "phase": PHASE, "status": "IN_SAMPLE_PREDECESSOR_COVERAGE_INSUFFICIENT",
        "input_rows": len(rows), "unique_accessions": len({r["acc"] for r in rows}),
        "role_counts": {
            "index_coded_amendment": role_counts["A"],
            "non_amendment_form_initial_status_unconfirmed": role_counts["N"],
            "cover_numbered_amendment_candidate": role_counts["C"],
            "total_amendment_candidates": len(amendments),
        },
        "item4_non_amendment_unconfirmed_candidates": len(item4_initial),
        "item4_candidates_with_valid_cusip": sum(cusip_is_valid(r["cusip"]) for r in item4_initial),
        "item4_candidates_with_body_issuer_hash": sum(bool(r["issuer_h96"]) for r in item4_initial),
        "item4_candidates_with_first_owner_hash": sum(bool(r["owner_h96"]) for r in item4_initial),
        "item4_candidates_with_complete_match_key": len(complete_initial),
        "item4_candidates_with_any_in_sample_predecessor": sum(x > 0 for x in initial_counts),
        "item4_candidates_without_in_sample_predecessor": sum(x == 0 for x in initial_counts),
        "amendment_candidates_with_any_in_sample_candidate": sum(x > 0 for x in amendment_counts),
        "amendment_candidates_with_unique_candidate": sum(x == 1 for x in amendment_counts),
        "amendment_candidates_with_ambiguous_candidates": sum(x > 1 for x in amendment_counts),
        "amendment_candidates_without_candidate": sum(x == 0 for x in amendment_counts),
        "candidate_pairs": pairs,
        "candidate_parent_documents_are_amendments": all(p["candidate_predecessor_role"] == "A" for p in pairs),
        "candidate_parent_documents_have_no_earlier_in_sample_anchor": True,
        "legacy_previous_accession_populated_rows": sum(r["prev"] == "1" for r in rows),
        "parent_edges_verified": 0, "initial_status_confirmed": 0,
        "feature_admission": False, "alpha_admission": False,
        "final_holdout_used": False, "f80_modified": False,
        "source": {
            "phase159_run_id": 42353084525, "phase159_artifact_id": 13565349554,
            "phase159_csv_sha256": SOURCE_PHASE159_CSV_SHA256,
            "phase157_run_id": 42353084472, "phase157_artifact_id": 13566915807,
            "phase157_csv_sha256": SOURCE_PHASE157_CSV_SHA256,
            "raw_submission_hash_matches": 180,
        },
        "input": {
            "gzip_sha256": INPUT_GZIP_SHA256, "csv_sha256": INPUT_CSV_SHA256,
            "raw_names_persisted": False, "item4_text_persisted": False,
        },
        "decision": "Keep all 55 Item 4 rows INITIAL_STATUS_UNCONFIRMED; keep two amendment pairs CANDIDATE_ONLY_UNVERIFIED; do not create state edges or run returns tests.",
    }

def run_audit(output_dir: Path | None = None) -> dict[str, Any]:
    input_path = Path(__file__).with_name(INPUT_NAME)
    gzip_bytes = input_path.read_bytes()
    if sha256(gzip_bytes) != INPUT_GZIP_SHA256: raise ValueError("compact_gzip_sha256_mismatch")
    rows = parse_rows(gzip.decompress(gzip_bytes))
    result = audit_rows(rows)
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "phase178_sec13d_legacy_parent_candidate_summary.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(run_audit(args.output_dir), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
