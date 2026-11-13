# Phase 358 — FINRA weekly firm-grain reconciliation audit

**Date:** 2026-11-13 UTC  
**Branch:** `phase358-finra-weekly-firm-grain-audit`  
**Run:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/43408201884  
**Artifact:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/43408201884/artifacts/14028533780  
**Follow-up:** Phase 359 product-type key diagnostic is running on `phase359-finra-product-type-crosswalk-diagnostic`.

## Objective

Test whether FINRA weekly symbol-level ATS/OTC aggregates can be joined to firm-grain symbol rows, using current Query API fields `MPID` and `firmCRDNumber`. This is a data-grain feasibility audit only.

## Retrieval and partition integrity

Four historical partitions were retrieved from `weeklySummaryHistoric`:

| Week | Tier | Rows | Pages | Aggregate symbol/product groups | Firm symbol/product groups |
|---|---:|---:|---:|---:|---:|
| 2022-01-03 | T1 | 46,834 | 10 | 3,887 | 3,887 |
| 2022-01-03 | T2 | 139,176 | 28 | 18,532 | 18,524 |
| 2025-10-20 | T1 | 65,116 | 14 | 4,834 | 4,834 |
| 2025-10-20 | T2 | 158,099 | 32 | 17,979 | 17,977 |
| **Total** | | **409,225** | **84** | **45,232** | **45,222** |

- All four API `Record-Total` values reconciled exactly to retrieved row counts.
- No request or pagination errors.
- Seven offline regression tests passed.
- No firm-grain rows had missing MPID/CRD identifiers or participant names in the four samples.
- No negative or invalid quantity cells were detected.
- Two rows in 2022-01-03/T2 lacked `issueSymbolIdentifier`: one firm-grain row and one symbol aggregate. These are retained as exceptions, not imputed.

**Important distinction:** the GitHub Actions job completed successfully, but the research data gate did **not** pass. The artifact records `schema_and_partition_gate=FAIL_OR_REVIEW` because of the two missing-symbol rows.

## Join result — not admitted

The attempted exact join on normalized (symbol, productTypeCode, mapped summary type) returned:

- Exact symbol/product key matches: **0** across all four partitions.
- Aggregate groups without matching firm rows: **45,232**.
- Firm groups not present in aggregate key set: **45,222**.
- Firm-to-aggregate volume/trade reconciliation: **not computable**.
- Participant concentration: **not computable**; no HHI or top-participant share was produced.

The equal or near-equal group counts and unique-symbol counts do not prove that the keys align. The cause of the zero overlap is unresolved. Product-type values may differ by row grain, or another key-field/representation issue may exist. Do not remove `productTypeCode`, join on symbol alone, sum rows, or compute concentration until a dedicated crosswalk audit establishes that doing so is unambiguous.

Phase 359 now reports product-type distributions by summary type and compares exact symbol/product overlap with symbol-only overlap, without calculating any firm sums or concentration.

## Publication and PIT observations

The final historical snapshots contain non-null `initialPublishedDate`, `lastUpdateDate` and `lastReportedDate` on every symbol aggregate group. In 610 of 45,232 aggregate groups, `lastUpdateDate` was later than `initialPublishedDate`. This is a count of final-snapshot fields, not a vintage history.

FINRA's current developer documentation says:
- Tier 1 publication is delayed about two weeks; Tier 2/OTC about four weeks.
- `initialPublishedDate` represents the initial publication date; `lastUpdateDate` is the most recent date total trades were updated from data received from ATS/OTC firms.
- `weeklySummaryHistoric` provides a rolling four-year window beginning one year before the current date; data older than one year is static.

The historical endpoint returns the current final snapshot, not all intermediate versions. Do not backdate revised final rows to initial publication. Exact historical PIT remains unadmitted.

## Structural disclosure limitation

FINRA's published OTC transparency specification says non-ATS firm information is published only for firms meeting volume thresholds or as a de-minimis aggregate; it also describes further aggregation for firms below the per-security activity threshold. Therefore:

- ATS firm-grain coverage and OTC non-ATS firm-grain coverage must be assessed separately.
- A non-ATS firm-level sum should not be expected to reconcile fully to the OTC symbol aggregate where de-minimis volume is aggregated.
- Even if a join is repaired, OTC participant concentration is censored and cannot be described as complete market concentration.
- MPID/CRD identifies a reporting intermediary, not the beneficial owner or trade direction.

## Decision

**Phase 358 is a retrieval pass but a research-gate fail/review.** Firm-grain FINRA data is present, but the join is not yet established and no participant concentration metric is valid. Phase 359 is restricted to diagnosing the key mismatch. If a unique symbol-only bridge is supported, any later reconciliation must be ATS-only for completeness checks and treat non-ATS OTC as threshold-censored.

No returns, features, alpha, OOS, bootstrap, LOO or holdout tests were run. No data was admitted as PIT. No raw rows were uploaded to artifacts. F80, production, universe, capital and parameters remain unchanged.
