# Phase 258 — Form 144/Form 4 accession-cluster-preserving conditional placebo

**Date:** 2026-11-10 UTC  
**Disposition:** conservative document-linkage sensitivity completed; observed exact date/share links remain above all simulated conditional placebos. This is not a stock-return or alpha result.

## Why this phase was needed

Phase 257 corrected the definition of a genuinely mutable lag group, but its randomization still operated on transaction-date blocks. A single Form 4 accession can contain multiple sale-date blocks. Permuting those blocks independently can split the internal filing cluster and create a synthetic filing structure that did not exist.

Phase 258 therefore freezes every multi-block accession intact and randomizes only accessions with exactly one selected sale block. Permutation strata use issuer × permanent reporting-owner CIK, optionally narrowed to filing month or ISO week. The filing date remains fixed and the observed 0–4 calendar-day filing lag is reassigned only among eligible single-block accessions within the same stratum.

The matching key remains the exact normalized reporting-owner name because Form 144 supplies seller names. In this immutable sample, the identity audit found zero cases where one issuer/name mapped to multiple reporting-owner CIKs and zero CIKs with multiple normalized names. Permutation grouping uses the permanent reporting-owner CIK.

## Immutable sample and accession structure

| Item | Count |
|---|---:|
| Form 144 panel rows | 21,634 |
| Eligible original notices | 1,451 |
| Eligible proposed-sale tranches | 1,460 |
| Form 4 submissions | 38,152 |
| Form 4 non-derivative rows | 59,885 |
| Form 4 sale blocks | 10,525 |
| Unique accessions with selected sale blocks | 8,897 |
| Single-block accessions eligible for this design | 7,512 |
| Multi-block accessions frozen intact | 1,385 |
| Blocks frozen inside multi-block accessions | 3,013 |
| Exact date/share links | 521 |
| Exact links in single-block accessions | 414 |
| Exact links in frozen multi-block accessions | 107 |
| Lower-confidence fallback links | 49 |

Form 144 CSV SHA-256: 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659.  
Form 4 inner ZIP SHA-256: a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3.

## Results — 1,000 permutations per stratum

| Conditional stratum | Mutable single-block accessions | Observed exact links | Null mean | p95 | Maximum | Exceedances | Holm-adjusted plus-one tail |
|---|---:|---:|---:|---:|---:|---:|---:|
| Issuer × owner CIK | 2,943 | 127 | 58.848 | 69 | 80 | 0/1,000 | 0.002997 |
| Issuer × owner CIK × filing month | 1,451 | 56 | 26.249 | 34 | 43 | 0/1,000 | 0.002997 |
| Issuer × owner CIK × ISO week | 565 | 28 | 14.208 | 20 | 24 | 0/1,000 | 0.002997 |

Observed-to-null-mean ratios are approximately 2.16, 2.13 and 1.97. Each raw plus-one Monte Carlo tail is 0.000999; Holm adjustment across the three Phase 258 strata gives 0.002997. With zero exceedances in 1,000 replicates, the one-sided 95% upper bound for the Monte Carlo tail probability is approximately 0.002991.

The Phase 258 observed counts are intentionally smaller than Phase 257 because 107 exact links in multi-block accessions are frozen and excluded, and additional single-block links are excluded when their local lag group is not genuinely mutable. This is a stricter subset, not a loss of the original 521-link graph.

## Interpretation and limitations

The document-linkage excess survives a more conservative conditional randomization that does not split multi-date Form 4 accessions. Phase 257 and Phase 258 use the same underlying 2026 Q3 Form 4 snapshot and Phase 69 Form 144 panel; they are nested sensitivity analyses, not independent replications.

This still does not establish informed trading or investment alpha:
- Form 144 is a proposed-sale notice, not proof of an executed market sale.
- Form 4 code S can include private dispositions.
- The Form 4 snapshot ends 2026-09-30 and the Form 144 sample is a selected issuer panel.
- Filing dates in the bulk table are date-only; first-public-availability timestamps and complete amendment lineage remain unresolved.
- The lag randomization assumes exchangeability within issuer × reporting-owner CIK × time strata. It is a conditional linkage placebo, not a causal design.
- No stock returns, PIT feature, alpha, bootstrap/LOO, chronological OOS or holdout test was run.

The result justifies preserving the linkage finding for multi-quarter replication. It does not justify promoting Form 144 to a trading feature.

## Workflow and reproducibility

The first Phase 258 attempt, run 42787340371, failed before data download because the workflow file contained escaped GitHub Actions token expressions. The expressions were corrected and the final run succeeded.

- Final hosted run: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42787526319
- Job: 129732394177
- Unit tests: 15/15 passed
- Artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42787526319/artifacts/13749584173
- Artifact SHA-256: e5f51d3d123f653275934f2cdfcc6e9fc491eeb09391a11dfa4533be3877602f
- Code: research/phase258_form144_form4_accession_cluster_preserving_placebo.py
- Tests: research/test_phase258_form144_form4_accession_cluster_preserving_placebo.py
- Workflow: .github/workflows/phase258_form144_form4_accession_cluster_preserving_placebo.yml
- Result: research/phase258_form144_form4_accession_cluster_preserving_placebo_result.json

**Decision:** document linkage only. Strict PIT, feature admission and alpha authorization remain false. No returns, bootstrap/LOO, chronological OOS or holdout were used. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe and capital are unchanged.
