#!/usr/bin/env python3
"""Phase 229: assign 13D/G regulatory cohorts by event-date proxy and compare filing-date splits."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from phase213_13dg_legacy_event_date_recovery import (
    ARTIFACT_SHA256,
    audit as audit_phase213,
)

CUTOFFS = {"13D": date(2024, 2, 5), "13G": date(2024, 9, 30)}
EXPECTED_CROSSING = {
    "accession": "0001554855-24-000055",
    "family": "13D",
    "event_date": "2024-01-31",
    "filing_date": "2024-02-08",
}


def weighted_quantile(values: list[float], weights: list[float], q: float) -> float | None:
    pairs = sorted((float(v), float(w)) for v, w in zip(values, weights) if w > 0)
    if not pairs:
        return None
    threshold = min(max(float(q), 0.0), 1.0) * sum(w for _, w in pairs)
    cumulative = 0.0
    for value, weight in pairs:
        cumulative += weight
        if cumulative >= threshold:
            return value
    return pairs[-1][0]


def assign_regimes(family: str, filing_date: date, event_date: date | None) -> tuple[str, str]:
    if family not in CUTOFFS:
        raise ValueError(f"Unsupported family: {family}")
    cutoff = CUTOFFS[family]
    filing_regime = "pre" if filing_date < cutoff else "post"
    event_regime = "unknown" if event_date is None else ("pre" if event_date < cutoff else "post")
    return filing_regime, event_regime


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0, "weight_sum": 0.0, "weighted_median_lag_days": None,
                "weighted_p90_lag_days": None, "weighted_quarter_end_pct": None}
    lags = [float(r["filing_minus_event_days"]) for r in rows]
    weights = [float(r["sample_weight"]) for r in rows]
    total_weight = sum(weights)
    qend_weight = sum(w for r, w in zip(rows, weights) if r["event_date_is_quarter_end"] is True)
    return {
        "n": len(rows),
        "weight_sum": round(total_weight, 6),
        "weighted_median_lag_days": weighted_quantile(lags, weights, 0.50),
        "weighted_p90_lag_days": weighted_quantile(lags, weights, 0.90),
        "weighted_quarter_end_pct": round(100.0 * qend_weight / total_weight, 4) if total_weight else None,
    }


def audit(input_dir: Path, zip_path: Path | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    zip_sha = None
    if zip_path is not None:
        zip_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
        if zip_sha != ARTIFACT_SHA256:
            raise ValueError(f"Phase 124 ZIP SHA-256 mismatch: {zip_sha}")

    rows, phase213_summary = audit_phase213(input_dir)
    actual = [r for r in rows if r["family"] in {"13D", "13G"}]
    if len(actual) != 599:
        raise ValueError(f"Expected 599 actual 13D/G rows, got {len(actual)}")
    parsed_n = sum(bool(r["event_date"]) for r in actual)
    if parsed_n != 553:
        raise ValueError(f"Expected 553 parsed event dates, got {parsed_n}")

    classified: list[dict[str, Any]] = []
    crossings: list[dict[str, Any]] = []
    for source in actual:
        filing = date.fromisoformat(source["filing_date"])
        event = date.fromisoformat(source["event_date"]) if source["event_date"] else None
        filing_regime, event_regime = assign_regimes(source["family"], filing, event)
        row = dict(source)
        row["filing_regime"] = filing_regime
        row["event_date_proxy_regime"] = event_regime
        row["regime_assignment_crosses_cutoff"] = bool(event is not None and filing_regime != event_regime)
        classified.append(row)
        if row["regime_assignment_crosses_cutoff"]:
            crossings.append({
                "accession": row["accession"], "family": row["family"],
                "index_amendment": bool(row["index_form_suffix_is_amendment"]),
                "event_date": row["event_date"], "filing_date": row["filing_date"],
                "filing_regime": filing_regime, "event_date_proxy_regime": event_regime,
                "acceptance_datetime_header_wall_clock": row["acceptance_datetime_header_wall_clock"],
                "filing_minus_event_days": row["filing_minus_event_days"],
            })

    if len(crossings) != 1 or any(crossings[0][k] != v for k, v in EXPECTED_CROSSING.items()):
        raise ValueError(f"Unexpected regime-boundary crossing set: {crossings}")

    by_basis: dict[str, Any] = {}
    for basis, field in (("filing_date", "filing_regime"),
                         ("event_date_proxy", "event_date_proxy_regime")):
        by_basis[basis] = {}
        for family in ("13D", "13G"):
            by_basis[basis][family] = {}
            for cohort, amendment in (("initial", False), ("amendment", True)):
                by_basis[basis][family][cohort] = {}
                for regime in ("pre", "post"):
                    subset = [
                        r for r in classified
                        if r["family"] == family
                        and bool(r["index_form_suffix_is_amendment"]) == amendment
                        and bool(r["event_date"])
                        and r[field] == regime
                    ]
                    by_basis[basis][family][cohort][regime] = summarize(subset)

    classification_counts: dict[str, Any] = {}
    for family in ("13D", "13G"):
        group = [r for r in classified if r["family"] == family]
        classification_counts[family] = {
            basis: {
                regime: sum(r[field] == regime for r in group)
                for regime in ("pre", "post", "unknown")
            }
            for basis, field in (("filing_date", "filing_regime"),
                                 ("event_date_proxy", "event_date_proxy_regime"))
        }

    family_summary: dict[str, Any] = {}
    for family in ("13D", "13G"):
        family_summary[family] = {}
        for basis, field in (("filing_date", "filing_regime"),
                             ("event_date_proxy", "event_date_proxy_regime")):
            family_summary[family][basis] = {
                regime: summarize([
                    r for r in classified
                    if r["family"] == family and r[field] == regime and bool(r["event_date"])
                ])
                for regime in ("pre", "post")
            }

    if classification_counts["13D"]["filing_date"]["pre"] != 162:
        raise ValueError("Unexpected 13D filing-date pre cohort size")
    if classification_counts["13D"]["event_date_proxy"]["pre"] != 155:
        raise ValueError("Unexpected 13D event-date-proxy pre parsed cohort size")
    if classification_counts["13D"]["event_date_proxy"]["post"] != 50:
        raise ValueError("Unexpected 13D event-date-proxy post parsed cohort size")
    if classification_counts["13G"]["filing_date"] != classification_counts["13G"]["event_date_proxy"]:
        raise ValueError("Unexpected 13G cutoff crossing")

    summary = {
        "phase": 229,
        "status": "COMPLETED_EVENT_DATE_PROXY_REGIME_ASSIGNMENT_AUDIT_NO_ALPHA",
        "source": {
            "phase124_run_id": 42073725379,
            "phase124_artifact_id": 13436764625,
            "zip_sha256_verified": zip_sha,
            "phase213_source_integrity": phase213_summary["integrity"],
            "actual_filings": len(actual),
            "parsed_event_dates": parsed_n,
            "unknown_event_dates": len(actual) - parsed_n,
        },
        "cutoffs": {k: v.isoformat() for k, v in CUTOFFS.items()},
        "assignment_rule": "Event-date proxy is used for descriptive trigger-regime assignment; SEC acceptance datetime remains the public-knowledge clock. Filing-date assignment is retained as a comparison.",
        "classification_counts": classification_counts,
        "family_level_weighted_lag_summaries": family_summary,
        "initial_amendment_weighted_lag_summaries": by_basis,
        "boundary_crossings": crossings,
        "limitations": [
            "The cover-page/XML event date is not a verified trade date and is only the best available proxy for the event that requires filing.",
            "13G deadlines differ by filer category and rule trigger; this audit does not infer one universal 13G deadline or test compliance.",
            "Pre-reform 13D amendments were subject to the qualitative promptly standard, so no fixed numeric pre-reform amendment deadline is inferred.",
            "The 46 unparsed event dates remain unknown and are not assigned to either event-date regime.",
            "The Phase 124 sample is stratified and weighted; all summaries are descriptive, not causal or population-wide estimates.",
            "The 2024-12-18 structured-data mandate is a separate format break, not a deadline-regime or knowledge-time change.",
        ],
        "governance": {
            "forward_returns_used": False,
            "alpha_test_performed": False,
            "bootstrap_or_loo_performed": False,
            "holdout_used": False,
            "production_changed": False,
            "universe_changed": False,
            "f80_changed": False,
            "f80_status": "FROZEN",
            "legacy_holdout_status": "CONSUMED_NOT_PRISTINE",
        },
    }
    return classified, summary


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "phase229_13dg_event_regime_assignment_rows.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "phase229_13dg_event_regime_assignment_audit_result.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--zip-path", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rows, summary = audit(args.input_dir, args.zip_path)
    write_outputs(rows, summary, args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
