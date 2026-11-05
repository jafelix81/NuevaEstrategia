# Phase 107 — FINRA ATS live revalidation: preliminary audit record

**Date:** 2026-11-05  
**Status:** live retrieval completed in first corrected attempt; output serialization failed. A corrected full run is in progress.  
**Scope:** feasibility and data integrity only. No returns or alpha test.

## 1. Execution evidence

- Initial corrected run: [Actions 41976736121](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41976736121)
- Job: `revalidation` (127077220477)
- Artifact: [phase100-finra-ats-revalidation, 13392981544](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41976736121/artifacts/13392981544)
- Offline parser tests: 15/15 passed.
- Live API retrieval: all 10 requested partitions completed. Every retrieved row count matched FINRA's `Record-Total` exactly.

| Week | T1 rows | T2 rows |
|---|---:|---:|
| 2022-01-03 | 46,834 | 139,176 |
| 2023-01-09 | 49,989 | 137,137 |
| 2024-01-08 | 50,329 | 128,202 |
| 2025-01-06 | 56,895 | 136,362 |
| 2025-10-20 | 65,116 | 158,099 |
| **Total** | **269,163** | **698,976** |

Total retrieved: **968,139 rows**. The partial artifact contains 108,444 symbol-level aggregates: 52,007 ATS and 56,437 non-ATS OTC rows.

## 2. Preliminary data-quality observations

- Zero invalid/negative quantity fields in the ten partitions.
- `initialPublishedDate` was non-null for 100% of the symbol-level rows in the partial artifact.
- Observed publication lag was 21 calendar days for T1 and 35 days for T2, consistent with the sample's two-/four-week reporting delays followed by the first Monday publication convention.
- 1,882 of 108,444 symbol-level rows (1.735%) had `lastUpdateDate` later than `initialPublishedDate`. The latest snapshot must not be backdated to first publication; use the later update date as the conservative candidate knowledge date, subject to validation of the exact publication semantics.
- Two conflicting duplicate aggregate-key groups were found for **LND**, week 2025-01-06, T2: one `ATS_W_SMBL` and one `OTC_W_SMBL`, both `CTS`. Values and `lastReportedDate` differ. Do not sum, select, or silently deduplicate them. Exclude unresolved duplicate keys from any later feature panel until their cause is understood.
- The 2022-01-03 T2 partition had two row-level integrity mismatches, including one `OTC_W_SMBL` row without a symbol. The initial artifact did not preserve the full mismatch examples because the run failed before writing the JSON summary; the corrected run must expose them.

The partial CSV also reports per-tier legacy-335 overlaps. These are only a comparison against the user's manually/arbitrarily selected F80 set, not broad-universe coverage.

## 3. Technical failure and correction

The live retrieval itself completed. The job failed while writing `page_hashes.csv`: the DictWriter schema predated new synchronous-pagination metadata (`record_offset`, `page_count_source`, `request_attempts`, `record_limit`, `total_records_on_page_header`). The partial artifact therefore contains `partition_summary.csv` and an empty `page_hashes.csv`, but not the final `summary.json`.

Corrections committed to `phase99-broad-pit-universe-charter`:
- `ddc26beb`: synchronize the page-hash CSV schema with both sync and async metadata; add the missing Record-Total reconciliation gate; separate coverage/schema from duplicate integrity; treat a completed audit with a failed research gate as a completed audit rather than a software crash; count all duplicate groups, not just the first ten.
- `6f3cec6a`: add regression tests for the page-hash schema, Record-Total reconciliation, legacy-335 diagnostic-only treatment, and complete duplicate-group counts.
- `239ab14d`: remove the 90% legacy-335 overlap requirement from the source-coverage gate. The 335 names are arbitrary and cannot be used as a representative market-coverage threshold.

The latest run, [41978867803](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41978867803), is executing the complete corrected audit. Intermediate runs were cancelled by the workflow concurrency group; no additional run was launched while the latest one was active.

## 4. Source-history and PIT interpretation

FINRA's official documentation states that production `weeklySummary` contains a rolling 12 months, while `weeklySummaryHistoric` contains a rolling four years starting one year prior to the current date; data older than one year is static and should not be repeatedly re-downloaded for updates. This gives a practical combined window of recent production data plus the historic archive, but it is not a multi-decade source. See [FINRA Weekly Summary documentation](https://developer.finra.org/docs#query_api-equity-weekly_summary), especially the dataset details.

The official FINRA Q1 2021 API update introduced the historical weekly dataset and described its four-year rolling history: [FINRA Q1 2021 API Update](https://developer.finra.org/news/q12021).

A final historical snapshot that contains post-initial-publication updates must be made available only from its last update date, not from the original first-publication date. This is conservative but still does not reconstruct interim vintages. No alpha test is authorized until the full output, row-level anomalies, security identity and PIT rules are resolved.

## 5. Decision

**Retain FINRA weekly ATS/non-ATS as a promising public candidate, not a Smart Money signal.** It measures off-exchange activity, not trade aggressor direction, beneficial ownership or investor sophistication. The current evidence supports a source-feasibility pass in scale and field availability, but the strict row-integrity and duplicate-key gates remain unresolved.

No forward returns, feature selection, alpha test, vendor contact, purchase, data acquisition or F80 change occurred. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
