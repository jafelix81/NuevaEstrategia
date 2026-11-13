# Phase 364 — FINRA weekly partition inventory census

**Date:** 2026-11-13 UTC  
**Status:** COMPLETED — partition metadata retrieved and structurally parsed; actual row availability remains unverified  
**Research class:** source feasibility / historical coverage only

## Executive result

Phase 364 queried the official metadata and partitions endpoints for both FINRA OTCMarket weekly datasets:

- `weeklySummaryHistoric`: **1,045 unique partition pairs**, covering 209 consecutive week anchors from 2021-11-15 through 2025-11-10.
- `weeklySummary`: **1,031 unique partition pairs**, covering 2021-12-06 through 2026-10-19, but with a materially irregular tier distribution.
- Union: **1,235 unique week/tier pairs across 258 calendar-week anchors**.
- Historic/current intersection: **841 pairs**.
- No duplicate partition pairs were returned by either endpoint.
- Metadata and partitions endpoints agreed on the partition-field order `weekStartDate,tierIdentifier` for both datasets.
- The metadata contains `totalNotionalSum`; it must not be treated as absent from the current schema.

The metadata census is a successful inventory retrieval, **not proof that every listed partition still contains queryable rows**.

## 1. Historical dataset

`weeklySummaryHistoric` returned five tier values, each with 209 weekly partitions and no missing calendar-week anchors:

| Tier | Pairs | Earliest | Latest | Metadata description |
|---|---:|---|---|---|
| NA | 209 | 2021-11-15 | 2025-11-10 | Undocumented |
| NMS | 209 | 2021-11-15 | 2025-11-10 | Undocumented |
| OTCE | 209 | 2021-11-15 | 2025-11-10 | Over-the-counter equity |
| T1 | 209 | 2021-11-15 | 2025-11-10 | S&P 500, Russell 1000 and selected ETPs |
| T2 | 209 | 2021-11-15 | 2025-11-10 | Other NMS stocks |

The metadata's `tierIdentifier` description documents T1, T2 and OTCE only. NA and NMS are present in the partition inventory but are not defined there. Do not silently map them to T1/T2 or treat them as equivalent market universes.

## 2. Current production dataset

The partition inventory does not look like the documented twelve-month rolling window:

| Tier | Pairs | Earliest | Latest | Missing weekly anchors |
|---|---:|---|---|---:|
| NA | 253 | 2021-12-06 | 2026-10-05 | 0 |
| NMS | 17 | 2023-06-05 | 2023-11-06 | 6 |
| OTCE | 253 | 2021-12-06 | 2026-10-05 | 0 |
| T1 | 255 | 2021-12-06 | 2026-10-19 | 0 |
| T2 | 253 | 2021-12-06 | 2026-10-05 | 0 |

This is a **partition-catalog anomaly**, not yet proof that old data rows remain queryable. FINRA's official documentation describes `weeklySummary` as a rolling twelve months and `weeklySummaryHistoric` as a rolling four-year historical dataset beginning one year before the current date. It also states that historic data older than one year are static. See https://developer.finra.org/docs.

## 3. Historic/current overlap

The two partition inventories overlap on 841 pairs:

| Tier | Overlap pairs | Overlap range |
|---|---:|---|
| NA | 206 | 2021-12-06 to 2025-11-10 |
| NMS | 17 | 2023-06-05 to 2023-11-06 |
| OTCE | 206 | 2021-12-06 to 2025-11-10 |
| T1 | 206 | 2021-12-06 to 2025-11-10 |
| T2 | 206 | 2021-12-06 to 2025-11-10 |

The large overlap is another reason not to infer actual current-dataset retention from the partitions endpoint alone.

## 4. Reproducibility

- GitHub Actions: [run 43444007387](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43444007387) — **SUCCESS**.
- Offline tests: **7/7 passed**.
- Artifact: [14046932092](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43444007387/artifacts/14046932092).
- Artifact ZIP SHA-256: `3b872a5cfc95786f515c79ca582d0e2fecfbced06eb417e6f8e708a5e0c2c17c`.
- The artifact contains only metadata, partition inventories and response headers; no trade-level rows were downloaded.

## 5. Decision and next gate

**Do not use the partition inventory as a historical row-coverage claim.** Phase 365 performs 50 targeted, low-volume data queries (five dates × five tier values × two datasets), requesting at most ten sample rows per query. It is designed to determine whether:

1. old `weeklySummary` partitions actually return rows despite the documented twelve-month window;
2. NA/NMS partitions contain meaningful rows or are legacy/undocumented partitions;
3. historic/current overlap pairs return matching counts and sample-level signatures;
4. the actual row schema and date fields agree with metadata.

Phase 365 run: [43444391496](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43444391496) (in progress at report preparation).

No signal, return, alpha, OOS, bootstrap, LOO or holdout test was run. No vendor or data purchase. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
