#!/usr/bin/env python3
"""Phase 335: audit SEC XBRL class-QName drift and listing-axis stability.

Consumes the immutable Phase 334 GitHub Actions artifact. It does not re-fetch
SEC data and never merges raw taxonomy QNames. Same-context Security12bTitle
agreement is only a candidate alias diagnostic, not a canonicalization rule.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

PHASE = 335
SOURCE_RUN_ID = 43226260351
SOURCE_ARTIFACT_ID = 13947767592
SOURCE_ARTIFACT_SHA256 = "f107cdeab68b9905a0fb8adfd10c97564bc03f2315148f986f58e91d5ed706a4"
SOURCE_AUDIT_JSON_SHA256 = "c360eac0358ca4181664ecf18ea6699bccedd0e3d2251ea936c296a19588bc46"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_phase334(path: Path) -> dict:
    digest = sha256_file(path)
    if digest != SOURCE_AUDIT_JSON_SHA256:
        raise ValueError(f"phase334_audit_json_sha256_mismatch:{digest}")
    source = json.loads(path.read_text(encoding="utf-8"))
    if source.get("phase") != 334:
        raise ValueError("phase334_source_phase_mismatch")
    if source.get("status") != "COMPLETED_STRATIFIED_CLASS_BINDING_AUDIT":
        raise ValueError("phase334_source_status_not_admitted")
    summary = source.get("summary", {})
    if (
        summary.get("documents_rechecked") != 26
        or summary.get("document_hash_matches") != 26
        or summary.get("document_hash_mismatches") != 0
        or summary.get("symbol_set_matches") != 26
        or summary.get("symbol_set_drifts") != 0
        or summary.get("symbol_facts_rechecked") != 98
    ):
        raise ValueError("phase334_source_summary_mismatch")
    return source


def classify_symbol_profile(class_members: list[str],
                            member_titles: dict[str, list[str]]) -> str:
    members = sorted(set(class_members))
    if not members:
        return "NO_DIRECT_CLASS_AXIS"
    if len(members) == 1:
        return "SINGLE_QNAME_IN_SAMPLE_NOT_LONGITUDINAL_PROOF"
    title_sets = [tuple(sorted(set(member_titles.get(member, [])))) for member in members]
    if title_sets and all(title_sets) and len(set(title_sets)) == 1:
        return "CANDIDATE_TAXONOMY_ALIAS_SAME_TITLE_NOT_MERGED"
    return "MULTIPLE_QNAME_VARIANTS_AMBIGUOUS"


def build_profiles(source: dict) -> dict:
    docs = source["documents"]
    fact_rows = []
    excluded_docs = []
    for doc in docs:
        if not doc.get("hash_match") or doc.get("symbol_set_status") != "MATCH_PHASE332_SYMBOL_SET":
            excluded_docs.append({
                "accession": doc.get("accession", ""),
                "reason": "SOURCE_HASH_OR_SYMBOL_SET_NOT_ADMITTED",
            })
            continue
        for assoc in doc.get("context_associations", []):
            fact_rows.append({
                "accession": doc["accession"],
                "filing_date": doc["filing_date"],
                "pair_ids": doc.get("source_pair_ids", []),
                "candidate_tickers": doc.get("candidate_tickers", []),
                "symbol": str(assoc.get("symbol") or "").upper(),
                "context_ref": str(assoc.get("context_ref") or ""),
                "class_axis_members": sorted(set(assoc.get("class_axis_members") or [])),
                "listing_axis_members": sorted(set(assoc.get("listing_axis_members") or [])),
                "same_context_security_titles": sorted(set(assoc.get("same_context_security_titles") or [])),
                "direct_class_binding": bool(assoc.get("direct_class_binding")),
            })

    by_symbol: dict[str, list[dict]] = defaultdict(list)
    by_listing: dict[str, dict] = defaultdict(lambda: {"symbols": set(), "accessions": set(), "filing_dates": set()})
    for row in fact_rows:
        if row["symbol"]:
            by_symbol[row["symbol"]].append(row)
        for member in row["listing_axis_members"]:
            by_listing[member]["symbols"].add(row["symbol"])
            by_listing[member]["accessions"].add(row["accession"])
            by_listing[member]["filing_dates"].add(row["filing_date"])

    symbol_profiles = []
    for symbol, rows in sorted(by_symbol.items()):
        members = sorted({m for row in rows for m in row["class_axis_members"]})
        member_titles: dict[str, set[str]] = defaultdict(set)
        member_accessions: dict[str, set[str]] = defaultdict(set)
        member_dates: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            for member in row["class_axis_members"]:
                member_titles[member].update(row["same_context_security_titles"])
                member_accessions[member].add(row["accession"])
                member_dates[member].add(row["filing_date"])
        member_title_lists = {k: sorted(v) for k, v in member_titles.items()}
        classification = classify_symbol_profile(members, member_title_lists)
        listings = sorted({m for row in rows for m in row["listing_axis_members"]})
        symbol_profiles.append({
            "symbol": symbol,
            "classification": classification,
            "document_count": len({x["accession"] for x in rows}),
            "symbol_fact_count": len(rows),
            "direct_class_fact_count": sum(bool(x["class_axis_members"]) for x in rows),
            "direct_listing_fact_count": sum(bool(x["listing_axis_members"]) for x in rows),
            "class_axis_members": members,
            "class_member_count": len(members),
            "class_member_title_evidence": [
                {
                    "member": member,
                    "same_context_titles": member_title_lists.get(member, []),
                    "accessions": sorted(member_accessions[member]),
                    "filing_dates": sorted(member_dates[member]),
                }
                for member in members
            ],
            "listing_axis_members": listings,
            "listing_member_count": len(listings),
            "filing_dates": sorted({x["filing_date"] for x in rows}),
            "pair_ids": sorted({p for x in rows for p in x["pair_ids"]}),
        })

    listing_profiles = [
        {
            "listing_axis_member": member,
            "symbols": sorted(value["symbols"]),
            "accessions": sorted(value["accessions"]),
            "filing_dates": sorted(value["filing_dates"]),
        }
        for member, value in sorted(by_listing.items())
    ]
    binding_counts = Counter(x["classification"] for x in symbol_profiles)
    listing_symbols = [x for x in symbol_profiles if x["listing_axis_members"]]
    class_fact_count = sum(bool(x["class_axis_members"]) for x in fact_rows)
    listing_fact_count = sum(bool(x["listing_axis_members"]) for x in fact_rows)
    listing_and_class_count = sum(bool(x["listing_axis_members"]) and bool(x["class_axis_members"]) for x in fact_rows)
    multi_member = [x for x in symbol_profiles if x["class_member_count"] > 1]
    title_alias_candidates = [x for x in symbol_profiles
                              if x["classification"] == "CANDIDATE_TAXONOMY_ALIAS_SAME_TITLE_NOT_MERGED"]
    summary = {
        "source_documents": len(docs),
        "admitted_documents": len(docs) - len(excluded_docs),
        "excluded_source_documents": len(excluded_docs),
        "symbol_fact_rows": len(fact_rows),
        "unique_symbols": len(symbol_profiles),
        "symbols_with_direct_class_axis": sum(bool(x["class_axis_members"]) for x in symbol_profiles),
        "symbols_without_direct_class_axis": sum(not bool(x["class_axis_members"]) for x in symbol_profiles),
        "symbols_with_one_class_qname": binding_counts["SINGLE_QNAME_IN_SAMPLE_NOT_LONGITUDINAL_PROOF"],
        "symbols_with_multiple_class_qnames": len(multi_member),
        "multi_qname_same_title_candidate_aliases": len(title_alias_candidates),
        "multi_qname_ambiguous": binding_counts["MULTIPLE_QNAME_VARIANTS_AMBIGUOUS"],
        "symbols_with_listing_axis": len(listing_symbols),
        "symbols_with_multiple_listing_members": sum(x["listing_member_count"] > 1 for x in symbol_profiles),
        "class_axis_fact_rows": class_fact_count,
        "listing_axis_fact_rows": listing_fact_count,
        "listing_and_class_axis_fact_rows": listing_and_class_count,
        "unique_listing_axis_members": len(listing_profiles),
        "documents_with_listing_axis": len({x["accession"] for x in fact_rows if any(
            row["listing_axis_members"] for row in fact_rows if row["accession"] == x["accession"]
        )}),
        "binding_classification_counts": dict(sorted(binding_counts.items())),
        "qname_aliases_merged": 0,
    }
    return {
        "symbol_profiles": symbol_profiles,
        "listing_profiles": listing_profiles,
        "fact_rows": fact_rows,
        "excluded_documents": excluded_docs,
        "summary": summary,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                if isinstance(v, (dict, list)) else v
                for k, v in row.items()
            })


def run_audit(input_path: Path, output_dir: Path) -> dict:
    source = load_phase334(input_path)
    profiles = build_profiles(source)
    controls = {
        "f80_frozen": True,
        "strict_pit_admitted": False,
        "security_master_admitted": False,
        "universe_coverage_admitted": False,
        "alpha_test_run": False,
        "return_test_run": False,
        "bootstrap_loo_run": False,
        "chronological_oos_run": False,
        "holdout_used": False,
        "production_changed": False,
        "universe_changed": False,
        "capital_changed": False,
        "parameters_changed": False,
        "qname_aliases_merged": False,
        "data_purchased": False,
    }
    result = {
        "phase": PHASE,
        "status": "COMPLETED_TAXONOMY_MEMBER_AND_LISTING_AXIS_STABILITY_AUDIT",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "phase": 334,
            "run_id": SOURCE_RUN_ID,
            "artifact_id": SOURCE_ARTIFACT_ID,
            "artifact_sha256": SOURCE_ARTIFACT_SHA256,
            "audit_json_sha256": sha256_file(input_path),
        },
        "summary": profiles["summary"],
        "symbol_profiles": profiles["symbol_profiles"],
        "listing_profiles": profiles["listing_profiles"],
        "fact_rows": profiles["fact_rows"],
        "excluded_documents": profiles["excluded_documents"],
        "controls": controls,
        "interpretation": {
            "same_context_title_agreement_is_candidate_alias_evidence_only": True,
            "raw_class_axis_qnames_preserved": True,
            "no_qname_aliases_merged": True,
            "single_qname_in_sample_is_not_permanent_stability_proof": True,
            "listing_axis_is_not_substituted_for_class_axis": True,
            "source_sample_is_purposive_collision_panel_not_universe_prevalence": True,
            "no_security_master_or_alpha_admission": True,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase335_taxonomy_listing_stability_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "phase335_summary.json").write_text(
        json.dumps(profiles["summary"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(output_dir / "phase335_symbol_profiles.csv", profiles["symbol_profiles"])
    write_csv(output_dir / "phase335_listing_profiles.csv", profiles["listing_profiles"])
    write_csv(output_dir / "phase335_fact_rows.csv", profiles["fact_rows"])
    print("PHASE335_STATUS=" + result["status"])
    print("PHASE335_SUMMARY=" + json.dumps(profiles["summary"], sort_keys=True))
    print("PHASE335_CONTROLS=" + json.dumps(controls, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", type=Path,
                        default=Path("phase334_source/phase334_symbol_class_binding_audit.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("phase335_output"))
    args = parser.parse_args()
    run_audit(args.input_json, args.output_dir)


if __name__ == "__main__":
    main()
