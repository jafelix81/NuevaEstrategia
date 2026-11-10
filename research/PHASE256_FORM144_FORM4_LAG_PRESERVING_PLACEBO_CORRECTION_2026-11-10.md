# Phase 256 — Form 144/Form 4 lag-preserving conditional-placebo correction

**Date:** 2026-11-10 UTC  
**Disposition:** material correction to the Phase 210 date/joint permutation nulls; the exact document-linkage result remains descriptively strong. Strict PIT, feature admission and alpha remain NOT ADMITTED.  
**Scope:** immutable Phase 69 Form 144 and Phase 39 Form 4 GitHub Actions artifacts only. No SEC request, vendor contact, purchase, return test, holdout use or production change.

## Executive result

The Phase 210 conditional date placebo shuffled raw Form 4 transaction dates within issuer × reporting-owner groups while leaving each Form 4 filing date fixed. But the source sample had already been selected using a filing-lag envelope of 0–4 calendar days. The raw-date shuffle did not preserve that selection condition.

A 1,000-replicate reproduction of the Phase 210 raw-date shuffle found that **4,247.36 of 10,525 Form 4 sale blocks per replicate (40.35%)** were assigned an invalid filing lag: 2,127.589 blocks on average had a negative lag and 2,119.771 had a lag greater than four days. Those blocks remained in the null sample.

Phase 256 corrects the design by permuting the observed filing-to-transaction lag within issuer × reporting-owner groups, keeping each block's filing date fixed and reconstructing its transaction date. This preserves the original 0–4-day sample-eligibility envelope and each group's lag multiset.

The corrected 1,000-replicate date null still leaves the observed exact-link count well above every simulated replicate:

- **340 observed** exact links in date-mutable groups;
- corrected null mean **210.735**, p95 **225**, maximum **238**;
- **0/1,000** replicates at or above observed; plus-one Monte Carlo tail frequency **0.000999**.

The linkage diagnostic therefore survives the corrected date null. It remains a document-linkage result, not a return-alpha p-value or proof of public-market execution.

## 1. Immutable inputs and reproduced linkage graph

| Input | Source |
|---|---|
| Form 144 expanded issuer-event CSV | Phase 69 run 41959603351, artifact 13385365595 |
| Form 144 CSV SHA-256 | 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659 |
| Form 4 Q3 2026 inner ZIP | Phase 39 run 40606706518, artifact 12781850078 |
| Form 4 inner ZIP SHA-256 | a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3 |

The immutable inputs reproduce 21,634 Form 144 panel rows, 1,451 eligible original notices, 1,460 sale tranches, 38,152 Form 4 submissions, 59,885 non-derivative rows and 10,525 unique-owner sale blocks. The Form 4 snapshot ends 2026-09-30; the Form 144 right-censor cutoff remains 2026-09-24.

The exact-first graph remains **521 mutually unique exact-date/exact-share links**, plus **49** lower-confidence mutually unique 0–2-day fallback links. Of the 521 exact links, 481 agree under the coarse security-class-family crosswalk and 40 remain conflicted or unresolved. The Phase 210 price concordance is unchanged and was not recomputed here: 521/521 exact links were within 5% of the Form 144 implied price and 503/521 within 1%.

## 2. Why the Phase 210 raw-date null was invalid for this selected sample

Phase 208's eligible Form 4 blocks require:

    0 <= filing_date - transaction_date <= 4 calendar days

Phase 210 then shuffled the raw transaction dates inside issuer × owner groups, but held each block's filing date fixed. The resulting block can have a negative filing lag or a lag greater than four days, even though the observed sample contained only eligible blocks.

The Phase 256 invalidity reproduction uses the same grouping, iteration order, Python RNG seed (211) and 1,000 replicates as the original date-shuffle design. It found:

| Invalidity diagnostic | Result |
|---|---:|
| Form 4 blocks per replicate | 10,525 |
| Mean invalid blocks | 4,247.36 |
| Median invalid blocks | 4,248 |
| p95 invalid blocks | 4,316 |
| Maximum invalid blocks | 4,383 |
| Mean negative-lag blocks | 2,127.589 |
| Mean lag-over-four blocks | 2,119.771 |
| Mean invalid fraction | **40.354964%** |

This does not change the observed 521 exact links. It means the Phase 210 raw-date and joint date/share null distributions should not be used as the final conditional date-placebo specification.

## 3. Corrected lag-preserving randomization

For each issuer × reporting-owner group with multiple Form 4 blocks:

1. Keep every block's original Form 4 filing date fixed.
2. Shuffle the observed 0–4 calendar-day filing lags within that group.
3. Reconstruct each permuted transaction date as filing_date minus permuted_lag.
4. For the joint null, independently shuffle share quantities within the same issuer × owner groups.
5. Rebuild the exact-date/exact-share one-to-one graph and count only links whose Form 4 block belongs to a group declared mutable before permutation.

This preserves each group's observed lag multiset and keeps every permuted block inside the same 0–4-day eligibility envelope. It is still a conditional randomization diagnostic; exchangeability within issuer × owner groups is an assumption, not a causal design.

## 4. Results — 1,000 deterministic replicates per null

| Conditional null | Observed mutable exact links | Null mean | p95 | Maximum | At/above observed | Plus-one tail |
|---|---:|---:|---:|---:|---:|---:|
| Owner identity within issuer | 475 | 156.800 | 171 | 184 | 0/1,000 | 0.000999 |
| Filing lag within issuer × owner | 340 | 210.735 | 225 | 238 | 0/1,000 | 0.000999 |
| Shares within issuer × owner | 340 | 194.945 | 208 | 223 | 0/1,000 | 0.000999 |
| Filing lag + shares within issuer × owner | 340 | 138.510 | 153 | 166 | 0/1,000 | 0.000999 |

For zero exceedances in 1,000 Monte Carlo replicates, the one-sided 95% binomial upper bound on the underlying randomization-tail probability is approximately **0.002991**. This is Monte Carlo precision for these linkage nulls, not a p-value for stock returns, a test of investment alpha, or evidence of an institutional information advantage.

The owner and share-only nulls are materially consistent with Phase 210's 500-replicate results. The date and joint nulls are replaced by the lag-preserving versions. The old Phase 210 raw-date date-null mean was 194.352; the corrected lag-null mean is 210.735. The observed 340 still exceeds the corrected null maximum of 238.

## 5. Interpretation and limits

- The exact-first Form 144/Form 4 document linkage remains strongly corroborated in this single 2026 Q3 sample under the corrected conditional date null.
- Form 144 is a proposed-sale notice, not proof of an executed sale.
- Form 4 code S includes open-market **or private** dispositions; the join does not prove an exchange execution or market impact.
- The 40 class-family conflicts/unresolved exact links remain quarantined from security-level inference.
- The sample is one quarter and a 289-issuer Form 144 subset, not a survivorship-free broad-market universe.
- Filing dates are date-only in the bulk data. Actual EDGAR acceptance/first-public-availability timestamps, complete Form 4/A lineage and multi-quarter replication remain unresolved.
- The legacy 335-name universe is not treated as the research universe; no current ticker mapping is used to rewrite historical identity.

**Decision:** retain Form 144 only as a conditional event-supply / ex-post document-linkage candidate. Do not promote it to a PIT feature or authorize a forward-return/alpha test. Form 4 remains ex-post validation, not a backfilled predictor.

## 6. Next gates

1. Obtain an authorized SEC_CONTACT_EMAIL secret before any adjacent-quarter SEC retrieval; Phase 153 and the broader acceptance-clock work remain blocked without it.
2. Extend the exact-first linkage and lag-preserving placebo to multiple adjacent quarters, including the 2023-04-13 electronic-reporting boundary.
3. Join actual EDGAR acceptance timestamps and preserve every original/amended accession as an append-only vintage.
4. Resolve security-class identity with an effective-dated permanent identifier; keep unresolved classes quarantined.
5. Obtain appropriately licensed, delisted-inclusive historical market data before computing ADV20 or forward returns. Do not substitute personal-use vendor data or current ticker mappings.
6. Only after those gates pass, preregister a next-session supply-pressure test against frozen LTM/F80 with identical exposure/costs, chronological walk-forward, date-block bootstrap, LOO, multiple-testing control and a new prospective final holdout.

No return, alpha, bootstrap/LOO, chronological OOS or holdout test was run. No new SEC request or vendor contact occurred. No data were purchased. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe and capital are unchanged.

## Reproducibility

- Code: research/phase256_form144_form4_lag_preserving_placebo_audit.py
- Tests: research/test_phase256_form144_form4_lag_preserving_placebo_audit.py
- Result: research/phase256_form144_form4_lag_preserving_placebo_audit_result.json
- Workflow: .github/workflows/phase256_form144_form4_lag_preserving_placebo_audit.yml
- Local unit tests: **8/8 passed**. Hosted validation is run by the dedicated Phase 256 workflow.
