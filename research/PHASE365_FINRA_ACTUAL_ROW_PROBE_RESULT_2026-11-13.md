# Phase 365 — FINRA actual-row probe: partial result and query-universe correction

**Date:** 2026-11-13 UTC  
**Status:** COMPLETED — 33/50 planned probes returned rows; 17 probes targeted partition combinations absent from the official inventory. The workflow failed its overly strict completeness gate; this is not evidence that the 33 successful responses were invalid.  
**Research class:** source feasibility / historical row availability only

## Executive result

Phase 365 moved the Phase 364 catalog anomaly beyond metadata: the current `weeklySummary` endpoint returned actual rows for sampled partitions dated 2022-01-03, 2025-10-20 and 2025-11-10. Each of those weeks returned nonzero T1, T2, OTCE and NA partitions. Across those 12 current-dataset partitions, the API reported the same record totals as the corresponding historic partitions.

This is evidence that some old current-dataset partitions remain queryable, despite FINRA's documentation describing `weeklySummary` as a rolling twelve-month dataset. It is not evidence that every catalogued partition is populated or that the full history is complete.

## 1. Probe accounting

- Planned: 50 probes (five weeks × five tier identifiers × two datasets).
- Completed with rows: **33**.
- Failed probes: **17**, all matching combinations absent from the Phase 364 inventory:
  - 5 historic `2026-10-19` combinations; the historic inventory ends at `2025-11-10`.
  - 5 current `2021-11-15` combinations; the current inventory begins at `2021-12-06`.
  - 3 current `NMS` combinations for 2022-01-03, 2025-10-20 and 2025-11-10; current NMS inventory contains only 17 weeks in 2023.
  - 4 current combinations for 2026-10-19 (`T2`, `OTCE`, `NA`, `NMS)); only `T1` is listed for that week.
- The absent current partitions generally returned an empty response body, which the probe recorded as JSON decode errors. The historic out-of-range combinations returned HTTP 400.
- The workflow failed because it required all 50 Cartesian-product probes to succeed. The inventory shows that this was the wrong gate: unavailable combinations should have been classified as expected absences, not queried as if they were valid partitions.

Run: [43444391496](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43444391496)  
Artifact: [14047148064](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43444391496/artifacts/14047148064)

## 2. Confirmed old current-dataset rows

The current `weeklySummary` endpoint returned these 12 nonzero partition samples:

| Week | T1 | T2 | OTCE | NA |
|---|---:|---:|---:|---:|
| 2022-01-03 | 46,834 | 139,176 | 23,754 | 6 |
| 2025-10-20 | 65,116 | 158,099 | 24,292 | 6 |
| 2025-11-10 | 65,650 | 159,660 | 25,350 | 6 |

The numbers are FINRA `Record-Total` values, not row counts retained in the artifact. Ten rows were sampled per partition; full partitions were not downloaded in Phase 365.

The same record totals were returned by `weeklySummaryHistoric` for all 12 overlap pairs. Eleven of twelve sample signatures matched. The only mismatch was `2025-10-20/OTCE`:

- Both datasets returned 24,292 total records.
- Both ten-row samples contained 10 `OTC_W_SMBL_FIRM` rows, 10 unique symbols and 10 rows labelled `De Minimis Firms`.
- The historic sample had participant identifiers present on 10/10 rows; the current sample had identifiers present on 0/10 rows.
- The other sampled type, tier-description and date summaries matched.

The mismatch may be caused by sample ordering/selection or a difference in the row vintage/schema. Phase 365 retained no raw rows and cannot distinguish these explanations. Do not infer anonymization, data corruption or identity loss from this ten-row comparison.

## 3. NA and NMS are not admitted as security tiers

The sampled `NA` partitions contained exactly six rows: three `ATS_W_VOL_STATS` and three `OTC_W_VOL_STATS`, with tier description `Not Applicable`. These are summary-statistic rows, not a stock-level tier.

Historic `NMS` samples contained mixed `NMS Tier 1`, `NMS Tier 2` and `Not Applicable` descriptions and mixed summary types. The current `NMS` partition inventory is sparse (17 weeks in 2023). Keep `NMS` quarantined as a combined/legacy category until its full-row semantics are documented. Do not map it to T1 or T2.

## 4. Next gate — Phase 366

Phase 366 performs full-page row-multiset comparisons for two overlapping 2025-10-20 partitions:

- T1: the main FINRA candidate slice.
- OTCE: the partition with the Phase 365 sample-signature mismatch.

It compares all rows from `weeklySummaryHistoric` and `weeklySummary` using a canonical, order-independent row fingerprint, identity-key group counts, numeric totals and field-presence summaries. Only counts and SHA-256 digests are retained. The comparison must determine whether the Phase 365 OTCE discrepancy is merely first-page selection or a genuine row-level vintage difference.

Phase 366 is not an alpha test. No returns, signals, OOS, bootstrap, LOO or holdout are used.

## 5. Decision

- Current `weeklySummary` old partitions are demonstrably queryable for the three sampled weeks and four sampled tiers, but full historical completeness remains unproven.
- T1 ATS remains a conditional market-structure candidate; OTC De Minimis aggregation and T2 row-grain limitations remain.
- NA is summary-only in the sampled partitions; NMS remains quarantined.
- The Phase 365 workflow failure is classified as a probe-design/gating defect caused by intentionally unavailable partition combinations, not a FINRA data outage.
- No signal admitted. No return test authorized. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

Official reference: [FINRA Developer Center — Query API and Weekly Summary documentation](https://developer.finra.org/docs).
