# Phase 480 — Phase 29 independent-alpha lab adjudication

**Audit cutoff:** 2026-11-18 13:24 UTC  
**Main at preflight:** `e2219017a365b1b692eda9cabff8bf042e214150`  
**Source branch:** `phase29-independent-alpha-lab` (PR #1 remains open/draft and is not merged)  
**Source run:** [40105752275](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40105752275)  
**Artifact:** [12565060248](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40105752275/artifacts/12565060248)  
**Disposition:** `MOM120_BASELINE_RECONFIRMATION_NOT_INCREMENTAL`; no signal admission, no strategy change.

## 1. Why this audit was necessary

The Phase 29 lab was designed as an independent benchmark rather than a Smart Money hypothesis. Its successful October 24 run produced positive final-OOS cross-sectional spreads for the selected factor `MOM120` at both tested horizons. The result deserves preservation, but it must not be described as independent alpha or a portfolio-level economic edge without reconciling it to the frozen baseline.

The run log was inspected directly. It reports 335 configured tickers and 335 price downloads, but 334 data series after removing QQQ from the investable cross-section. QQQ is itself present in the frozen Phase-4 universe and is removed to serve as the residual-momentum benchmark. Thus the reported cross-section is 334 names, not the full 335-name universe.

## 2. Reproduced result summary

The script defines `MOM120 = Close / Close.shift(120) - 1`, selects the factor using discovery only, applies a fixed validation gate, and reports final OOS from 2024 onward. Results below are gross cross-sectional diagnostics, not portfolio returns.

| Horizon | Stage | Dates | Mean IC | Mean D10−D1 | Top decile − universe | Partial IC | Hit rate |
|---|---|---:|---:|---:|---:|---:|---:|
| 20 sessions | Discovery | 54 | +0.0552 | +3.23% | +2.42% | +0.0536 | 64.8% |
| 20 sessions | Validation | 36 | +0.0092 | +0.12% | +0.49% | −0.0005 | 61.1% |
| 20 sessions | Final OOS | 33 | +0.0393 | +3.19% | +1.96% | +0.0444 | 60.6% |
| 60 sessions | Discovery | 54 | +0.0892 | +9.57% | +8.73% | +0.0857 | 74.1% |
| 60 sessions | Validation | 36 | +0.0366 | +4.09% | +1.59% | +0.0295 | 61.1% |
| 60 sessions | Final OOS | 31 | +0.0199 | +3.74% | +4.43% | +0.0363 | 61.3% |

Block-bootstrap 95% intervals for final-OOS D10−D1:
- 20 sessions: **+0.33% to +6.19%** (33 date observations).
- 60 sessions: **−4.16% to +11.99%** (31 date observations).

The 20-session validation result is economically small and its partial IC is slightly negative. The 60-session validation is more coherent, but its final-OOS bootstrap interval includes zero. The final OOS was selected only after discovery/validation, but the candidate family and two horizons still require multiplicity-aware interpretation.

## 3. Incremental-information adjudication

The selected factor is not independent of F80/LTM:

- Phase 29's selected feature is raw 120-session price momentum.
- The existing Phase-4 research family explicitly includes `R100/R120/R140/R160`; F80/LTM is built from this long-term-momentum family.
- The Phase 29 lab does not regress or residualize `MOM120` against the actual frozen F80 score, and it does not report a matched F80-versus-F80+MOM120 comparison.
- Therefore these results are a **reconfirmation of a known momentum family**, not evidence of incremental Smart Money information or a new independent source of alpha.

Further limitations prevent an economic promotion:
1. `COST_BPS=10` is recorded in the report metadata but is not applied to the reported spreads.
2. No portfolio-level exposure, turnover, rebalance execution, borrow, financing or matched transaction-cost comparison is performed.
3. The script has block bootstrap but no leave-one-date-out (LOO) analysis.
4. The historical price panel is Yahoo-based and does not establish a survivorship-free, effective-dated 335-name universe. The cross-section is 334 after excluding QQQ.
5. No exact comparison against frozen `F80_TOP20_PARTIAL50_BASELINE_C20` was run.

## 4. Decision

- Preserve the Phase 29 OOS result as a descriptive, gross momentum diagnostic.
- Classify `MOM120` as **baseline-family confirmation / non-incremental**.
- Do not merge the old Phase 29 code branch into main solely on the strength of this result.
- Do not rerun the same ten-factor selection or optimize the horizon, date cadence, direction, thresholds or costs to improve the reported result.
- Do not admit MOM120 as a new signal, alter F80, or use the legacy holdout.

This is not a negative finding about momentum generally. It is a finding that the tested feature is already part of the baseline family and the reported diagnostics do not establish incremental economic value.

## 5. Re-entry standard

Any future independent-alpha work must be preregistered as a genuinely distinct feature and compared directly with frozen F80 using:
- the exact same effective-dated universe and entry/exit timestamps;
- identical capital, gross/net exposure, turnover and realistic costs;
- baseline and augmented portfolios on the same dates;
- controls for prior returns, volatility, liquidity, sector and market regime;
- chronological discovery/validation/final OOS with untouched holdout;
- block bootstrap and LOO/event-block sensitivity;
- multiplicity control across the candidate family.

The seven missing/delisted histories and corporate-action terminal returns must be resolved before a full-universe economic comparison. Until then, no F80 incremental claim is authorized.

## 6. Operational preflight

- Latest Actions inventory at cutoff: 7,844 total runs; no active or queued run.
- Latest observed run: Phase 403 PR regression [44304878119](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44304878119), successful. Its live-capture job was skipped as designed.
- Latest scheduled Phase 403 run: [44302697069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44302697069), failed the stale Phase 464 offline assertions; the live-capture job was skipped and no artifact/data mutation occurred. PR #140 subsequently fixed the regression and merged.
- No later scheduled event appears in the repository's 22-run schedule inventory at this cutoff. This does not prove workflow disablement; GitHub schedule delivery can be delayed. Do not manually dispatch or duplicate either SEC poller.
- Phase 476 Form 4/4-A minute-17 first scheduled capture remains unverified. Phase 403 Form 144 minute-47 post-merge capture remains unverified.
- Cboe public sample artifact rights issue #132 remains open. No artifact deletion or licensing claim is made here.

## 7. Frozen controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameter, holding-period, capital, exposure, cost, production or holdout change. No new backtest, OOS test, bootstrap or LOO was run in Phase 480; this phase is an independent audit/adjudication of the already completed Phase 29 run.
