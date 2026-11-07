# Phase 100 — FINRA short-flow walk-forward decision

Date: 2026-11-05  
Source run: [Phase 20C FINRA walk-forward](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254)  
Artifact: [phase20c-finra-walkforward](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254/artifacts/12562171831)  
Status: **KILL CURRENT STOCK-SELECTION IMPLEMENTATION; preserve final holdout unused.**

## 1. Diagnostic sample

The completed Phase 20C run reported:

- Valid current-universe names: 329; failures: 6.
- FINRA-eligible training signals: 20.
- Pseudo-OOS test dates: 12.
- Final holdout signals: 6, not evaluated.
- Training cutoff: 2024-10-30.
- FINRA CNMS history start: 2018-08-01.
- Files requested: 2,020 calendar dates; files returned: 1,382. This ratio is **not** a valid coverage rate because the denominator includes weekends and market holidays; a trading-calendar reconciliation was not produced.

The tested universe was the legacy 335-name list. As now clarified by the user, that list was manually selected arbitrarily and has no formal sampling rule. These results are conditional on that list and cannot be generalized to the U.S. equity market.

## 2. Pseudo-OOS results

The reported outcome is replacement portfolio minus the blocked/bottom F80 names, in decimal return units:

| Horizon | Test dates | Mean delta | Median delta | Positive dates | Positive rate | Std. dev. |
|---|---:|---:|---:|---:|---:|---:|
| 5 sessions | 12 | +0.141% | -0.050% | 5 | 41.7% | 5.27% |
| 10 sessions | 12 | -1.687% | -1.837% | 3 | 25.0% | 7.50% |
| 20 sessions | 12 | -0.858% | -0.333% | 5 | 41.7% | 16.53% |

Training-selected factor frequency across the 12 pseudo-OOS dates:

- SHORT_RATIO_Z20: 6
- SHORT_EXEMPT_RATIO: 5
- SHORT_RATIO_PERSIST20: 1

The weak 5-session mean is offset by a negative median and a 41.7% positive-date rate. The 10- and 20-session results are negative. Factor selection also changes across dates. The run did not provide block-bootstrap inference, issuer-clustered uncertainty, or leave-one-out stability.

## 3. Decision

**Kill this current FINRA daily short-volume-ratio feature-selection/replacement implementation for stock selection.**

Reasons:

1. No stable positive pseudo-OOS spread across horizons.
2. The apparent short-horizon mean is not supported by its median or hit rate.
3. Longer horizons are negative, with substantial dispersion.
4. The selected factor is not stable across pseudo-OOS dates.
5. The current 335-name universe is arbitrary and not point-in-time representative.
6. The output does not establish that daily short-sale volume identifies informed buyers, beneficial owners, or persistent short positions. FINRA short-sale volume is not short interest.

The six final holdout signals remain unused. Do not consume them merely to obtain another result after the pseudo-OOS diagnostic failed. Reopen only if a materially different, pre-registered mechanism and a valid broad/PIT universe become available.

This decision does not invalidate every possible use of FINRA data. Weekly ATS/non-ATS off-exchange aggregates are a distinct market-structure source and are being revalidated separately in Phase 100. The prior Phase 31 flow × short-interest divergence remains killed as independent alpha.

## 4. Baseline and permissions

- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No feature or portfolio parameter was changed.
- No final OOS result was inspected.
- No vendor was contacted and no data was purchased.
- No production signal was added.
