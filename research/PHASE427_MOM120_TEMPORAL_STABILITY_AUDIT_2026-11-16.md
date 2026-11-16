# Phase 427 — MOM120 temporal concentration and recent-period stability audit

**Date:** 2026-11-16 UTC  
**Disposition:** retain MOM120 as a research-only candidate; do not promote.  
**Source:** Phase 426 matched-exposure C20 paired daily-return artifact only. No new market prices or universe data were acquired.

## Executive finding

Phase 426's positive cumulative MOM120-minus-LTM result is real within its historical diagnostic, but it is **temporally concentrated**. Of the total cumulative log-relative wealth gain, 91.8% accrued in 2024–2025. The 2026 year-to-date segment through 2026-11-13 contributes only 8.2% and does not show statistically clear positive paired excess under an HAC estimator with an 80-session lag.

The latest 75-session rebalance-cycle fragment also underperformed LTM. This does not prove that the momentum effect has disappeared; it means the historical result is not sufficiently stable to support a model change.

## Reproducibility and source integrity

- Source Actions run: [43789923762](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43789923762), final Phase 426 run.
- Source artifact: [phase426-mom120-frozen-f80-exact-engine, artifact 14191029663](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43789923762/artifacts/14191029663).
- Input: paired_exposure_matched_excess_C20.csv, 721 paired daily observations from 2024-01-02 through 2026-11-13.
- Input SHA-256: 4ac2215f18ba67d0f5b21a5549928a34fc37872e4a8361e42a4ea3112f846b1d.
- Phase 427 script recomputes the paired daily, calendar-year, and rebalance-cycle summaries from that CSV. It does not download prices, tune parameters, or use the holdout.

## Overall matched-exposure result

| Metric | Phase 426 C20 result |
|---|---:|
| Paired daily observations | 721 |
| Mean daily MOM120 − LTM excess | 5.1686 bps |
| Cumulative log-relative wealth | 0.36578 |
| Relative wealth multiple (MOM120 / LTM) | 1.4416x |
| Relative wealth gain | 44.16% |

This is a relative comparison, not a claim that the strategy itself earned a 44.16% return. Phase 426 reported matched-exposure final multiples of 2.126x for MOM120 and 1.474x for LTM, but the 2024+ period had already been examined in Phases 29/30 and is not a fresh holdout.

## Calendar-year concentration

| Segment | Sessions | Mean daily excess | HAC(80) t | HAC(80) 95% CI |
|---|---:|---:|---:|---:|
| 2024 | 252 | 7.10 bps | 3.30 | +2.88 to +11.32 bps |
| 2025 | 250 | 6.39 bps | 3.22 | +2.50 to +10.28 bps |
| 2026 through Nov 13 | 219 | 1.55 bps | 0.75 | −2.52 to +5.63 bps |

2024 and 2025 account for **91.81%** of cumulative log-relative wealth gain. The 2026 segment accounts for **8.19%**. The 2026 interval is not statistically distinguishable from zero using the stated HAC(80) diagnostic.

These calendar-year splits are post-hoc stability diagnostics on a previously examined period. Their HAC intervals are not a fresh confirmatory test and are not corrected for multiple inspection.

## Rebalance-cycle concentration

There are ten OOS cycle fragments:
- Eight complete 80-session cycles, all positive.
- The initial six-session boundary fragment was negative.
- The latest 75-session boundary fragment (2026-07-31 to 2026-11-13) was negative.

Across all ten fragments, 8/10 were positive. A one-sided exact sign test gives **p = 0.0547**, which does not pass a 5% threshold. The eight complete cycles being positive is descriptive only: consecutive cycles are not guaranteed independent and selecting only complete cycles must not be used to manufacture significance.

The last 75-session fragment's compounded difference was approximately −0.875 percentage points (MOM120 minus LTM). This reinforces the weaker 2026 calendar-year result.

## Interpretation

1. The Phase 426 gross-exposure control and accounting invariants remain useful; Phase 427 does not invalidate the mechanical reconciliation.
2. The apparent advantage is not evenly distributed over time. Most of the relative gain came in 2024–2025.
3. The current 2026 segment and most recent incomplete cycle do not confirm continued incremental advantage.
4. MOM120 is a momentum reweighting already contained in LTM, not an institutional-flow or Smart Money source.
5. Phase 426's 2024+ data are not a fresh holdout; the 335-name universe and Yahoo history are not point-in-time or survivorship-free. Only ten cycle fragments exist, with serial dependence.

## Decision and next steps

**Decision: PROMISING_BUT_TEMPORALLY_CONCENTRATED_NO_PROMOTION.**

- Keep F80_TOP20_PARTIAL50_BASELINE_C20 frozen.
- Do not promote MOM120 or change the LTM composite.
- Continue prospective shadow observation without parameter tuning.
- Before any later promotion, require a genuinely new chronological OOS period, point-in-time universe/security identity, and a pre-registered conditional/residual test of R120 versus the full LTM composite.
- Continue the independent Smart Money source gates (CFTC TFF, FINRA, Form 4/13D/G, options); Phase 426/427 does not validate those sources.

No holdout was used. No production, universe, parameter, capital, exposure policy, or baseline change was made.
