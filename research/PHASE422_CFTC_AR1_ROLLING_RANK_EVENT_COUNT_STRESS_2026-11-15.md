# Phase 422 — CFTC rolling-rank event-count stress under serial persistence

**Audit time:** 2026-11-15 19:58 UTC  
**Main HEAD before this phase:** `bd4d566f47fe6570985906ca2cee7773fb4eb657`  
**Disposition:** Phase 420/421's IID event-count calendar is not robust to plausible serial-persistence stress. Keep Phase 387 preregistration unchanged; use longer conditional planning envelopes only as a sensitivity, not as a revised signal rule or empirical forecast.

## 1. Actions and source preflight

- Rechecked the latest 100 Actions runs (7,659 total): 62 success, 37 failure, 1 cancelled; zero queued/in-progress/waiting/requested.
- Inspected all 261 branches across three pages, 56 open PRs and all 63 workflow files. No workflow was started or rerun; no PR was changed.
- Latest run remains SEC Form 144 schedule run [43743993846](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43743993846), created 2026-11-15 17:57:31 UTC and completed successfully. Both jobs passed; offline regression 15/15. Live receipt 17:58:03 UTC; 55 feed observations; zero new accessions/events/candidate matches/XML resolutions; no feed-window gap detected at that poll. Artifact [14173342433](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43743993846/artifacts/14173342433), SHA-256 `0f00cbcc4b2809f18cd8e7c0292b67713c21d55015aff6c06452d56031e50a10`.
- The nominal 18:37 and 19:37 UTC SEC schedule slots are not visible in the latest run list as of 19:58 UTC. This is an unobserved schedule interval, not proof of workflow deactivation or a known root cause. Do not dispatch manually or edit the cron.
- CFTC Phase 384's latest run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) remains a branch-push bootstrap: 11/11 tests, 3,035 historical rows, zero signal-eligible rows; artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705). No prospective scheduled TFF observation exists yet.
- The first expected post-release Phase 384 poll remains Monday 2026-11-16 at 22:15 UTC, after the CFTC's scheduled 20:30 UTC publication. The CFTC's October 27 announcement describes a planned twice-weekly COT rollout by year-end, but does not specify whether TFF Futures Only is included; Phase 411 correctly treats this as an announced possibility, not an observed TFF cadence change. See [CFTC announcement](https://www.cftc.gov/PressRoom/PressReleases/9316-26) and [current TFF dataset](https://publicreportinghub.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if).

## 2. Why another sensitivity was necessary

Phase 420/421 corrected the overlapping-window dependence created by the 52-observation rolling rank under IID continuous raw inputs. That was a meaningful correction, but the resulting 342-report (~6.6-year) and 350-report (~6.7-year) calendar envelopes still assume the underlying positioning series itself is serially independent.

CFTC positioning is a persistent stock/position measure. Without using the historical CFTC archive for Phase 387 features or labels, the prudent next design check is to stress the event-count gates under explicit synthetic persistence assumptions. The persistence parameter below is not estimated from CFTC data.

## 3. Reproducible simulation

Added `research/phase422_cftc_ar1_rolling_rank_event_count_stress.py`.

- 100,000 independent synthetic paths per persistence setting; 500,000 paths total.
- Stationary Gaussian AR(1) raw series with unit marginal variance and `phi ∈ {0.0, 0.2, 0.4, 0.6, 0.8}`.
- Base seed `20261116`; each phi uses `base_seed + round(1000 × phi)`; chunk size 5,000.
- Each HIGH state is computed strictly from the prior 52 raw observations; HIGH iff at least 42 of those 52 values are strictly below the current value. Under this continuous simulation, ties have probability zero and this is equivalent to the preregistered mid-rank threshold ≥0.80.
- The 4-report training-outcome maturity gap is excluded from both event-count blocks; its raw observations still enter later rolling reference windows.
- Training gates remain ≥20 HIGH and ≥40 non-HIGH; evaluation gates remain ≥30 HIGH and ≥100 non-HIGH.
- Wilson 95% Monte Carlo intervals are reported for each joint gate probability.
- No CFTC archive rows, prices, forward returns, labels, market data or legacy holdout are read.

## 4. Results

The HIGH-event rate rises only modestly, but the HIGH indicator becomes increasingly clustered as raw-series persistence rises.

| AR(1) phi | HIGH rate | HIGH-indicator lag-1 correlation | 116+166 | 120+170 | 135+185 | 140+190 |
|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 20.763% | -0.000 | 91.111% | 95.322% | 99.719% | 99.918% |
| 0.2 | 20.866% | 0.104 | 89.041% | 93.884% | 99.551% | 99.818% |
| 0.4 | 21.028% | 0.223 | 85.527% | 90.923% | 99.009% | 99.555% |
| 0.6 | 21.359% | 0.363 | 80.995% | 86.776% | 97.524% | 98.694% |
| 0.8 | 22.296% | 0.540 | 74.788% | 80.256% | 93.437% | 95.775% |

Each probability is a joint pass rate for both the training and evaluation event-count gates. For the worst tested persistence case (`phi=0.8`), the corresponding Wilson 95% intervals are:

- 116+166: 74.518%–75.056%.
- 120+170: 80.008%–80.502%.
- 135+185: 93.282%–93.589%.
- 140+190: 95.649%–95.898%.

The IID reference reproduces Phase 421 closely: the 116+166 plan is 91.111% here versus 91.1355% in the 200,000-path Phase 421 run; 120+170 is 95.322% here versus 95.3600% in Phase 421. Differences are Monte Carlo variation.

### Planning implication

The earlier IID-only 342/350-report envelopes should not be described as robust to serial persistence. At the tested stress points:

- **Conditional ≥90% planning envelope:** 135 training + 185 evaluation observations, with 52 warm-up reports, a 4-report training-maturity gap and 4 final-outcome-maturity reports: **380 weekly reports (~7.3 years)**. At `phi=0.8`, the joint gate probability is 93.437% (Wilson lower bound 93.282%).
- **Conditional ≥95% planning envelope:** 140 training + 190 evaluation observations with the same warm-up/maturity accounting: **390 weekly reports (~7.5 years)**. At `phi=0.8`, the joint gate probability is 95.775% (Wilson lower bound 95.649%).

These are conservative illustrative envelopes over the discrete stress grid, not minimum sample sizes, completion forecasts, empirical CFTC event rates or statistical power. A different persistence process, non-Gaussian tails, ties, regime changes, missing reports or semiweekly cadence could produce different results.

## 5. Interpretation and decision

1. **The IID assumption materially affects planning.** With `phi=0.8`, the old 116+166 and 120+170 plans fall to 74.788% and 80.256% joint event-count feasibility, respectively.
2. **Clustering, not just the marginal HIGH rate, is the main issue.** The simulated HIGH rate changes from 20.763% to 22.296%, while HIGH-indicator lag-1 correlation rises from approximately zero to 0.540.
3. **Do not estimate phi from the historical CFTC archive for Phase 387.** The preregistration continues to prohibit archive rows from signal features, thresholds, training labels, returns and evaluation observations. These AR(1) values are stress assumptions only.
4. **Do not change Phase 387's preregistered feature, 0.80 threshold, 20/40 training gate, 30/100 evaluation gate, 20-session outcome, chronology, bootstrap/HAC or kill rules.** The 20-session outcome is specific to this risk hypothesis and does not impose a holding-period limit on the broader strategy.
5. Once prospective TFF observations exist, actual first-receipt timestamps, report-date cadence and NYSE session dates govern eligibility and outcome maturity. Any semiweekly TFF transition requires a separate preregistration; weekly and semiweekly observations must not be stitched.

## 6. Other source dispositions unchanged

- FINRA T1 remains an ATS/firm venue-concentration source, not investor or beneficial-owner flow; its effective-dated security identity and inactive-price gates remain unresolved.
- Form 4 has a long official archive and accession-level PIT work, but the candidate identity cohorts remain below the 95% security-identity gate; no return test is authorized.
- SEC 13D/G exact-parent retrieval remains blocked until the repository's `SEC_USER_AGENT` Actions secret contains a project identifier and monitored contact email. No SEC request was retried.
- N-PORT raw share-growth remains killed as currently specified; 13F remains parked.
- ORATS, Cboe and OptionMetrics remain conditional; no sample/license/PIT admission or data purchase.

## 7. Controls

- No source or signal admitted.
- No forward-return, alpha, OOS, bootstrap, LOO or holdout test.
- No CFTC historical data used in this simulation.
- No workflow, schedule, branch, PR, credential or vendor setting changed.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged.
