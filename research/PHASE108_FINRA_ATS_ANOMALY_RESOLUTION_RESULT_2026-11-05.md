# Phase 108 — FINRA ATS anomaly-resolution result

**Date:** 2026-11-05  
**Run:** [41983989795](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41983989795)  
**Commit executed:** `21d803e650deee3cdc09d5d7c332ffe72cfc7734`  
**Artifact:** `phase108-finra-ats-anomaly-resolution` (ID `13395870951`, SHA-256 `8f8357fc1789515816ffb9b5be56e52de065a05a80ded80851fc62cb46e08364`)  
**Status:** targeted data-integrity probe passed; definitive FINRA natural-key and revision semantics remain unproven. No returns or alpha test.

## Execution

- Actions job `audit`: success; offline regression tests passed.
- Two complete partitions re-queried with 16 fields, including MPID, firm CRD, participant name, first publication, last update and last-reported dates.
- 56 pages downloaded; both partitions reconciled exactly to FINRA `Record-Total`.
- No request errors and no requested-week/tier mismatches.

| Week / tier | Rows | Pages | Missing-symbol rows | Symbol-firm rows | Symbol aggregates | Aggregates updated after first publication | Coarse collisions | Expanded-key collisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022-01-03 / T2 | 139,176 | 28 | 2 | 120,447 | 18,533 | 123 (0.664%) | 9,653 | 0 |
| 2025-01-06 / T2 | 136,362 | 28 | 0 | 119,497 | 16,677 | 6 (0.036%) | 8,964 | 0 |
| **Total** | **275,538** | **56** | **2** | **239,944** | **35,210** | **129** | **18,617** | **0** |

The coarse key (symbol, week, tier, summary type, product type) is insufficient. It collapses separate participant contributions and/or different `lastReportedDate` cohorts. The diagnostic expanded key (coarse key + MPID + firm CRD + `lastReportedDate`) produced zero collision groups in both full partitions. This is evidence that the Phase 100 LND “duplicate” finding was a key-design false positive, not proof that the proposed expanded key is FINRA's definitive natural key.

## Resolved anomalies

### 1. LND, 2025-01-06 / T2

The re-query returned 28 LND rows, not two conflicting duplicates. They include distinct ATS MPIDs, two De Minimis Firm rows, symbol-level aggregate rows and different `lastReportedDate` values. No two rows collided on the expanded diagnostic key.

The two `ATS_W_SMBL` rows have different `lastReportedDate` values (2025-01-08 and 2025-01-10) and different quantities. The two `OTC_W_SMBL` rows likewise have different last-reported dates. For OTC, each symbol-level row exactly matches its De Minimis Firm row for the same date. For ATS, the 2025-01-08 symbol aggregate equals the sum of the firm-level rows reported on 2025-01-07 and 2025-01-08; the 2025-01-10 symbol aggregate matches the firm-level contribution for 2025-01-10.

This is consistent with distinct reporting cohorts / overlapping aggregation levels, not duplicate records. It also demonstrates why the symbol-level and symbol-firm rows must not be added together as independent volume. A broader reconciliation is still required before deciding whether symbol-only rows are incremental cohorts, snapshots, or another FINRA aggregation convention.

### 2. Missing-symbol rows, 2022-01-03 / T2

Both rows have the correct requested week and tier. They are not partition mismatches:

- One `OTC_W_SMBL_FIRM` row is attributed to “De Minimis Firms” (`firmCRDNumber=0`, no MPID, no symbol).
- One `OTC_W_SMBL` row has `productTypeCode=UTP`, no symbol, MPID or firm CRD.

They cannot be mapped to a security and must be excluded from security-level features while retained in an unallocated completeness/reconciliation bucket. They should not invalidate the entire partition or be silently assigned to a ticker.

## PIT and feature-construction decision

- `lastReportedDate` is a reporting/update field, not the date on which the underlying trades occurred.
- `lastUpdateDate` later than `initialPublishedDate` signals that the current historical record incorporates a later update. The 129 such symbol-aggregate records in these two samples (0.366% of 35,210) do not carry a historical revision ledger.
- Do not backfill the latest current value to `initialPublishedDate` as though it were the value investors originally saw.
- Until a revision ledger is proven, a conservative candidate panel may retain only rows with `lastUpdateDate <= initialPublishedDate`; rows with later updates must be excluded from a first-publication-vintage test, or separately quarantined. This is a proposed filter, not yet validated against every partition.
- Keep symbol-only and symbol-firm datasets separate. Use symbol-only aggregates for total-activity features and firm-level records for participant concentration/composition only after reconciliation; never sum both levels.
- Participant/MPID concentration is a market-structure hypothesis, not proof of beneficial ownership, informed trading or directional demand.

## Decision

**Phase 108 passed its targeted anomaly-resolution objective.** The LND coarse-key collision is resolved as distinct rows; the two blank-symbol records are classified as unallocated OTC rows; both partitions have exact page/record reconciliation and zero expanded-key collisions.

**FINRA ATS remains conditional, not ready for an alpha test.** Next gate: re-audit all ten Phase 100 partitions with the expanded fields, reconcile symbol and symbol-firm aggregation by reporting cohort, verify the natural key/revision interpretation, and establish security identity/PIT linkage over the broad historical universe. The historic endpoint's limited rolling window remains a material history constraint.

No prices or forward returns were used. No alpha test was authorized. No vendor was contacted or purchased. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
