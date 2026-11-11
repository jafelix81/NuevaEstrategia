#!/usr/bin/env python3
"""Phase 259: independent audit of Phase 29 MOM120 cross-sectional and Phase 30 portfolio evidence.

Uses immutable GitHub Actions artifacts only. No new market data is downloaded.
"""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

PHASE29_REPORT_SHA = "a935ca2994a1041ad458a76fa203576cdd330e33fc253143879c9491bcc4db65"
PHASE30_FILES = {
    "phase30_report.json": "fb34f1aa54783348ccfe9d0cf61e5d943a3167466e1152155cf9a3d537dd808f",
    "LTM_ledger_C10.csv": "f7d9e2949bdecd36ae12cbdc7bd1ff4e4c77d0c4774545746b85c3645052dc6c",
    "LTM_ledger_C20.csv": "b46fc6a11e681d5462cd560a70dff9624676e97879560a0f70f0d1b7511e20ad",
    "LTM_ledger_C50.csv": "1c3f2a1afc525482530be6fa49b8db894e9c9377192c17c343659d6c3cc480a3",
    "MOM120_ledger_C10.csv": "488c7e1c1e83b95aab386026915fd5f3f42745f699d7639b149c893046224264",
    "MOM120_ledger_C20.csv": "5b7ae2ccc8f20ff0fd8295207465a84a254041052cd1d34ad5bfc69f6c2da415",
    "MOM120_ledger_C50.csv": "a4ca89f021054dee2a04439b3605d61c20885170c17da78a58bcb47c74cf1a47",
    "LTM_trades_C10.csv": "3e880dddc1f48a537ad31fb21a6459f41c828052efabf951cccfbf18cde78495",
    "LTM_trades_C20.csv": "ad0bf514d81ffe0b02fa4a56f9a101039e6c4446c3a3a34932b86f885629b729",
    "LTM_trades_C50.csv": "bac8fe0e905818869fad4eaa39b03036d0258899b7057279b8d52ce848bce1d6",
    "MOM120_trades_C10.csv": "e8dc9e11a778fb11aee5b0d2d1b4ede597eeec5a3f13a49e6aee42fb85b16d1d",
    "MOM120_trades_C20.csv": "4bbe4ebec50636de1f87df1d39875e09e783a6dccb6d328a298b7f09d75fa58f",
    "MOM120_trades_C50.csv": "2f3adf4b8a656ca5c4a6da80b8afda24d92f1d25a51dca7da0af341aac51d5f2",
}

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def verify_artifact_files(phase29_dir, phase30_dir):
    p29 = Path(phase29_dir) / "phase29_report.json"
    if sha_bytes(p29.read_bytes()) != PHASE29_REPORT_SHA:
        raise ValueError("Phase 29 report SHA-256 mismatch")
    hashes = {}
    for filename, expected in PHASE30_FILES.items():
        path = Path(phase30_dir) / filename
        actual = sha_bytes(path.read_bytes())
        hashes[filename] = actual
        if actual != expected:
            raise ValueError("Phase 30 artifact file SHA-256 mismatch: " + filename)
    return hashes

def audit_ledger_frame(df, top_n=20, gross_cap=1.0, tol=1e-7):
    required = {"Date","Equity","DailyReturn","Cash","GrossValue","Positions","Gross"}
    if not required.issubset(df.columns):
        raise ValueError("ledger schema incomplete")
    x = df.copy()
    x["Date"] = pd.to_datetime(x["Date"])
    if x["Date"].duplicated().any() or not x["Date"].is_monotonic_increasing:
        raise ValueError("ledger dates must be unique and chronological")
    numeric = ["Equity","DailyReturn","Cash","GrossValue","Positions","Gross"]
    if not np.isfinite(x[numeric].to_numpy(dtype=float)).all():
        raise ValueError("ledger contains non-finite numeric values")
    if (x["Equity"] <= 0).any() or (x["Cash"] < -tol).any() or (x["GrossValue"] < -tol).any():
        raise ValueError("equity/cash/gross-value invariant failed")
    if (x["Positions"] < 0).any() or (x["Positions"] > top_n).any():
        raise ValueError("Top-N position-count invariant failed")
    if (x["Gross"] > gross_cap + tol).any() or (x["Gross"] < -tol).any():
        raise ValueError("gross exposure cap invariant failed")
    equity_error = float(np.max(np.abs(x["Equity"].to_numpy() - x["Cash"].to_numpy() - x["GrossValue"].to_numpy())))
    gross_error = float(np.max(np.abs(x["Gross"].to_numpy() - x["GrossValue"].to_numpy()/x["Equity"].to_numpy())))
    sequential = x["Equity"].pct_change().fillna(0.0).to_numpy()
    return_error = float(np.max(np.abs(x["DailyReturn"].to_numpy() - sequential)))
    if equity_error > tol or gross_error > tol or return_error > tol:
        raise ValueError("ledger accounting identity mismatch")
    return {
        "rows": int(len(x)), "start": x["Date"].iloc[0].date().isoformat(),
        "end": x["Date"].iloc[-1].date().isoformat(),
        "max_positions": int(x["Positions"].max()),
        "avg_positions": float(x["Positions"].mean()),
        "max_gross": float(x["Gross"].max()),
        "min_cash": float(x["Cash"].min()),
        "max_equity_cash_error": equity_error,
        "max_gross_identity_error": gross_error,
        "max_sequential_return_error": return_error,
    }, x

def corrected_oos_metrics(ledger, oos_start="2024-01-01"):
    x = ledger.copy()
    x["Date"] = pd.to_datetime(x["Date"])
    start = pd.Timestamp(oos_start)
    oos = x[x["Date"] >= start].copy().reset_index(drop=True)
    prior = x[x["Date"] < start]
    if oos.empty or prior.empty:
        raise ValueError("OOS window lacks a pre-OOS close baseline")
    prior_close = prior.iloc[-1]
    returns = oos["DailyReturn"].to_numpy(dtype=float)
    start_equity = float(prior_close["Equity"])
    end_equity = float(oos["Equity"].iloc[-1])
    multiple = end_equity / start_equity
    years = len(returns) / 252.0
    curve = np.concatenate(([1.0], np.cumprod(1.0 + returns)))
    drawdown = curve / np.maximum.accumulate(curve) - 1.0
    vol = float(np.std(returns, ddof=1))
    first_oos_close = float(oos["Equity"].iloc[0])
    reported_multiple = end_equity / first_oos_close
    return {
        "oos_start_date": oos["Date"].iloc[0].date().isoformat(),
        "oos_end_date": oos["Date"].iloc[-1].date().isoformat(),
        "oos_return_observations": int(len(returns)),
        "pre_oos_close_date": prior_close["Date"].date().isoformat(),
        "pre_oos_close_equity": start_equity,
        "first_oos_close_equity": first_oos_close,
        "end_equity": end_equity,
        "corrected_final_multiple": float(multiple),
        "corrected_cagr": float(multiple ** (1.0 / years) - 1.0),
        "mean_daily": float(np.mean(returns)),
        "vol_ann": float(vol * np.sqrt(252.0)),
        "sharpe": float(np.mean(returns) / vol * np.sqrt(252.0)) if vol > 0 else None,
        "max_drawdown": float(np.min(drawdown)),
        "first_oos_daily_return": float(returns[0]),
        "published_multiple_end_over_first_oos_close": float(reported_multiple),
        "published_multiple_overstatement_pct": float((reported_multiple / multiple - 1.0) * 100.0),
        "returns": returns.tolist(),
    }

def circular_block_bootstrap_mean(d, reps=5000, block=20, seed=30):
    d = np.asarray(d, dtype=float)
    if len(d) < 100 or block < 1:
        raise ValueError("insufficient observations or invalid block length")
    rng = np.random.default_rng(seed)
    means = np.empty(reps, dtype=float)
    n = len(d)
    for rep in range(reps):
        idx = []
        while len(idx) < n:
            start = int(rng.integers(0, n))
            idx.extend((start + np.arange(block)) % n)
        means[rep] = float(np.mean(d[np.asarray(idx[:n], dtype=int)]))
    q = np.quantile(means, [0.025, 0.5, 0.975])
    return {
        "reps": reps, "block_length": block, "seed": seed,
        "mean": float(np.mean(d)), "ci95_low": float(q[0]),
        "bootstrap_median": float(q[1]), "ci95_high": float(q[2]),
        "ci_includes_zero": bool(q[0] <= 0.0 <= q[2]),
    }

def hac_mean(d, max_lag=20):
    d = np.asarray(d, dtype=float)
    n = len(d)
    mean = float(np.mean(d))
    u = d - mean
    gamma0 = float(np.dot(u, u) / n)
    long_run = gamma0
    for lag in range(1, min(max_lag, n-1) + 1):
        gamma = float(np.dot(u[lag:], u[:-lag]) / n)
        weight = 1.0 - lag / (max_lag + 1.0)
        long_run += 2.0 * weight * gamma
    se = float(np.sqrt(max(long_run, 0.0) / n))
    return {
        "n": n, "mean": mean, "hac_max_lag": max_lag, "se": se,
        "t_stat": mean / se if se > 0 else None,
        "ci95_low": mean - 1.96 * se, "ci95_high": mean + 1.96 * se,
        "ci_includes_zero": bool(mean - 1.96*se <= 0 <= mean + 1.96*se),
    }

def trade_cost_audit(df, bps_side, tol=1e-7):
    required = {"Notional","Cost","Side","Date","Ticker"}
    if not required.issubset(df.columns):
        raise ValueError("trade ledger schema incomplete")
    notional = pd.to_numeric(df["Notional"], errors="coerce").to_numpy(float)
    cost = pd.to_numeric(df["Cost"], errors="coerce").to_numpy(float)
    if not np.isfinite(notional).all() or not np.isfinite(cost).all() or (notional < 0).any() or (cost < -tol).any():
        raise ValueError("invalid trade notional or cost")
    err = float(np.max(np.abs(cost - notional * bps_side / 10000.0))) if len(df) else 0.0
    if err > tol:
        raise ValueError("trade-level transaction cost mismatch")
    return {"trades": int(len(df)), "total_notional": float(notional.sum()),
            "total_cost": float(cost.sum()), "max_cost_identity_error": err}

def audit(phase29_dir, phase30_dir, reps=5000):
    hashes = verify_artifact_files(phase29_dir, phase30_dir)
    p29 = json.loads((Path(phase29_dir)/"phase29_report.json").read_text())
    p30 = json.loads((Path(phase30_dir)/"phase30_report.json").read_text())
    phase29 = {}
    for horizon in (20, 60):
        row = next(x for x in p29["results"] if int(x["horizon"]) == horizon)
        phase29[str(horizon)] = {
            "discovery_mean_ic": row["discovery"]["mean_ic"],
            "validation_mean_ic": row["validation"]["mean_ic"],
            "validation_mean_q10_q1": row["validation"]["mean_d10_d1"],
            "oos_dates": row["final_oos"]["dates"],
            "oos_mean_ic": row["final_oos"]["mean_ic"],
            "oos_mean_q10_q1": row["final_oos"]["mean_d10_d1"],
            "oos_q10_q1_bootstrap_ci95": [
                row["final_bootstrap_d10_d1"]["ci95_low"],
                row["final_bootstrap_d10_d1"]["ci95_high"],
            ],
        }
    ledgers, ledger_audits, corrected = {}, {}, {}
    trade_audits = {}
    for cost in (10,20,50):
        for factor in ("LTM","MOM120"):
            filename = f"{factor}_ledger_C{cost}.csv"
            df = pd.read_csv(Path(phase30_dir)/filename)
            audit_row, normalized = audit_ledger_frame(df)
            ledgers[(factor,cost)] = normalized
            ledger_audits[f"{factor}_C{cost}"] = audit_row
            corrected[f"{factor}_C{cost}"] = corrected_oos_metrics(normalized)
            tfile = f"{factor}_trades_C{cost}.csv"
            trades = pd.read_csv(Path(phase30_dir)/tfile)
            trade_audits[f"{factor}_C{cost}"] = trade_cost_audit(trades,cost)
    cost_sensitivity = {}
    for cost in (10,20,50):
        l = ledgers[("LTM",cost)]
        m = ledgers[("MOM120",cost)]
        if not l["Date"].equals(m["Date"]):
            raise ValueError("LTM and MOM120 dates differ")
        mask = l["Date"] >= pd.Timestamp("2024-01-01")
        d = m.loc[mask,"DailyReturn"].to_numpy(float) - l.loc[mask,"DailyReturn"].to_numpy(float)
        boot = circular_block_bootstrap_mean(d,reps=reps,block=20,seed=30)
        loo = (d.sum()-d)/(len(d)-1)
        lmet, mmet = corrected[f"LTM_C{cost}"], corrected[f"MOM120_C{cost}"]
        cost_sensitivity[str(cost)] = {
            "mean_excess_daily": float(np.mean(d)),
            "mean_excess_daily_bps": float(np.mean(d)*10000.0),
            "annualized_simple_mean_excess_pct": float(np.mean(d)*252.0*100.0),
            "relative_oos_growth_pct": float((mmet["corrected_final_multiple"]/lmet["corrected_final_multiple"]-1.0)*100.0),
            "bootstrap_block20": boot,
            "loo_min_daily_bps": float(np.min(loo)*10000.0),
            "loo_max_daily_bps": float(np.max(loo)*10000.0),
            "positive_loo_fraction": float(np.mean(loo>0.0)),
        }
    l20,m20 = ledgers[("LTM",20)],ledgers[("MOM120",20)]
    mask20 = l20["Date"] >= pd.Timestamp("2024-01-01")
    d20 = m20.loc[mask20,"DailyReturn"].to_numpy(float)-l20.loc[mask20,"DailyReturn"].to_numpy(float)
    block_sensitivity = {}
    for block in (5,10,20,40,80):
        block_sensitivity[str(block)] = circular_block_bootstrap_mean(d20,reps=reps,block=block,seed=30+block if block!=20 else 30)
    hac = {str(lag): hac_mean(d20,lag) for lag in (0,5,10,20,40,80)}
    return {
        "phase":259,"status":"MOM120_PORTFOLIO_INCREMENTAL_EDGE_NOT_DEMONSTRATED",
        "inputs":{
            "phase29_run_id":40105752275,"phase29_artifact_id":12565060248,
            "phase29_artifact_sha256":"85480d28d6d24c8a167c67baee5b3c28c2915e0a3bc3b2eb2f13b490d4167d77",
            "phase30_run_id":40149358003,"phase30_artifact_id":12581524526,
            "phase30_artifact_sha256":"b57190f1d979bde7bb38cff0c6fa0e294cbfed029c5bc702ab62574bb459bc48",
            "verified_file_sha256":hashes,
        },
        "phase29_cross_sectional_context":phase29,
        "phase30_protocol":p30["protocol"],
        "phase30_signal_dates":p30["signal_dates"],
        "ledger_integrity":ledger_audits,
        "trade_cost_integrity":trade_audits,
        "corrected_oos_metrics":corrected,
        "cost_sensitivity":cost_sensitivity,
        "c20_block_length_sensitivity":block_sensitivity,
        "c20_hac_sensitivity":hac,
        "published_boundary_issue":{
            "description":"The Phase 30 metrics function divides final equity by the first OOS close while the OOS DailyReturn series includes the first OOS day's return from the prior close. Correct base for the 706 included daily returns is the 2023-12-29 close.",
            "affects_daily_excess_series":False,
            "affects_published_absolute_final_multiple_and_cagr":True,
        },
        "decision":{
            "mom120_cross_sectional_hypothesis_retained":True,
            "mom120_incremental_upgrade_to_f80_demonstrated":False,
            "incremental_ci_excludes_zero":False,
            "incremental_hac_ci_excludes_zero":False,
            "promote_mom120":False,
            "strict_pit_admitted":False,
            "phase29_phase30_oos_consumed_not_pristine":True,
            "holdout_used_in_this_audit":False,
            "f80_frozen":True,
            "production_changed":False,
            "universe_changed":False,
            "capital_changed":False,
        },
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--phase29-dir",required=True)
    p.add_argument("--phase30-dir",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--bootstrap-reps",type=int,default=5000)
    a=p.parse_args()
    result=audit(a.phase29_dir,a.phase30_dir,a.bootstrap_reps)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
