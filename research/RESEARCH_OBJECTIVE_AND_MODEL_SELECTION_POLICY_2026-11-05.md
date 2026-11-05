# Research objective and model-selection policy

**Effective date:** 2026-11-05  
**Applies to:** Smart Money Research, F80/LTM challengers, independent signals, combinations and regime-specialized models.

## 1. Objective

The objective is to discover the most investable strategy supported by genuine statistical and economic evidence: attractive net return relative to risk, controlled drawdowns and tail exposure, feasible liquidity/capacity, realistic execution and operational simplicity.

There is **no CAGR target** and no prescribed holding period. Holding horizon, rebalance frequency and exit design are empirical choices, selected only inside chronological development/validation data and frozen before final OOS evaluation.

A high backtest return is not sufficient. The project must establish that the result is not an artifact of universe survivorship, lookahead, data revisions, return chasing, exposure differences, costs, issuer concentration, regime selection or repeated hypothesis testing.

## 2. F80 is a frozen benchmark, not a protected incumbent

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen so comparisons have a stable reference. Its frozen status does **not** mean it must be preserved, combined with every challenger or remain the final strategy.

A standalone candidate may replace F80 if it demonstrates superior, robust and economically feasible OOS performance under the same investable universe, timing, exposure, execution and cost assumptions. F80 may be retired if it is consistently inferior. Do not alter F80 to make a challenger look better.

Every candidate is allowed to be:
- an independent replacement strategy;
- a complementary signal that adds measurable incremental value;
- a conditional/regime-specialized strategy; or
- a risk overlay that improves the return/risk profile without adding alpha.

Do not force an ensemble, blend or F80 feature. Combine models only when the combination itself passes preregistered tests and improves the investable portfolio.

## 3. Model-selection standard

Compare candidates on:
- net return and return distribution, not CAGR alone;
- volatility, drawdown depth/duration, downside and tail loss;
- Sharpe/Sortino and consistency across chronological folds;
- turnover, spread/market-impact assumptions, borrow/short constraints and liquidity;
- capital utilization, concentration, capacity and execution feasibility;
- stability by issuer, sector, size/liquidity bucket and market regime;
- operational complexity and dependence on expensive or fragile data.

A candidate must be evaluated as a **standalone model** and, where economically justified, as an incremental addition to F80 and other surviving candidates. Comparisons must use identical exposure and realistic costs. Report gross and net results separately.

## 4. Evidence and validation discipline

1. Preregister the economic mechanism, feature construction, knowledge timestamp, execution boundary, universe, horizons, controls, model family and kill criteria before examining forward returns.
2. Enforce no-lookahead at both the source and security/universe levels. Keep event date, report date, filing date, acceptance time, publication time, record-known time and effective time distinct.
3. Use chronological development, nested validation/model selection and a final untouched OOS holdout. Once a holdout has been inspected repeatedly, it is no longer a final holdout; use a genuinely new future period for final confirmation.
4. Use identical exposure, rebalance, execution and costs for benchmark and challenger. Do not compare a fully invested candidate to a lower-exposure baseline without exposure matching.
5. Use block bootstrap, issuer-clustered uncertainty, leave-one-issuer-out, regime/subperiod analysis and multiple-testing controls. Purge/embargo overlapping labels where appropriate.
6. Control return-chasing alternatives: prior 1/5/20/60-session returns, momentum/trend, volatility, gaps, liquidity, market/sector beta, earnings and relevant event windows. Separate information effects from dealer hedging, inventory, volatility, leverage and mechanical disclosure timing.
7. Report failures, missingness and all tested variants. Do not select the best horizon, sign, threshold or subset after viewing OOS results.

## 5. Data-source gate and research-budget allocation

Before any economic test or paid acquisition, audit:
- historical depth and continuity, including inactive/delisted names and expired contracts;
- coverage of the actual eligible universe by year, issuer, size, liquidity and regime;
- permanent issuer/security/contract identifiers and corporate-action continuity;
- source publication/acceptance/availability timestamps and conservative KnowledgeDate;
- backfills, restatements, corrections, methodology/version changes and archived vintages;
- raw reproducibility, licensing, retention and total cost.

Set source-specific coverage thresholds before acquisition. A current ticker/CIK map is not a historical security master; a security master cannot restore names omitted from a curated historical universe.

Allocate research effort by expected value of information: likelihood the source can answer a distinct economic question, historical/PIT feasibility, coverage, independent verifiability, cost and implementation burden. Novelty, a user's observation, vendor marketing or a published in-sample result does not confer priority. No vendor contact, purchase or new data entitlement is authorized without explicit user consent.

## 6. Interpretation and kill rules

“Smart money,” “institutional,” “retail,” “informed,” “opening,” “closing” and similar labels are hypotheses, not identities or causal explanations. Participant capacity, a filing label, a large trade, a fund registrant CIK or a vendor classifier does not prove beneficial ownership, information advantage or a position change.

Kill or park a hypothesis when its PIT/coverage/identity gate fails, its mechanism is not distinguishable from return-chasing or mechanical effects, its result does not survive chronological OOS and robustness tests, or costs/capacity erase the effect. Archive the reason and do not tune the failed implementation to rescue it. Reopen only with a materially new source, mechanism or preregistered test.

## 7. Current project implications (2026-11-05)

- **Historical universe/security identity is the central blocker.** Phase 70/71 did not recover the original 335-name selection rule or dated membership. Fixed-335 results remain conditional diagnostics, not proof of a survivorship-free cross-sectional edge. Build a separate PIT broad-universe line if the original rule cannot be recovered; do not silently substitute it into F80.
- **13D/13G:** Phase 84/89/91/93 demonstrate a workable role-aware discovery and parsing path on a limited sample. Phase 35's issuer-specific CIK-submissions panel is separately invalidated as an issuer-event panel by the Phase 96 positive-control audit. No 13D/G returns test is authorized until identity, amendment/person normalization and historical universe gates are satisfied.
- **Form 144:** Phase 67's current-CIK full census passed XML issuer/filer resolution for its 309-CIK candidate set; Phase 68 expanded current mapping to 335/335 tickers and 319 CIKs. Phase 69's ten-CIK incremental extension is running. This remains a proposed-sale notice, not proof of execution, and is not yet a PIT-universe alpha panel.
- **Options/DOOD:** Phase 94 validates formula arithmetic only. Phase 95 found unresolved volume/delta units and a 2016-versus-March-2018 history discrepancy. DOOD is a conditional candidate, not an automatic priority; no data, purchase, vendor contact or returns test has occurred.
- **CFTC TFF:** regime context only; historical release-time reconstruction remains a PIT blocker.
- **FINRA short-flow × short-interest, standalone Form 4, CFTC equity-index positioning and the tested N-PORT dose-response remain killed for their tested hypotheses.** Do not reopen without a materially different preregistered mechanism or source.

F80 remains frozen during research. It may be replaced, retired, supplemented or left unchanged solely according to the evidence standard above.
