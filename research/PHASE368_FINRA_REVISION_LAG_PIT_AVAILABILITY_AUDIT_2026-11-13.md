# Phase 368 — FINRA revision-lag / PIT availability audit

**Date:** 2026-11-13 UTC  
**Status:** PROTOCOL FROZEN; full-partition retrieval pending.  
**Research class:** source feasibility / date-field diagnostics only.

## Question

Do the date fields in FINRA weeklySummaryHistoric support a defensible reconstruction of when final weekly-summary values became publicly knowable?

This phase does not assume that any date field is a publication timestamp. It measures date-field gaps on five complete partitions and keeps field semantics separate.

## Preregistered sample

| Week | Tier | Purpose |
|---|---|---|
| 2022-01-03 | T1 | Older-history control |
| 2025-01-06 | T1 | Intermediate-history control |
| 2025-10-20 | T1 | Partition used in Phases 366–367 |
| 2025-10-20 | OTCE | Separate OTC-equity tier control |
| 2025-11-10 | T1 | Latest historical partition in the audited inventory |

The workflow retrieves every row in each partition and reconciles the row count to FINRA Record-Total and page headers. It does not retain raw rows, symbols, MPIDs, CRDs or firm names.

## Measures

For each partition and summaryTypeCode, compute date-only differences:

- initialPublishedDate minus weekStartDate
- lastUpdateDate minus initialPublishedDate
- lastReportedDate minus initialPublishedDate
- lastUpdateDate minus weekStartDate
- lastReportedDate minus weekStartDate
- lastUpdateDate minus lastReportedDate

Report missing/invalid date counts, positive/zero/negative gaps, nearest-rank p50/p90/p95/p99, extrema and counts exceeding 1/7/30/90/180/365/730 calendar days.

## Interpretation constraints

FINRA's current Developer Center documentation describes the weekly-summary fields and data-versioning behavior. The API documentation explains that much of its Equity API data becomes static after one year, and the historic weekly dataset is not a time-version archive of every intermediate public vintage.

- initialPublishedDate is a first-publication date field, but has date-level rather than intraday precision in the sampled schema.
- lastUpdateDate is an update-date field, not a first-receipt timestamp for a revised public value.
- lastReportedDate is a contributing firm's last-report date, not the public release timestamp.
- A positive lastUpdateDate minus initialPublishedDate gap proves only that the final row carries a later update date than its first-publication date. It does not reveal the time the updated value first became available to an external user.
- No historical value may be backdated to initialPublishedDate merely because that field exists.
- If first-receipt timestamps and intermediate vintages cannot be recovered, historical FINRA alpha testing remains inadmissible. Prospectively archived snapshots may support a future forward-only study after a new preregistration.

## Decision gate

A successful retrieval completes only the date-field measurement. It does not establish PIT availability. The final disposition must explicitly state whether the available fields are sufficient for an availability ledger; default is NO unless the source provides a defensible public-release timestamp or archived version history.

No forward returns, signal construction, alpha test, OOS, bootstrap, LOO or holdout use is authorized. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
