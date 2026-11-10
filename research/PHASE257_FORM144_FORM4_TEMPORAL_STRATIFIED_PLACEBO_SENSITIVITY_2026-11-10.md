# Phase 257 — Form 144/Form 4 temporal-stratification sensitivity

**Date:** 2026-11-10 UTC  
**Disposition:** hosted sensitivity completed; exact document linkage remains descriptively elevated under finer time strata. This is not a return-alpha test.

## Executive result

The Phase 257 push-triggered workflow was inspected after completion. Run **42775383915** succeeded; job **129692649023** completed every step; artifact **13743028950** was uploaded with SHA-256 b2ec9653ab66da858bf3e7f42376176a67011413de4d543d8ff93fd74dba7c2f. The job log and downloaded artifact were both inspected.

The sensitivity tightens Phase 256's definition of a mutable group: a group must contain at least two Form 4 sale blocks and at least two distinct observed filing lags. Blocks in groups with identical lags are fixed under the randomization and therefore excluded from the observed mutable-link statistic.

This correction matters. Under the broad issuer-owner stratum, Phase 256 counted 340 links in groups with more than one block; Phase 257 identifies only **241** of those as actually mutable. The other 99 links belong to groups whose lag multiset cannot change. The month and ISO-week strata similarly reduce 228 to 169 and 157 to 139.

## Immutable sample

| Item | Count |
|---|---:|
| Form 144 panel rows | 21,634 |
| Eligible original notices | 1,451 |
| Eligible proposed-sale tranches | 1,460 |
| Form 4 submissions | 38,152 |
| Form 4 non-derivative rows | 59,885 |
| Unique-owner sale blocks | 10,525 |
| Exact date/share links | 521 |
| Lower-confidence fallback links | 49 |

Form 144 CSV SHA-256: 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659.  
Form 4 inner ZIP SHA-256: a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3.

## Results — 1,000 permutations per stratum

| Conditional stratum | Actually mutable Form 4 blocks | Observed exact links in mutable blocks | Null mean | p95 | Maximum | Exceedances | Holm-adjusted plus-one tail |
|---|---:|---:|---:|---:|---:|---:|---:|
| Issuer × owner | 6,266 | 241 | 111.604 | 126 | 141 | 0/1,000 | 0.002997 |
| Issuer × owner × filing month | 4,748 | 169 | 83.976 | 97 | 111 | 0/1,000 | 0.002997 |
| Issuer × owner × ISO week | 3,746 | 139 | 85.332 | 97 | 112 | 0/1,000 | 0.002997 |

All three conditional randomization tails are 0.000999 before Holm adjustment and 0.002997 after adjustment. With zero exceedances in 1,000 replicates, the one-sided 95% upper bound for the Monte Carlo tail probability is approximately 0.002991. These are linkage-placebo tails only.

## Interpretation

The exact date/share linkage remains above every simulated replicate under all three time strata. The observed-to-null-mean ratios are approximately 2.16, 2.01 and 1.63, respectively.

This does not establish an informed-trading signal:
- Form 144 reports a proposed sale, not an executed market sale.
- Form 4 code S can include private dispositions.
- The data cover one Form 4 quarter and a selected Form 144 issuer panel.
- Filing dates in the bulk table are date-only; first-public-availability timestamps and complete amendment lineage remain unresolved.
- Exchangeability of filing lags within issuer-owner-time strata is a conditional randomization assumption, not a causal design.
- No stock returns, PIT feature, alpha, bootstrap/LOO, chronological OOS or holdout test was run.

## Reproducibility

- Code: research/phase257_form144_form4_temporal_stratified_placebo_audit.py
- Tests: research/test_phase257_form144_form4_temporal_stratified_placebo_audit.py (14 tests)
- Workflow: .github/workflows/phase257_form144_form4_temporal_stratified_placebo_audit.yml
- Hosted run: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42775383915
- Job: 129692649023
- Artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42775383915/artifacts/13743028950

**Decision:** retain as document-linkage evidence only. Strict PIT and feature admission remain false; no alpha test is authorized. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
