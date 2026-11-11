#!/usr/bin/env python3
"""Phase 260: XNYS-session-valid, accession-preserving Form 144/Form 4 linkage placebo."""
from __future__ import annotations
import argparse
import json
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import exchange_calendars as xc
import pandas as pd

from research.phase208_form144_form4_execution_conversion_audit import (
    form144_data, form4_blocks, sha,
)
from research.phase209_form144_form4_exact_first_matching_audit import exact_first_match
from research.phase256_form144_form4_lag_preserving_placebo_audit import (
    count_unique_mutable_matches_fast, summarize_counts,
)
from research.phase258_form144_form4_accession_cluster_preserving_placebo import (
    EXPECTED_FORM144_SHA, EXPECTED_FORM4_SHA, attach_owner_ciks,
    build_accession_clusters, holm_adjust, owner_cik_by_accession, summarize_identity,
)

STRATA = (
    "issuer_owner_cik_weekday",
    "issuer_owner_cik_month_weekday",
    "issuer_owner_cik_iso_week_weekday",
)


def valid_xnys_lags(filing: date, calendar) -> tuple[int, ...]:
    """0–4 calendar-day lags that reconstruct to an actual XNYS session."""
    if not isinstance(filing, date):
        raise ValueError("filing date must be a date")
    return tuple(
        lag for lag in range(5)
        if calendar.is_session(pd.Timestamp(filing - timedelta(days=lag)))
    )


def session_group_key(block, mode, valid_lags):
    issuer = str(block.get("issuer") or "")
    owner_cik = str(block.get("owner_cik") or "")
    filing = block.get("filing")
    if not issuer or not owner_cik:
        raise ValueError("missing issuer or permanent reporting-owner CIK")
    if not isinstance(filing, date):
        raise ValueError("filing date must be a date")
    if not valid_lags:
        raise ValueError("empty XNYS candidate-lag signature")
    base = (issuer, owner_cik)
    weekday_signature = (filing.weekday(), tuple(valid_lags))
    if mode == "issuer_owner_cik_weekday":
        return base + weekday_signature
    if mode == "issuer_owner_cik_month_weekday":
        return base + ((filing.year, filing.month),) + weekday_signature
    if mode == "issuer_owner_cik_iso_week_weekday":
        iso = filing.isocalendar()
        return base + ((iso.year, iso.week),) + weekday_signature
    raise ValueError("unsupported temporal stratum: " + str(mode))


def build_session_groups(blocks, single_indices, mode, calendar):
    """Group only single-block accessions whose observed transaction date is XNYS."""
    groups = defaultdict(list)
    valid_by_index = {}
    eligible, frozen_non_session = set(), set()
    for index in sorted(single_indices):
        block = blocks[index]
        lag = block.get("lag")
        if not isinstance(lag, int) or lag < 0 or lag > 4:
            raise ValueError("Form 4 lag outside the admitted 0–4 calendar-day envelope")
        filing = block.get("filing")
        tx_date = block.get("date")
        if not isinstance(filing, date) or not isinstance(tx_date, date):
            raise ValueError("Form 4 filing/transaction date is invalid")
        candidates = valid_xnys_lags(filing, calendar)
        observed_is_session = calendar.is_session(pd.Timestamp(tx_date))
        if not observed_is_session or lag not in candidates:
            frozen_non_session.add(index)
            continue
        eligible.add(index)
        valid_by_index[index] = candidates
        groups[session_group_key(block, mode, candidates)].append(index)
    return dict(groups), eligible, frozen_non_session, valid_by_index


def mutable_indices(groups, blocks):
    mutable, mutable_groups = set(), 0
    for indices in groups.values():
        lags = [blocks[i]["lag"] for i in indices]
        if len(indices) > 1 and len(set(lags)) > 1:
            mutable.update(indices)
            mutable_groups += 1
    return mutable, mutable_groups


def permute_session_lags(blocks, groups, eligible, valid_by_index, calendar, rng):
    dates = [b["date"] for b in blocks]
    lags_out = [b["lag"] for b in blocks]
    for indices in groups.values():
        if any(i not in eligible for i in indices):
            raise ValueError("non-session or multi-block accession entered a permutation group")
        values = [blocks[i]["lag"] for i in indices]
        if len(indices) <= 1 or len(set(values)) <= 1:
            continue
        shuffled = values.copy()
        rng.shuffle(shuffled)
        for index, lag in zip(indices, shuffled):
            candidate = blocks[index]["filing"] - timedelta(days=lag)
            if lag not in valid_by_index[index]:
                raise AssertionError("permuted lag escaped its XNYS candidate signature")
            if not calendar.is_session(pd.Timestamp(candidate)):
                raise AssertionError("permutation created a non-XNYS transaction date")
            dates[index] = candidate
            lags_out[index] = lag
    return dates, lags_out


def run_placebo(tranches, blocks, exact_ids, by_accession, single_indices, multi_indices,
                mode, calendar, reps=1000, seed=260):
    groups, eligible, frozen_non_session, valid_by_index = build_session_groups(
        blocks, single_indices, mode, calendar
    )
    mutable, mutable_groups = mutable_indices(groups, blocks)
    observed = len(exact_ids & mutable)
    base = {
        "stratification": mode,
        "groups": len(groups),
        "permutable_groups": mutable_groups,
        "single_block_accessions": len(single_indices),
        "session_eligible_single_block_accessions": len(eligible),
        "single_block_non_session_frozen": len(frozen_non_session),
        "multi_block_accessions_frozen": len(by_accession) - len(single_indices),
        "multi_accession_blocks_frozen": len(multi_indices),
        "mutable_session_accessions": len(mutable),
        "observed_mutable_exact_links": observed,
        "seed": seed,
        "interpretation": (
            "conditional document-linkage placebo; filing dates fixed; only single-block "
            "accessions with observed XNYS transaction dates are permuted; groups share "
            "issuer, permanent owner CIK, filing weekday and identical valid 0–4-day "
            "XNYS candidate-lag signatures; multi-block and non-session records are frozen; "
            "not a return-alpha p-value"
        ),
    }
    if not mutable:
        return {
            **base, "status": "INSUFFICIENT_MUTABLE_XNYS_SINGLE_BLOCK_ACCESSIONS",
            "replicates": 0, "null_mean": None, "null_median": None, "null_p95": None,
            "null_max": None, "null_replicates_at_or_above_observed": None,
            "empirical_tail_plus_one": None, "zero_exceedance_one_sided_95pct_upper": None,
        }
    owners = [b["owner"] for b in blocks]
    shares = [b["shares"] for b in blocks]
    rng = random.Random(seed)
    counts = []
    for _ in range(reps):
        dates, lags = permute_session_lags(
            blocks, groups, eligible, valid_by_index, calendar, rng
        )
        if any(lags[i] not in valid_by_index[i] for i in eligible):
            raise AssertionError("permuted lag signature changed")
        counts.append(
            count_unique_mutable_matches_fast(
                tranches, blocks, owners, dates, shares, mutable
            )
        )
    return {**base, **summarize_counts(counts, observed, len(mutable)), "status": "COMPLETED"}


def audit(form144_path, form4_path, reps=1000, seed=260):
    h144, h4 = sha(form144_path), sha(form4_path)
    if h144 != EXPECTED_FORM144_SHA or h4 != EXPECTED_FORM4_SHA:
        raise ValueError("Unexpected immutable input SHA-256")
    rows, originals, eligible_notices, tranches, _ = form144_data(form144_path)
    submissions, rawtx, filing_dates, blocks, _ = form4_blocks(form4_path)
    if max(filing_dates).isoformat() != "2026-09-30":
        raise ValueError("Unexpected Form 4 snapshot end")
    owner_map, ambiguous = owner_cik_by_accession(form4_path)
    attach_owner_ciks(blocks, owner_map)
    if {b["accession"] for b in blocks} & set(ambiguous):
        raise ValueError("selected sale block has multiple reporting-owner CIKs")
    by_accession, single, multi = build_accession_clusters(blocks)
    identity = summarize_identity(blocks)
    if identity["issuer_normalized_names_mapped_to_multiple_ciks"] or identity["owner_ciks_with_multiple_normalized_names"]:
        raise ValueError("owner-name/CIK identity is ambiguous in this immutable sample")
    linkage = exact_first_match(tranches, blocks)
    exact_unique, fallback_unique = linkage["exact_unique"], linkage["fallback_unique"]
    if len(blocks) != 10525 or len(by_accession) != 8897 or len(single) != 7512 or len(multi) != 3013:
        raise ValueError("Unexpected immutable Form 4 accession/block structure")
    if len(exact_unique) != 521 or len(fallback_unique) != 49:
        raise ValueError("Unexpected immutable exact-first linkage graph")
    block_index = {(b["accession"], b["date"]): i for i, b in enumerate(blocks)}
    exact_ids = {block_index[(b["accession"], b["date"])] for _, b, _ in exact_unique}
    exact_single, exact_multi = len(exact_ids & single), len(exact_ids & multi)
    if (exact_single, exact_multi) != (414, 107):
        raise ValueError("Unexpected exact-link single-/multi-block accession split")

    calendar = xc.get_calendar("XNYS")
    results = {}
    for offset, mode in enumerate(STRATA):
        results[mode] = run_placebo(
            tranches, blocks, exact_ids, by_accession, single, multi,
            mode, calendar, reps, seed + offset
        )
    raw_p = {
        key: value["empirical_tail_plus_one"]
        for key, value in results.items()
        if value["empirical_tail_plus_one"] is not None
    }
    adjusted = holm_adjust(raw_p)
    for key, value in results.items():
        value["holm_adjusted_tail"] = adjusted.get(key)

    session_groups, session_eligible, non_session_frozen, valid = build_session_groups(
        blocks, single, STRATA[0], calendar
    )
    return {
        "phase": 260,
        "status": "XNYS_SESSION_VALID_ACCESSION_CLUSTER_PRESERVING_PLACEBO",
        "inputs": {
            "form144_sha256": h144, "form144_artifact_run_id": 41959603351,
            "form144_artifact_id": 13385365595, "form4_inner_zip_sha256": h4,
            "form4_artifact_run_id": 40606706518, "form4_artifact_id": 12781850078,
            "form4_snapshot_end": "2026-09-30",
        },
        "calendar": {
            "name": "XNYS",
            "library": "exchange_calendars",
            "library_version": xc.__version__,
            "valid_lag_window_calendar_days": [0, 4],
            "filing_weekday_and_candidate_signature_preserved": True,
        },
        "sample": {
            "form144_panel_rows": len(rows), "eligible_original_notices": len(eligible_notices),
            "eligible_proposed_sale_tranches": len(tranches), "form4_submissions": len(submissions),
            "form4_nonderivative_rows": len(rawtx), "form4_sale_blocks": len(blocks),
            "unique_form4_accessions": len(by_accession), "single_block_accessions": len(single),
            "multi_block_accessions": len(by_accession) - len(single),
            "multi_block_sale_blocks_frozen": len(multi), "exact_date_share_links": len(exact_unique),
            "exact_links_in_single_block_accessions": exact_single,
            "exact_links_in_multi_block_accessions_frozen": exact_multi,
            "fallback_links_separate": len(fallback_unique),
            "session_eligible_single_block_accessions": len(session_eligible),
            "single_block_non_session_accessions_frozen": len(non_session_frozen),
        },
        "owner_identity_audit": identity,
        "permutations_per_stratification": reps,
        "base_seed": seed,
        "placebos": results,
        "multiple_testing": {
            "method": "Holm step-down", "family": list(raw_p),
            "raw_plus_one_tails": raw_p, "holm_adjusted_tails": adjusted,
            "scope": "exploratory document-linkage placebo sensitivity only; not alpha inference",
        },
        "decision": {
            "document_linkage_descriptive_only": True,
            "strict_pit_admitted": False, "feature_admitted": False,
            "alpha_test_authorized": False, "return_test_run": False,
            "bootstrap_loo_oos_run": False, "holdout_used": False,
            "legacy_holdout": "CONSUMED_NOT_PRISTINE", "f80_frozen": True,
            "production_changed": False, "universe_changed": False, "capital_changed": False,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--form144-csv", required=True)
    parser.add_argument("--form4-zip", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--permutations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=260)
    args = parser.parse_args()
    result = audit(args.form144_csv, args.form4_zip, args.permutations, args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
