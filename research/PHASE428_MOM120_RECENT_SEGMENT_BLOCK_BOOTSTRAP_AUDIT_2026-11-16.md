# Phase 428 — MOM120 recent-segment block-bootstrap sensitivity audit

**Date:** 2026-11-16 UTC  
**Disposition:** retain MOM120 as research-only; no promotion.  
**Purpose:** independently check whether Phase 427's 2026 non-significant result depends on the HAC(80) estimator alone.

## Executive finding

The 2026 paired excess of MOM120 over LTM is **+1.553 bps per session**, but it is not statistically distinguishable from zero under any of the tested circular block-bootstrap lengths (20, 40, 60 sessions) or Newey–West/Bartlett HAC lags (20, 40, 60, 80 sessions). Every 2026 interval includes zero.

By contrast, the previously inspected 2024 and 2025 segments remain positive under the same exploratory procedures. This confirms that the positive full-period average is concentrated in earlier years and that the recent segment does not independently confirm the effect. It does **not** establish a statistically significant structural break or prove that momentum has stopped working.

## Immutable input and reproducibility

- Source Actions run: [43789923762](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43789923762).
- Source artifact: [phase426-mom120-frozen-f80-exact-engine, artifact 14191029663](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43789923762/artifacts/14191029663).
- Input: `paired_exposure_matched_excess_C20.csv`, 721 paired daily observations, 2024-01-02 through 2026-11-13.
- Input SHA-256: `4ac2215f18ba67d0f5b21a5549928a34fc37872e4a8361e42a4ea3112f846b1d`.
- The input contains only dates, paired LTM/MOM120 daily portfolio returns and cycle IDs. No new prices, security universe, signals, or trades were downloaded or reconstructed.
- The script was compiled and run twice with 50,000 bootstrap replicates per segment/block. Both executions produced the identical report SHA-256: `50212facaa15ca4881f30df1cc09a6a5d499fa6844054f07de0d19beb7f452a6`.

## Segment results

Mean daily excess is `DailyReturn_mom - DailyReturn_ltm`.

| Segment | Sessions | Mean excess | Positive-session fraction |
|---|---:|---:|---:|
| 2024 | 252 | +7.099 bps | 55.16% |
| 2025 | 250 | +6.390 bps | 52.40% |
| 2026 through Nov 13 | 219 | +1.553 bps | 53.42% |
| Full sample | 721 | +5.169 bps | 53.68% |

### Circular block-bootstrap 95% intervals (bps/session)

| Segment | 20-session blocks | 40-session blocks | 60-session blocks |
|---|---:|---:|---:|
| 2024 | [2.426, 12.497] | [2.871, 12.560] | [3.256, 11.763] |
| 2025 | [1.765, 11.030] | [2.303, 10.728] | [2.158, 10.736] |
| 2026 | **[-2.440, 6.085]** | **[-2.378, 5.609]** | **[-2.049, 5.162]** |
| Full sample | [2.426, 8.087] | [2.386, 8.137] | [2.476, 7.942] |

### HAC lag sensitivity for 2026

| HAC lag | t-statistic | 95% interval (bps/session) |
|---:|---:|---:|
| 20 | 0.706 | [-2.759, 5.865] |
| 40 | 0.718 | [-2.684, 5.789] |
| 60 | 0.749 | [-2.509, 5.614] |
| 80 | 0.747 | [-2.523, 5.629] |

## Interpretation

1. The full-sample positive bootstrap interval is not a sufficient reason to promote MOM120: it pools the strong 2024–2025 segments with the weaker 2026 segment.
2. The 2026 result is robustly inconclusive across the tested dependence treatments; the point estimate remains positive, but uncertainty is wide.
3. The 2026 segment has only 219 sessions. At 60-session block length, each resample contains roughly four sampled blocks; the resulting interval is a sensitivity diagnostic, not a large-regime sample.
4. All periods are post-hoc slices of a 2024+ window already examined in Phases 29/30. These are not fresh confirmatory tests, not multiple-testing adjusted, and not a new holdout.
5. The 335-name universe is not point-in-time or survivorship-free. MOM120 is a momentum reweighting, not a Smart Money or institutional-flow source.

## Decision

**Decision: NO_PROMOTION_RECENT_SEGMENT_UNCONFIRMED.**

- Keep `F80_TOP20_PARTIAL50_BASELINE_C20` frozen.
- Do not promote MOM120 or alter LTM weights.
- Continue only prospective shadow observation and, before any future decision, require a preregistered residual/conditional test of R120 against the complete LTM composite using a point-in-time security master and a genuinely new chronological OOS period.
- Do not use the already-inspected 2024–2026 data as a fresh holdout.

No production, universe, parameters, capital, exposure, or holdout was changed. No Smart Money source or new signal was admitted.
