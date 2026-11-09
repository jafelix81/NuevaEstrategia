# Phase 182 — Legacy Smart Money Experiment Validity and Promotion-Gate Audit

**Date:** 2026-11-07  
**Status:** NO LEGACY SMART MONEY SIGNAL PROMOTED  
**Control:** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.  
**Scope:** Static audit of prior FINRA, CFTC and SEC Form 4 experiments, source code, Actions logs and immutable artifacts. No new return test was run.

## Executive decision

The audit found three different reasons not to promote the legacy results:

1. **FINRA short flow:** Phase 20C's chronological pseudo-OOS results are weak and inconsistent, with only 68.42% of required daily files available. Phase 20B has a favorable six-date replacement result, but it is exploratory, has no cost/bootstrapped uncertainty analysis, and uses a final-date set that was also examined by other hypotheses.
2. **CFTC COT:** Phase 23C's walk-forward code does not enforce horizon-specific training-label maturity. A small number of 5-day training labels were not mature before six of the twelve test dates; the reported 20-day training diagnostics include three or four immature labels at every test date. Its performance is quarantined as not strict no-lookahead.
3. **SEC Form 4:** Phase 21C's own bootstrap intervals cross zero at every horizon; mean residual rank correlations after LTM control are negative. The tested insider-buying feature family remains killed for now.

No existing result justifies a change to F80.

## 1. FINRA short flow — Phase 20A/20B/20C

### Phase 20C: chronological pseudo-OOS

Source run: [40098425254](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254) · [Artifact 12562171831](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254/artifacts/12562171831)

The run used 329 valid names from the configured 335, six ticker failures, 20 FINRA-eligible training signal dates, and 12 chronological pseudo-OOS dates inside the training era. It explicitly left six later final-OOS signal dates unevaluated.

| Horizon | Mean replacement − blocked | Median | Positive dates | SD across dates |
|---|---:|---:|---:|---:|
| 5 sessions | +0.1411 pp | −0.0495 pp | 5/12 (41.7%) | 5.273 pp |
| 10 sessions | −1.6865 pp | −1.8368 pp | 3/12 (25.0%) | 7.501 pp |
| 20 sessions | −0.8578 pp | −0.3334 pp | 5/12 (41.7%) | 16.533 pp |

The 5-session mean is small relative to its cross-date dispersion, its median is negative, and fewer than half the dates are positive. The 10- and 20-session means are negative. Factor selection also changes across the twelve dates: SHORT_RATIO_Z20 six times, SHORT_EXEMPT_RATIO five times, and SHORT_RATIO_PERSIST20 once.

Only 1,382 of 2,020 required daily files were available (68.42%). The 98.21% ticker-count coverage does not repair this time-series gap. The phase did not report costs, a bootstrap interval or capacity-adjusted portfolio economics.

**Decision:** no promotion; do not retune the same factor family against the same pseudo-OOS dates.

### Phase 20B: favorable but non-confirmatory final-date comparison

Source run: [39324762076](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39324762076) · [Artifact 12222238141](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39324762076/artifacts/12222238141)

Training selected SHORT_EXEMPT_RATIO, direction −1, from 20 FINRA-eligible training signal dates (mean training Spearman −0.01733). Across six final signal dates, the reported blocked-F80-minus-replacement mean was negative at all horizons:

| Horizon | Blocked − replacement | Pairs |
|---|---:|---:|
| 5 sessions | −2.6652 pp | 24 vs 24 |
| 10 sessions | −1.3073 pp | 24 vs 24 |
| 20 sessions | −2.0878 pp | 20 vs 20 |

The sign favors the replacements, so this is an interesting exploratory observation. It is not a promotion result: only six signal dates, no costs, no bootstrap confidence interval, and the output is a blocked-versus-replacement subset comparison rather than a fully costed portfolio attribution test. The same six dates were also used by Phase 20A and SEC Form 4 Phase 21C.

**Decision:** retain as historical exploratory evidence only. Do not call it independent confirmation and do not reuse those dates for model selection.

### Holdout-integrity correction

The six dates below were evaluated by FINRA Phase 20A/20B and SEC Form 4 Phase 21C:

- 2025-02-25
- 2025-06-20
- 2025-10-14
- 2026-02-09
- 2026-06-04
- 2026-09-29

They are therefore **consumed, not pristine**. Earlier state summaries that described this same six-date set as an untouched final holdout must not be carried forward. Phase 20C itself did not evaluate these six dates, but that does not restore their global independence. Establish a new prospective final holdout only after feature definitions and model-selection rules are frozen.

## 2. CFTC COT — Phase 23C label-maturity audit

Source run: [39375172026](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39375172026) · [Artifact 12243346515](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39375172026/artifacts/12243346515)

Phase 23C used twelve quarterly test dates for NASDAQ/QQQ and S&P 500/SPY. It set KnowledgeDate = ReportDate + 6 calendar days (the following Monday, a conservative proxy) and selected feature/direction using 5-day Spearman on rows with KnowledgeDate < TestDate.

The code does **not** require the training label to have matured before the test date (for example, label_end < TestDate or an equivalent horizon-specific embargo). A post-hoc weekday-only session-count audit of the archived feature panel found:

- Six of twelve test dates contain one 5-day training label that had not matured strictly before the test date.
- Every test date contains three or four 20-day training labels that had not matured strictly before the test date.
- The 20-day training correlation is reported but feature/direction selection is based on 5-day correlation. The 5-day selection still has the six-date maturity defect.

The weekday-only count is a conservative diagnostic proxy, not a replacement for an exchange calendar. The static code defect is definitive: there is no horizon-specific maturity embargo.

Reported strategy summaries were mixed: NASDAQ 5-day mean +0.192% / 66.7% hit rate, but 20-day mean −0.460%; SP500 5-day mean −0.049% / 50.0% hit rate, and 20-day mean −3.058% / 16.7% hit rate. These are twelve sparse dates, without costs or portfolio-risk analysis.

**Decision:** quarantine the Phase 23C performance as not strict no-lookahead. Do not reuse its twelve dates as a fresh OOS set. Any future CFTC test must freeze an exchange-calendar-aware, horizon-specific maturity embargo before evaluation. COT is a broad index-positioning context candidate, not an individual-stock beneficial-owner signal.

## 3. SEC Form 4 — Phase 21C

Source run: [39369692938](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39369692938) · [Artifact 12240403992](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39369692938/artifacts/12240403992) · [Research state](https://github.com/jafelix81/NuevaEstrategia/blob/phase21c-sec-form4-predictability/research_state_smart_money_phase21c.md)

The six-date OOS results had bootstrap mean-advantage intervals crossing zero at H5, H10 and H20. Mean residual Spearman after LTM control was negative at all three horizons (−0.0642, −0.0244, −0.0275). H10's small positive mean had a negative median and only three positive dates; H20 had only five mature dates and a very wide interval.

**Decision:** retain the existing KILLED_FOR_NOW status. Do not retune the same feature family on the consumed six dates.

## 4. Promotion decisions

| Line | Decision | Reason |
|---|---|---|
| FINRA 20C | No promotion | Weak/inconsistent pseudo-OOS; 68.42% file coverage; no costs/bootstrap |
| FINRA 20B | Exploratory only | Six dates; no costs/bootstrap; consumed holdout |
| CFTC 23C | Quarantined | Missing horizon-specific label-maturity embargo |
| SEC Form 4 21C | Killed for now | All bootstrap intervals cross zero; residual rank correlations nonpositive |

## 5. Required controls going forward

- Do not use the six consumed dates as a locked final holdout again.
- For every forward-return label, record its actual label-end timestamp and require it to precede the model-selection cutoff by the full horizon-specific embargo.
- Separate feature availability time from report/event date.
- Do not promote cross-sectional subset differences without full-portfolio exposure, turnover, transaction costs, capacity and risk attribution.
- Preserve negative and inconclusive results; do not retune failed features on the same evaluation dates.
- A future independent final holdout must be prospective or otherwise genuinely untouched after all definitions are frozen.

## Reproducibility and integrity

The Phase 182 auditor consumes only the tracked metadata snapshot. It performs no network requests, no return calculation, no final-holdout access and no production write. It is intended to prevent old diagnostic results from being described as stronger evidence than they are.

- Snapshot: research/phase182_legacy_experiment_validity_snapshot.json
- Auditor: research/phase182_legacy_experiment_validity_audit.py
- Tests: research/test_phase182_legacy_experiment_validity_audit.py
- Workflow: .github/workflows/phase182_legacy_experiment_validity_audit.yml

No data were purchased, no vendor was contacted, and F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
