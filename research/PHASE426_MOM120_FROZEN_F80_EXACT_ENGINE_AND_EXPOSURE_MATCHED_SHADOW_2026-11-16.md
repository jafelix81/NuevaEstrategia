# Phase 426 — MOM120 versus frozen F80: exact-engine and exposure-matched shadow test

**Date:** 2026-11-16  
**Status:** Promising historical diagnostic; prospective confirmation required  
**Decision:** \`PROMISING_HISTORICAL_DIAGNOSTIC_REQUIRES_PROSPECTIVE_CONFIRMATION\`

## Executive result

The Phase 29 candidate, positive cross-sectional \`rank_R120\` (MOM120), outperformed the frozen LTM ranking in a corrected portfolio comparison using the exact Phase 11 v4 state machine. The advantage remained after a separate shadow simulation forced both rankings to the same gross exposure at every daily open and charged the same transaction-cost schedule to both.

This is the first materially positive portfolio-level result for MOM120 relative to the frozen LTM comparator. It is **not** a production promotion: the 2024+ window has already been examined in Phase 29/30, the 335-name universe is not point-in-time, and the OOS portfolio has only nine 80-session signal refreshes.

MOM120 is a momentum reweighting, not evidence of institutional or informed trading. It is already one of the four components of the LTM composite.

## Why this retest was necessary

Phase 29 selected MOM120 as a candidate using chronological discovery/validation and a later 2024+ signal-level OOS. Its 20-session validation was weak: mean IC was approximately 0.009, Q10–Q1 spread approximately 0.12%, and partial IC slightly negative. The later signal-level OOS was positive, but contained only 33 signal dates.

The corrected Phase 30 run (run 40126095357) did not reproduce the frozen F80 engine exactly. Its standalone simulator used a different state machine, a different signal-calendar offset, and an adjusted-price convention that did not match Phase 11 v4. Its near-zero incremental result is retained as an audit record, but it is not the decisive frozen-baseline comparison.

Phase 426 therefore imports the exact Phase 11 v4 implementation, without editing it:
- \`build_target\` and \`execute_rebalance\` are reused unchanged.
- The frozen LTM signal is the average cross-sectional percentile rank of R100, R120, R140 and R160.
- MOM120 is the positive cross-sectional percentile rank of R120, fixed before the 2024+ evaluation.
- Both use the same 80-session signal calendar, TOP20, PARTIAL50, 20% maximum entry weight, 100% gross cap, $1,000 starting capital and next-session-open execution.
- The Phase 11 v4 price convention is preserved (\`auto_adjust=False\`).
- Holding periods remain variable; no fixed minimum or maximum holding period is imposed.

## Data and chronology

| Item | Result |
|---|---:|
| Configured universe | 335 |
| Loaded universe | 335 |
| Failed tickers | 0 |
| First session | 2016-01-04 |
| Last session | 2026-11-13 |
| Cross-sectional snapshots | 2,573 |
| OOS daily observations | 721 |
| OOS period | 2024-01-02 to 2026-11-13 |
| OOS 80-session signal refreshes | 9 |
| Costs tested | 10 / 20 / 50 bps per side |

Signals use information available through close \(t\); execution is modeled at the next session's open. No OOS parameter tuning or candidate reselection was performed. The separate frozen holdout was not used.

**Important data limitation:** the current 335-name universe is not a point-in-time security master and is not survivorship-free. Yahoo's current historical price series is not a vintage archive. These results are therefore comparative research evidence, not an investability claim.

## Raw exact-engine comparison

At 20 bps per side, the unadjusted exact-engine results were:

| Metric | Frozen LTM | MOM120 |
|---|---:|---:|
| OOS final multiple | 1.399x | 2.296x |
| Annualized volatility | 29.44% | 33.61% |
| Daily Sharpe | 0.547 | 1.033 |
| Maximum drawdown | -29.88% | -31.58% |
| Average close gross exposure | 63.30% | 68.52% |
| Annualized turnover | 2.49x | 2.36x |

The raw paired daily excess was about 7.39 bps/day, but the candidate carried approximately 5.2 percentage points more average gross exposure. This raw result alone cannot isolate ranking quality.

## Exposure-matched shadow simulation

To address the exposure mismatch, a separate research-only shadow simulation was run for both rankings.

The common gross target was set to **59.8667%**, calculated solely from the frozen LTM C20 engine's 2016–2023 training-period average gross exposure. The target was fixed before the 2024+ OOS period. At every daily open, both portfolios were normalized to that same gross target. The same 10/20/50 bps per-side cost assumptions were charged on both selection trades and gross-normalization trades.

This is a controlled shadow comparison, not a change to the frozen F80 production engine.

### C20 results

| Metric | Frozen LTM | MOM120 |
|---|---:|---:|
| OOS final multiple | 1.474x | 2.126x |
| Mean daily return | 0.0696% | 0.1213% |
| Annualized volatility | 28.12% | 28.95% |
| Daily Sharpe | 0.624 | 1.056 |
| Maximum drawdown | -29.39% | -27.20% |
| Average close gross exposure | 59.853% | 59.864% |
| Maximum close gross exposure | 63.83% | 63.56% |
| Average positions | 20.0 | 20.0 |
| Annualized turnover | 3.88x | 3.82x |
| Costs / average equity | 2.22% | 2.18% |

The open gross target was matched to machine precision. Average close gross exposure differed by only about 0.011 percentage points. Both portfolios remained below the 20% entry and marked-position limits in this shadow run; no fresh close marks were missing.

### Paired incremental result

| Cost | Mean daily excess (MOM120 − LTM) | 80-session block-bootstrap 95% CI |
|---|---:|---:|
| 10 bps/side | 5.165 bps | 2.452 to 7.894 bps |
| 20 bps/side | 5.169 bps | 2.463 to 7.922 bps |
| 50 bps/side | 5.179 bps | 2.409 to 7.939 bps |

At C20:
- HAC t-statistic with 80-day lag: 3.79.
- Circular block-bootstrap 95% CIs remained positive for block lengths 20, 40, 80, 120 and 160 sessions.
- Daily leave-one-out mean remained positive for 100% of omitted observations.
- Eight of ten OOS rebalance cycles had positive compounded excess.
- Leave-one-cycle-out average excess remained positive for all ten omissions.

The cycle count is small. Daily observations within each 80-session holding cycle are not independent, so the block-80/160 and cycle-level results are more informative than a naive IID daily test, but they do not create additional independent market regimes.

## Redundancy with the frozen LTM composite

MOM120 is highly correlated with the existing LTM signal:
- Mean cross-sectional Spearman correlation on OOS rebalance dates: **0.9481**.
- Mean overlap in the selected TOP20: **15.78 of 20 names**.
- Mean TOP20 Jaccard overlap: **0.6622**.

This is not an independent data source. It is evidence that emphasizing the 120-session momentum component may have improved this historical portfolio comparison. A conditional/residual test is still needed to establish how much genuinely incremental information MOM120 contains after controlling for the full LTM composite.

## Integrity checks

The final GitHub Actions run completed successfully. All 335 tickers loaded, and the exact-engine and exposure-matched accounting checks passed.

For the exposure-matched shadow:
- Maximum open gross-target error: below \(5\times10^{-16}\).
- Maximum accounting identity error: below \(2\times10^{-12}\).
- Maximum return-decomposition error: below \(5\times10^{-16}\).
- Maximum close gross exposure: 63.83%.
- Maximum close position weight: 17.74%.
- Missing fresh close marks: zero.
- All trade executions occurred after the prior signal/close timestamp.
- Cash remained nonnegative and equity remained positive.

## Interpretation and decision

**Decision: promising historical diagnostic; do not promote yet.**

The MOM120 advantage survived:
1. Exact reuse of the frozen F80 state machine.
2. Equal gross exposure at every daily open.
3. Identical per-side cost assumptions, including costs on exposure-normalization trades.
4. Block-bootstrap sensitivity up to 160 sessions.
5. Daily and rebalance-cycle leave-one-out checks.

That is meaningful evidence, but not enough to change the strategy:
- 2024+ was already examined in Phase 29/30; this is not a fresh untouched holdout.
- Only nine OOS 80-session signal refreshes are available.
- The 335-name universe is not point-in-time and has survivorship risk.
- The Phase 29 2021–2023 validation was weak.
- MOM120 is highly correlated with LTM and is not a new smart-money source.

### Next research steps

1. Keep F80 frozen and prospectively shadow-track MOM120 without parameter tuning.
2. Reconstruct or obtain a point-in-time universe/security master, including delisted constituents, before making an investability claim.
3. Test MOM120 residualized against LTM to distinguish genuine incremental information from simple reweighting.
4. Continue the separate SEC/FINRA/CFTC/options feasibility work; this result does not validate any institutional-flow hypothesis.

No production code, baseline parameters, universe, capital, exposure policy or holdout was changed.

## Reproducibility

- Final Actions run: [43789923762](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43789923762)
- Artifact: [phase426-mom120-frozen-f80-exact-engine](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43789923762/artifacts/14191029663)
- Script: [phase426_mom120_frozen_f80_engine_audit.py](https://github.com/jafelix81/NuevaEstrategia/blob/main/research/phase426_mom120_frozen_f80_engine_audit.py)
- Workflow: [phase426_mom120_frozen_f80_engine_audit.yml](https://github.com/jafelix81/NuevaEstrategia/blob/main/.github/workflows/phase426_mom120_frozen_f80_engine_audit.yml)
- Frozen engine blob SHA: \`06dc0ece5dd4a3def6a7e2b603564bfc588c0b27\`
- Source main commit used for the experiment: \`2d7d163da1988e923bdcc7958daefc33d1a38536\`
