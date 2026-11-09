#!/usr/bin/env python3
"""Phase 228: hash-pinned 13D/G event-lag split at actual compliance dates.

Uses Phase 213's immutable raw-submission parser. Descriptive only; no returns.
"""
from __future__ import annotations
import argparse, hashlib, json, statistics
from datetime import date
from pathlib import Path
from typing import Any

CUTOFFS = {"13D": date(2024, 2, 5), "13G": date(2024, 9, 30)}
EXPECTED = {
    "13D_pre": {"n": 162, "parsed_n": 154, "lag_median_calendar_days_weighted": 4.0},
    "13D_post": {"n": 52, "parsed_n": 51, "lag_median_calendar_days_weighted": 2.0},
    "13G_pre": {"n": 308, "parsed_n": 272, "lag_median_calendar_days_weighted": 41.0},
    "13G_post": {"n": 77, "parsed_n": 76, "lag_median_calendar_days_weighted": 38.0},
}

def weighted_quantile(values: list[float], weights: list[float], q: float) -> float | None:
    pairs = sorted((float(v), float(w)) for v, w in zip(values, weights) if v is not None and w > 0)
    if not pairs:
        return None
    threshold = min(max(float(q), 0.0), 1.0) * sum(w for _, w in pairs)
    cumulative = 0.0
    for value, weight in pairs:
        cumulative += weight
        if cumulative >= threshold:
            return value
    return pairs[-1][0]

def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    parsed = [r for r in rows if r.get("event_date")]
    total_weight = sum(float(r["sample_weight"]) for r in rows)
    parsed_weight = sum(float(r["sample_weight"]) for r in parsed)
    lags = [int(r["filing_minus_event_days"]) for r in parsed]
    weights = [float(r["sample_weight"]) for r in parsed]
    qend = [r for r in parsed if r.get("event_date_is_quarter_end") is True]
    qend_weight = sum(float(r["sample_weight"]) for r in qend)
    return {
        "n": len(rows),
        "parsed_n": len(parsed),
        "coverage_unweighted_pct": round(100 * len(parsed) / len(rows), 4) if rows else None,
        "coverage_sample_weighted_pct": round(100 * parsed_weight / total_weight, 4) if total_weight else None,
        "quarter_end_unweighted_pct_within_parsed": round(100 * len(qend) / len(parsed), 4) if parsed else None,
        "quarter_end_sample_weighted_pct_within_parsed": round(100 * qend_weight / parsed_weight, 4) if parsed_weight else None,
        "lag_median_calendar_days_unweighted": float(statistics.median(lags)) if lags else None,
        "lag_median_calendar_days_weighted": weighted_quantile(lags, weights, 0.5),
        "lag_p90_calendar_days_weighted": weighted_quantile(lags, weights, 0.9),
        "lag_over_90_days_n": sum(x > 90 for x in lags),
        "lag_over_365_days_n": sum(x > 365 for x in lags),
        "same_day_event_filing_n": sum(x == 0 for x in lags),
        "future_event_date_n": sum(x < 0 for x in lags),
    }

def run(input_dir: Path, source_zip: Path, prior_result_path: Path | None = None) -> dict[str, Any]:
    from research.phase213_13dg_legacy_event_date_recovery import ARTIFACT_SHA256, audit as audit_phase213
    zip_sha = hashlib.sha256(source_zip.read_bytes()).hexdigest()
    if zip_sha != ARTIFACT_SHA256:
        raise ValueError("phase124_source_zip_sha256_mismatch")
    rows, p213 = audit_phase213(input_dir)
    if (p213["integrity"]["raw_file_sha256_verified"], p213["integrity"]["sec_header_accession_acceptance_filing_date_verified"], p213["integrity"]["primary_13dg_documents_found"]) != (600, 600, 599):
        raise ValueError("phase213_source_integrity_counts_mismatch")
    result = {}
    cohorts = {}
    for family, cutoff in CUTOFFS.items():
        family_rows = [r for r in rows if r["family"] == family]
        pre = [r for r in family_rows if date.fromisoformat(r["filing_date"]) < cutoff]
        post = [r for r in family_rows if date.fromisoformat(r["filing_date"]) >= cutoff]
        result[f"{family}_pre"] = summarize(pre)
        result[f"{family}_post"] = summarize(post)
        for era, group in (("pre", pre), ("post", post)):
            for cohort, is_amendment in (("initial", False), ("amendment", True)):
                cohorts[f"{family}_{era}_{cohort}"] = summarize([r for r in group if bool(r["index_form_suffix_is_amendment"]) == is_amendment])
    for key, expected in EXPECTED.items():
        for metric, value in expected.items():
            actual = result[key][metric]
            if actual != value:
                raise ValueError(f"expected_count_or_metric_mismatch:{key}:{metric}:{actual}!={value}")
    if prior_result_path is None:
        prior_result_path = Path(__file__).with_name("phase225_13dg_event_semantics_lag_audit_result.json")
    prior = None
    if prior_result_path and prior_result_path.exists():
        prior = json.loads(prior_result_path.read_text(encoding="utf-8"))
    prior_omits_regime_split = bool(prior is not None and not any(k in prior for k in ("regulatory_era_descriptive", "regulatory_era_descriptives", "reform_era_descriptives")))
    return {
        "phase": 228,
        "status": "PASS_HASH_PINNED_REGULATORY_ERA_RECONSTRUCTION_DESCRIPTIVE_ONLY",
        "source": {
            "phase124_run_id": 42073725379,
            "phase124_artifact_id": 13436764625,
            "artifact_zip_sha256": zip_sha,
            "csv_sha256": p213["source"]["csv_sha256_verified"],
            "sampling_frame": "43 quarters, 2016Q1-2026Q3; stratified quarter x form-family x amendment sample",
            "source_rows": 600,
            "actual_filings": 599,
            "index_aliases_quarantined": 1,
            "raw_hashes_verified": p213["integrity"]["raw_file_sha256_verified"],
            "headers_verified": p213["integrity"]["sec_header_accession_acceptance_filing_date_verified"],
            "primary_documents_verified": p213["integrity"]["primary_13dg_documents_found"],
            "xml_event_dates_verified": p213["integrity"]["structured_xml_event_dates_exact_to_phase124"],
            "sample_design_warning": "Stratified descriptive sample, not an unstratified random sample; no causal inference or population-prevalence claim.",
        },
        "compliance_cutoffs": {
            "13D": {"date": "2024-02-05", "basis": "Revised 13D deadlines effective; initial filing five business days, amendments two business days."},
            "13G": {"date": "2024-09-30", "basis": "Compliance date for revised 13G filing deadlines; not the general February 2024 effective date."},
            "structured_data": {"date": "2024-12-18", "basis": "Separate structured-data compliance date; affects document format/field coverage, not the filing knowledge clock."},
        },
        "by_family_and_regulatory_era": result,
        "by_family_era_and_index_amendment_cohort": cohorts,
        "prior_phase225_result_missing_regime_split": prior_omits_regime_split,
        "interpretation": {
            "13D": "Weighted median event-to-filing lag falls from 4 to 2 calendar days overall. Initial filings remain a small post-reform cohort; the post-reform initial weighted P90 is dominated by a long-lag observation and should not be summarized by the median alone. Amendments move from 3 to 2 days weighted median, directionally consistent with the two-business-day rule but not a compliance test.",
            "13G": "Weighted median changes from 41 to 38 calendar days and weighted P90 remains 45 days. Quarter-end concentration remains high and rises from about 74.8% to 81.7% weighted. This is consistent with quarter-end reporting mechanics, not transaction-level flow.",
            "event_date": "Declared event date is not a verified trade timestamp or public-knowledge timestamp. SEC acceptance datetime remains the knowledge clock; no same-day feature use.",
        },
        "controls": {
            "forward_returns_used": False,
            "alpha_test": False,
            "bootstrap_loo": False,
            "holdout_used": False,
            "production_changed": False,
            "f80_changed": False,
            "ownership_rows_summed": False,
        },
    }

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", type=Path, required=True)
    p.add_argument("--source-zip", type=Path, required=True)
    p.add_argument("--prior-result", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    r = run(a.input_dir, a.source_zip, a.prior_result)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(r, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
