# Phase 386 — SEC 13F / N-PORT institutional-ownership hypothesis disposition

**Date:** 2026-11-13 UTC  
**Status:** completed research adjudication; no new raw SEC data acquired and no new return test run.  
**Purpose:** archive the existing N-PORT dose-response evidence and reconcile it with the latest 13F PIT/coverage decision so failed hypotheses are not repeatedly re-run.

## Executive decision

1. **Kill the current standalone N-PORT quarter-over-quarter share-growth decile hypothesis** as a stock-selection signal. The six-period dose-response diagnostic is mostly negative and does not show a stable positive relationship.
2. **Keep SEC Form 13F parked** for broad-universe stock selection. The historical security-identity and coverage evidence remains below the standard needed for a fair identical-exposure comparison with frozen LTM/F80.
3. Neither conclusion means the SEC sources contain no information. They mean the currently specified, reproducible hypotheses and data routes have not earned further return-testing priority. Re-entry requires a materially different, pre-registered hypothesis and a solved PIT identity gate.

## 1. N-PORT Phase 27O dose-response result

Source run: [39503800069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39503800069)  
Artifact: [12303188100](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39503800069/artifacts/12303188100)  
Branch: \`phase27o-nport-dose-response\`

The pre-specified diagnostic ranked the frozen 335-name universe by quarter-over-quarter aggregate reported share growth, requiring positive shares in both snapshots and prior aggregate reported value of at least $50m. It evaluated the next 63 trading days. The printed period tuple is (formation period, cross-sectional Spearman IC, top-decile minus bottom-decile mean return):

| Formation period | Spearman IC | Top − bottom |
|---|---:|---:|
| 2020Q4 | -0.1199 | -11.77% |
| 2021Q4 | -0.0768 | -5.56% |
| 2022Q4 | +0.0161 | +12.03% |
| 2023Q4 | -0.0292 | +6.12% |
| 2024Q4 | -0.1076 | -4.78% |
| 2025Q4 | -0.1006 | -1.74% |

Across the six reported formation periods:
- Mean Spearman IC: **-0.0697**; positive in **1/6** periods.
- Mean top-minus-bottom spread: **-0.95 percentage points**; positive in **2/6** periods.
- Median top-minus-bottom spread: **-3.26 percentage points**.

The 2026Q3 snapshot was signal-only because its 63-session forward horizon was not yet complete. The hosted logs also show repeated price-download failures for six symbols (EQR, AVB, WBS, WBD, EA, LPRO) in multiple later windows. This makes the diagnostic incomplete rather than stronger.

### Interpretation

This is not a formal strategy backtest: no transaction costs, identical-exposure LTM/F80 comparison, bootstrap, LOO, or multiplicity-adjusted inference was run. Nevertheless, the pre-specified dose-response evidence is directionally poor: five of six ICs are negative, and the mean top-minus-bottom spread is negative. The current raw share-growth ranking therefore fails its promotion criterion.

**Disposition:** archive/kill \`NPORT_QOQ_AGGREGATE_SHARE_GROWTH_TOP_BOTTOM\` as a standalone candidate. Do not optimize the threshold, holding period, decile cut or universe to rescue it. Do not repeat the same test with alternative cut points.

Related prior runs:
- [Phase 27K](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39481291430) initially produced zero tickers because its ticker-only identity filter was defective; this was a code defect, not evidence against N-PORT.
- [Phase 27O corrected PIT flow pilot](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39493106882) still produced zero ranked names across its transitions, so it supplied no testable signal.
- [Phase 27L/27M/27O audit notes](https://github.com/jafelix81/NuevaEstrategia/tree/phase27o-nport-dose-response/research) document the identifier and series-panel corrections.

## 2. Form 13F remains parked

The latest re-entry decision is [Phase 289](https://github.com/jafelix81/NuevaEstrategia/blob/phase289-sec13f-reentry-adjudication/research/PHASE289_SEC_13F_REENTRY_DECISION_AND_SOURCE_PRIORITY_2026-11-11.md).

The full frozen-universe denominator matters. Phase 22C V6 reports:
- 2016Q1: 212/335 = **63.28%**.
- 2020Q1: 246/335 = **73.43%**.
- 2024Q1: 280/335 = **83.58%**.

The often-cited 83.18% in Phase 166 is a Section 13(f)-eligibility-list cross-check for a separate 13D/G filing sample, **not** Form 13F holdings coverage. It must not be used to promote a 13F panel.

Phase 205's ten accession cases were purposively selected edge cases, not a representative sample. They demonstrate that filing date can differ from EDGAR acceptance date and that amendments can restate or supplement earlier reports. A valid 13F panel must preserve accession-level public availability and amendment state; it cannot treat quarter-end holdings or later amendments as known earlier.

**Disposition:** retain 13F as a delayed contextual ownership source only. Do not acquire the full historical ZIP corpus or start a broad-universe return test until an effective-dated security master covers active, inactive and delisted securities and demonstrates adequate coverage against the full historical universe.

## 3. Re-entry conditions

A future N-PORT or 13F re-entry must state a new hypothesis before accessing forward returns and must solve:
1. Effective-dated security identity, including share classes, CUSIP/ISIN changes, mergers, spin-offs and delistings.
2. First-publication/acceptance timestamps and amendment lineage; never backdate a later amendment.
3. Stable series/manager identity and duplicate/shared-discretion handling.
4. Coverage measured against the full predeclared universe, not only names that map today.
5. Explicit controls for prior returns, momentum, market cap, liquidity, volatility, sector and index membership to separate holdings changes from return-chasing.
6. A frozen feature definition and chronological validation against LTM/F80 with identical exposure, realistic costs, bootstrap/LOO and multiplicity control.

A new hypothesis must add genuinely different information (for example a verified short-equity disclosure or a predeclared manager-breadth measure), not merely relabel the failed raw share-growth feature.

## 4. Portfolio and research controls

- \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
- No production, universe, capital, exposure or parameter changes.
- No new holdout use; the legacy holdout remains consumed.
- No new alpha/OOS/bootstrap/LOO test was run in Phase 386.
- No SEC contact, vendor contact, data purchase or license acceptance occurred.

## Final disposition

**N-PORT raw quarterly share-growth: KILLED as currently specified.**  
**Form 13F broad-universe ownership-change: PARKED pending security identity and PIT coverage.**  
Neither source is admitted as a Smart Money signal.
