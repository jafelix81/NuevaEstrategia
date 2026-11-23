#!/usr/bin/env python3
"""Reproduce Phase 574 cycle-cluster bootstrap sensitivity from the Phase 426 artifact."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

EXPECTED_CSV_SHA256 = "4ac2215f18ba67d0f5b21a5549928a34fc37872e4a8361e42a4ea3112f846b1d"
EXPECTED_ROWS = 721
SEED = 20261123
DEFAULT_BOOTSTRAP_DRAWS = 200_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_rows(path: Path, verify_hash: bool = True) -> list[dict[str, Any]]:
    actual_hash = sha256_file(path)
    if verify_hash and actual_hash != EXPECTED_CSV_SHA256:
        raise ValueError(f"Input SHA-256 mismatch: {actual_hash}")
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"Date", "DailyReturn_ltm", "DailyReturn_mom", "cycle_id"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing required columns: {sorted(required - set(reader.fieldnames or []))}")
        for raw in reader:
            d = date.fromisoformat(raw["Date"])
            ltm = float(raw["DailyReturn_ltm"])
            mom = float(raw["DailyReturn_mom"])
            cycle = int(raw["cycle_id"])
            if not all(math.isfinite(x) for x in (ltm, mom)) or ltm <= -1 or mom <= -1:
                raise ValueError(f"Invalid return on {d}")
            rows.append({"date": d.isoformat(), "ltm": ltm, "mom": mom, "cycle": cycle})
    if verify_hash and len(rows) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} rows, received {len(rows)}")
    if [r["date"] for r in rows] != sorted(r["date"] for r in rows):
        raise ValueError("Input dates are not sorted")
    if len({r["date"] for r in rows}) != len(rows):
        raise ValueError("Duplicate dates in paired-return input")
    return rows


def cycle_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["cycle"]].append(row)
    records = []
    for cycle, group in sorted(grouped.items()):
        ltm_log = sum(math.log1p(r["ltm"]) for r in group)
        mom_log = sum(math.log1p(r["mom"]) for r in group)
        rel_log = mom_log - ltm_log
        records.append({
            "cycle_id": cycle,
            "start": group[0]["date"],
            "end": group[-1]["date"],
            "sessions": len(group),
            "mean_daily_excess": sum(r["mom"] - r["ltm"] for r in group) / len(group),
            "relative_compounded_return": math.expm1(rel_log),
            "relative_log_return": rel_log,
        })
    return records


def exact_one_sided_sign_p(positive: int, n: int) -> float:
    return sum(math.comb(n, k) for k in range(positive, n + 1)) / (2 ** n)


def summarize_clusters(records: list[dict[str, Any]], draws: int, seed: int) -> dict[str, Any]:
    values = np.asarray([r["mean_daily_excess"] for r in records], dtype=float)
    weights = np.asarray([r["sessions"] for r in records], dtype=float)
    relative_logs = np.asarray([r["relative_log_return"] for r in records], dtype=float)
    n = len(values)
    if n < 2:
        raise ValueError("At least two cycle clusters are required")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n, size=(draws, n))
    equal_cycle_boot = values[indices].mean(axis=1)
    day_weighted_boot = (values[indices] * weights[indices]).sum(axis=1) / weights[indices].sum(axis=1)
    lo, hi = np.quantile(equal_cycle_boot, [0.025, 0.975])
    wlo, whi = np.quantile(day_weighted_boot, [0.025, 0.975])
    positive = int((relative_logs > 0).sum())
    loo_means = [float(np.delete(values, i).mean()) for i in range(n)]
    return {
        "clusters": n,
        "sessions": int(weights.sum()),
        "positive_relative_cycles": positive,
        "equal_cycle_mean_daily_excess_bps": float(values.mean() * 10_000),
        "equal_cycle_bootstrap_95ci_bps": [float(lo * 10_000), float(hi * 10_000)],
        "day_weighted_mean_daily_excess_bps": float(np.average(values, weights=weights) * 10_000),
        "day_weighted_bootstrap_95ci_bps": [float(wlo * 10_000), float(whi * 10_000)],
        "one_sided_sign_test_p_descriptive": exact_one_sided_sign_p(positive, n),
        "minimum_leave_one_cycle_out_mean_bps": min(loo_means) * 10_000,
        "mean_log_relative_return_per_cycle": float(relative_logs.mean()),
        "geometric_relative_return_per_cycle_pct": float(math.expm1(relative_logs.mean()) * 100),
    }


def analyze(rows: list[dict[str, Any]], draws: int = DEFAULT_BOOTSTRAP_DRAWS, seed: int = SEED) -> dict[str, Any]:
    records = cycle_records(rows)
    if not records:
        raise ValueError("No cycle records")
    initial = records[0]
    if initial["sessions"] != 6 or initial["start"] != "2024-01-02" or initial["end"] != "2024-01-09":
        raise ValueError("Expected the known 6-session initial boundary stub; review protocol before changing exclusion")
    all_summary = summarize_clusters(records, draws, seed)
    comparable_summary = summarize_clusters(records[1:], draws, seed)
    return {
        "phase": 574,
        "input_rows": len(rows),
        "first_date": rows[0]["date"],
        "last_date": rows[-1]["date"],
        "bootstrap_draws": draws,
        "seed": seed,
        "all_cycle_groups": all_summary,
        "excluding_initial_6_session_boundary_stub": comparable_summary,
        "cycle_records": records,
        "disposition": "HISTORICAL_SENSITIVITY_ONLY_NO_FRESH_OOS_OR_PROMOTION",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="paired_exposure_matched_excess_C20.csv from artifact 14191029663")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--draws", type=int, default=DEFAULT_BOOTSTRAP_DRAWS)
    args = parser.parse_args()
    rows = load_rows(args.input)
    result = analyze(rows, draws=args.draws)
    result["input_sha256"] = sha256_file(args.input)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
