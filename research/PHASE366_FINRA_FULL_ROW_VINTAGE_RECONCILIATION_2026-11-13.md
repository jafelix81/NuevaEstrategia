# Phase 366 — FINRA full-row vintage reconciliation

**Date:** 2026-11-13 UTC  
**Status:** COMPLETED — all four targeted partitions were fully retrieved; OTCE selected-field row multiset matched, while T1 had 24 row-level mismatches requiring field diagnosis.  
**Research class:** historical row consistency only

## Executive result

Phase 366 downloaded all rows from the 2025-10-20 T1 and OTCE partitions in both `weeklySummaryHistoric` and `weeklySummary`: **178,816 rows across four partition-dataset combinations, 38 pages, zero retrieval errors**.

The result is mixed:

- **OTCE:** 24,292/24,292 row fingerprints matched exactly across the 16 canonical fields used by the audit. The Phase 365 first-page discrepancy in participant-ID presence was a sampling/order effect: full-partition participant-ID rows were 13,425 in both datasets; De Minimis rows were 7,834 in both; unique symbols were 8,229 in both.
- **T1:** record totals and broad composition matched, but 24 of 65,116 rows differed under the same selected-field fingerprint (0.0369%). There were 24 current-only rows, 24 historic-only rows and 24 identity-key groups whose row content differed. The differing fields have not yet been isolated.

The result is not a blanket approval of current-vs-historic interchangeability.

## 1. Retrieval and partition counts

| Tier | Current rows | Historic rows | Pages per dataset | Record totals equal |
|---|---:|---:|---:|---|
| OTCE | 24,292 | 24,292 | 5 | Yes |
| T1 | 65,116 | 65,116 | 14 | Yes |

All page-level counts and offsets reconciled to FINRA response headers. The workflow completed successfully; 7/7 offline tests passed.

Run: [43455306406](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43455306406)  
Artifact: [14054525109](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43455306406/artifacts/14054525109)

## 2. OTCE — first-page discrepancy resolved, with one schema caveat

The complete OTCE row multiset matched across the 16 canonical fields. The Phase 365 sample had shown 10/10 participant-ID rows in the historic sample and 0/10 in the current sample. Full-partition counts were identical instead:

- 13,425 rows with MPID or CRD in both datasets.
- 7,834 De Minimis rows in both datasets.
- 8,229 unique symbols in both datasets.
- Summary-type, tier-description, product-type and date distributions matched.

Therefore the ten-row difference was caused by which rows appeared on the unsorted first page, not evidence of systematic participant-ID removal.

**Caveat:** Phase 366's canonical field set omitted `summaryStartDate`, which was present in both datasets. The historic endpoint also returned an extra `historicalweek` helper field. The exact-match result is therefore exact only over the selected canonical fields, not every field in the full schema. Phase 367 will include `summaryStartDate` and explicitly exclude only the historic query-helper field from the cross-dataset comparison.

## 3. T1 — small but real selected-field discrepancy

- Exact selected-field row matches: **65,092 / 65,116**.
- Current-only rows: 24.
- Historic-only rows: 24.
- Mismatched identity-key groups: 24.
- Difference rate: **0.0369%** of rows.

Counts by summary type, tier description and product type matched. Unique-symbol count (2,420), participant-ID row count (60,282) and De Minimis row count (2,420) also matched.

The summed `totalNotionalSum` differed slightly between datasets: the ATS aggregate totals differed by approximately 0.000003 and OTC aggregate totals by approximately 0.000005 in absolute terms, depending on summary type. These are very small differences, but they must not be dismissed as formatting until row-level field comparisons establish which records and fields differ.

The numeric-total equality flag also reported false for OTCE because the output comparison retained differing decimal scale/trailing zeros (for example `1` vs `1.000000`). This is a comparison-normalization defect, not evidence of a numeric difference for OTCE. Phase 367 will normalize Decimal values before testing numeric equality.

## 4. Audit limitations

Phase 366 hashed a fixed set of 16 canonical fields. It did not compare `summaryStartDate`; it did not persist raw rows, symbol keys, MPIDs, CRDs or firm names. The 24 T1 row mismatches therefore remain unresolved at field level.

The full partition results do establish:
- old current-dataset partitions are genuinely queryable;
- the sampled current/historic record totals match;
- OTCE selected-field content matches in full;
- T1 has a small but nonzero set of selected-field differences.

They do not establish full historical coverage, first-receipt timestamps, original publication vintages or strict point-in-time availability.

## 5. Next gate — Phase 367

Re-fetch the 2025-10-20 T1 partition from both datasets and compare rows by hashed identity key. Add `summaryStartDate` to the canonical field set, normalize numeric fields with Decimal semantics, and report only anonymized per-field mismatch counts, signed/absolute numeric differences and mismatch counts by summary type. No raw row values or identifiers will be retained.

## 6. Decision

- Keep FINRA T1 ATS as a conditional market-structure candidate, but do not use current and historic rows interchangeably until the 24 mismatches are explained.
- OTCE selected-field comparison passes for this one week, but its historical universe/coverage and PIT availability remain unproven.
- Do not treat participant IDs as beneficial-owner identities or as evidence of informed trading.
- No signal admitted. No return, alpha, OOS, bootstrap, LOO or holdout test was run.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

Official reference: [FINRA Developer Center — Query API, historical datasets and data versioning](https://developer.finra.org/docs).
