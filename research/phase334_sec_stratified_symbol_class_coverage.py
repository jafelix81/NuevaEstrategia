#!/usr/bin/env python3
"""Phase 334: stratified SEC event-filing symbol/class coverage with a hard freshness gate.

Re-runs the Phase 332 collision-pair event screen, then examines every unique
hash-bearing TradingSymbol document observed in a fresh (<=365 calendar day)
prior-periodic window. Co-filer rows are deduplicated by accession only after
hash/schema consistency checks. Class mapping is accepted only from the
TradingSymbol fact's own class-axis dimensions (Phase 333 rule).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from research.phase328_sec_collision_prior_filing_xbrl_pilot import SECClient
from research.phase332_sec_event_driven_identity_audit import run_audit as run_phase332
from research.phase333_symbol_class_binding_audit import audit_document

PHASE = 334
MAX_ANCHOR_AGE_DAYS = 365


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def classify_anchor_observation(observation: dict, max_age_days: int = MAX_ANCHOR_AGE_DAYS) -> dict:
    """Apply the predeclared fresh-anchor and completeness gate to one CIK-side observation."""
    event = _parse_date(observation.get("event_date", ""))
    anchor = _parse_date(observation.get("prior_periodic_filed_date", ""))
    base = {
        "pair_id": str(observation.get("pair_id") or ""),
        "side": str(observation.get("side") or ""),
        "issuer_cik": str(observation.get("issuer_cik") or ""),
        "event_date": str(observation.get("event_date") or ""),
        "prior_periodic_filed_date": str(observation.get("prior_periodic_filed_date") or ""),
        "anchor_age_days": None,
    }
    if event is None or anchor is None:
        return {**base, "anchor_status": "NO_VALID_PRIOR_PERIODIC_ANCHOR"}
    age = (event - anchor).days
    base["anchor_age_days"] = age
    if age <= 0:
        return {**base, "anchor_status": "INVALID_ANCHOR_CHRONOLOGY"}
    if age > max_age_days:
        return {**base, "anchor_status": "STALE_ANCHOR"}
    if bool(observation.get("event_window_truncated")):
        return {**base, "anchor_status": "INCOMPLETE_TRUNCATED_EVENT_WINDOW"}
    try:
        shard_errors = int(observation.get("shard_errors") or 0)
    except (TypeError, ValueError):
        shard_errors = 1
    if shard_errors:
        return {**base, "anchor_status": "INCOMPLETE_SHARD_ERRORS"}
    if observation.get("submissions_status") not in {"OK", "CACHED_OK"}:
        return {**base, "anchor_status": "INCOMPLETE_SUBMISSIONS"}
    return {**base, "anchor_status": "FRESH_COMPLETE"}


def build_fresh_document_manifest(observations: list[dict], event_filings: list[dict],
                                  max_age_days: int = MAX_ANCHOR_AGE_DAYS) -> dict:
    """Select all symbol-bearing event documents from complete fresh windows.

    Duplicate accession rows (normally co-filers) are collapsed only when the
    document hash and document-level schema signature agree. Any conflict is
    quarantined rather than resolved by ticker, CIK order, or row summation.
    """
    anchor_rows = [classify_anchor_observation(x, max_age_days) for x in observations]
    anchor_map = {(x["pair_id"], x["side"]): x for x in anchor_rows}
    fresh_keys = {k for k, v in anchor_map.items() if v["anchor_status"] == "FRESH_COMPLETE"}

    grouped: dict[str, list[dict]] = defaultdict(list)
    rejected_rows = Counter()
    for row in event_filings:
        key = (str(row.get("pair_id") or ""), str(row.get("side") or ""))
        if key not in fresh_keys:
            rejected_rows["outside_fresh_complete_anchor"] += 1
            continue
        filed = _parse_date(row.get("filing_date", ""))
        event = _parse_date(row.get("event_date", ""))
        anchor = _parse_date(anchor_map[key]["prior_periodic_filed_date"])
        if filed is None or event is None or anchor is None or not (anchor < filed < event):
            rejected_rows["invalid_or_non_pre_event_filing_date"] += 1
            continue
        symbols = sorted({str(x).strip().upper() for x in (row.get("trading_symbols") or []) if str(x).strip()})
        digest = str(row.get("document_sha256") or "").lower()
        if not symbols:
            rejected_rows["no_trading_symbol_fact"] += 1
            continue
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            rejected_rows["missing_or_invalid_document_hash"] += 1
            continue
        accession = str(row.get("accession") or "").strip()
        if not accession:
            rejected_rows["missing_accession"] += 1
            continue
        enriched = dict(row)
        enriched["_anchor_age_days"] = anchor_map[key]["anchor_age_days"]
        enriched["_anchor_date"] = anchor_map[key]["prior_periodic_filed_date"]
        grouped[accession].append(enriched)

    documents = []
    quarantines = []
    duplicate_rows_collapsed = 0
    for accession, rows in sorted(grouped.items()):
        signatures = {
            (
                str(x.get("document_sha256") or "").lower(),
                str(x.get("primary_document") or ""),
                str(x.get("form") or ""),
                str(x.get("filing_date") or ""),
                tuple(sorted({str(v).upper() for v in (x.get("trading_symbols") or [])})),
            )
            for x in rows
        }
        if len(signatures) != 1:
            quarantines.append({
                "accession": accession,
                "reason": "COFILER_DOCUMENT_HASH_OR_SCHEMA_CONFLICT",
                "rows": len(rows),
                "signatures": [list(x) for x in sorted(signatures, key=str)],
                "issuer_ciks": sorted({str(x.get("issuer_cik") or "") for x in rows}),
            })
            continue
        duplicate_rows_collapsed += max(0, len(rows) - 1)
        chosen = sorted(rows, key=lambda x: (str(x.get("issuer_cik") or "").zfill(10),
                                             str(x.get("pair_id") or ""), str(x.get("side") or "")))[0]
        contexts = []
        for row in sorted(rows, key=lambda x: (str(x.get("pair_id") or ""), str(x.get("side") or ""))):
            contexts.append({
                "pair_id": str(row.get("pair_id") or ""),
                "side": str(row.get("side") or ""),
                "issuer_cik": str(row.get("issuer_cik") or ""),
                "candidate_ticker": str(row.get("ticker_candidate") or "").upper(),
                "event_date": str(row.get("event_date") or ""),
                "anchor_date": str(row.get("_anchor_date") or ""),
                "anchor_age_days": row.get("_anchor_age_days"),
            })
        event_dates = [str(x.get("event_date") or "") for x in rows]
        documents.append({
            "accession": accession,
            "issuer_cik": str(chosen.get("issuer_cik") or ""),
            "filing_date": str(chosen.get("filing_date") or ""),
            "form": str(chosen.get("form") or ""),
            "primary_document": str(chosen.get("primary_document") or ""),
            "expected_instance_sha256": str(chosen.get("document_sha256") or "").lower(),
            "candidate_ticker": str(chosen.get("ticker_candidate") or "").upper(),
            "expected_symbols": sorted({str(v).upper() for v in (chosen.get("trading_symbols") or [])}),
            "event_date": min(event_dates),
            "pair_id": str(chosen.get("pair_id") or ""),
            "source_pair_ids": sorted({str(x.get("pair_id") or "") for x in rows}),
            "source_issuer_ciks": sorted({str(x.get("issuer_cik") or "") for x in rows}),
            "candidate_tickers": sorted({str(x.get("ticker_candidate") or "").upper() for x in rows}),
            "cofiler_duplicate_rows": len(rows) - 1,
            "source_contexts": contexts,
        })

    status_counts = Counter(x["anchor_status"] for x in anchor_rows)
    return {
        "anchor_rows": anchor_rows,
        "fresh_keys": sorted([list(x) for x in fresh_keys]),
        "documents": documents,
        "quarantines": quarantines,
        "rejected_event_rows": dict(sorted(rejected_rows.items())),
        "summary": {
            "observations": len(anchor_rows),
            "fresh_complete_anchor_observations": status_counts["FRESH_COMPLETE"],
            "stale_anchor_observations": status_counts["STALE_ANCHOR"],
            "no_valid_prior_anchor_observations": status_counts["NO_VALID_PRIOR_PERIODIC_ANCHOR"],
            "invalid_anchor_chronology_observations": status_counts["INVALID_ANCHOR_CHRONOLOGY"],
            "incomplete_observations": sum(v for k, v in status_counts.items() if k.startswith("INCOMPLETE_")),
            "anchor_status_counts": dict(sorted(status_counts.items())),
            "fresh_complete_pairs": len({x["pair_id"] for x in anchor_rows if x["anchor_status"] == "FRESH_COMPLETE"}),
            "fresh_symbol_bearing_unique_accessions": len(documents),
            "cofiler_duplicate_rows_collapsed": duplicate_rows_collapsed,
            "accession_conflict_quarantines": len(quarantines),
            "rejected_event_rows": dict(sorted(rejected_rows.items())),
        },
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
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


def run_audit(email: str, manifest_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_dir = output_dir / "phase332_source"
    source = run_phase332(email, source_dir, manifest_path)
    if source.get("status") != "COMPLETED_SEC_EVENT_DRIVEN_IDENTITY_FEASIBILITY_PILOT":
        result = {
            "phase": PHASE, "status": source.get("status", "BLOCKED_PHASE332_SOURCE"),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_phase": 332, "source_summary": source.get("summary", {}),
            "documents": [], "controls": {
                "f80_frozen": True, "strict_pit_admitted": False,
                "security_master_admitted": False, "universe_coverage_admitted": False,
                "alpha_test_run": False, "return_test_run": False,
                "bootstrap_loo_run": False, "chronological_oos_run": False,
                "holdout_used": False, "production_changed": False,
                "universe_changed": False, "capital_changed": False,
                "parameters_changed": False, "data_purchased": False,
            },
        }
        (output_dir / "phase334_symbol_class_binding_audit.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("PHASE334_STATUS=" + result["status"])
        return result

    selection = build_fresh_document_manifest(source["observations"], source["event_filings"])
    selected_manifest = {
        "phase": PHASE,
        "source_phase": 332,
        "source_generated_at_utc": source.get("generated_at_utc", ""),
        "fresh_anchor_rule": f"0 < event_date - prior_periodic_filed_date <= {MAX_ANCHOR_AGE_DAYS} calendar days; complete, non-truncated event window; zero shard errors",
        "deduplication_rule": "one row per accession only after identical document SHA-256, form, filing date, primary document and TradingSymbol set across co-filer observations",
        "documents": selection["documents"],
        "quarantines": selection["quarantines"],
    }
    (output_dir / "phase334_selected_manifest.json").write_text(
        json.dumps(selected_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    client = SECClient(email)
    summaries = []
    all_symbol_facts = []
    all_title_facts = []
    for i, row in enumerate(selection["documents"], 1):
        summary, symbol_facts, title_facts = audit_document(client, row)
        summary["source_pair_ids"] = row["source_pair_ids"]
        summary["source_issuer_ciks"] = row["source_issuer_ciks"]
        summary["candidate_tickers"] = row["candidate_tickers"]
        summary["cofiler_duplicate_rows"] = row["cofiler_duplicate_rows"]
        summary["source_contexts"] = row["source_contexts"]
        if summary["symbol_set_status"] != "MATCH_PHASE332_SYMBOL_SET" and summary["hash_match"]:
            summary["binding_status"] = "SYMBOL_SET_DRIFT_NOT_ADMITTED"
        summaries.append(summary)
        for fact in symbol_facts:
            all_symbol_facts.append({
                "accession": row["accession"],
                "pair_ids": row["source_pair_ids"],
                "issuer_ciks": row["source_issuer_ciks"],
                **fact,
            })
        for fact in title_facts:
            all_title_facts.append({
                "accession": row["accession"],
                "pair_ids": row["source_pair_ids"],
                "issuer_ciks": row["source_issuer_ciks"],
                **fact,
            })
        print(f"PHASE334_PROGRESS={i}/{len(selection['documents'])}")

    binding_counts = Counter(x["binding_status"] for x in summaries)
    year_counts = Counter(str(x["filing_date"])[:4] for x in summaries)
    pair_counts = Counter(pair for x in summaries for pair in x["source_pair_ids"])
    matched = [x for x in summaries if x["hash_match"] and x["symbol_set_status"] == "MATCH_PHASE332_SYMBOL_SET"]
    valid_symbol_facts = [x for x in all_symbol_facts
                          if next((d for d in matched if d["accession"] == x["accession"]), None)]
    direct_symbol_facts = sum(bool(x.get("class_axis_members")) for x in valid_symbol_facts)
    summary = {
        **selection["summary"],
        "documents_rechecked": len(summaries),
        "document_hash_matches": sum(bool(x["hash_match"]) for x in summaries),
        "document_hash_mismatches": sum(not bool(x["hash_match"]) for x in summaries),
        "symbol_set_matches": sum(x["symbol_set_status"] == "MATCH_PHASE332_SYMBOL_SET" for x in summaries),
        "symbol_set_drifts": sum(x["symbol_set_status"] == "SYMBOL_SET_DRIFT" for x in summaries),
        "documents_with_direct_class_binding": sum(x["binding_status"] == "DIRECT_CLASS_AXIS_ON_ALL_SYMBOL_FACTS" for x in summaries),
        "documents_with_partial_direct_class_binding": sum(x["binding_status"] == "PARTIAL_DIRECT_CLASS_AXIS_BINDING" for x in summaries),
        "documents_without_direct_class_binding": sum(
            x["binding_status"] in {
                "MULTI_SYMBOLS_AND_CLASS_AXES_UNLINKED",
                "MULTI_SYMBOLS_NO_CLASS_AXIS_BINDING",
                "SINGLE_SYMBOL_AND_CLASS_AXES_UNLINKED",
                "SINGLE_ISSUER_SYMBOL_NO_CLASS_BINDING",
            } for x in summaries
        ),
        "documents_not_admitted": sum(x["binding_status"] in {
            "HASH_MISMATCH_NOT_ADMITTED", "SYMBOL_SET_DRIFT_NOT_ADMITTED"
        } for x in summaries),
        "symbol_facts_rechecked": len(all_symbol_facts),
        "symbol_facts_with_direct_class_axis": direct_symbol_facts,
        "symbol_facts_without_direct_class_axis": len(valid_symbol_facts) - direct_symbol_facts,
        "binding_status_counts": dict(sorted(binding_counts.items())),
        "filing_year_distribution": dict(sorted(year_counts.items())),
        "pair_document_distribution": dict(sorted(pair_counts.items())),
        "latest_phase333_accessions_recovered": 0,
    }
    phase333_manifest_path = Path("research/phase333_symbol_class_binding_manifest.json")
    if phase333_manifest_path.exists():
        prior = json.loads(phase333_manifest_path.read_text(encoding="utf-8"))
        prior_accessions = {str(x["accession"]) for x in prior.get("documents", [])}
        current_accessions = {str(x["accession"]) for x in selection["documents"]}
        summary["latest_phase333_accessions_recovered"] = len(prior_accessions & current_accessions)
        summary["latest_phase333_accessions_missing"] = sorted(prior_accessions - current_accessions)

    controls = {
        "f80_frozen": True, "strict_pit_admitted": False,
        "security_master_admitted": False, "universe_coverage_admitted": False,
        "alpha_test_run": False, "return_test_run": False,
        "bootstrap_loo_run": False, "chronological_oos_run": False,
        "holdout_used": False, "production_changed": False,
        "universe_changed": False, "capital_changed": False,
        "parameters_changed": False, "data_purchased": False,
    }
    status = "COMPLETED_STRATIFIED_CLASS_BINDING_AUDIT"
    if summary["document_hash_mismatches"] or summary["symbol_set_drifts"] or selection["quarantines"]:
        status = "COMPLETED_WITH_EXPLICIT_QUARANTINES"
    result = {
        "phase": PHASE, "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_phase": 332, "source_summary": source.get("summary", {}),
        "fresh_anchor_rule": selected_manifest["fresh_anchor_rule"],
        "deduplication_rule": selected_manifest["deduplication_rule"],
        "summary": summary,
        "anchor_observations": selection["anchor_rows"],
        "selected_manifest": selected_manifest,
        "documents": summaries,
        "symbol_facts": all_symbol_facts,
        "security_title_facts": all_title_facts,
        "controls": controls,
        "interpretation": {
            "sample_is_purposive_collision_panel_not_universe_prevalence": True,
            "event_date_is_daily_collision_proxy_not_transaction_timestamp": True,
            "same_day_event_filings_excluded": True,
            "direct_binding_requires_class_axis_on_symbol_fact_context": True,
            "cofiler_accessions_deduplicated_only_after_hash_and_schema_match": True,
            "fresh_anchor_rule_encoded_ex_ante_in_audit": True,
            "no_security_master_or_alpha_admission": True,
        },
    }
    (output_dir / "phase334_symbol_class_binding_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "phase334_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_csv(output_dir / "phase334_document_summary.csv", summaries)
    _write_csv(output_dir / "phase334_symbol_facts.csv", all_symbol_facts)
    _write_csv(output_dir / "phase334_security_title_facts.csv", all_title_facts)
    _write_csv(output_dir / "phase334_anchor_observations.csv", selection["anchor_rows"])
    print("PHASE334_STATUS=" + status)
    print("PHASE334_SUMMARY=" + json.dumps(summary, sort_keys=True))
    print("PHASE334_CONTROLS=" + json.dumps(controls, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path,
                        default=Path("research/phase328_collision_pair_manifest.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("phase334_output"))
    parser.add_argument("--email", default=os.environ.get("SEC_CONTACT_EMAIL", ""))
    args = parser.parse_args()
    run_audit(args.email, args.manifest, args.output_dir)


if __name__ == "__main__":
    main()
