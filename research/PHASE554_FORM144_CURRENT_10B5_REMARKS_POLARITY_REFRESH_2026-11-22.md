# Phase 554 — Current Form 144 Rule 10b5-1 polarity refresh (2026-11-22)

**Audit cutoff:** 2026-11-22 11:50 UTC  
**Main base before this documentation update:** `01f456832bd50e0892db33db8f8b56dbed5d1474`  
**Disposition:** descriptive classifier refresh only; no signal, return test or strategy change.

## 1. Reproducible inputs

- Current main ledger: `research/data/sec_form144_first_seen/sale_details.csv`
- Git blob: `486033425d43d9dbdcaba78c0260d2ebbb8c22e9` (1,705,244 bytes)
- Ledger grain: 2,072 detail rows / 275 accessions; 273 Form 144 and 2 Form 144/A.
- Phase 516 post-capture artifact: run [45012113618](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45012113618), artifact [14750197356](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45012113618/artifacts/14750197356). It independently reports 275 filing headers / 2,072 rows, 2,072 source-hash matches, zero mismatches, zero parse errors, zero public-availability-certified headers and zero signal-eligible headers.
- Classifier source reapplied: PR #202 branch `phase549-form144-10b5-plan-date-polarity-audit`, blob `771bdf268b4915ccbcf0c4b735f1408ba416f815`.
- Classifier tests reviewed: blob `0f67567a13d0699f75354253e1551db1c9e693df`.

The clause-level rules were independently reapplied to the current main ledger at accession grain, preserving the PR implementation's mention detector, explicit-negative patterns, explicit-positive patterns, contradictory-clause fail-closed behavior and ambiguous fallback. Seven polarity edge-case checks were reproduced and passed, including explicit negative, positive, compact-token ambiguity, negated plan language and contradictory clauses. This is a current-data refresh, not a merge of PR #202.

## 2. Current accession-grain results

| Classification | Accessions |
|---|---:|
| Positive explicit 10b5-1 reliance | 8 |
| Negative explicit | 4 |
| Ambiguous mention | 1 |
| No mention | 262 |
| **Total** | **275** |

All 13 raw Remarks keyword mentions were classified: 8 positive, 4 negative and 1 ambiguous. The raw keyword flag alone must not be interpreted as plan reliance.

### Important semantic adjustments

- One of the eight positive classifications is Verano Holdings Form 144/A, accession `0001493152-26-053320`. Its Remarks describe the prior non-discretionary plan and expressly terminate it; it is **not** a new forward-sale event. Excluding this termination leaves **7 positive proposed-sale notices across 6 distinct issuers**.
- The four explicit negatives are Fermi Inc. notices describing automatic sell-to-cover transactions for tax withholding, explicitly not pursuant to a Rule 10b5-1 plan. They are a mechanical/administrative negative control, not discretionary bearish insider sales.
- The single ambiguous case is Teva, accession `0001973379-26-000377`, which uses compact `10B51` notation. It remains ambiguous; no token normalization promotes it to positive.
- Two positive Constellation Energy notices relate to the same seller and the same 2026-05-18 plan. They are separate notices, not independent seller/plan observations.

### Formal plan dates

- 101 accessions have a structured formal plan-adoption date: **36.73%** of this bounded 275-accession ledger.
- 62 distinct plan-adoption dates.
- Plan-date-to-notice lag: n=101; min 72 days; p25 97; median 185; p75 268; max 546.
- No formal plan date is after its notice date.
- 92 accessions have a formal date but no Remarks mention; 9 have both a formal date and a Remarks mention; 4 have a Remarks mention but no formal date.
- 11 accessions contain both sell-to-cover and tax-withholding wording; one accession is a plan-termination filing.

These are counts in a bounded newest-first filing ledger, not population prevalence estimates. A formal plan date is historical context, not the signal-availability timestamp. Form 144 is a proposed-sale notice, not proof of execution.

## 3. PIT and strategy disposition

- Phase 516 records 275 research-observation filing headers with bounded first-seen intervals, but **0 public-availability-certified headers** and **0 signal-eligible headers**. Poll receipt remains an upper bound, not an exact public release timestamp.
- No forward-return or event study was run.
- No feature was admitted; no OOS, bootstrap, LOO or holdout was used.
- No universe, exposure, costs, holding-period policy or production setting changed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 4. PR #202 disposition

PR [#202](https://github.com/jafelix81/NuevaEstrategia/pull/202) remains Draft and non-mergeable/diverged against current main. Its committed report is a historical 245-accession snapshot. This Phase 554 refresh is recorded separately on main; do not merge the stale branch or cite its original aggregate counts as current without first reconciling the branch and refreshing its artifacts.

## Decision

**Keep Form 144 Rule 10b5-1 as descriptive context / a future conditional event-study candidate only. Do not promote it as an insider signal.** The current evidence distinguishes planned sales, explicit non-plan mechanical sales and ambiguous mentions, but does not establish execution, certified public availability or predictive incremental information versus frozen F80.
