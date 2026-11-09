# Phase 238 — Form 144 / Form 4 reverse-linkage coverage and plan-flag selection audit

**Date:** 2026-11-09 UTC  
**Disposition:** Form 144 is a selective Rule 144 notice subset, not a census of insider sales. The raw AFF10B5ONE linkage gap is not supported as an incremental issuer/role-conditioned predictor. **No feature or alpha admission.**  
**Scope:** immutable Phase 69 Form 144 issuer panel and Phase 39 2026 Q3 Form 4 bulk snapshot. No SEC request, purchase, forward-return test, holdout use, or production change.

## Executive result

I reversed the Phase 208–210 linkage perspective. Instead of asking how many Form 144 notices can be linked to Form 4 dispositions, I asked how many eligible Form 4 sale blocks from the same 289-issuer panel link back to a Form 144 notice under the existing conservative exact-first protocol.

- The 2026 Q3 Form 4 snapshot contains **1,665 eligible single-owner non-derivative code-S disposition blocks** for issuers represented in the 289-CIK Form 144 panel.
- **570/1,665 (34.23%)** link one-to-one to an eligible Form 144 notice: 521 exact date-and-share links plus 49 mutually unique 0–2-day fallback links.
- The remaining **1,095 blocks are unmatched**, but cannot be classified as missing or noncompliant Form 144 filings. Form 4 code S includes open-market or private sales, and not every Form 4 sale is necessarily a Rule 144 notice event.
- A crude comparison shows lower Form 144 linkage for Form 4 transactions with AFF10B5ONE=true (29.17%) than for false (47.99%), an unadjusted gap of **−18.82 percentage points**.
- That gap is not robust after conditioning on issuer and reporting-owner relationship: within issuer × relationship strata, the plan-minus-nonplan difference is **−6.96 pp**, with a two-sided conditional-randomization p-value of **0.960** (20,000 permutations).

**Decision:** do not use AFF10B5ONE as a standalone predictor of Form 144 notice linkage. The unadjusted difference is largely a composition effect in this one-quarter sample. This is a source-selection diagnostic, not a return or alpha test.

## 1. Immutable inputs and sample boundary

| Input | Source |
|---|---|
| Form 144 | Phase 69 run 41959603351, artifact 13385365595, member expanded_issuer_event_raw.csv |
| Form 144 CSV SHA-256 | 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659 |
| Form 4 | Phase 39 run 40606706518, artifact 12781850078, member 2026q3_form345.zip |
| Form 4 inner ZIP SHA-256 | a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3 |

The Form 144 issuer panel contains 21,634 unique accession rows and 289 issuer CIKs. The 2026 Q3 sample contains 1,487 original Form 144 notices and 1,460 sale tranches. To avoid right-censoring against the Form 4 bulk snapshot ending 2026-09-30, a notice is eligible only when its **latest** approximate tranche date is on or before 2026-09-24. This leaves 1,451 notices and 1,460 tranches; 36 notices are excluded for right-censoring or unparseable dates.

The Form 4 snapshot contains 38,152 submissions and 59,885 non-derivative transaction rows. The conservative eligible-sale filter yields 1,665 blocks from 220 of the 289 panel issuers.

## 2. Form 4 eligibility and identity rules

A Form 4 sale block is included only when all conditions hold:

1. Original Form 4 submission (DOCUMENT_TYPE=4), not Form 4/A.
2. Table I non-derivative transaction (TRANS_FORM_TYPE=4).
3. Disposition code S (TRANS_CODE=S) and disposition indicator D.
4. Not marked late (TRANS_TIMELINESS != L).
5. Exactly one reporting owner in the accession.
6. Positive reported shares, valid transaction date and filing date, and filing lag from 0 to 4 calendar days.
7. Issuer CIK is one of the 289 issuer CIKs represented in the Form 144 panel.

Transactions are aggregated by Form 4 accession and transaction date. The AFF10B5ONE flag is accession-level; it is not a transaction-line intent field. All 1,665 retained blocks have a parseable true/false flag in this snapshot.

Form 144 matching uses exact normalized issuer CIK and exact normalized seller/reporting-owner name. No fuzzy aliases, token reordering, joint-owner expansion, or class-based rescue is used.

## 3. Exact-first linkage results

| Linkage stage | Result |
|---|---:|
| Exact date + exact shares candidate edges | 521 |
| Mutually unique exact links | 521 |
| Ambiguous exact tranche nodes | 0 |
| Ambiguous exact Form 4 block nodes | 0 |
| Fallback candidate edges after reserving exact nodes | 80 |
| Additional mutually unique fallback links (0–2 days) | 49 |
| **Total mutually unique links** | **570** |
| Distinct Form 144 notices linked | 570 |
| Distinct Form 4 sale blocks linked | 570 |
| Issuer CIKs with at least one link | 137 |
| Form 4 blocks linked / eligible panel-issuer blocks | **34.23%** |

The 49 fallback links comprise 31 same-day, 16 one-day and 2 two-day gaps. All 521 exact links are one-to-one under the exact graph. The exact-link class-family diagnostic agrees for 481/521 (92.32%); 40 remain conflicted or unresolved. Class-family agreement is descriptive only and is not a complete effective-dated security crosswalk.

The 34.23% figure is a **cross-source linkage rate within this selected issuer panel and one quarter**. It is not Form 144 recall, a compliance rate, or the fraction of all legally notice-required sales.

## 4. AFF10B5ONE selection diagnostic

| Form 4 accession-level flag | Blocks | Linked blocks | Linkage rate | Wilson 95% interval |
|---|---:|---:|---:|---:|
| true | 1,217 | 355 | 29.17% | 26.69%–31.79% |
| false | 448 | 215 | 47.99% | 43.40%–52.61% |

The unadjusted difference is **−18.82 pp** (plan minus non-plan). It is not a valid independent effect estimate because the plan and non-plan blocks have different issuer and reporting-owner-role composition.

I therefore ran a conditional randomization diagnostic that preserves the number of plan and non-plan labels within each stratum and permutes only those labels. The statistic is the plan-minus-nonplan linkage-rate difference among blocks in mixed strata.

| Conditioning strata | Mixed strata | Blocks | Observed difference | Two-sided p-value |
|---|---:|---:|---:|---:|
| Issuer | 63 | 851 | −15.83 pp | 0.557 |
| Issuer × reporting-owner relationship | 55 | 313 | −6.96 pp | 0.960 |

Each test uses 20,000 permutations and plus-one p-value correction (seeds 238 and 239). The null assumes AFF10B5ONE labels are exchangeable within the stated strata; it is a diagnostic, not a causal test. The issuer × role result provides no evidence that the raw plan-flag gap survives this coarse conditioning. Sparse mixed strata and remaining differences in sale size, security class, affiliate status, restrictions, and timing remain limitations.

The role table is retained in the JSON result for transparency. Several role cells are small and should not be interpreted independently.

## 5. Sale-size diagnostic

The matched Form 4 blocks have a median reported size of 7,717.5 shares versus 10,000 shares for unmatched blocks. Linkage rates by share-size bin are non-monotonic:

| Form 4 block shares | Blocks | Linked | Linkage rate |
|---|---:|---:|---:|
| ≤1,000 | 219 | 91 | 41.55% |
| 1,001–5,000 | 412 | 155 | 37.62% |
| 5,001–10,000 | 304 | 82 | 26.97% |
| 10,001–50,000 | 532 | 174 | 32.71% |
| 50,001–100,000 | 84 | 31 | 36.90% |
| >100,000 | 114 | 37 | 32.46% |

This is not a Rule 144 threshold test: the legal notice threshold is based on aggregate sales over a three-month period and applies only to qualifying restricted/control securities and affiliates. A single Form 4 block's share count is not sufficient to determine whether a Form 144 notice was required. The non-monotonic pattern also cautions against treating the linkage subset as simply “the largest sales.”

## 6. Interpretation limits

- Form 144 is a Rule 144 proposed-sale notice, not a census of insider sales.
- Form 4 code S covers open-market **or private** sales; it is not an exchange execution tape and does not establish venue, aggressor side, or market impact.
- The 1,095 unmatched Form 4 blocks are **not** classified as missing or noncompliant Form 144 filings. They may not be Rule 144 notice events, may involve unrestricted securities, may be outside the electronic Form 144 panel, or may fail conservative name/owner matching.
- Exact seller-name matching misses aliases, trusts, name changes, joint owners and multi-owner Form 4 accessions.
- The sample is one quarter and the Form 144 panel is a current-universe 289-CIK subset, not a survivorship-free historical universe.
- Form 144 approximate sale date is not an EDGAR acceptance timestamp. The Form 4 bulk snapshot has date-only filing dates. This phase does not admit strict PIT.
- No forward returns, price-impact analysis, compliance conclusion, bootstrap/LOO return test, or OOS test was run.

## 7. Decision and next gates

1. **Reject Form 144 as a census of insider sales.** Retain it only as a threshold-censored Rule 144 notice event candidate.
2. **Do not use AFF10B5ONE alone to predict Form 144 linkage.** The unadjusted gap is not robust after issuer and reporting-owner-role conditioning.
3. Do not backfill Form 4 details into a Form 144 feature. Form 4 remains ex-post linkage/validation only.
4. Continue only after full-panel acceptance-header vintages, effective-dated issuer/class identity, and independent PIT shares/float/ADV are admitted.
5. If the composite Form 144 notice event later passes those gates, preregister one mixed-route event study with explicit threshold-censoring and seller-role controls. Compare to frozen LTM/F80 with identical exposure/costs, chronological validation, date-block bootstrap and LOO. Use a new prospective final holdout.

**No alpha test is authorized by Phase 238.** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; the legacy holdout remains CONSUMED_NOT_PRISTINE and was not used.

## 8. Reproducibility

- Auditor: research/phase238_form144_form4_selection_coverage_audit.py
- Tests: research/test_phase238_form144_form4_selection_coverage_audit.py
- Result: research/phase238_form144_form4_selection_coverage_audit_result.json
- Offline tests: **5/5 passed**.
- Full reproduction: 20,000 conditional permutations per stratification, deterministic seeds 238 and 239.
- The script accepts local paths to the two immutable artifact members and verifies both SHA-256 hashes before analysis.
- No hosted CI run is claimed; this phase's commits use [skip ci] to avoid triggering the legacy PR workflow matrix.

## Sources and prior controls

- Phase 207 — Form 144 panel semantic/event feasibility.
- Phase 208 — Form 144 to Form 4 execution-conversion audit.
- Phase 209 — exact-first matching-order sensitivity.
- Phase 210 — linkage placebos and price concordance.
- Phase 211 — EDGAR acceptance-clock pilot.
- Phase 212 — intermediary/route identifiability.
- 17 CFR 230.144: https://www.ecfr.gov/current/title-17/chapter-II/part-230/section-230.144
- SEC, File Form 144 Electronically: https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically
- SEC Form 4 and transaction reporting instructions: https://www.sec.gov/files/form4.pdf
