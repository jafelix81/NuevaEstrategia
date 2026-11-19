# Phase 499 — MOM120 incremental OOS adjudication

**Date:** 2026-11-19  
**Main baseline:** \`812090390ae03a72c9d51218eb8d4cd70e686b71\`  
**Scope:** immutable artifact-only audit of the Phase 29 discovery/validation result and the corrected Phase 30 Top-20 economic simulation.  
**Disposition:** **MOM120 standalone replacement is not promoted; no statistically reliable incremental portfolio edge over LTM was demonstrated.**

## 1. Why this audit was necessary

The earlier Phase 30 implementation had an invalid portfolio-state issue: residual positions could accumulate beyond the stated Top-20 limit. A later branch, \`phase30-mom120-top20-state-machine\`, implemented a bounded state machine and completed run [40149358003](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40149358003).

This audit does not rely on the earlier invalid Phase 30 run. It verifies the later artifact, the daily equity/return accounting, exposure and position limits, and paired incremental results against the LTM control.

## 2. Immutable evidence

| Source | Run | Artifact | SHA-256 |
|---|---:|---:|---|
| Phase 29 independent alpha lab | [40105752275](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40105752275) | [12565060248](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40105752275/artifacts/12565060248) | \`85480d28d6d24c8a167c67baee5b3c28c2915e0a3bc3b2eb2f13b490d4167d77\` |
| Phase 30 corrected Top-20 simulation | [40149358003](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40149358003) | [12581524526](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40149358003/artifacts/12581524526) | \`b57190f1d979bde7bb38cff0c6fa0e294cbfed029c5bc702ab62574bb459bc48\` |

Both artifacts were downloaded and independently hashed. The Phase 499 workflow re-downloads these exact artifacts, verifies their hashes, audits the CSV ledgers in memory, and uploads only an aggregate JSON summary. No ticker-level ledger or trade rows are copied into the repository.

## 3. Phase 29: candidate selection

Phase 29 used a preregistered discovery/validation split:
- Discovery: 2017–2020, 54 signal dates.
- Validation: 2021–2023, 36 signal dates.
- Candidate selected: MOM120 for both 20- and 60-session forward horizons.
- The Phase 29 validation gate was marked passed for both horizons.

The 60-session validation was stronger than the 20-session result:
- H20 mean Q10–Q1: +0.122%; partial IC: -0.00054.
- H60 mean Q10–Q1: +4.089%; partial IC: +0.02953.

This establishes a plausible cross-sectional momentum hypothesis, not incremental portfolio alpha.

## 4. Phase 30: corrected economic implementation

The later Phase 30 state-machine run used:
- 335 configured names and 335 downloaded price series;
- signal at close \(t\), execution at open \(t+1\);
- F80 rebalance cadence;
- Top-20 equal-weight target, PARTIAL50;
- maximum 20 positions and 100% gross exposure;
- 10, 20 and 50 bps per-side transaction-cost scenarios;
- continuous simulation with temporal OOS beginning 2024-01-01.

The audited OOS interval is 2024-01-02 through 2026-10-23, with 706 daily observations. All six candidate/baseline ledgers passed:
- exact date alignment;
- daily return/equity chain reconciliation;
- cash plus gross value equals equity;
- non-negative cash;
- gross exposure no greater than 100%;
- no more than 20 positions.

There were only **eight observed OOS trade/rebalance dates**. The 706 daily rows therefore must not be treated as 706 independent signal decisions.

## 5. Incremental results versus LTM

| Cost per side | Mean daily excess | Block-80 95% interval | Relative OOS final-multiple difference |
|---:|---:|---:|---:|
| 10 bps | +0.705 bps | -3.525 to +5.206 bps | +4.30% |
| 20 bps | +0.710 bps | -3.526 to +5.222 bps | +4.34% |
| 50 bps | +0.725 bps | -3.528 to +5.259 bps | +4.47% |

The block-bootstrap intervals also include zero at block lengths 20 and 160. The sign-test p-value is 0.214 and the naive paired daily t-test p-value is approximately 0.75 at C20. Leave-one-day-out means remain positive, but that does not overcome the wide uncertainty or the small number of OOS rebalance decisions.

At C20, the descriptive OOS profile was:
- MOM120 final multiple: 4.096 versus LTM 3.925;
- MOM120 Sharpe: 1.247 versus LTM 1.227;
- MOM120 maximum drawdown: -41.89% versus LTM -42.30%.

These small differences are descriptive only. They do not establish a statistically reliable incremental advantage. The conclusion is unchanged at 10, 20 and 50 bps per side.

## 6. Data and inference limitations

This is temporal OOS on a static 335-name universe, **not strict point-in-time OOS**:
- the universe is not an effective-dated historical constituent panel;
- Yahoo Finance does not provide the required reproducible historical security-master and delisted-security return coverage for this test;
- historical membership and terminal/delisting treatment are not independently certified;
- fixed bps costs do not model name-specific spread, market impact, borrow or capacity;
- only eight OOS trade/rebalance dates occurred.

The artifact's daily bootstrap is therefore not a substitute for a PIT universe, and daily observations do not create more independent rebalance events.

## 7. Decision

**REJECT FOR PROMOTION:** the tested MOM120 standalone replacement did not demonstrate a reliable incremental portfolio edge over LTM.

This does not kill the general momentum hypothesis: LTM already contains overlapping long-term momentum information, and Phase 29's cross-sectional H60 result remains a hypothesis. It does kill promotion of this specific standalone replacement on the current evidence.

No additional signal is admitted. No new return test, parameter search, universe substitution or holdout access is authorized by this phase.

## 8. Frozen controls

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains unchanged:
- no universe or parameter change;
- no holding-period constraint change;
- no capital, exposure or cost change;
- no holdout or production change.

The next useful research step is not another momentum variant. It is to find a genuinely complementary source or feature, then establish effective-dated identity, point-in-time availability and delisted coverage before testing incremental value against LTM/F80.
