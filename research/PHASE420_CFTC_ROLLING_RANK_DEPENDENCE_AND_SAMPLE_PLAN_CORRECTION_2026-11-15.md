# Phase 420 — CFTC rolling-rank dependence and sample-plan correction

**Audit time:** 2026-11-15 17:34 UTC  
**Main HEAD before this report:** `6c7e26a714078ff1440023140d5bc9aec48ca0b6`  
**Disposition:** Phase 419's independent-binomial event-count probabilities and calendar estimate are superseded. Phase 387's preregistered feature, thresholds, outcome, sample gates and inference rules remain unchanged. No CFTC historical data, return test or signal was added.

## 1. Repository and Actions preflight

- Inspected the latest 100 Actions runs (7,658 total reported), latest SEC/CFTC/Phase 411 runs, jobs, step summaries, logs and artifacts, the Phase 387 preregistration, Phase 419 report, current research state, workflow directory, branch pages and open PRs.
- Latest 100 runs: 62 success, 37 failure, 1 cancelled; zero queued, in-progress, waiting or requested. No workflow was started, rerun or duplicated.
- Mainline workflow inventory: 63 files. Branch inventory: 261 across three pages. Open PRs: 56 (52 draft, 4 ready); no PR was merged or retargeted.

### Relevant run evidence

| Run | Event / result | Evidence |
|---|---|---|
| [43709012759](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43709012759) | SEC Form 144 schedule / success | Both jobs passed; offline regression 15/15; live receipt 2026-11-15 11:28:22 UTC; 55 feed observations; zero new feed entries/accessions/events; no detected feed-window gap; artifact [14159294388](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43709012759/artifacts/14159294388). |
| [43681298839](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43681298839) | Phase 411 PR regression / success | 17/17 offline tests; no live CFTC request. |
| [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) | Phase 384 CFTC push/bootstrap / success | 11/11 tests; 3,035 historical warm-up rows; zero signal-eligible historical rows; artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705). This is not a scheduled prospective capture. |

No later SEC schedule run is visible after 11:28:27 UTC in the latest 100 runs, despite the hourly `:37` cron. This is an unobserved schedule interval, not proof of a disabled workflow or a known root cause. Do not manually dispatch or duplicate polling.

The official CFTC schedule currently lists **Monday 2026-11-16 at 3:30 p.m. ET (20:30 UTC)** as a holiday-delayed release. The TFF Futures Only dataset still reports last updated 2026-11-06. Phase 384's next expected poll is Monday at 22:15 UTC. Sources: [CFTC release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm), [TFF Futures Only](https://publicreporting.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if), [semiweekly announcement](https://www.cftc.gov/PressRoom/PressReleases/9316-26).

## 2. Methodological correction to Phase 419

Phase 387 defines the high state using the empirical percentile of the current observation against the **prior 52 valid prospective weekly observations**:

`P_t = count(x_j < x_t)/52 + 0.5\,count(x_j = x_t)/52`

with `HIGH = P_t >= 0.80`. Under IID continuous inputs with no ties, this is equivalent to at least **42 of the 52 prior observations being below the current observation**, and the marginal high-state probability is `11/53 = 20.7547%`.

Phase 419 applied a Binomial(n, 11/53) tail to the number of high states. That assumes the rolling high-state indicators are independent Bernoulli observations. They are not: adjacent indicators use heavily overlapping 52-observation reference windows. Even when the underlying input series is IID, the rolling-rank indicators have small negative dependence across the overlapping window, materially reducing the variance of the event count. The independent-binomial tail therefore misstates the event-count gate probability.

A second calendar omission was identified: Phase 419's total-report estimate did not include (a) the first 52 prospective reports needed to create the first valid percentile, or (b) the approximately four additional weekly intervals needed for the final evaluation outcome to mature.

## 3. Reproducible synthetic rolling-rank simulation

Added `research/phase420_cftc_rolling_rank_event_count_simulation.py`.

- 200,000 independent synthetic paths; NumPy `default_rng(20261115)`; float64 continuous IID inputs.
- 52-observation prior-only rolling reference; current observation excluded.
- High state iff at least 42 prior values are below the current value.
- 316 post-warm-up rolling indicators per path; consecutive training and evaluation blocks are simulated on the same path.
- Wilson 95% intervals are reported for Monte Carlo probabilities.
- No CFTC historical backfill, actual TFF positions, labels, returns or market prices are used.

The simulated marginal high-state rate was 20.7568%, consistent with the theoretical 11/53 reference. The indicator autocorrelation was negative across the overlapping window (lag 13: -0.0043; lag 26: -0.0082; lag 39: -0.0118; lag 51: -0.0153). At 150 evaluation observations, the high-count variance was 8.41 versus 24.67 under an independent Bernoulli model with the same marginal probability (variance ratio 0.34).

### Event-count results

| Consecutive complete-case blocks | Train gate | Evaluation gate | Joint probability | Wilson 95% interval |
|---|---:|---:|---:|---:|
| 111 train + 161 eval | 90.74% | 91.19% | 82.14% | 81.98–82.31% |
| **116 train + 166 eval** | **95.53%** | **95.54%** | **91.11%** | **90.98–91.23%** |
| **120 train + 170 eval** | **97.71%** | **97.61%** | **95.33%** | **95.24–95.42%** |

The training gate is `>=20 high and >=40 non-high`; the evaluation gate is `>=30 high and >=100 non-high`. The non-high constraints had zero failures in 200,000 simulations at the displayed block sizes; the high-event thresholds bind.

For comparison, the independent-binomial approximation gives only 85.33% for 20 high events in 116 observations and 82.80% for 30 high events in 166 observations. The rolling-rank simulation gives 95.53% and 95.54%, respectively. At the hard 150-observation evaluation minimum, the rolling-rank probability of meeting both event counts is 71.37%, versus 62.20% under the independent-binomial approximation.

The joint probability matters: two separate ~90% gate probabilities do not imply a 90% probability of satisfying both sequential gates. The 111+161 plan has only 82.14% joint probability.

## 4. Corrected conditional calendar planning

The first 52 prospective reports are reference warm-up. They do not have a valid `P_t` of their own and are not counted as complete-case high/non-high training observations. For paired baseline/augmented-model comparisons, the conservative planning convention is to use the same complete-case training rows in both models. The Phase 387 wording that warm-up outcomes may enter training is retained as a possible baseline-only use, but such rows cannot satisfy the augmented model's high/non-high event gate or enter a paired common-row comparison.

Assuming the weekly TFF cadence remains in place, no missed captures, and approximately four weekly intervals for each 20-NYSE-session outcome-maturity wait:

- **~90% joint event-count planning:** 52 warm-up + 116 training + 4 training-maturity + 166 evaluation + 4 final-evaluation-maturity = **342 weekly reports (~6.6 years)**.
- **~95% joint event-count planning:** 52 warm-up + 120 training + 4 training-maturity + 170 evaluation + 4 final-evaluation-maturity = **350 weekly reports (~6.7 years)**.

These are conditional event-count planning envelopes, not power calculations, expected completion dates or evidence about actual TFF crowding frequency. Exact outcome maturity must use NYSE session dates, not a hard-coded four-week offset.

## 5. Limitations and decision

1. The IID continuous simulation isolates the rolling-rank mechanics. Real Leveraged Money net-OI may be serially correlated, discrete/tied, regime-dependent, or affected by missing/late reports. The simulated marginal rate and count probabilities are not empirical estimates.
2. No actual historical TFF rows were used to estimate event frequency or serial dependence; Phase 387 continues to prohibit historical archive rows from feature, training, label, return or backtest use.
3. This is not a statistical-power analysis for the drawdown effect and does not change Phase 387's 10,000 paired moving-block bootstrap (block length 4), HAC lag 4, ES/NQ separate reporting, or kill/advance rules.
4. Keep all Phase 387 feature definitions, the 0.80 threshold, training/evaluation event gates, outcomes, chronology and kill rules frozen. Do not use the revised planning numbers to relax any gate.
5. Inspect the first genuine Phase 384 scheduled capture after the 2026-11-16 release. Only reproducible first-receipt observations can enter the prospective ledger. If TFF changes to semiweekly, suspend the weekly hypothesis and preregister a separate cadence-specific design.

## 6. Strategy controls

- No CFTC historical backfill was used in this simulation.
- No forward-return, alpha, OOS, bootstrap, LOO or holdout test was run.
- No source or signal was admitted.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged.
- No data purchase, vendor contact, credential change, manual dispatch or workflow modification occurred.
