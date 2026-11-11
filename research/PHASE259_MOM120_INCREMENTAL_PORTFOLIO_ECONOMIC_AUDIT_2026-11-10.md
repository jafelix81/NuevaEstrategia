# Phase 259 — MOM120 incremental portfolio economic audit

**Date:** 2026-11-10 UTC  
**Disposition:** MOM120 remains a research hypothesis; its incremental portfolio advantage over the LTM/F80-style baseline is not statistically demonstrated. No promotion.

## Question

Does the Phase 29-selected 120-day momentum factor (MOM120) improve the Phase 30 LTM/C20 portfolio under the same 80-session rebalance, top-20, 50%-partial sizing, 20% maximum position and 1.0 gross-cap protocol?

This is a portfolio-level comparison, not a Smart Money source test. The OOS period was previously used in Phases 29/30 and is **consumed, not pristine**.

## Immutable inputs and audit

- Phase 29 cross-sectional artifact: run 40105752275, artifact 12565060248, report SHA-256 a935ca2994a1041ad458a76fa203576cdd330e33fc253143879c9491bcc4db65.
- Phase 30 portfolio artifact: run 40149358003, artifact 12581524526, SHA-256 b57190f1d979bde7bb38cff0c6fa0e294cbfed029c5bc702ab62574bb459bc48.
- Six daily ledgers (LTM/MOM120 × 10/20/50 bps per side) each contain 2,718 unique chronological sessions from 2016-01-04 through 2026-10-23.
- Each ledger passed equity = cash + gross value, gross exposure, top-N, finite-value and sequential-return identities.
- Trade-level cost identities were exact for all six trade ledgers.
- An additional paired-ledger cross-check found identical date arrays, daily position counts, gross exposure, gross-value/equity and cash/equity paths between LTM and MOM120 at each cost level. This confirms matched exposure for the paired comparison.
- The daily-return convention is close(t-1) → open(t) → close(t), with signal close(t) → open(t+1).

## Corrected OOS boundary

The OOS return series includes the first 2024 session's return from the 2023-12-29 close. Phase 30's published absolute multiple divided final equity by the first OOS close, omitting that first return from its denominator.

Phase 259 therefore uses the **2023-12-29 pre-OOS close** as the starting capital for the 706 included daily returns (2024-01-02 through 2026-10-23). The original Phase 30 absolute final multiple was overstated by 3.65% for LTM/C20 and 3.73% for MOM120/C20 under this boundary convention. The paired daily excess-return series itself is unaffected.

## C20 results

| Metric | LTM baseline | MOM120 |
|---|---:|---:|
| Corrected OOS final multiple | 3.7873× | 3.9486× |
| Sharpe (zero risk-free approximation) | 1.2266 | 1.2471 |
| Annualized volatility | 48.35% | 48.99% |
| Maximum drawdown | -42.30% | -41.89% |

MOM120's relative OOS growth was 4.26% higher, but its paired mean excess return was only **0.710 bps per day** (simple annualized mean 1.79%).

- 20-session circular block bootstrap, 5,000 replicates: 95% CI **[-3.533, +4.811] bps/day**.
- Newey–West/HAC with 20 lags: mean 0.710 bps/day, t = **0.338**, 95% CI **[-3.409, +4.830] bps/day**.
- Block-length sensitivity at 5, 10, 20, 40 and 80 sessions: every 95% bootstrap interval includes zero.
- Cost sensitivity at 10, 20 and 50 bps per side: relative growth was +4.22%, +4.26% and +4.38%, respectively, but every block-bootstrap interval includes zero.

The positive daily leave-one-out means are descriptive only; serial dependence makes the block bootstrap and HAC results more relevant. Neither supports promotion.

## Phase 29 cross-sectional context

MOM120 was selected in the earlier discovery process. Its 20-session final cross-sectional OOS slice contains only 33 rebalance dates (mean IC 0.0393; Q10–Q1 spread 3.19%; date-level bootstrap CI 0.33% to 6.19%). The 60-session slice contains 31 dates (mean IC 0.0199; Q10–Q1 3.74%; CI -4.16% to +11.99%). These same historical periods were already used in the earlier research and do not constitute a pristine replication.

## Decision

- Retain MOM120 as a research hypothesis; do **not** promote it over LTM/F80.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No strict PIT admission, Smart Money feature admission, production change, universe change, capital change or holdout use.
- The legacy holdout remains CONSUMED_NOT_PRISTINE.

## Reproducibility

- Final same-head hosted run: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42790753655
- Job: 129743242259; 15/15 tests passed.
- Metadata/result artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42790753655/artifacts/13750088994, SHA-256 b04a5b6d3ed6b3a0f7c3386c850c68d6ed2db038db5239c761fe252cee2380d8.
- Earlier corrected run: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42790083272, artifact https://github.com/jafelix81/NuevaEstrategia/actions/runs/42790083272/artifacts/13751701677.
- Code: research/phase259_mom120_incremental_portfolio_economic_audit.py
- Tests: research/test_phase259_mom120_incremental_portfolio_economic_audit.py
- Workflow: .github/workflows/phase259_mom120_incremental_portfolio_economic_audit.yml

The first attempt exposed an incorrect synthetic ledger fixture; the next exposed a NumPy-array JSON serialization defect. Both were corrected. The final same-head run passed all 15 tests and completed the immutable-data, accounting, bootstrap, HAC and no-promotion gates.
