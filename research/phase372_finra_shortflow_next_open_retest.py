#!/usr/bin/env python3
"""Phase 372: re-test FINRA short-flow replacements with next-session-open entry.

This corrects Phase 20C's close-to-close execution timing. FINRA daily files are
posted after the regular close, so the signal at date t is entered at the next
common trading session's open. H5/H10/H20 exits occur at the close of the
5th/10th/20th entry session. Only the 12 predeclared training-era pseudo-OOS
dates from Phase 20C are evaluated. The six final holdout signals are not used.

The original universe, LTM/F80 target, factor set, walk-forward selection
family, 20% replacement fraction and H5/H10/H20 horizons are retained.
Flat per-leg cost sensitivity (0/5/10/20 bps) is shown separately; it is not
a market-impact or spread model. No production signal is admitted.
"""
from __future__ import annotations

import json
import math
import time
from bisect import bisect_right
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.stats import spearmanr

import Nueva_Estrategia_Fase12_FinalOOS_Selection_LTM as P12
import Nueva_Estrategia_Fase11_Real1000_LTM_v4 as P11

OUTDIR = Path("phase372_finra_shortflow_next_open_retest")
RAW_DIR = Path("phase372_raw_cnms")
OUTDIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

LOOKBACK_DAYS = 100
TIMEOUT = 30
RETRIES = 4
MIN_TOTAL_VOLUME = 100_000
FINRA_CNM_START = pd.Timestamp("2018-08-01")
URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{date}.txt"
FACTORS = [
    "SHORT_RATIO", "SHORT_RATIO_Z20", "SHORT_RATIO_Z60",
    "SHORT_RATIO_CHANGE", "SHORT_RATIO_ACCEL", "SHORT_RATIO_PERSIST20",
    "SHORT_EXEMPT_RATIO",
]
HORIZONS = (5, 10, 20)
F80_FREQ = 80
TOPN = 20
REPLACEMENT_FRAC = 0.20
MIN_PRIOR_SIGNALS = 8
COST_BPS_PER_LEG = (0, 5, 10, 20)
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 372

# Freeze the exact 10-year Yahoo window used by the original Phase 20C run
# (workflow started 2026-10-24); do not let a rolling period=10y shift signals.
FIXED_PRICE_START = "2016-10-24"
FIXED_PRICE_END = "2026-10-24"
EXPECTED_VALID_UNIVERSE = 329
EXPECTED_TRAIN_END = "2024-10-30"
EXPECTED_TRAIN_SIGNALS = 24
EXPECTED_ELIGIBLE_SIGNALS = 20
EXPECTED_HOLDOUT_SIGNALS = 6
ROKU_FIRST_TRADING_DATE = "2017-09-28"

EXPECTED_TEST_DATES = (
    "2021-05-03", "2021-08-25", "2021-12-17", "2022-04-13",
    "2022-08-09", "2022-12-01", "2023-03-29", "2023-07-25",
    "2023-11-15", "2024-03-13", "2024-07-09", "2024-10-30",
)


def nd(value):
    return pd.Timestamp(value).normalize()


def fetch_file(dt):
    ds = pd.Timestamp(dt).strftime("%Y%m%d")
    path = RAW_DIR / f"CNMSshvol{ds}.txt"
    if path.exists() and path.stat().st_size > 100:
        return path, "cached"
    last = None
    for attempt in range(RETRIES):
        try:
            response = requests.get(URL.format(date=ds), timeout=TIMEOUT)
            if response.status_code == 200 and response.content:
                path.write_bytes(response.content)
                return path, "downloaded"
            if response.status_code in (403, 404):
                return None, f"not_available_{response.status_code}"
            last = f"http_{response.status_code}"
        except Exception as exc:
            last = repr(exc)
        time.sleep(2 ** attempt)
    return None, f"error_{last}"


def parse_file(path, wanted):
    frame = pd.read_csv(path, sep="|", dtype={"Date": str, "Symbol": str}, engine="python")
    frame.columns = [str(c).strip() for c in frame.columns]
    required = {"Date", "Symbol", "ShortVolume", "ShortExemptVolume", "TotalVolume", "Market"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"Bad FINRA schema: {frame.columns.tolist()}")
    frame = frame[frame.Symbol.notna()].copy()
    frame["Date"] = pd.to_datetime(frame["Date"].astype(str), format="%Y%m%d", errors="coerce").dt.normalize()
    for col in ("ShortVolume", "ShortExemptVolume", "TotalVolume"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame[
        frame.Date.notna()
        & frame.Symbol.isin(wanted)
        & (frame.TotalVolume > 0)
    ]
    return frame[["Date", "Symbol", "ShortVolume", "ShortExemptVolume", "TotalVolume", "Market"]]


def sf_features(group):
    group = group.sort_values("Date").copy()
    group["SHORT_RATIO"] = group.ShortVolume / group.TotalVolume
    group["SHORT_EXEMPT_RATIO"] = group.ShortExemptVolume / group.TotalVolume
    m20 = group.SHORT_RATIO.rolling(20, min_periods=10)
    m60 = group.SHORT_RATIO.rolling(60, min_periods=30)
    group["SHORT_RATIO_Z20"] = (group.SHORT_RATIO - m20.mean()) / m20.std(ddof=1)
    group["SHORT_RATIO_Z60"] = (group.SHORT_RATIO - m60.mean()) / m60.std(ddof=1)
    group["SHORT_RATIO_CHANGE"] = group.SHORT_RATIO.diff()
    group["SHORT_RATIO_ACCEL"] = group.SHORT_RATIO_CHANGE.diff()
    group["SHORT_RATIO_PERSIST20"] = (
        (group.SHORT_RATIO >= m20.quantile(.80)).rolling(20, min_periods=10).mean()
    )
    return group


def ltm_features(data, dt):
    rows = []
    for ticker, history in data.items():
        x = history[pd.to_datetime(history.Date).dt.normalize() <= nd(dt)]
        close = pd.to_numeric(x.Close, errors="coerce").dropna()
        if len(close) >= 161:
            rows.append({
                "Ticker": str(ticker),
                "R100": close.iloc[-1] / close.iloc[-101] - 1,
                "R120": close.iloc[-1] / close.iloc[-121] - 1,
                "R140": close.iloc[-1] / close.iloc[-141] - 1,
                "R160": close.iloc[-1] / close.iloc[-161] - 1,
            })
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    for col in ("R100", "R120", "R140", "R160"):
        frame[col + "_PCT"] = frame[col].rank(pct=True, method="average")
    frame["LTM"] = frame[[col + "_PCT" for col in ("R100", "R120", "R140", "R160")]].mean(axis=1)
    return frame[["Ticker", "LTM"]]


def build_price_indices(data):
    indices = {}
    for ticker, history in data.items():
        x = history.copy()
        x["Date"] = pd.to_datetime(x.Date, errors="coerce").dt.normalize()
        x = x.dropna(subset=["Date"]).drop_duplicates("Date").set_index("Date")
        indices[str(ticker)] = x[["Open", "Close"]]
    return indices


def next_open_forward_return(price_frame, calendar, calendar_index, signal_date, horizon):
    """Return from next common-session open to the horizon-th session close."""
    signal = nd(signal_date)
    pos = calendar_index.get(signal)
    if pos is None:
        return np.nan
    entry_pos = pos + 1
    exit_pos = pos + int(horizon)
    if exit_pos >= len(calendar):
        return np.nan
    entry_date = calendar[entry_pos]
    exit_date = calendar[exit_pos]
    if entry_date not in price_frame.index or exit_date not in price_frame.index:
        return np.nan
    open_price = pd.to_numeric(pd.Series([price_frame.loc[entry_date, "Open"]]), errors="coerce").iloc[0]
    close_price = pd.to_numeric(pd.Series([price_frame.loc[exit_date, "Close"]]), errors="coerce").iloc[0]
    if not np.isfinite(open_price) or not np.isfinite(close_price) or open_price <= 0:
        return np.nan
    return float(close_price / open_price - 1.0)


def forward_panel(data, price_indices, calendar, calendar_index, dt):
    rows = []
    for ticker, price_frame in price_indices.items():
        row = {"Ticker": ticker}
        for horizon in HORIZONS:
            row[f"FwdRet_{horizon}D"] = next_open_forward_return(
                price_frame, calendar, calendar_index, dt, horizon
            )
        rows.append(row)
    return pd.DataFrame(rows)


def cross_section(data, raw, price_indices, calendar, calendar_index, dt):
    subset = raw[(raw.Date <= nd(dt)) & (raw.TotalVolume >= MIN_TOTAL_VOLUME)]
    rows = []
    for ticker, group in subset.groupby("Symbol"):
        features = sf_features(group)
        current = features[features.Date == nd(dt)]
        if not current.empty:
            rows.append(current.iloc[-1])
    short = pd.DataFrame(rows)
    if short.empty:
        return pd.DataFrame()
    short = short.rename(columns={"Symbol": "Ticker"})
    return (
        short.merge(ltm_features(data, dt), on="Ticker", how="inner")
        .merge(forward_panel(data, price_indices, calendar, calendar_index, dt), on="Ticker", how="left")
    )


def matured_exit_date(calendar, calendar_index, signal_date, horizon):
    pos = calendar_index.get(nd(signal_date))
    exit_pos = None if pos is None else pos + int(horizon)
    return calendar[exit_pos] if exit_pos is not None and exit_pos < len(calendar) else None


def score_prior(panels, prior_dates, current_dt, calendar, calendar_index):
    rows = []
    for signal_dt in prior_dates:
        panel = panels.get(signal_dt)
        if panel is None or panel.empty:
            continue
        for factor in FACTORS:
            for horizon in HORIZONS:
                exit_dt = matured_exit_date(calendar, calendar_index, signal_dt, horizon)
                if exit_dt is None or exit_dt > nd(current_dt):
                    continue
                pair = panel[[factor, f"FwdRet_{horizon}D"]].dropna()
                if len(pair) >= 50:
                    rows.append({
                        "DateSignal": signal_dt,
                        "Factor": factor,
                        "Horizon": horizon,
                        "N": len(pair),
                        "Spearman": float(spearmanr(pair[factor], pair[f"FwdRet_{horizon}D"])[0]),
                    })
    training = pd.DataFrame(rows)
    if training.empty:
        return None, training
    score = training.groupby("Factor")["Spearman"].agg(["mean", "median", "count"]).reset_index()
    score["abs_mean"] = score["mean"].abs()
    score = score.sort_values(["abs_mean", "count"], ascending=[False, False]).reset_index(drop=True)
    return score.iloc[0], training


def portfolio_delta_net(group_delta, replacement_fraction, cost_bps_per_leg):
    gross = replacement_fraction * float(group_delta)
    incremental_cost = replacement_fraction * 2.0 * float(cost_bps_per_leg) / 10_000.0
    return gross - incremental_cost


def bootstrap_mean_interval(values, reps=BOOTSTRAP_REPS, seed=BOOTSTRAP_SEED):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return None, None
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(reps, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(samples, .025)), float(np.quantile(samples, .975))


def price_start_for_ticker(ticker):
    """Use the actual listing date for ROKU; other names retain the frozen window."""
    return ROKU_FIRST_TRADING_DATE if str(ticker).upper() == "ROKU" else FIXED_PRICE_START


def download_pinned_universe():
    original_download = P11.yf.download
    def pinned_download(ticker, period=None, interval="1d", auto_adjust=False, progress=False, threads=False, **kwargs):
        return original_download(
            ticker, start=FIXED_PRICE_START, end=FIXED_PRICE_END,
            interval=interval, auto_adjust=auto_adjust, progress=progress, threads=threads,
        )
    P11.yf.download = pinned_download
    try:
        data, failures = P12.download_universe(P12.DEFAULT_UNIVERSE)
    finally:
        P11.yf.download = original_download

    # Retry transient Yahoo failures without changing the frozen price window.
    remaining, recovered = [], 0
    for failure in failures:
        ticker = str(failure.get("Ticker", ""))
        ok = False
        for attempt in range(3):
            try:
                start_date = price_start_for_ticker(ticker)
                raw = original_download(
                    ticker, start=start_date, end=FIXED_PRICE_END,
                    interval="1d", auto_adjust=False, progress=False, threads=False,
                )
                # yfinance's download() returned an empty pre-IPO range for ROKU
                # in the first run. Retry the same Yahoo source through history()
                # from ROKU's actual first trading date; no post-listing observations
                # are lost and the fixed end date remains unchanged.
                if raw is None or raw.empty:
                    raw = P11.yf.Ticker(ticker).history(
                        start=start_date, end=FIXED_PRICE_END, interval="1d",
                        auto_adjust=False, actions=False,
                    )
                if raw is None or raw.empty:
                    raise ValueError(f"empty retry from {start_date}")
                feat = P11.build_features(raw)
                if len(feat) < 220:
                    raise ValueError(f"insufficient retry rows: {len(feat)}")
                data[ticker] = feat
                recovered += 1
                ok = True
                break
            except Exception as exc:
                time.sleep(2 ** attempt)
                last_error = str(exc)
        if not ok:
            remaining.append({"Ticker": ticker, "Error": failure.get("Error", last_error if "last_error" in locals() else "retry_failed")})
    return data, remaining, recovered


def main():
    start = time.time()
    print("PHASE 372 — FINRA short-flow next-session-open retest", flush=True)
    print(f"PINNED_PRICE_WINDOW={FIXED_PRICE_START}..{FIXED_PRICE_END} (end exclusive)", flush=True)
    data, failures, recovered = download_pinned_universe()
    if len(data) != EXPECTED_VALID_UNIVERSE:
        raise RuntimeError(
            f"Valid universe drift: expected {EXPECTED_VALID_UNIVERSE}, got {len(data)}; "
            f"recovered={recovered}; remaining_failures={[x.get('Ticker') for x in failures]}"
        )
    calendar = sorted({nd(d) for frame in data.values() for d in frame.Date.dropna().tolist()})
    snapshots = P12.build_snapshots(data, calendar)
    signals = P12.signal_dates_for(calendar, snapshots, F80_FREQ)
    split = int(math.floor(len(signals) * .80)) - 1
    train_end = signals[split]
    train_all = [d for d in signals if d <= train_end]
    eligible = [d for d in train_all if nd(d) >= FINRA_CNM_START]
    holdout = [d for d in signals if d > train_end]
    test_dates = tuple(nd(d).strftime("%Y-%m-%d") for d in eligible[MIN_PRIOR_SIGNALS:])

    if len(train_all) != EXPECTED_TRAIN_SIGNALS or len(eligible) != EXPECTED_ELIGIBLE_SIGNALS:
        raise RuntimeError(f"Phase20C training sample drift: train={len(train_all)}, eligible={len(eligible)}")
    if nd(train_end).strftime("%Y-%m-%d") != EXPECTED_TRAIN_END:
        raise RuntimeError(f"Phase20C train end drift: {nd(train_end).date()}")
    if len(holdout) != EXPECTED_HOLDOUT_SIGNALS:
        raise RuntimeError(f"Holdout count drift: expected {EXPECTED_HOLDOUT_SIGNALS}, got {len(holdout)}")
    if test_dates != EXPECTED_TEST_DATES:
        raise RuntimeError(f"Pseudo-OOS dates differ from original Phase20C: {test_dates}")
    if max(HORIZONS) >= F80_FREQ:
        raise RuntimeError("Prior signal outcomes may overlap the next signal")

    print(
        f"UNIVERSE={len(data)} FAILURES={len(failures)} TRAIN_END={nd(train_end).date()} "
        f"TRAIN_SIGNALS={len(train_all)} FINRA_ELIGIBLE={len(eligible)} "
        f"PSEUDO_OOS={len(test_dates)} HOLDOUT_UNTOUCHED={len(holdout)}",
        flush=True,
    )

    wanted = set(map(str, data.keys()))
    needed = sorted({
        day for signal_dt in eligible
        for day in calendar
        if nd(signal_dt) - pd.Timedelta(days=LOOKBACK_DAYS) <= day <= nd(signal_dt)
    })
    audit, frames = [], []
    for index, dt in enumerate(needed, 1):
        path, status = fetch_file(dt)
        audit.append({"Date": nd(dt).strftime("%Y-%m-%d"), "Status": status})
        if path:
            try:
                frames.append(parse_file(path, wanted))
            except Exception as exc:
                audit[-1]["Status"] = f"parse_error:{type(exc).__name__}"
        if index % 100 == 0 or index == len(needed):
            print(f"FINRA_FILES={index}/{len(needed)}", flush=True)
    pd.DataFrame(audit).to_csv(OUTDIR / "phase372_finra_download_audit.csv", index=False)
    if not frames:
        raise RuntimeError("No FINRA daily short-volume files were parsed")
    raw = pd.concat(frames, ignore_index=True)
    duplicate_keys = int(raw.duplicated(["Date", "Symbol"]).sum())
    if duplicate_keys:
        raise RuntimeError(f"Unexpected duplicate FINRA Date/Symbol keys: {duplicate_keys}")
    raw = raw.sort_values(["Symbol", "Date"]).reset_index(drop=True)
    raw["Date"] = pd.to_datetime(raw["Date"]).dt.normalize()

    price_indices = build_price_indices(data)
    calendar_index = {dt: i for i, dt in enumerate(calendar)}
    panels = {
        dt: cross_section(data, raw, price_indices, calendar, calendar_index, dt)
        for dt in eligible
    }
    panels = {k: v for k, v in panels.items() if not v.empty}

    selections, results, exclusions = [], [], []
    for i, dt in enumerate(eligible):
        if nd(dt).strftime("%Y-%m-%d") not in EXPECTED_TEST_DATES:
            continue
        prior_dates = eligible[:i]
        prior = {d: panels[d] for d in prior_dates if d in panels}
        if len(prior) < MIN_PRIOR_SIGNALS:
            exclusions.append({"DateSignal": dt, "Reason": "insufficient_prior_panels", "PriorPanels": len(prior)})
            continue
        selected, training = score_prior(prior, list(prior.keys()), dt, calendar, calendar_index)
        if selected is None:
            exclusions.append({"DateSignal": dt, "Reason": "no_valid_prior_factor"})
            continue
        factor = str(selected["Factor"])
        train_mean = float(selected["mean"])
        direction = 1 if train_mean >= 0 else -1
        selections.append({
            "TestDate": nd(dt).strftime("%Y-%m-%d"),
            "PriorSignalCount": len(prior),
            "SelectedFactor": factor,
            "TrainMeanSpearman": train_mean,
            "Direction": direction,
            "PriorTrainingRows": len(training),
        })

        q = panels.get(dt)
        if q is None or q.empty:
            exclusions.append({"DateSignal": dt, "Reason": "missing_current_panel"})
            continue
        base, _ = P12.build_target(snapshots[dt], TOPN, {})
        base = set(map(str, base))
        q = q.copy()
        q["F80Target"] = q.Ticker.astype(str).isin(base)
        q["RuleScore"] = direction * pd.to_numeric(q[factor], errors="coerce")
        f80_all = q[q.F80Target]
        f80 = f80_all.dropna(subset=["RuleScore"]).sort_values("RuleScore", ascending=True)
        outside = q[~q.F80Target].dropna(subset=["RuleScore"]).sort_values("RuleScore", ascending=False)
        nblock = max(1, int(round(TOPN * REPLACEMENT_FRAC)))
        if len(base) != TOPN or len(f80) != TOPN or len(outside) < nblock:
            exclusions.append({
                "DateSignal": dt, "Reason": "incomplete_cross_section",
                "F80TargetCount": len(base), "F80WithFactor": len(f80), "OutsideWithFactor": len(outside),
            })
            continue
        blocked = f80.head(nblock)
        replacement = outside.head(nblock)
        date_rows = []
        failure = None
        for horizon in HORIZONS:
            b = pd.to_numeric(blocked[f"FwdRet_{horizon}D"], errors="coerce")
            a = pd.to_numeric(replacement[f"FwdRet_{horizon}D"], errors="coerce")
            if b.notna().sum() != nblock or a.notna().sum() != nblock:
                failure = {
                    "DateSignal": nd(dt).strftime("%Y-%m-%d"),
                    "Reason": f"missing_forward_returns_H{horizon}",
                    "NBlocked": int(b.notna().sum()),
                    "NReplacement": int(a.notna().sum()),
                }
                break
            blocked_mean = float(b.mean())
            replacement_mean = float(a.mean())
            group_delta = replacement_mean - blocked_mean
            gross_portfolio_delta = REPLACEMENT_FRAC * group_delta
            for cost_bps in COST_BPS_PER_LEG:
                date_rows.append({
                    "DateSignal": nd(dt).strftime("%Y-%m-%d"),
                    "Horizon": horizon,
                    "SelectedFactor": factor,
                    "Direction": direction,
                    "NBlocked": int(b.notna().sum()),
                    "NReplacement": int(a.notna().sum()),
                    "BlockedMeanNextOpen": blocked_mean,
                    "ReplacementMeanNextOpen": replacement_mean,
                    "GroupDelta": group_delta,
                    "PortfolioDeltaGross": gross_portfolio_delta,
                    "CostBpsPerLeg": cost_bps,
                    "PortfolioDeltaNet": portfolio_delta_net(group_delta, REPLACEMENT_FRAC, cost_bps),
                })
        if failure:
            exclusions.append(failure)
        elif len(date_rows) == len(HORIZONS) * len(COST_BPS_PER_LEG):
            results.extend(date_rows)
        else:
            exclusions.append({"DateSignal": nd(dt).strftime("%Y-%m-%d"), "Reason": "forward_return_gate_failed"})

    selection_df = pd.DataFrame(selections)
    result_df = pd.DataFrame(results)
    exclusion_df = pd.DataFrame(exclusions)
    selection_df.to_csv(OUTDIR / "phase372_walkforward_selections.csv", index=False)
    result_df.to_csv(OUTDIR / "phase372_next_open_cost_sensitivity.csv", index=False)
    exclusion_df.to_csv(OUTDIR / "phase372_exclusions.csv", index=False)

    summary_rows, bootstrap_rows = [], []
    if not result_df.empty:
        for horizon in HORIZONS:
            gross = result_df[(result_df.Horizon == horizon) & (result_df.CostBpsPerLeg == 0)]
            for cost_bps in COST_BPS_PER_LEG:
                group = result_df[(result_df.Horizon == horizon) & (result_df.CostBpsPerLeg == cost_bps)]
                values = group.PortfolioDeltaNet.dropna().to_numpy(dtype=float)
                low, high = bootstrap_mean_interval(values, seed=BOOTSTRAP_SEED + horizon + cost_bps)
                loo = [float(np.delete(values, i).mean()) for i in range(len(values)) if len(values) > 1]
                bootstrap_rows.append({
                    "Horizon": horizon,
                    "CostBpsPerLeg": cost_bps,
                    "N_TestDates": len(values),
                    "MeanPortfolioDeltaNet": float(np.mean(values)) if len(values) else np.nan,
                    "MedianPortfolioDeltaNet": float(np.median(values)) if len(values) else np.nan,
                    "PositiveDates": int((values > 0).sum()),
                    "Bootstrap95Low": low,
                    "Bootstrap95High": high,
                    "LOO_Mean_Min": min(loo) if loo else np.nan,
                    "LOO_Mean_Max": max(loo) if loo else np.nan,
                })
            gross_values = gross.PortfolioDeltaGross.dropna().to_numpy(dtype=float)
            summary_rows.append({
                "Horizon": horizon,
                "N_TestDates": len(gross_values),
                "MeanGroupDelta": float(gross.GroupDelta.mean()) if len(gross) else np.nan,
                "MedianGroupDelta": float(gross.GroupDelta.median()) if len(gross) else np.nan,
                "PositiveDatesGross": int((gross_values > 0).sum()),
                "MeanPortfolioDeltaGross": float(gross_values.mean()) if len(gross_values) else np.nan,
            })
    pd.DataFrame(summary_rows).to_csv(OUTDIR / "phase372_summary.csv", index=False)
    pd.DataFrame(bootstrap_rows).to_csv(OUTDIR / "phase372_bootstrap_loo_summary.csv", index=False)

    observed_dates = sorted(result_df.DateSignal.unique().tolist()) if not result_df.empty else []
    audit = {
        "phase": 372,
        "status": "COMPLETED_DIAGNOSTIC" if len(observed_dates) == len(EXPECTED_TEST_DATES) else "INCOMPLETE_PSEUDO_OOS_COVERAGE",
        "entry_rule": "next common trading session open after FINRA signal date",
        "exit_rule": "close of the 5th/10th/20th entry session",
        "universe_size_valid": len(data),
        "universe_failures": len(failures),
        "universe_recovered_after_retry": recovered,
        "fixed_price_window_start": FIXED_PRICE_START,
        "fixed_price_window_end_exclusive": FIXED_PRICE_END,
        "train_signals": len(train_all),
        "finra_eligible_train_signals": len(eligible),
        "train_end": nd(train_end).strftime("%Y-%m-%d"),
        "pseudo_oos_test_dates_expected": list(EXPECTED_TEST_DATES),
        "pseudo_oos_test_dates_observed": observed_dates,
        "pseudo_oos_dates_completed": len(observed_dates),
        "final_oos_holdout_signals": len(holdout),
        "holdout_used": False,
        "forward_returns_used": True,
        "prior_outcomes_maturity_checked": True,
        "finra_files_needed": len(needed),
        "finra_files_available": int(pd.Series([x["Status"] for x in audit]).astype(str).str.startswith(("downloaded", "cached")).sum()),
        "finra_duplicate_date_symbol_rows_before_dedup": duplicate_keys,
        "min_prior_signals": MIN_PRIOR_SIGNALS,
        "horizons": list(HORIZONS),
        "cost_sensitivity_bps_per_leg": list(COST_BPS_PER_LEG),
        "bootstrap_reps": BOOTSTRAP_REPS,
        "signal_admitted": False,
        "f80_changed": False,
        "production_changed": False,
        "legacy_holdout_reused": False,
        "raw_finra_files_in_artifact": False,
        "no_lookahead_controls": {
            "short_flow_cutoff": "signal date inclusive; FINRA files arrive after regular close",
            "feature_cutoff": "signal date close",
            "entry": "next common session open",
            "selection": "prior signal dates only",
            "prior_return_maturity": "exit date must be on or before current test signal date",
        },
        "limitations": [
            "This is a corrected training-era pseudo-OOS retest, not a pristine final OOS test.",
            "The six Phase 20B final-OOS dates were not used.",
            "Flat cost sensitivity is not a spread, borrow or market-impact model.",
            "Current Yahoo Finance history is used for price outcomes; historical universe survivorship and data-vintage limitations remain.",
        ],
    }
    (OUTDIR / "phase372_audit.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    print(json.dumps(audit, indent=2, default=str), flush=True)
    print(pd.DataFrame(summary_rows).to_string(index=False), flush=True)
    if len(observed_dates) != len(EXPECTED_TEST_DATES):
        raise SystemExit("Phase 372 did not complete all 12 frozen pseudo-OOS dates")
    print(f"Runtime={time.time()-start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
