#!/usr/bin/env python3
"""Phase 332: conservative SEC event-filing chronology for historical issuer-symbol identity.

For each side of the 28 purposive Phase 325 collision pairs, inspect only SEC
corporate-action/listing-related filings filed strictly after the latest prior
periodic filing and strictly before the Form 4 collision date. Same-day sources
are excluded because intraday ordering is not established. This is identity
feasibility only; it is not a security master or trading-signal test.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from research.phase328_sec_collision_prior_filing_xbrl_pilot import (
    SECClient,
    _parallel_rows,
    load_collision_pairs,
    retrieve_filing_facts,
    select_prior_periodic_filing,
    summarize_facts,
)

PHASE = 332
EVENT_FORMS = {
    "8-K", "8-K/A", "6-K", "6-K/A",
    "25", "25-NSE", "15-12B", "15-12G", "15-15D",
    "10-12B", "10-12G", "8-A", "8-A12B",
    "S-4", "S-4/A", "F-4", "F-4/A", "425",
    "DEFM14A", "PREM14A", "SC 14D9", "SC TO",
    "S-1", "S-1/A", "S-3", "S-3/A",
}
MAX_EVENT_FILINGS_PER_OBSERVATION = 25


def _valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(str(value))
        return True
    except (TypeError, ValueError):
        return False


def select_event_filings(rows: list[dict], start_date: str, event_date: str) -> list[dict]:
    """Return exact allowed event forms in the open interval (start, event)."""
    if not _valid_iso_date(start_date) or not _valid_iso_date(event_date):
        raise ValueError("invalid_event_window_date")
    if start_date >= event_date:
        raise ValueError("non_positive_event_window")
    selected = []
    seen = set()
    for row in rows:
        form = str(row.get("form") or "").upper().strip()
        filed = str(row.get("filingDate") or "")
        accession = str(row.get("accessionNumber") or "").strip()
        if form not in EVENT_FORMS or not _valid_iso_date(filed) or not accession:
            continue
        if not (start_date < filed < event_date):
            continue
        if accession in seen:
            continue
        seen.add(accession)
        selected.append({
            "form": form,
            "filingDate": filed,
            "accessionNumber": accession,
            "primaryDocument": str(row.get("primaryDocument") or ""),
            "reportDate": str(row.get("reportDate") or ""),
        })
    return sorted(selected, key=lambda r: (r["filingDate"], r["accessionNumber"]), reverse=True)


def load_submission_rows_in_window(submissions: dict, start_date: str, event_date: str,
                                   client: SECClient) -> tuple[list[dict], list[dict]]:
    """Load recent rows plus only historical shards overlapping the event window."""
    rows = _parallel_rows(submissions.get("filings", {}).get("recent", {}))
    errors = []
    recent_dates = [r["filingDate"] for r in rows if _valid_iso_date(r.get("filingDate", ""))]
    recent_min = min(recent_dates) if recent_dates else ""
    if not recent_min or start_date < recent_min:
        shards = submissions.get("filings", {}).get("files", []) or []
        eligible = []
        for shard in shards:
            filing_from = str(shard.get("filingFrom") or "")
            filing_to = str(shard.get("filingTo") or "")
            name = str(shard.get("name") or "")
            if not name or not _valid_iso_date(filing_from):
                continue
            if filing_from >= event_date:
                continue
            if filing_to and _valid_iso_date(filing_to) and filing_to <= start_date:
                continue
            eligible.append(shard)
        for shard in sorted(eligible, key=lambda x: str(x.get("filingFrom") or "")):
            name = str(shard.get("name") or "")
            raw, status, err, _ = client.get(
                f"https://data.sec.gov/submissions/{name}", max_bytes=20_000_000
            )
            if raw is None:
                errors.append({"shard": name, "http_status": status, "error": err})
                continue
            try:
                obj = json.loads(raw)
                rows.extend(_parallel_rows(obj.get("filings", {}).get("recent", {})))
            except (ValueError, AttributeError, TypeError) as exc:
                errors.append({"shard": name, "http_status": status,
                               "error": f"SHARD_JSON_PARSE:{type(exc).__name__}"})
    deduped = {}
    for row in rows:
        accession = str(row.get("accessionNumber") or "").strip()
        if accession:
            deduped.setdefault(accession, row)
    return list(deduped.values()), errors


def classify_latest_symbol_evidence(event_results: list[dict], candidate: str) -> dict:
    """Use the latest pre-event filing with an actual TradingSymbol fact; no inference."""
    evidence = [r for r in event_results if r.get("trading_symbols")]
    if not evidence:
        return {
            "latest_symbol_evidence_status": "NO_TARGET_SYMBOL_FACT",
            "latest_symbol_evidence_date": "",
            "latest_symbol_evidence_form": "",
            "latest_symbol_evidence_accession": "",
            "latest_symbol_evidence_symbols": [],
        }
    latest = max(evidence, key=lambda r: (r["filing_date"], r["accession"]))
    symbols = sorted(set(str(x).upper() for x in latest["trading_symbols"]))
    if candidate.upper() in symbols:
        status = "MATCH_SINGLE_SYMBOL" if len(symbols) == 1 else "MATCH_AMONG_MULTIPLE_SYMBOLS"
    else:
        status = "MISMATCH"
    return {
        "latest_symbol_evidence_status": status,
        "latest_symbol_evidence_date": latest["filing_date"],
        "latest_symbol_evidence_form": latest["form"],
        "latest_symbol_evidence_accession": latest["accession"],
        "latest_symbol_evidence_symbols": symbols,
    }


def audit_observation(client: SECClient, pair: dict, side: str,
                      submissions_cache: dict[str, dict]) -> tuple[dict, list[dict]]:
    suffix = side.lower()
    cik = str(pair[f"issuer_cik_{suffix}"])
    name = str(pair[f"issuer_name_{suffix}"])
    event_date = str(pair["event_date"])
    candidate = str(pair["ticker_candidate"]).upper()
    base = {
        "pair_id": pair["pair_id"], "side": side, "ticker_candidate": candidate,
        "issuer_cik": cik, "issuer_name": name, "event_date": event_date,
        "submissions_status": "", "prior_periodic_form": "",
        "prior_periodic_accession": "", "prior_periodic_filed_date": "",
        "event_filing_candidates": 0, "event_filings_retrieved": 0,
        "event_window_truncated": False, "shard_errors": 0,
    }
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    if cik in submissions_cache:
        submissions = submissions_cache[cik]
        submissions_status = "CACHED_OK"
    else:
        raw, status, err, _ = client.get(url, max_bytes=20_000_000)
        if raw is None:
            return ({**base, "submissions_status": err or f"HTTP_{status}",
                     "observation_status": "SUBMISSIONS_UNAVAILABLE",
                     "latest_symbol_evidence_status": "NOT_TESTED"}, [])
        try:
            submissions = json.loads(raw)
        except ValueError:
            return ({**base, "submissions_status": "JSON_PARSE_ERROR",
                     "observation_status": "SUBMISSIONS_PARSE_ERROR",
                     "latest_symbol_evidence_status": "NOT_TESTED"}, [])
        submissions_cache[cik] = submissions
        submissions_status = "OK"

    prior, prior_source = select_prior_periodic_filing(submissions, event_date, client)
    if not prior:
        return ({**base, "submissions_status": submissions_status,
                 "prior_periodic_source": prior_source,
                 "observation_status": "NO_PRIOR_PERIODIC_ANCHOR",
                 "latest_symbol_evidence_status": "NOT_TESTED"}, [])

    start_date = str(prior["filingDate"])
    rows, shard_errors = load_submission_rows_in_window(submissions, start_date, event_date, client)
    event_filings = select_event_filings(rows, start_date, event_date)
    truncated = len(event_filings) > MAX_EVENT_FILINGS_PER_OBSERVATION
    selected = event_filings[:MAX_EVENT_FILINGS_PER_OBSERVATION]
    results = []
    for filing in selected:
        facts, meta = retrieve_filing_facts(client, cik, filing)
        fact_summary = summarize_facts(facts, candidate)
        results.append({
            "pair_id": pair["pair_id"], "side": side, "issuer_cik": cik,
            "ticker_candidate": candidate, "event_date": event_date,
            "filing_date": filing["filingDate"], "form": filing["form"],
            "accession": filing["accessionNumber"],
            "primary_document": filing["primaryDocument"],
            "document_status": meta.get("document_status", ""),
            "document_sha256": meta.get("document_sha256", ""),
            "document_bytes": meta.get("document_bytes", 0),
            "trading_symbols": fact_summary.get("trading_symbols", []),
            "symbol_match_status": fact_summary.get("symbol_match_status", ""),
            "security_titles": fact_summary.get("security_titles", []),
            "class_axis_members": fact_summary.get("class_axis_members", []),
            "listing_axis_members": fact_summary.get("listing_axis_members", []),
            "is_pre_event_by_filing_date": filing["filingDate"] < event_date,
        })
    latest = classify_latest_symbol_evidence(results, candidate)
    if truncated:
        observation_status = "TRUNCATED_EVENT_WINDOW"
    elif not event_filings:
        observation_status = "NO_INTERVENING_EVENT_FILINGS"
    elif latest["latest_symbol_evidence_status"] == "NO_TARGET_SYMBOL_FACT":
        observation_status = "EVENT_FILINGS_NO_TARGET_SYMBOL_FACTS"
    else:
        observation_status = "PRE_EVENT_SYMBOL_EVIDENCE_FOUND"
    observation = {
        **base,
        "submissions_status": submissions_status,
        "prior_periodic_source": prior_source,
        "prior_periodic_form": prior.get("form", ""),
        "prior_periodic_accession": prior.get("accessionNumber", ""),
        "prior_periodic_filed_date": start_date,
        "event_filing_candidates": len(event_filings),
        "event_filings_retrieved": len(selected),
        "event_window_truncated": truncated,
        "shard_errors": len(shard_errors),
        "observation_status": observation_status,
        **latest,
    }
    return observation, results


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


def run_audit(email: str, output_dir: Path, manifest_path: Path) -> dict:
    pairs = load_collision_pairs(manifest_path)
    if not email or "@" not in email:
        summary = {"pairs": len(pairs), "observations": len(pairs) * 2,
                   "submissions_ok": 0, "periodic_anchors": 0,
                   "event_filing_candidates": 0, "event_filings_retrieved": 0,
                   "symbol_fact_observations": 0, "latest_symbol_matches": 0,
                   "latest_symbol_mismatches": 0, "no_target_symbol_facts": 0}
        result = {
            "phase": PHASE, "status": "BLOCKED_MISSING_SEC_CONTACT_EMAIL",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "summary": summary, "observations": [], "event_filings": [],
            "controls": {"f80_frozen": True, "strict_pit_admitted": False,
                         "security_master_admitted": False, "universe_coverage_admitted": False,
                         "alpha_test_authorized": False, "return_test_run": False,
                         "bootstrap_loo_run": False, "chronological_oos_run": False,
                         "holdout_used": False, "production_changed": False,
                         "universe_changed": False, "capital_changed": False,
                         "parameters_changed": False, "vendor_contacted": False,
                         "data_purchased": False, "email_sent": False},
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "phase332_event_identity_audit.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("PHASE332_STATUS=" + result["status"])
        return result

    client = SECClient(email)
    submissions_cache: dict[str, dict] = {}
    observations, event_results = [], []
    for i, pair in enumerate(pairs, 1):
        for side in ("A", "B"):
            observation, filings = audit_observation(client, pair, side, submissions_cache)
            observations.append(observation)
            event_results.extend(filings)
        print(f"PHASE332_PROGRESS={i}/{len(pairs)}")
    status_counts = Counter(x["observation_status"] for x in observations)
    summary = {
        "pairs": len(pairs), "observations": len(observations),
        "submissions_ok": sum(x["submissions_status"] in {"OK", "CACHED_OK"} for x in observations),
        "periodic_anchors": sum(bool(x.get("prior_periodic_accession")) for x in observations),
        "event_filing_observations": sum(x["event_filing_candidates"] > 0 for x in observations),
        "event_filing_candidates": sum(x["event_filing_candidates"] for x in observations),
        "event_filings_retrieved": len(event_results),
        "event_documents_with_target_symbol_facts": sum(bool(x["trading_symbols"]) for x in event_results),
        "symbol_fact_observations": sum(x["latest_symbol_evidence_status"] not in {
            "NOT_TESTED", "NO_TARGET_SYMBOL_FACT"} for x in observations),
        "latest_symbol_matches": sum(x["latest_symbol_evidence_status"] in {
            "MATCH_SINGLE_SYMBOL", "MATCH_AMONG_MULTIPLE_SYMBOLS"} for x in observations),
        "latest_symbol_mismatches": sum(x["latest_symbol_evidence_status"] == "MISMATCH" for x in observations),
        "no_target_symbol_facts": sum(x["latest_symbol_evidence_status"] == "NO_TARGET_SYMBOL_FACT" for x in observations),
        "truncated_observations": sum(bool(x["event_window_truncated"]) for x in observations),
        "shard_error_observations": sum(bool(x["shard_errors"]) for x in observations),
        "observation_status_counts": dict(sorted(status_counts.items())),
    }
    controls = {
        "f80_frozen": True, "strict_pit_admitted": False,
        "security_master_admitted": False, "universe_coverage_admitted": False,
        "alpha_test_authorized": False, "return_test_run": False,
        "bootstrap_loo_run": False, "chronological_oos_run": False,
        "holdout_used": False, "production_changed": False,
        "universe_changed": False, "capital_changed": False,
        "parameters_changed": False, "vendor_contacted": False,
        "data_purchased": False, "email_sent": False,
    }
    result = {
        "phase": PHASE, "status": "COMPLETED_SEC_EVENT_DRIVEN_IDENTITY_FEASIBILITY_PILOT",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "provider": "U.S. Securities and Exchange Commission",
            "selection": "all 28 Phase 325 same-day ticker-collision pairs; both issuer CIK sides",
            "event_forms": sorted(EVENT_FORMS),
            "window": "latest prior supported periodic filing < event filing date < Form 4 collision date",
            "same_day_filings": "excluded; no intraday ordering inferred",
            "max_event_filings_per_observation": MAX_EVENT_FILINGS_PER_OBSERVATION,
        },
        "summary": summary, "observations": observations,
        "event_filings": event_results, "controls": controls,
        "interpretation": {
            "sample_is_purposive_not_universe_prevalence": True,
            "filing_date_is_daily_availability_proxy_not_first_public_receipt": True,
            "same_day_filings_excluded_for_no_intraday_order": True,
            "ticker_fact_is_issuer_level_not_share_class_identity": True,
            "missing_fact_means_unknown": True,
            "identity_crosswalk_admitted": False,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase332_event_identity_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "phase332_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(output_dir / "phase332_observations.csv", observations)
    write_csv(output_dir / "phase332_event_filings.csv", event_results)
    print("PHASE332_SUMMARY=" + json.dumps(summary, sort_keys=True))
    print("PHASE332_CONTROLS=" + json.dumps(controls, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path,
                        default=Path("research/phase328_collision_pair_manifest.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("phase332_output"))
    parser.add_argument("--email", default=os.environ.get("SEC_CONTACT_EMAIL", ""))
    args = parser.parse_args()
    run_audit(args.email, args.output_dir, args.manifest)


if __name__ == "__main__":
    main()
