# Phase 368 — FINRA revision-lag / PIT availability audit

**Date:** 2026-11-13 UTC  
**Status:** RETRIEVAL PASS; generic FINRA PIT reconstruction NOT ESTABLISHED; T1 ATS advances to a wider validation gate.  
**Research class:** source feasibility / date-field diagnostics only.

## Executive result

All five preregistered full partitions were retrieved without error: **258,787 rows across 55 pages**. Every partition's row count matched FINRA Record-Total. All four date fields were populated and parseable in every sampled row.

The important refinement is that late update-date gaps were confined to OTC summary types within the four T1 partitions. The sampled ATS summary types had **zero** rows where lastUpdateDate exceeded initialPublishedDate. This is a promising, narrow T1 ATS PIT candidate, not a general FINRA PIT pass.

## Preregistered sample and retrieval

| Week | Tier | Rows | Pages |
|---|---|---:|---:|
| 2022-01-03 | T1 | 46,834 | 10 |
| 2025-01-06 | T1 | 56,895 | 12 |
| 2025-10-20 | T1 | 65,116 | 14 |
| 2025-10-20 | OTCE | 24,292 | 5 |
| 2025-11-10 | T1 | 65,650 | 14 |
| **Total** | | **258,787** | **55** |

- All 5/5 partitions complete; zero retrieval errors.
- All page totals and partition Record-Total values reconciled.
- Zero missing or invalid values in weekStartDate, initialPublishedDate, lastUpdateDate or lastReportedDate.
- No raw rows, symbols, MPIDs, CRDs or firm names retained; only aggregate counts/distributions were uploaded.

Run: https://github.com/jafelix81/NuevaEstrategia/actions/runs/43460727228  
Artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/43460727228/artifacts/14056611466

## Main findings

### 1. Late update-date gaps are in OTC summary types, not sampled ATS summary types

| Partition | Rows with lastUpdateDate > initialPublishedDate | Share of partition | Maximum gap |
|---|---:|---:|---:|
| 2022-01-03 T1 | 964 | 2.0583% | 282 days |
| 2025-01-06 T1 | 100 | 0.1758% | 248 days |
| 2025-10-20 T1 | 31 | 0.0476% | 324 days |
| 2025-10-20 OTCE | 0 | 0.0000% | 0 days |
| 2025-11-10 T1 | 111 | 0.1691% | 303 days |

For all four T1 partitions, every positive update-date gap occurred in OTC_W_FIRM, OTC_W_SMBL or OTC_W_SMBL_FIRM. The sampled ATS_W_FIRM, ATS_W_SMBL and ATS_W_SMBL_FIRM rows had zero positive gaps: lastUpdateDate equaled initialPublishedDate.

The OTCE partition had no positive update-date gaps in any summary type.

In the four T1 partitions, the overall p50, p90 and p95 update-date gaps were zero days. The 2022-01-03 T1 p99 was 148 days; p99 was zero in the other three T1 partitions because the late-updated fraction was below 1%. The maxima are nevertheless large and cannot be ignored for OTC rows.

The 2025-10-20 and 2025-11-10 T1 partitions contain lastUpdateDate values as late as 2026-09-30. These are 324 and 303 calendar days after initial publication, respectively. The affected rows were OTC summary types, not ATS summary types.

### 2. Publication-delay fields behave consistently with FINRA's documented schedule

- For every T1 row, initialPublishedDate was exactly 21 calendar days after weekStartDate.
- For every OTCE row in the sample, initialPublishedDate was exactly 35 calendar days after weekStartDate.
- The observed lastReportedDate values were generally before initialPublishedDate; the few positive gaps were also in the late-updated OTC rows.

FINRA's Weekly Summary metadata defines weekStartDate as the first business day of the week; initialPublishedDate as the first Monday or next business day after the reporting delay (two weeks for NMS Tier 1, four weeks for NMS Tier 2 and OTC); lastUpdateDate as the most recent date total trades were updated from ATS/OTC data; and lastReportedDate as the last time a firm sent an update contributing to the aggregate.

Official documentation: https://developer.finra.org/docs

### 3. FINRA API Data Versioning is schema versioning, not historical row-vintage storage

The Developer Center's Data Versioning section explicitly describes versioning of field structure and data representation for backward compatibility. Existing Query datasets begin at schema version 1; this is not an archive of every prior row value or public release vintage.

Therefore, the presence of lastUpdateDate and initialPublishedDate does not reconstruct the first receipt time of each revised row. A final historic response still cannot prove what value an external user saw on each intervening date.

## Interpretation and disposition

### Generic FINRA weekly data

**PIT NOT ESTABLISHED.** The current API fields are date-level metadata, not a complete publication/version ledger. Do not use final OTC rows as if their final values were available on initialPublishedDate. Do not use lastReportedDate as a join key or public availability timestamp.

### T1 ATS summary types

**CONDITIONAL CANDIDATE — ADVANCE TO WIDER AUDIT.** Across four sampled T1 weeks, ATS_W_FIRM, ATS_W_SMBL and ATS_W_SMBL_FIRM have no post-initial update-date gaps. This supports testing a conservative date-level availability rule: next tradable session after initialPublishedDate. It does not yet establish universal historical stability or exact intraday availability.

Before any historical ATS signal test, Phase 369 must:
1. Expand the sample across years and seasons, not just four T1 weeks.
2. Confirm that all ATS summary types remain free of post-initial update dates.
3. Reconcile ATS aggregate symbol/product rows to firm-level rows without using lastReportedDate as a universal key.
4. Measure symbols and participant coverage, and preserve inactive/delisted names where the source supports them.
5. Keep the next-session rule conservative and validate holidays/calendar handling.

If any ATS rows are updated after initial publication, those rows/weeks must be quarantined unless a defensible public-availability date can be reconstructed.

## Separate FINRA daily short-flow review (Phase 20C artifact)

The completed Phase 20C run used 12 rolling pseudo-OOS training-era dates (2021-05-03 through 2024-10-30), with the final six signal dates held untouched. The final holdout was not used.

Exploratory replacement-minus-blocked deltas from the artifact:

| Horizon | Mean | Median | Positive dates |
|---|---:|---:|---:|
| 5 sessions | +0.141% | -0.049% | 5/12 |
| 10 sessions | -1.686% | -1.837% | 3/12 |
| 20 sessions | -0.858% | -0.333% | 5/12 |

A post-hoc date-resampling diagnostic produced 95% percentile intervals that all included zero: 5D [-2.68%, +3.01%], 10D [-5.84%, +2.32%], 20D [-10.34%, +7.58%]. With only 12 dates and four blocked/four replacement names per date, this is not promotion-grade evidence. Factor selection also changed across three factors (SHORT_RATIO_Z20 on 6 dates, SHORT_EXEMPT_RATIO on 5, SHORT_RATIO_PERSIST20 on 1), showing weak stability.

A separate execution-timing issue remains: FINRA states that daily Reg SHO files are posted no later than 6:00 p.m. ET on the trade date, with rare later corrections. Phase 20C measures forward returns from close t to close t+h. Because the file arrives after the regular-session close, close t is not an executable entry price for a strategy using that file. A corrected pseudo-OOS diagnostic must use next-session open as entry and a consistently defined close exit. Do not reuse the six Phase 20B final-OOS dates; that legacy holdout is consumed.

Official FINRA daily file timing and correction policy: https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files

Phase 20C run/artifact:
- https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254
- https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254/artifacts/12562171831

## Controls

No forward returns, alpha test, new OOS, bootstrap, LOO or holdout use occurred in Phase 368. The small post-hoc resampling summary above only describes the existing Phase 20C pseudo-OOS artifact; it does not authorize promotion or consume the final holdout.

No signal admitted. No parameter, universe, capital, exposure or production change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
