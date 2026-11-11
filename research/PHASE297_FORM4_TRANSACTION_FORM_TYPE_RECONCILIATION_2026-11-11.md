# Phase 297 — Form 4 transaction-form-type reconciliation

**Date:** 2026-11-11 UTC  
**Status:** Completed offline data-quality correction; no return or alpha test. Hosted verification: [run 43094005689](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43094005689) passed with 6/6 deterministic tests; metadata artifact [13889458408](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43094005689/artifacts/13889458408).  
**Source:** immutable Phase 294 SEC Form 345 sample artifact, run 43083625013 / artifact 13884014630; outer SHA-256 8b256375a68ffc581134e3fb05dd96ca3a02f6acd47925a003aa3f4b3d1680f4.

## Executive finding

A reproducibility pass found one eligibility omission in the Phase 296 conservative cohort: it required an original Form 4 submission, but did not also require transaction-level TRANS_FORM_TYPE=4. The existing Phase 271 Table I contract does require that transaction-form-type condition.

The Phase 296 count of 15,590 candidate rows therefore included 115 rows with TRANS_FORM_TYPE=5. Requiring TRANS_FORM_TYPE=4 reduces the candidate cohort to **15,475 rows**. This is a small 0.74% correction, but it is necessary before event construction or modeling.

| Measure | Phase 296 definition | Corrected Table I definition |
|---|---:|---:|
| Transaction rows | 15,590 | **15,475** |
| Unique accessions | 11,088 | **10,997** |
| Unique issuer CIKs | 3,243 | **3,226** |
| Unique reporting-owner CIKs | 6,728 | **6,677** |

The 115 excluded type-5 rows occur across 97 accessions, 42 issuer CIKs and 70 reporting-owner CIKs. Those are gross affected identities; some accessions, issuers and owners also have valid type-4 rows, which is why the net cohort reductions are smaller.

## Reconciled population

The six purposive quarterly archives contain 317,267 Form 4/4-A accessions: 310,561 with one reporting owner, 6,706 with multiple reporting owners and none without an owner. No duplicate reporting-owner CIK rows were found.

Among the 28,663 broad P / acquired / direct rows, 28,016 have transaction form type 4 and 647 have type 5. The positive-price/positive-share screen contains 27,902 rows across both types; 27,286 are type 4, and 25,381 are type-4 rows with one reporting owner.

The corrected 15,475-row cohort retains the original Phase 296 requirements: code P, acquired direction, direct ownership, positive shares and price, original Form 4 submission, one reporting owner, and a 0–2 calendar-day transaction-to-filing lag. It now also requires transaction form type 4.

### Plan-status handling

| AFF10B5ONE status | Before correction | Corrected cohort |
|---|---:|---:|
| Explicit false | 6,995 | 6,963 |
| Explicit true | 201 | 201 |
| Unknown / blank / field absent | 8,394 | 8,311 |

Unknown remains unknown, never false. The checkbox gate is applied using each filing's actual date from 2023-04-01 onward; it is not inferred from the quarter label.

## Explicit-open-market footnote screen

The versioned Phase 271 high-precision / low-recall text screen was recomputed across all six purposive quarters. It requires an explicit open-market phrase, no explicit private / plan / mechanical-compensation wording, direct ownership, one reporting owner, common-stock title, and (for filings on or after 2023-04-01) AFF10B5ONE explicitly false.

| Quarter | High-precision rows | Also positive shares and price |
|---|---:|---:|
| 2006Q1 | 10 | 10 |
| 2012Q1 | 102 | 54 |
| 2023Q1 | 59 | 59 |
| 2023Q2 | 92 | 92 |
| 2025Q3 | 65 | 65 |
| 2026Q3 | 85 | 85 |
| **Total** | **413** | **365** |

The 2012Q1 difference is a useful warning: 48 rows pass the textual screen but do not have both a positive reported share quantity and price. These must not be silently converted into dollar purchase values.

All referenced footnote IDs in the six archives resolved (zero missing references). The previous Phase 296 lexical category hit-counts were not backed by a committed regex implementation; this phase retains the versioned Phase 271 patterns instead of relying on those unversioned counts.

## Interpretation and decision

- This corrects a data-definition omission; it is not evidence of predictive power.
- The corrected P-code cohort is still not an open-market-only cohort. SEC code P includes open-market or private purchases.
- The 413-row high-precision screen is explicit text evidence, not proof of discretionary intent, beneficial ownership independence or informed trading.
- The six quarters are purposive endpoint samples, not a continuous quarterly panel or a coverage census.
- No acceptance/PAC vintage, strict historical PIT, effective-dated share-class identity or survivorship-free universe coverage is established here.
- No forward returns, alpha, bootstrap/LOO, chronological OOS or holdout test was run.

**Decision:** use the corrected TRANS_FORM_TYPE=4 condition in any future Form 4 Table I event panel. Keep the high-precision footnote cohort as a separate sensitivity hypothesis. Continue with acceptance/PAC clock coverage and effective-dated security identity before preregistering returns.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. Production, universe, capital, parameters and holdout are unchanged.

## Reproducibility

- Auditor: research/phase297_form4_transaction_form_type_reconciliation.py
- Tests: research/test_phase297_form4_transaction_form_type_reconciliation.py
- Result: research/phase297_form4_transaction_form_type_reconciliation_result.json
- Workflow downloads the immutable Phase 294 artifact by run/artifact ID, verifies outer and six inner SHA-256 hashes, runs the offline tests and recomputes the report.
