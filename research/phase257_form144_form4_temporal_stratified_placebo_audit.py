#!/usr/bin/env python3
"""Phase 257: test sensitivity of Form 144/Form 4 lag placebos to finer time strata.

Document-linkage diagnostic only. No return, PIT or alpha inference is performed.
"""
from __future__ import annotations
import argparse
import json
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from research.phase208_form144_form4_execution_conversion_audit import form144_data, form4_blocks, sha
from research.phase209_form144_form4_exact_first_matching_audit import exact_first_match
from research.phase256_form144_form4_lag_preserving_placebo_audit import count_unique_mutable_matches_fast, summarize_counts

EXPECTED_FORM144_SHA = "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659"
EXPECTED_FORM4_SHA = "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3"
STRATA = ("issuer_owner", "issuer_owner_month", "issuer_owner_iso_week")


def temporal_group_key(block, mode):
    issuer = str(block.get("issuer") or "")
    owner = str(block.get("owner") or "")
    filing = block.get("filing")
    if not issuer or not owner:
        raise ValueError("missing issuer or reporting owner")
    if not isinstance(filing, date):
        raise ValueError("filing date must be a date")
    base = (issuer, owner)
    if mode == "issuer_owner":
        return base
    if mode == "issuer_owner_month":
        return base + ((filing.year, filing.month),)
    if mode == "issuer_owner_iso_week":
        iso = filing.isocalendar()
        return base + ((iso.year, iso.week),)
    raise ValueError(f"unsupported temporal stratum: {mode}")


def build_temporal_groups(blocks, mode):
    groups = defaultdict(list)
    for i, block in enumerate(blocks):
        groups[temporal_group_key(block, mode)].append(i)
    return dict(groups)


def mutable_indices(groups, blocks):
    """Only include groups whose lag multiset can actually change under permutation."""
    mutable = set()
    permutable_groups = 0
    for ids in groups.values():
        lags = [blocks[i].get("lag") for i in ids]
        if len(ids) > 1 and len(set(lags)) > 1:
            mutable.update(ids)
            permutable_groups += 1
    return mutable, permutable_groups


def permute_lags_in_groups(blocks, groups, rng):
    """Shuffle observed 0-4 day lags only within genuinely permutable groups."""
    for block in blocks:
        lag = block.get("lag")
        if not isinstance(lag, int) or lag < 0 or lag > 4:
            raise ValueError("Form 4 lag outside the admitted 0-4 day envelope")
        if not isinstance(block.get("filing"), date):
            raise ValueError("missing or invalid Form 4 filing date")
        if (block["filing"] - block["date"]).days != lag:
            raise ValueError("stored lag does not reconcile to filing and transaction dates")
    dates = [block["date"] for block in blocks]
    lags_out = [block["lag"] for block in blocks]
    for ids in groups.values():
        lag_values = [blocks[i]["lag"] for i in ids]
        if len(ids) <= 1 or len(set(lag_values)) <= 1:
            continue
        shuffled = lag_values.copy()
        rng.shuffle(shuffled)
        for i, lag in zip(ids, shuffled):
            lags_out[i] = lag
            dates[i] = blocks[i]["filing"] - timedelta(days=lag)
    return dates, lags_out


def summarize_group_structure(groups, blocks, mutable, permutable_groups, exact_unique):
    index = {}
    for i, block in enumerate(blocks):
        key = (block["accession"], block["date"])
        if key in index:
            raise ValueError("Form 4 accession/date block key is not unique")
        index[key] = i
    legacy_multi = {i for ids in groups.values() if len(ids) > 1 for i in ids}
    exact_ids = {index[(block["accession"], block["date"])] for _, block, _ in exact_unique}
    return {
        "groups": len(groups),
        "multi_block_groups": sum(1 for ids in groups.values() if len(ids) > 1),
        "legacy_multi_block_indices": len(legacy_multi),
        "actually_permutable_groups": permutable_groups,
        "actually_permutable_blocks": len(mutable),
        "exact_links_in_legacy_multi_block_groups": len(exact_ids & legacy_multi),
        "exact_links_in_actually_permutable_groups": len(exact_ids & mutable),
    }


def run_stratified_placebo(tranches, blocks, exact_unique, mode, reps=1000, seed=257):
    if reps < 100:
        raise ValueError("Use at least 100 permutations")
    groups = build_temporal_groups(blocks, mode)
    mutable, permutable_group_count = mutable_indices(groups, blocks)
    if not mutable:
        raise ValueError(f"no genuinely permutable groups for {mode}")
    block_index = {(block["accession"], block["date"]): i for i, block in enumerate(blocks)}
    exact_ids = {block_index[(block["accession"], block["date"])] for _, block, _ in exact_unique}
    observed = len(exact_ids & mutable)
    if observed <= 0:
        raise ValueError(f"no exact links in genuinely permutable groups for {mode}")
    owners = [block["owner"] for block in blocks]
    shares = [block["shares"] for block in blocks]
    rng = random.Random(seed)
    counts = []
    for _ in range(reps):
        dates, permuted_lags = permute_lags_in_groups(blocks, groups, rng)
        if any(lag < 0 or lag > 4 for lag in permuted_lags):
            raise AssertionError("permuted lag escaped the 0-4 day eligibility envelope")
        counts.append(count_unique_mutable_matches_fast(tranches, blocks, owners, dates, shares, mutable))
    summary = summarize_counts(counts, observed, len(mutable))
    summary.update(summarize_group_structure(groups, blocks, mutable, permutable_group_count, exact_unique))
    summary["stratification"] = mode
    summary["seed"] = seed
    summary["interpretation"] = (
        "conditional document-linkage placebo; filing dates fixed; observed filing lags "
        "permuted only within issuer-owner and the specified local time stratum; "
        "not a return-alpha p-value"
    )
    return summary


def holm_adjust(p_values):
    """Holm step-down adjustment for the small, explicitly exploratory sensitivity family."""
    items = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    m = len(items)
    adjusted = {}
    running = 0.0
    for rank, (name, p_value) in enumerate(items):
        candidate = min(1.0, (m - rank) * float(p_value))
        running = max(running, candidate)
        adjusted[name] = running
    return adjusted


def audit(form144_path, form4_path, reps=1000, seed=257):
    form144_sha = sha(form144_path)
    form4_sha = sha(form4_path)
    if form144_sha != EXPECTED_FORM144_SHA:
        raise ValueError("Unexpected immutable Form 144 input")
    if form4_sha != EXPECTED_FORM4_SHA:
        raise ValueError("Unexpected immutable Form 4 input")
    rows, originals, eligible, tranches, _ = form144_data(form144_path)
    submissions, rawtx, filing_dates, blocks, _ = form4_blocks(form4_path)
    if max(filing_dates).isoformat() != "2026-09-30":
        raise ValueError("Unexpected Form 4 snapshot end")
    linkage = exact_first_match(tranches, blocks)
    exact_unique = linkage["exact_unique"]
    fallback_unique = linkage["fallback_unique"]
    if len(exact_unique) != 521 or len(fallback_unique) != 49:
        raise ValueError("Unexpected immutable exact-first linkage graph")
    results = {}
    for offset, mode in enumerate(STRATA):
        results[mode] = run_stratified_placebo(tranches, blocks, exact_unique, mode, reps=reps, seed=seed + offset)
    raw_p = {name: result["empirical_tail_plus_one"] for name, result in results.items()}
    adjusted = holm_adjust(raw_p)
    for name, value in adjusted.items():
        results[name]["holm_adjusted_tail"] = value
    return {
        "phase": 257,
        "status": "TEMPORAL_STRATIFICATION_SENSITIVITY_DESCRIPTIVE_ONLY",
        "inputs": {
            "form144_sha256": form144_sha,
            "form144_artifact_run_id": 41959603351,
            "form144_artifact_id": 13385365595,
            "form4_inner_zip_sha256": form4_sha,
            "form4_artifact_run_id": 40606706518,
            "form4_artifact_id": 12781850078,
            "form4_snapshot_end": "2026-09-30",
        },
        "sample": {
            "form144_panel_rows": len(rows),
            "eligible_notices": len(eligible),
            "eligible_tranches": len(tranches),
            "form4_submissions": len(submissions),
            "form4_nonderivative_rows": len(rawtx),
            "form4_unique_owner_sale_blocks": len(blocks),
            "exact_date_share_links": len(exact_unique),
            "fallback_links": len(fallback_unique),
        },
        "permutations_per_stratification": reps,
        "base_seed": seed,
        "placebos": results,
        "multiple_testing": {
            "method": "Holm step-down",
            "family": list(STRATA),
            "raw_plus_one_tails": raw_p,
            "holm_adjusted_tails": adjusted,
            "scope": "exploratory sensitivity family only; not alpha inference",
        },
        "decision": {
            "document_linkage_descriptive_only": True,
            "strict_pit_admitted": False,
            "feature_admitted": False,
            "alpha_test_authorized": False,
            "return_test_run": False,
            "bootstrap_loo_oos_run": False,
            "holdout_used": False,
            "legacy_holdout": "CONSUMED_NOT_PRISTINE",
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--form144-csv", required=True)
    parser.add_argument("--form4-zip", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--permutations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=257)
    args = parser.parse_args()
    result = audit(args.form144_csv, args.form4_zip, args.permutations, args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
