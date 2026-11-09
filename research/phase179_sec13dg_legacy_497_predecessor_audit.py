#!/usr/bin/env python3
"""Phase 179: expand the legacy SEC 13D/G predecessor screen to all 497 sampled HTML filings.

This is an in-sample coverage and false-match sensitivity audit only. It does not
establish parent links, initial status, beneficial ownership, or predictive alpha.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

PHASE = 179
COMPACT_FIELDS = ("acc", "dt", "family", "role", "filer", "cusip", "issuer_h96", "owner_h96", "i4")
INPUT_CSV_SHA256 = "6d0cc2a0841dc58a362be1e2b61d055a4e300da53ff157dedb9df5096d919626"
SOURCE_PHASE157_CSV_SHA256 = "154b628436d6c438e54bb953f7d77b0a82f89b5c19373e9f1b642a5140f20072"
SOURCE_PHASE159_CSV_SHA256 = "bb6411e78fc3eca1ca8c7aae6c76a1b26e6ef03138bb5eb622d8747cf330cfa4"
FIELDS = {"acc", "dt", "family", "role", "filer", "cusip", "issuer_h96", "owner_h96", "i4"}
FAMILIES = {"13D", "13G"}
ROLES = {"A", "N", "C"}
STRICT_KEYS = ("issuer_h96", "cusip", "filer", "owner_h96")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def cusip_is_valid(value: str) -> bool:
    c = (value or "").strip().upper()
    if len(c) != 9 or not c[-1].isdigit():
        return False
    values = []
    for ch in c[:8]:
        if ch.isdigit(): v = int(ch)
        elif "A" <= ch <= "Z": v = ord(ch) - 55
        elif ch == "*": v = 36
        elif ch == "@": v = 37
        elif ch == "#": v = 38
        else: return False
        values.append(v)
    total = 0
    for i, value in enumerate(values):
        product = value * (2 if i % 2 else 1)
        total += product // 10 + product % 10
    return (10 - total % 10) % 10 == int(c[8])

def normalized_name_hash(value: str) -> str:
    normalized = re.sub(r"[^A-Z0-9]", "", (value or "").upper())
    return hashlib.sha256(normalized.encode("ascii")).hexdigest()[:24] if normalized else ""

def build_compact_input(input_dir: Path) -> bytes:
    """Rebuild the hash-only 497-row fixture from immutable Phase 157/159 artifacts."""
    p157_path = input_dir / "phase157_legacy_13dg_html_field_audit.csv"
    p159_path = input_dir / "phase159_13d_cover_amendment_roles.csv"
    p157_bytes = p157_path.read_bytes()
    p159_bytes = p159_path.read_bytes()
    if sha256(p157_bytes) != SOURCE_PHASE157_CSV_SHA256:
        raise ValueError("phase157_source_csv_sha256_mismatch")
    if sha256(p159_bytes) != SOURCE_PHASE159_CSV_SHA256:
        raise ValueError("phase159_source_csv_sha256_mismatch")
    with p157_path.open("r", encoding="utf-8", newline="") as handle:
        p157_rows = list(csv.DictReader(handle))
    with p159_path.open("r", encoding="utf-8", newline="") as handle:
        p159_rows = list(csv.DictReader(handle))
    if len(p157_rows) != 497 or len(p159_rows) != 180:
        raise ValueError("source_artifact_row_count_mismatch")
    p159_by_accession = {row["accession"]: row for row in p159_rows}
    p157_13d = {row["accession"]: row for row in p157_rows if row["family"] == "13D"}
    if set(p157_13d) != set(p159_by_accession):
        raise ValueError("phase159_accession_reconciliation_mismatch")
    if any(p157_13d[acc]["raw_sha256"] != row["raw_sha256"] for acc, row in p159_by_accession.items()):
        raise ValueError("phase159_raw_document_hash_reconciliation_mismatch")
    compact_rows = []
    for source in p157_rows:
        accession = source["accession"]
        role_record = p159_by_accession.get(accession)
        if role_record and role_record["corrected_role_class"] == "COVER_NUMBERED_AMENDMENT_CANDIDATE":
            role = "C"
        elif source["is_amendment"].lower() == "true":
            role = "A"
        else:
            role = "N"
        compact_rows.append({
            "acc": accession,
            "dt": source["filing_date"],
            "family": source["family"],
            "role": role,
            "filer": source["filer_header_cik"],
            "cusip": source["cusip"],
            "issuer_h96": normalized_name_hash(source["body_issuer_name_candidate"]),
            "owner_h96": normalized_name_hash(source["first_reporting_person_candidate"]),
            "i4": "1" if source["item4_purpose_section_present"].lower() == "true" else "0",
        })
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=COMPACT_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(compact_rows)
    csv_bytes = buffer.getvalue().encode("utf-8")
    if sha256(csv_bytes) != INPUT_CSV_SHA256:
        raise ValueError("rebuilt_compact_csv_sha256_mismatch")
    return csv_bytes

def parse_rows(csv_bytes: bytes) -> list[dict[str, str]]:
    if sha256(csv_bytes) != INPUT_CSV_SHA256:
        raise ValueError("compact_csv_sha256_mismatch")
    rows = list(csv.DictReader(csv_bytes.decode("utf-8").splitlines()))
    if not rows or set(rows[0]) != FIELDS:
        raise ValueError("compact_input_schema_mismatch")
    if len(rows) != 497:
        raise ValueError("compact_input_row_count_mismatch")
    seen = set()
    for row in rows:
        if not row["acc"] or row["acc"] in seen:
            raise ValueError("duplicate_or_blank_accession")
        seen.add(row["acc"])
        if row["family"] not in FAMILIES:
            raise ValueError("unknown_family")
        if row["role"] not in ROLES:
            raise ValueError("unknown_role")
        try:
            date.fromisoformat(row["dt"])
        except ValueError as exc:
            raise ValueError("invalid_filing_date") from exc
        if row["i4"] not in {"0", "1"}:
            raise ValueError("invalid_item4_flag")
        for key in ("issuer_h96", "owner_h96"):
            if row[key] and not re.fullmatch(r"[0-9a-f]{24}", row[key]):
                raise ValueError("invalid_name_hash")
        if row["filer"] and not row["filer"].isdigit():
            raise ValueError("invalid_filer_cik")
    return rows

def prior_candidates(
    rows: list[dict[str, str]],
    child: dict[str, str],
    *,
    keys: tuple[str, ...] = STRICT_KEYS,
    same_family: bool = True,
) -> list[dict[str, str]]:
    # Missing identifiers never act as wildcards. CUSIP must pass its check digit.
    if any(not child.get(k) for k in keys):
        return []
    if "cusip" in keys and not cusip_is_valid(child["cusip"]):
        return []
    child_date = date.fromisoformat(child["dt"])
    matches = []
    for candidate in rows:
        if candidate["acc"] == child["acc"]:
            continue
        if date.fromisoformat(candidate["dt"]) >= child_date:
            continue
        if same_family and candidate["family"] != child["family"]:
            continue
        if any(not candidate.get(k) or candidate[k] != child[k] for k in keys):
            continue
        if "cusip" in keys and not cusip_is_valid(candidate["cusip"]):
            continue
        matches.append(candidate)
    return matches

def tier_summary(
    rows: list[dict[str, str]],
    children: list[dict[str, str]],
    *,
    keys: tuple[str, ...],
    same_family: bool,
) -> dict[str, int]:
    eligible = any_count = unique = ambiguous = none = total_edges = 0
    for child in children:
        if any(not child.get(k) for k in keys):
            continue
        if "cusip" in keys and not cusip_is_valid(child["cusip"]):
            continue
        eligible += 1
        count = len(prior_candidates(rows, child, keys=keys, same_family=same_family))
        total_edges += count
        any_count += count > 0
        unique += count == 1
        ambiguous += count > 1
        none += count == 0
    return {
        "children": len(children),
        "eligible": eligible,
        "missing_or_invalid_key": len(children) - eligible,
        "with_candidate": any_count,
        "unique_candidate": unique,
        "ambiguous_candidate": ambiguous,
        "without_candidate": none,
        "candidate_edges": total_edges,
    }

def candidate_pair(parent: dict[str, str], child: dict[str, str], tier: str) -> dict[str, Any]:
    return {
        "parent_accession": parent["acc"],
        "parent_filing_date": parent["dt"],
        "parent_family": parent["family"],
        "parent_role": parent["role"],
        "child_accession": child["acc"],
        "child_filing_date": child["dt"],
        "child_family": child["family"],
        "child_role": child["role"],
        "match_tier": tier,
        "same_filer": bool(parent["filer"]) and parent["filer"] == child["filer"],
        "same_first_owner_hash": bool(parent["owner_h96"]) and parent["owner_h96"] == child["owner_h96"],
        "same_issuer_hash": bool(parent["issuer_h96"]) and parent["issuer_h96"] == child["issuer_h96"],
        "same_valid_cusip": cusip_is_valid(parent["cusip"]) and parent["cusip"] == child["cusip"],
        "verified_parent_edge": False,
    }

def audit_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    amendments = [r for r in rows if r["role"] in {"A", "C"}]
    nonamendments = [r for r in rows if r["role"] == "N"]
    item4_13d_nonamend = [r for r in nonamendments if r["family"] == "13D" and r["i4"] == "1"]
    family_role_counts = {
        family: {
            role: sum(r["family"] == family and r["role"] == role for r in rows)
            for role in ("A", "N", "C")
        }
        for family in ("13D", "13G")
    }

    strict_same = tier_summary(rows, amendments, keys=STRICT_KEYS, same_family=True)
    strict_cross = tier_summary(rows, amendments, keys=STRICT_KEYS, same_family=False)
    strict_nonamend = tier_summary(rows, nonamendments, keys=STRICT_KEYS, same_family=True)
    strict_item4 = tier_summary(rows, item4_13d_nonamend, keys=STRICT_KEYS, same_family=True)
    no_owner = tier_summary(rows, amendments, keys=("issuer_h96", "cusip", "filer"), same_family=True)
    no_filer = tier_summary(rows, amendments, keys=("issuer_h96", "cusip", "owner_h96"), same_family=True)
    issuer_cusip_same = tier_summary(rows, amendments, keys=("issuer_h96", "cusip"), same_family=True)
    issuer_cusip_cross = tier_summary(rows, amendments, keys=("issuer_h96", "cusip"), same_family=False)
    nonamend_issuer_cusip = tier_summary(rows, nonamendments, keys=("issuer_h96", "cusip"), same_family=True)

    strict_pairs = []
    weak_pairs = []
    for child in amendments:
        strict = prior_candidates(rows, child, keys=STRICT_KEYS, same_family=True)
        relaxed = prior_candidates(rows, child, keys=("issuer_h96", "cusip"), same_family=True)
        if len(strict) == 1:
            strict_pairs.append(candidate_pair(strict[0], child, "issuer+valid_CUSIP+filer+first_owner"))
        for parent in relaxed:
            if parent not in strict:
                weak_pairs.append(candidate_pair(parent, child, "issuer+valid_CUSIP_only"))

    # Every strict candidate predecessor is itself an amendment; test whether it
    # has an earlier strict-key anchor anywhere in the full 497-row cohort.
    parent_anchor_counts = []
    for pair in strict_pairs:
        parent = next(r for r in rows if r["acc"] == pair["parent_accession"])
        parent_anchor_counts.append(len(prior_candidates(rows, parent, keys=STRICT_KEYS, same_family=True)))

    # Cross-family issuer/CUSIP-only candidates are reported separately; they are
    # not merged into the same-family weak-collision count.
    cross_family_pairs = []
    for child in amendments:
        matches = prior_candidates(rows, child, keys=("issuer_h96", "cusip"), same_family=False)
        same = prior_candidates(rows, child, keys=("issuer_h96", "cusip"), same_family=True)
        same_accessions = {r["acc"] for r in same}
        for parent in matches:
            if parent["acc"] not in same_accessions:
                cross_family_pairs.append(candidate_pair(parent, child, "cross_family_issuer+valid_CUSIP_only"))

    return {
        "phase": PHASE,
        "status": "IN_SAMPLE_PREDECESSOR_COVERAGE_INSUFFICIENT_497_ROW_COHORT",
        "input_rows": len(rows),
        "unique_accessions": len({r["acc"] for r in rows}),
        "family_counts": {f: sum(r["family"] == f for r in rows) for f in ("13D", "13G")},
        "family_role_counts": family_role_counts,
        "amendment_candidates": len(amendments),
        "nonamendment_status_unconfirmed": len(nonamendments),
        "13d_item4_nonamendment_unconfirmed": len(item4_13d_nonamend),
        "13d_item4_complete_strict_key": sum(
            bool(r["issuer_h96"] and r["filer"] and r["owner_h96"] and cusip_is_valid(r["cusip"]))
            for r in item4_13d_nonamend
        ),
        "strict_amendment_candidates_same_family": strict_same,
        "strict_amendment_candidates_all_families": strict_cross,
        "strict_nonamendment_candidates_same_family": strict_nonamend,
        "strict_13d_item4_nonamendment_candidates": strict_item4,
        "three_key_without_owner_same_family": no_owner,
        "three_key_without_filer_same_family": no_filer,
        "issuer_cusip_amendment_candidates_same_family": issuer_cusip_same,
        "issuer_cusip_amendment_candidates_all_families": issuer_cusip_cross,
        "issuer_cusip_nonamendment_candidates_same_family": nonamend_issuer_cusip,
        "strict_candidate_pairs": strict_pairs,
        "strict_candidate_parent_anchor_counts": parent_anchor_counts,
        "weak_same_family_collision_pairs": weak_pairs,
        "cross_family_collision_pairs": cross_family_pairs,
        "weak_same_family_collision_count": len(weak_pairs),
        "cross_family_collision_count": len(cross_family_pairs),
        "all_relaxed_collisions_fail_filer_and_owner": all(
            not p["same_filer"] and not p["same_first_owner_hash"]
            for p in weak_pairs + cross_family_pairs
        ),
        "strict_candidate_parents_are_amendments": all(p["parent_role"] == "A" for p in strict_pairs),
        "strict_candidate_parents_have_no_earlier_strict_anchor": all(n == 0 for n in parent_anchor_counts),
        "verified_parent_edges": 0,
        "initial_status_confirmed": 0,
        "feature_admission": False,
        "alpha_admission": False,
        "final_holdout_used": False,
        "f80_modified": False,
        "source": {
            "phase157_run_id": 42354802427,
            "phase157_artifact_id": 13567167891,
            "phase157_csv_sha256": SOURCE_PHASE157_CSV_SHA256,
            "phase159_run_id": 42354802447,
            "phase159_artifact_id": 13566809056,
            "phase159_csv_sha256": SOURCE_PHASE159_CSV_SHA256,
            "phase159_13d_rows_reconciled": 180,
            "phase159_raw_hash_matches": 180,
        },
        "input": {
            "csv_sha256": INPUT_CSV_SHA256,
            "representation": "compact_csv_rebuilt_in_memory_from_pinned_phase157_phase159_artifacts",
            "raw_names_persisted": False,
            "item4_text_persisted": False,
        },
        "decision": (
            "The full 497-row legacy HTML sample still does not support parent reconstruction. "
            "Only two strict same-family amendment-to-amendment candidates survive; both have no "
            "earlier strict anchor. Three same-family and three cross-family issuer/CUSIP-only collisions "
            "all fail both filer and first-owner continuity. Keep non-/A forms unconfirmed; no state "
            "edges, features, returns tests or alpha admission."
        ),
    }

def run_audit(output_dir: Path | None = None, input_dir: Path | None = None) -> dict[str, Any]:
    source_dir = input_dir or Path(__file__).with_name("phase179_inputs")
    csv_bytes = build_compact_input(source_dir)
    rows = parse_rows(csv_bytes)
    result = audit_rows(rows)
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "phase179_sec13dg_legacy_497_parent_summary.json").write_text(
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
