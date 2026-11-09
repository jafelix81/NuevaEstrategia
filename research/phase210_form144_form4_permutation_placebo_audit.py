#!/usr/bin/env python3
"""Phase 210: conditional permutation placebos and price concordance for Form 144/Form 4."""
import argparse
import csv
import io
import json
import random
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from research.phase208_form144_form4_execution_conversion_audit import (
    form144_data, form4_blocks, sha, tsv, cik, name, secdate, dec, flag,
)
from research.phase209_form144_form4_exact_first_matching_audit import exact_first_match

EXPECTED_FORM144_SHA = "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659"
EXPECTED_FORM4_SHA = "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3"


def quantile_linear(values, q):
    xs = sorted(values)
    if not xs:
        return None
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def statistics_median(values):
    xs = sorted(values)
    n = len(xs)
    if n % 2:
        return xs[n // 2]
    return (xs[n // 2 - 1] + xs[n // 2]) / 2


def count_unique_mutable_matches(tranches, blocks, owners, dates, shares, mutable_block_ids):
    index = defaultdict(list)
    for bi, block in enumerate(blocks):
        index[(block["issuer"], owners[bi], dates[bi], shares[bi])].append(bi)
    edges = []
    for tranche in tranches:
        tkey = (tranche["accession"], tranche["idx"])
        key = (tranche["issuer"], tranche["seller"], tranche["date"], tranche["units"])
        for bi in index.get(key, []):
            edges.append((tkey, bi))
    td = Counter(tkey for tkey, _ in edges)
    bd = Counter(bi for _, bi in edges)
    return sum(1 for tkey, bi in edges if td[tkey] == 1 and bd[bi] == 1 and bi in mutable_block_ids)


def permutation_summary(counts, observed, mutable_blocks):
    ge = sum(value >= observed for value in counts)
    mean = sum(counts) / len(counts)
    return {
        "observed_mutable_exact_links": observed,
        "mutable_form4_blocks": mutable_blocks,
        "null_mean": round(mean, 6),
        "null_median": statistics_median(counts),
        "null_p95": round(quantile_linear(counts, 0.95), 6),
        "null_max": max(counts),
        "null_replicates_at_or_above_observed": ge,
        "empirical_tail_plus_one": round((1 + ge) / (len(counts) + 1), 6),
        "observed_to_null_mean_ratio": round(observed / mean, 6) if mean else None,
    }


def build_form144_price_map(originals):
    prices = {}
    for row in originals:
        accession = row.get("accession", "")
        try:
            tranches = json.loads(row.get("sale_tranches_json") or "[]")
        except json.JSONDecodeError:
            tranches = []
        for tranche in tranches:
            idx = str(tranche.get("sale_tranche_index", ""))
            units = dec(str(tranche.get("units_numeric", "")))
            value = dec(str(tranche.get("value_numeric", "")))
            if accession and idx and units is not None and units > 0 and value is not None and value > 0:
                prices[(accession, idx)] = value / units
    return prices


def build_form4_price_map(path):
    with zipfile.ZipFile(path) as archive:
        submissions = list(tsv(archive, "SUBMISSION.tsv"))
        owners = list(tsv(archive, "REPORTINGOWNER.tsv"))
        transactions = list(tsv(archive, "NONDERIV_TRANS.tsv"))

    submission_map = {r.get("ACCESSION_NUMBER", ""): r for r in submissions if r.get("ACCESSION_NUMBER")}
    owner_map = defaultdict(dict)
    for row in owners:
        accession = row.get("ACCESSION_NUMBER", "")
        owner_cik = cik(row.get("RPTOWNERCIK", ""))
        if accession and owner_cik:
            owner_map[accession][owner_cik] = row.get("RPTOWNERNAME", "")

    seen = set()
    totals = defaultdict(lambda: {
        "shares": dec("0"), "priced_shares": dec("0"), "consideration": dec("0")
    })
    for row in transactions:
        accession = row.get("ACCESSION_NUMBER", "")
        transaction_key = (accession, row.get("NONDERIV_TRANS_SK", ""))
        if transaction_key in seen:
            continue
        seen.add(transaction_key)
        submission = submission_map.get(accession)
        if not submission or submission.get("DOCUMENT_TYPE") != "4" or row.get("TRANS_FORM_TYPE") != "4":
            continue
        if row.get("TRANS_CODE") != "S" or row.get("TRANS_ACQUIRED_DISP_CD") != "D":
            continue
        if row.get("TRANS_TIMELINESS") == "L" or len(owner_map.get(accession, {})) != 1:
            continue
        issuer = cik(submission.get("ISSUERCIK", ""))
        owner = name(next(iter(owner_map[accession].values())))
        transaction_date = secdate(row.get("TRANS_DATE", ""))
        filing_date = secdate(submission.get("FILING_DATE", ""))
        shares = dec(row.get("TRANS_SHARES", ""))
        if not issuer or not owner or transaction_date is None or filing_date is None or shares is None or shares <= 0:
            continue
        lag = (filing_date - transaction_date).days
        if lag < 0 or lag > 4:
            continue
        key = (accession, transaction_date)
        totals[key]["shares"] += shares
        price = dec(row.get("TRANS_PRICEPERSHARE", ""))
        if price is not None and price > 0:
            totals[key]["priced_shares"] += shares
            totals[key]["consideration"] += shares * price

    result = {}
    for key, total in totals.items():
        priced_shares = total["priced_shares"]
        shares = total["shares"]
        result[key] = {
            "weighted_avg_price": total["consideration"] / priced_shares if priced_shares > 0 else None,
            "priced_share_fraction": priced_shares / shares if shares > 0 else None,
        }
    return result


def summarize_price_matches(matches, form144_prices, form4_prices):
    observations = []
    for tranche, block, gap in matches:
        estimate = form144_prices.get((tranche["accession"], tranche["idx"]))
        actual = form4_prices.get((block["accession"], block["date"]))
        if estimate is None or estimate <= 0 or not actual or actual["weighted_avg_price"] is None:
            continue
        difference = abs(actual["weighted_avg_price"] - estimate)
        observations.append({
            "relative": float(difference / estimate),
            "absolute": float(difference),
            "priced_fraction": float(actual["priced_share_fraction"] or 0),
            "family_agree": tranche.get("class_family") == block.get("class_family")
                and tranche.get("class_family") not in ("UNKNOWN", "MULTI_OR_UNKNOWN"),
        })
    if not observations:
        return {"matches": len(matches), "priced_matches": 0}
    relative = [x["relative"] for x in observations]
    absolute = [x["absolute"] for x in observations]
    return {
        "matches": len(matches),
        "priced_matches": len(observations),
        "all_form4_shares_priced": sum(x["priced_fraction"] >= 0.999999 for x in observations),
        "min_priced_share_fraction": round(min(x["priced_fraction"] for x in observations), 6),
        "median_abs_relative_difference_pct": round(100 * statistics_median(relative), 6),
        "p90_abs_relative_difference_pct": round(100 * quantile_linear(relative, 0.90), 6),
        "p95_abs_relative_difference_pct": round(100 * quantile_linear(relative, 0.95), 6),
        "max_abs_relative_difference_pct": round(100 * max(relative), 6),
        "within_1pct": sum(x <= 0.01 for x in relative),
        "within_2_5pct": sum(x <= 0.025 for x in relative),
        "within_5pct": sum(x <= 0.05 for x in relative),
        "within_10pct": sum(x <= 0.10 for x in relative),
        "within_20pct": sum(x <= 0.20 for x in relative),
        "median_abs_price_difference_usd_per_share": round(statistics_median(absolute), 6),
    }


def plan_flag_concordance(matches):
    table = Counter()
    for tranche, block, _ in matches:
        plan = bool(tranche.get("plan"))
        disclosed = flag(block.get("flag"))
        left = "plan_date_present" if plan else "no_plan_date"
        right = "form4_true" if disclosed is True else "form4_false" if disclosed is False else "form4_unknown"
        table[f"{left}|{right}"] += 1
    concordant = table["plan_date_present|form4_true"] + table["no_plan_date|form4_false"]
    known = sum(v for k, v in table.items() if not k.endswith("|form4_unknown"))
    return {
        "table": dict(sorted(table.items())),
        "concordant": concordant,
        "discordant": known - concordant,
        "known_pairs": known,
        "concordance_rate": round(concordant / known, 6) if known else None,
    }


def run_permutations(tranches, blocks, exact_unique, form144_prices, form4_prices, reps=500, seed=210):
    base_owners = [b["owner"] for b in blocks]
    base_dates = [b["date"] for b in blocks]
    base_shares = [b["shares"] for b in blocks]
    by_issuer, by_owner = defaultdict(list), defaultdict(list)
    for i, block in enumerate(blocks):
        by_issuer[block["issuer"]].append(i)
        by_owner[(block["issuer"], block["owner"])].append(i)

    owner_mutable = {i for ids in by_issuer.values()
                     if len({base_owners[i] for i in ids}) > 1 for i in ids}
    date_mutable = {i for ids in by_owner.values() if len(ids) > 1 for i in ids}
    block_index = {(b["accession"], b["date"]): i for i, b in enumerate(blocks)}
    observed_owner = sum(1 for _, b, _ in exact_unique
                         if block_index[(b["accession"], b["date"])] in owner_mutable)
    observed_date = sum(1 for _, b, _ in exact_unique
                        if block_index[(b["accession"], b["date"])] in date_mutable)

    specs = [
        ("owner_identity_within_issuer", "owner", owner_mutable, observed_owner, 0),
        ("date_within_issuer_owner", "date", date_mutable, observed_date, 1),
        ("shares_within_issuer_owner", "shares", date_mutable, observed_date, 2),
        ("date_and_shares_within_issuer_owner", "both", date_mutable, observed_date, 3),
    ]
    summaries = {}
    for label, mode, mutable, observed, offset in specs:
        rng = random.Random(seed + offset)
        counts = []
        for _ in range(reps):
            owners, dates, shares = base_owners.copy(), base_dates.copy(), base_shares.copy()
            if mode == "owner":
                for ids in by_issuer.values():
                    if len({base_owners[i] for i in ids}) > 1:
                        vals = [base_owners[i] for i in ids]
                        rng.shuffle(vals)
                        for i, value in zip(ids, vals):
                            owners[i] = value
            else:
                for ids in by_owner.values():
                    if len(ids) <= 1:
                        continue
                    if mode in ("date", "both"):
                        vals = [base_dates[i] for i in ids]
                        rng.shuffle(vals)
                        for i, value in zip(ids, vals):
                            dates[i] = value
                    if mode in ("shares", "both"):
                        vals = [base_shares[i] for i in ids]
                        rng.shuffle(vals)
                        for i, value in zip(ids, vals):
                            shares[i] = value
            counts.append(count_unique_mutable_matches(tranches, blocks, owners, dates, shares, mutable))
        summaries[label] = permutation_summary(counts, observed, len(mutable))

    price_rng = random.Random(seed + 4)
    base_prices = [form4_prices.get((b["accession"], b["date"]), {}).get("weighted_avg_price") for b in blocks]
    observed_price = 0
    for tranche, block, _ in exact_unique:
        bi = block_index[(block["accession"], block["date"])]
        estimate = form144_prices.get((tranche["accession"], tranche["idx"]))
        actual = base_prices[bi]
        if bi in date_mutable and estimate and estimate > 0 and actual is not None:
            if abs(actual - estimate) / estimate <= 0.05:
                observed_price += 1
    price_counts = []
    for _ in range(reps):
        assigned = base_prices.copy()
        for ids in by_owner.values():
            if len(ids) > 1:
                vals = [base_prices[i] for i in ids]
                price_rng.shuffle(vals)
                for i, value in zip(ids, vals):
                    assigned[i] = value
        count = 0
        for tranche, block, _ in exact_unique:
            bi = block_index[(block["accession"], block["date"])]
            estimate = form144_prices.get((tranche["accession"], tranche["idx"]))
            actual = assigned[bi]
            if bi in date_mutable and estimate and estimate > 0 and actual is not None:
                if abs(actual - estimate) / estimate <= 0.05:
                    count += 1
        price_counts.append(count)
    summaries["price_within_5pct_within_issuer_owner"] = permutation_summary(
        price_counts, observed_price, len(date_mutable)
    )

    return {
        "replicates": reps,
        "seed": seed,
        "group_structure": {
            "issuer_groups": len(by_issuer),
            "issuers_with_multiple_reporting_owners": sum(
                1 for ids in by_issuer.values() if len({base_owners[i] for i in ids}) > 1
            ),
            "issuer_owner_groups": len(by_owner),
            "issuer_owner_groups_with_multiple_form4_blocks": sum(1 for ids in by_owner.values() if len(ids) > 1),
            "owner_identity_mutable_form4_blocks": len(owner_mutable),
            "date_and_share_mutable_form4_blocks": len(date_mutable),
            "exact_links_in_owner_mutable_groups": observed_owner,
            "exact_links_in_date_share_mutable_groups": observed_date,
            "exact_links_in_price_mutable_groups_within_5pct": observed_price,
        },
        "placebos": summaries,
    }


def audit(form144_path, form4_path, reps=500, seed=210):
    form144_sha, form4_sha = sha(form144_path), sha(form4_path)
    if form144_sha != EXPECTED_FORM144_SHA:
        raise ValueError("Unexpected immutable Form 144 input")
    if form4_sha != EXPECTED_FORM4_SHA:
        raise ValueError("Unexpected immutable Form 4 input")
    rows, originals, eligible, tranches, _ = form144_data(form144_path)
    submissions, rawtx, filing_dates, blocks, _ = form4_blocks(form4_path)
    linkage = exact_first_match(tranches, blocks)
    exact_unique = linkage["exact_unique"]
    fallback = linkage["fallback_unique"]
    if len(exact_unique) != 521 or len(fallback) != 49:
        raise ValueError("Unexpected exact-first linkage graph")

    form144_prices = build_form144_price_map(originals)
    form4_prices = build_form4_price_map(form4_path)
    family_agree = normalized_equal = 0
    family_pairs = Counter()
    for tranche, block, _ in exact_unique:
        tf, bf = tranche.get("class_family", "UNKNOWN"), block.get("class_family", "MULTI_OR_UNKNOWN")
        family_pairs[f"{tf}|{bf}"] += 1
        if tf == bf and tf not in ("UNKNOWN", "MULTI_OR_UNKNOWN"):
            family_agree += 1
        tn, bn = tranche.get("class_norm", ""), block.get("class_norm", "")
        if tn and bn and tn == bn:
            normalized_equal += 1

    exact_price = summarize_price_matches(exact_unique, form144_prices, form4_prices)
    family_price = summarize_price_matches(
        [x for x in exact_unique if x[0].get("class_family") == x[1].get("class_family")
         and x[0].get("class_family") not in ("UNKNOWN", "MULTI_OR_UNKNOWN")],
        form144_prices, form4_prices
    )
    unresolved_price = summarize_price_matches(
        [x for x in exact_unique if x[0].get("class_family") != x[1].get("class_family")
         or x[0].get("class_family") in ("UNKNOWN", "MULTI_OR_UNKNOWN")],
        form144_prices, form4_prices
    )
    fallback_price = summarize_price_matches(fallback, form144_prices, form4_prices)
    plan = plan_flag_concordance(exact_unique)
    permutations = run_permutations(tranches, blocks, exact_unique, form144_prices, form4_prices, reps, seed)

    return {
        "phase": 210,
        "inputs": {
            "form144_csv_sha256": form144_sha, "form144_artifact_run_id": 41959603351,
            "form144_artifact_id": 13385365595, "form4_inner_zip_sha256": form4_sha,
            "form4_artifact_run_id": 40606706518, "form4_artifact_id": 12781850078,
        },
        "sample": {
            "form144_panel_rows": len(rows), "eligible_notices": len(eligible),
            "eligible_tranches": len(tranches), "form4_submissions": len(submissions),
            "form4_nonderivative_rows": len(rawtx), "form4_unique_owner_sale_blocks": len(blocks),
        },
        "exact_link_graph": {
            "edges": len(linkage["exact_edges"]), "mutually_unique_edges": len(exact_unique),
            "ambiguous_tranches": linkage["exact_ambiguous_tranches"],
            "ambiguous_form4_blocks": linkage["exact_ambiguous_blocks"],
            "class_family_agree": family_agree,
            "class_family_agreement_rate": round(family_agree / len(exact_unique), 6),
            "normalized_class_text_equal": normalized_equal,
            "family_agree_but_normalized_text_differs": family_agree - normalized_equal,
            "family_conflict_or_unknown": len(exact_unique) - family_agree,
            "class_family_pairs": dict(sorted(family_pairs.items())),
            "fallback_mutually_unique_links": len(fallback),
            "total_hierarchical_links": len(exact_unique) + len(fallback),
        },
        "price_concordance": {
            "exact_links": exact_price,
            "class_family_agree_exact_links": family_price,
            "class_family_conflict_or_unresolved_exact_links": unresolved_price,
            "fallback_links": fallback_price,
        },
        "plan_flag_concordance": plan,
        "permutation_audit": permutations,
        "decision": {
            "disposition": "LINKAGE_PLACEBO_AND_PRICE_ALIGNMENT_ENHANCED_DESCRIPTIVE_ONLY",
            "strict_pit_admitted": False, "feature_admitted": False,
            "alpha_test_authorized": False, "return_test_run": False,
            "holdout_used": False, "legacy_holdout": "CONSUMED_NOT_PRISTINE",
            "f80_frozen": True, "production_changed": False,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--form144-csv", required=True)
    parser.add_argument("--form4-zip", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--permutations", type=int, default=500)
    parser.add_argument("--seed", type=int, default=210)
    args = parser.parse_args()
    if args.permutations < 100:
        raise ValueError("Use at least 100 permutations")
    result = audit(args.form144_csv, args.form4_zip, args.permutations, args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
