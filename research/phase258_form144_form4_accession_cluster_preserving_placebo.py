#!/usr/bin/env python3
"""Phase 258: accession-cluster-preserving Form 144/Form 4 linkage placebo.

The null freezes multi-date accessions rather than splitting their filing clusters.
"""
from __future__ import annotations
import argparse, json, random, zipfile
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from research.phase208_form144_form4_execution_conversion_audit import cik, form144_data, form4_blocks, sha, tsv
from research.phase209_form144_form4_exact_first_matching_audit import exact_first_match
from research.phase256_form144_form4_lag_preserving_placebo_audit import count_unique_mutable_matches_fast, summarize_counts

EXPECTED_FORM144_SHA = "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659"
EXPECTED_FORM4_SHA = "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3"
STRATA = ("issuer_owner_cik", "issuer_owner_cik_month", "issuer_owner_cik_iso_week")


def owner_cik_by_accession(form4_path):
    by_accession = defaultdict(dict)
    with zipfile.ZipFile(form4_path) as archive:
        for row in tsv(archive, "REPORTINGOWNER.tsv"):
            accession = (row.get("ACCESSION_NUMBER") or "").strip()
            owner_cik = cik(row.get("RPTOWNERCIK", ""))
            if accession and owner_cik:
                by_accession[accession][owner_cik] = row.get("RPTOWNERNAME", "")
    unique = {a: next(iter(v)) for a, v in by_accession.items() if len(v) == 1}
    ambiguous = {a: sorted(v) for a, v in by_accession.items() if len(v) > 1}
    return unique, ambiguous


def attach_owner_ciks(blocks, owner_map):
    for block in blocks:
        owner_cik = owner_map.get(block.get("accession"))
        if not owner_cik:
            raise ValueError("sale block lacks one unique reporting-owner CIK")
        block["owner_cik"] = owner_cik
    return blocks


def build_accession_clusters(blocks):
    by_accession = defaultdict(list)
    for index, block in enumerate(blocks):
        accession = block.get("accession")
        if not accession:
            raise ValueError("missing Form 4 accession")
        by_accession[accession].append(index)
    for indices in by_accession.values():
        identity = {(blocks[i].get("issuer"), blocks[i].get("owner_cik"), blocks[i].get("filing")) for i in indices}
        if len(identity) != 1:
            raise ValueError("one accession spans multiple issuer/owner/filing identities")
    single = {v[0] for v in by_accession.values() if len(v) == 1}
    multi = {i for v in by_accession.values() if len(v) > 1 for i in v}
    return dict(by_accession), single, multi


def temporal_group_key(block, mode):
    issuer, owner_cik, filing = str(block.get("issuer") or ""), str(block.get("owner_cik") or ""), block.get("filing")
    if not issuer or not owner_cik:
        raise ValueError("missing issuer or permanent reporting-owner CIK")
    if not isinstance(filing, date):
        raise ValueError("filing date must be a date")
    base = (issuer, owner_cik)
    if mode == "issuer_owner_cik":
        return base
    if mode == "issuer_owner_cik_month":
        return base + ((filing.year, filing.month),)
    if mode == "issuer_owner_cik_iso_week":
        iso = filing.isocalendar()
        return base + ((iso.year, iso.week),)
    raise ValueError("unsupported temporal stratum: " + str(mode))


def build_single_accession_groups(blocks, single_indices, mode):
    groups = defaultdict(list)
    for index in sorted(single_indices):
        groups[temporal_group_key(blocks[index], mode)].append(index)
    return dict(groups)


def mutable_indices(groups, blocks):
    mutable, count = set(), 0
    for indices in groups.values():
        lags = [blocks[i].get("lag") for i in indices]
        if len(indices) > 1 and len(set(lags)) > 1:
            mutable.update(indices)
            count += 1
    return mutable, count


def permute_single_accession_lags(blocks, groups, single_indices, rng):
    for block in blocks:
        lag = block.get("lag")
        if not isinstance(lag, int) or lag < 0 or lag > 4:
            raise ValueError("Form 4 lag outside the admitted 0-4 calendar-day envelope")
        if not isinstance(block.get("filing"), date):
            raise ValueError("missing or invalid Form 4 filing date")
    dates = [b["date"] for b in blocks]
    lags_out = [b["lag"] for b in blocks]
    for indices in groups.values():
        if any(i not in single_indices for i in indices):
            raise ValueError("multi-block accession entered a permutation group")
        if len(indices) <= 1:
            continue
        values = [blocks[i]["lag"] for i in indices]
        if len(set(values)) <= 1:
            continue
        shuffled = values.copy()
        rng.shuffle(shuffled)
        for index, lag in zip(indices, shuffled):
            lags_out[index] = lag
            dates[index] = blocks[index]["filing"] - timedelta(days=lag)
    return dates, lags_out


def summarize_identity(blocks):
    issuer_name_to_ciks, owner_cik_to_names = defaultdict(set), defaultdict(set)
    for b in blocks:
        issuer_name_to_ciks[(b["issuer"], b["owner"])].add(b["owner_cik"])
        owner_cik_to_names[b["owner_cik"]].add(b["owner"])
    return {
        "issuer_normalized_names_mapped_to_multiple_ciks": sum(len(v) > 1 for v in issuer_name_to_ciks.values()),
        "owner_ciks_with_multiple_normalized_names": sum(len(v) > 1 for v in owner_cik_to_names.values()),
        "distinct_reporting_owner_ciks": len(owner_cik_to_names),
        "distinct_issuer_owner_cik_groups": len({(b["issuer"], b["owner_cik"]) for b in blocks}),
        "matching_still_uses_exact_normalized_owner_name": True,
        "permutation_grouping_uses_reporting_owner_cik": True,
    }


def holm_adjust(p_values):
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    adjusted, running, count = {}, 0.0, len(ordered)
    for rank, (label, p_value) in enumerate(ordered):
        running = max(running, min(1.0, (count - rank) * float(p_value)))
        adjusted[label] = running
    return adjusted


def run_placebo(tranches, blocks, exact_ids, by_accession, single_indices, mode, reps=1000, seed=258):
    groups = build_single_accession_groups(blocks, single_indices, mode)
    mutable, permutable_groups = mutable_indices(groups, blocks)
    observed = len(exact_ids & mutable)
    base = {
        "stratification": mode, "groups": len(groups), "permutable_groups": permutable_groups,
        "single_accession_blocks": len(single_indices),
        "multi_accession_blocks_frozen": sum(len(v) for v in by_accession.values() if len(v) > 1),
        "mutable_single_accession_blocks": len(mutable), "observed_mutable_exact_links": observed,
        "seed": seed,
        "interpretation": "conditional document-linkage placebo; filing dates fixed; one lag per single-block accession permuted within issuer x reporting-owner CIK and local time stratum; multi-block accessions frozen; not a return-alpha p-value",
    }
    if not mutable:
        return {**base, "status": "INSUFFICIENT_PERMUTABLE_SINGLE_BLOCK_ACCESSIONS", "replicates": 0,
                "null_mean": None, "null_median": None, "null_p95": None, "null_max": None,
                "null_replicates_at_or_above_observed": None, "empirical_tail_plus_one": None,
                "zero_exceedance_one_sided_95pct_upper": None}
    owners, shares, counts = [b["owner"] for b in blocks], [b["shares"] for b in blocks], []
    rng = random.Random(seed)
    for _ in range(reps):
        dates, lags = permute_single_accession_lags(blocks, groups, single_indices, rng)
        if any(x < 0 or x > 4 for x in lags):
            raise AssertionError("permuted lag escaped the original eligibility envelope")
        counts.append(count_unique_mutable_matches_fast(tranches, blocks, owners, dates, shares, mutable))
    return {**base, **summarize_counts(counts, observed, len(mutable)), "status": "COMPLETED"}


def audit(form144_path, form4_path, reps=1000, seed=258):
    h144, h4 = sha(form144_path), sha(form4_path)
    if h144 != EXPECTED_FORM144_SHA or h4 != EXPECTED_FORM4_SHA:
        raise ValueError("Unexpected immutable input SHA-256")
    rows, originals, eligible, tranches, _ = form144_data(form144_path)
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
    results = {}
    for offset, mode in enumerate(STRATA):
        results[mode] = run_placebo(tranches, blocks, exact_ids, by_accession, single, mode, reps, seed + offset)
    raw_p = {k: v["empirical_tail_plus_one"] for k, v in results.items() if v["empirical_tail_plus_one"] is not None}
    adjusted = holm_adjust(raw_p)
    for k, v in results.items():
        v["holm_adjusted_tail"] = adjusted.get(k)
    return {
        "phase": 258, "status": "ACCESSION_CLUSTER_PRESERVING_DOCUMENT_LINKAGE_SENSITIVITY_ONLY",
        "inputs": {"form144_sha256": h144, "form144_artifact_run_id": 41959603351, "form144_artifact_id": 13385365595,
                   "form4_inner_zip_sha256": h4, "form4_artifact_run_id": 40606706518, "form4_artifact_id": 12781850078,
                   "form4_snapshot_end": "2026-09-30"},
        "sample": {"form144_panel_rows": len(rows), "eligible_notices": len(eligible), "eligible_tranches": len(tranches),
                   "form4_submissions": len(submissions), "form4_nonderivative_rows": len(rawtx),
                   "form4_unique_owner_sale_blocks": len(blocks), "unique_form4_accessions_with_selected_sale_blocks": len(by_accession),
                   "single_block_accessions": len(single), "multi_block_accessions": len(by_accession)-len(single),
                   "blocks_in_multi_block_accessions_frozen": len(multi), "exact_date_share_links": len(exact_unique),
                   "fallback_links": len(fallback_unique), "exact_links_in_single_block_accessions": exact_single,
                   "exact_links_in_multi_block_accessions_frozen": exact_multi},
        "owner_identity_audit": identity, "permutations_per_stratification": reps, "base_seed": seed,
        "placebos": results,
        "multiple_testing": {"method": "Holm step-down", "family": list(raw_p), "raw_plus_one_tails": raw_p,
                             "holm_adjusted_tails": adjusted, "scope": "exploratory linkage-placebo sensitivity only; not alpha inference"},
        "decision": {"document_linkage_descriptive_only": True, "strict_pit_admitted": False, "feature_admitted": False,
                     "alpha_test_authorized": False, "return_test_run": False, "bootstrap_loo_oos_run": False,
                     "holdout_used": False, "legacy_holdout": "CONSUMED_NOT_PRISTINE", "f80_frozen": True,
                     "production_changed": False, "universe_changed": False, "capital_changed": False},
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--form144-csv", required=True)
    p.add_argument("--form4-zip", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--permutations", type=int, default=1000)
    p.add_argument("--seed", type=int, default=258)
    a = p.parse_args()
    result = audit(a.form144_csv, a.form4_zip, a.permutations, a.seed)
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
