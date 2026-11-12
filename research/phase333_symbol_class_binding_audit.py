#!/usr/bin/env python3
"""Phase 333: determine whether SEC TradingSymbol XBRL facts bind directly to share classes.

Uses nine unique, hash-pinned 8-K/8-K/A documents from Phase 332. A symbol is
linked to a class only when the TradingSymbol fact's own XBRL context carries
an explicit class axis. Document-level co-occurrence of symbols and class
members is not treated as a mapping.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from research.phase328_sec_collision_prior_filing_xbrl_pilot import (
    SECClient,
    norm_symbol,
    retrieve_filing_facts,
)

PHASE = 333


def _axis_members(fact: dict, token: str) -> list[str]:
    return sorted({
        f"{d.get('dimension','')}={d.get('member','')}"
        for d in fact.get("dimensions", [])
        if token in str(d.get("dimension", ""))
    })


def extract_symbol_fact_rows(facts: list[dict]) -> list[dict]:
    rows = []
    for fact in facts:
        if fact.get("name") != "TradingSymbol":
            continue
        value = norm_symbol(str(fact.get("value") or ""))
        if not value:
            continue
        rows.append({
            "symbol": value,
            "context_ref": str(fact.get("context_ref") or ""),
            "dimensions": fact.get("dimensions", []) or [],
            "class_axis_members": _axis_members(fact, "StatementClassOfStockAxis")
                + _axis_members(fact, "ClassesOfShareCapitalAxis"),
            "listing_axis_members": _axis_members(fact, "EntityListingsExchangeAxis"),
        })
    return rows


def extract_title_fact_rows(facts: list[dict]) -> list[dict]:
    rows = []
    for fact in facts:
        if fact.get("name") not in {"Security12bTitle", "Security12gTitle"}:
            continue
        value = " ".join(str(fact.get("value") or "").split())
        if not value:
            continue
        rows.append({
            "name": fact["name"], "value": value,
            "context_ref": str(fact.get("context_ref") or ""),
            "dimensions": fact.get("dimensions", []) or [],
            "class_axis_members": _axis_members(fact, "StatementClassOfStockAxis")
                + _axis_members(fact, "ClassesOfShareCapitalAxis"),
        })
    return rows


def classify_document_binding(symbol_facts: list[dict], all_class_axis_members: list[str],
                              hash_ok: bool) -> str:
    if not hash_ok:
        return "HASH_MISMATCH_NOT_ADMITTED"
    if not symbol_facts:
        return "NO_TRADING_SYMBOL_FACT"
    direct = sum(bool(x.get("class_axis_members")) for x in symbol_facts)
    unique_symbols = {x["symbol"] for x in symbol_facts}
    if direct == len(symbol_facts):
        return "DIRECT_CLASS_AXIS_ON_ALL_SYMBOL_FACTS"
    if direct:
        return "PARTIAL_DIRECT_CLASS_AXIS_BINDING"
    if len(unique_symbols) > 1 and all_class_axis_members:
        return "MULTI_SYMBOLS_AND_CLASS_AXES_UNLINKED"
    if len(unique_symbols) > 1:
        return "MULTI_SYMBOLS_NO_CLASS_AXIS_BINDING"
    if all_class_axis_members:
        return "SINGLE_SYMBOL_AND_CLASS_AXES_UNLINKED"
    return "SINGLE_ISSUER_SYMBOL_NO_CLASS_BINDING"


def build_context_associations(symbol_facts: list[dict], title_facts: list[dict]) -> list[dict]:
    titles_by_context = defaultdict(list)
    for row in title_facts:
        if row["context_ref"]:
            titles_by_context[row["context_ref"]].append(row)
    associations = []
    for symbol in symbol_facts:
        same_context_titles = titles_by_context.get(symbol["context_ref"], [])
        associations.append({
            "symbol": symbol["symbol"],
            "context_ref": symbol["context_ref"],
            "class_axis_members": symbol["class_axis_members"],
            "listing_axis_members": symbol["listing_axis_members"],
            "same_context_security_titles": sorted({x["value"] for x in same_context_titles}),
            "same_context_title_class_axis_members": sorted({
                member for x in same_context_titles for member in x["class_axis_members"]
            }),
            "direct_class_binding": bool(symbol["class_axis_members"]),
        })
    return associations


def audit_document(client: SECClient, row: dict) -> tuple[dict, list[dict], list[dict]]:
    filing = {
        "accessionNumber": row["accession"],
        "primaryDocument": row["primary_document"],
        "form": row["form"],
        "filingDate": row["filing_date"],
    }
    facts, meta = retrieve_filing_facts(client, row["issuer_cik"], filing)
    actual_hash = str(meta.get("document_sha256") or "")
    hash_ok = actual_hash == row["expected_instance_sha256"]
    symbol_facts = extract_symbol_fact_rows(facts)
    title_facts = extract_title_fact_rows(facts)
    class_members = sorted({
        member for fact in facts
        for member in _axis_members(fact, "StatementClassOfStockAxis")
            + _axis_members(fact, "ClassesOfShareCapitalAxis")
    })
    symbols = sorted({x["symbol"] for x in symbol_facts})
    expected_symbols = sorted({str(x).upper() for x in row["expected_symbols"]})
    context_associations = build_context_associations(symbol_facts, title_facts)
    binding_status = classify_document_binding(symbol_facts, class_members, hash_ok)
    if not hash_ok:
        symbol_set_status = "NOT_ADMITTED_HASH_MISMATCH"
    elif symbols == expected_symbols:
        symbol_set_status = "MATCH_PHASE332_SYMBOL_SET"
    else:
        symbol_set_status = "SYMBOL_SET_DRIFT"
    summary = {
        "pair_id": row["pair_id"], "accession": row["accession"],
        "issuer_cik": row["issuer_cik"], "filing_date": row["filing_date"],
        "form": row["form"], "primary_document": row["primary_document"],
        "candidate_ticker": row["candidate_ticker"], "event_date": row["event_date"],
        "document_status": meta.get("document_status", ""),
        "document_name": meta.get("document_name", ""),
        "expected_sha256": row["expected_instance_sha256"],
        "actual_sha256": actual_hash, "hash_match": hash_ok,
        "expected_symbols": expected_symbols, "actual_symbols": symbols,
        "symbol_set_status": symbol_set_status,
        "symbol_fact_count": len(symbol_facts),
        "symbol_facts_with_class_axis": sum(bool(x["class_axis_members"]) for x in symbol_facts),
        "unique_class_axis_members": class_members,
        "security_title_fact_count": len(title_facts),
        "binding_status": binding_status,
        "direct_symbol_class_pairs": sum(bool(x["direct_class_binding"]) for x in context_associations),
        "symbol_facts": symbol_facts,
        "security_title_facts": title_facts,
        "context_associations": context_associations,
    }
    return summary, symbol_facts, title_facts


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                if isinstance(v, (dict, list)) else v
                for k, v in row.items()
            })


def run_audit(email: str, manifest_path: Path, output_dir: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    documents = manifest["documents"]
    if len(documents) != 9 or len({x["accession"] for x in documents}) != 9:
        raise ValueError("manifest_must_contain_nine_unique_accessions")
    if not email or "@" not in email:
        result = {
            "phase": PHASE, "status": "BLOCKED_MISSING_SEC_CONTACT_EMAIL",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "documents": [], "controls": {"f80_frozen": True, "strict_pit_admitted": False,
                "security_master_admitted": False, "alpha_test_run": False,
                "return_test_run": False, "holdout_used": False,
                "production_changed": False, "vendor_contacted": False, "data_purchased": False},
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "phase333_symbol_class_binding_audit.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("PHASE333_STATUS=" + result["status"])
        return result
    client = SECClient(email)
    summaries = []
    all_symbol_rows = []
    all_title_rows = []
    for i, row in enumerate(documents, 1):
        summary, symbols, titles = audit_document(client, row)
        summaries.append(summary)
        for fact in symbols:
            all_symbol_rows.append({
                "accession": row["accession"], "issuer_cik": row["issuer_cik"],
                "candidate_ticker": row["candidate_ticker"], **fact,
            })
        for fact in titles:
            all_title_rows.append({
                "accession": row["accession"], "issuer_cik": row["issuer_cik"], **fact,
            })
        print(f"PHASE333_PROGRESS={i}/{len(documents)}")
    counts = Counter(x["binding_status"] for x in summaries)
    summary = {
        "documents": len(summaries),
        "hash_matches": sum(x["hash_match"] for x in summaries),
        "hash_mismatches": sum(not x["hash_match"] for x in summaries),
        "documents_with_trading_symbol_facts": sum(bool(x["actual_symbols"]) for x in summaries),
        "documents_with_class_axis": sum(bool(x["unique_class_axis_members"]) for x in summaries),
        "documents_with_direct_symbol_class_binding": sum(x["direct_symbol_class_pairs"] > 0 for x in summaries),
        "symbol_facts": len(all_symbol_rows),
        "symbol_facts_with_class_axis": sum(bool(x["class_axis_members"]) for x in all_symbol_rows),
        "binding_status_counts": dict(sorted(counts.items())),
    }
    controls = {
        "f80_frozen": True, "strict_pit_admitted": False,
        "security_master_admitted": False, "alpha_test_run": False,
        "return_test_run": False, "holdout_used": False,
        "production_changed": False, "universe_changed": False,
        "vendor_contacted": False, "data_purchased": False,
    }
    result = {
        "phase": PHASE, "status": "COMPLETED_SEC_SYMBOL_CLASS_BINDING_PILOT",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_phase": manifest["source_phase"],
        "source_run_id": manifest["source_run_id"],
        "source_artifact_id": manifest["source_artifact_id"],
        "selection": manifest["selection_rule"],
        "summary": summary, "documents": summaries,
        "symbol_facts": all_symbol_rows, "security_title_facts": all_title_rows,
        "controls": controls,
        "interpretation": {
            "only_symbol_fact_context_dimensions_count_as_direct_class_binding": True,
            "document_level_symbol_and_class_axis_cooccurrence_is_not_a_mapping": True,
            "same_context_title_without_class_axis_is_not_a_class_mapping": True,
            "hash_mismatch_invalidates_document": True,
            "purposive_nine_document_sample_not_universe_prevalence": True,
            "no_security_master_or_alpha_admission": True,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase333_symbol_class_binding_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "phase333_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(output_dir / "phase333_document_summary.csv", summaries)
    write_csv(output_dir / "phase333_symbol_facts.csv", all_symbol_rows)
    write_csv(output_dir / "phase333_security_title_facts.csv", all_title_rows)
    print("PHASE333_SUMMARY=" + json.dumps(summary, sort_keys=True))
    print("PHASE333_CONTROLS=" + json.dumps(controls, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path,
                        default=Path("research/phase333_symbol_class_binding_manifest.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("phase333_output"))
    parser.add_argument("--email", default=os.environ.get("SEC_CONTACT_EMAIL", ""))
    args = parser.parse_args()
    run_audit(args.email, args.manifest, args.output_dir)


if __name__ == "__main__":
    main()
