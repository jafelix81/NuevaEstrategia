# Phase 107 — FINRA weekly ATS/off-exchange final live revalidation

**Date:** 2026-11-05  
**Workflow:** [Phase 100 run 41978867803](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41978867803)  
**Artifact:** [phase100-finra-ats-revalidation, artifact 13394110956](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41978867803/artifacts/13394110956)  
**Artifact SHA-256:** `803c58a5301df8b505b487c5367a449696c6bc467cab39121c50eda762d1f3e9`  
**Execution:** SUCCESS. **Research data gates:** PARTIAL/FAIL; no returns test authorized.

## 1. Live retrieval and partition reconciliation

The corrected Phase 100 run completed all 10 requested week/tier partitions and 199 synchronous pages:

- 5 historical weeks × NMS Tier 1 and Tier 2.
- 968,139 rows retrieved.
- Every partition's retrieved row count exactly matched FINRA's `Record-Total`.
- All 199 page hashes and offsets were recorded.
- 108,444 symbol-level aggregates: 52,007 ATS and 56,437 non-ATS OTC.
- No negative or invalid share-quantity/trade-count fields.
- Both ATS and OTC symbol aggregates were present in every sampled week/tier.

The earlier absent `Total-Records-On-Page` header was handled correctly by advancing on parsed body length while requiring `Record-Total` and checking `Record-Offset` when supplied. The 19 offline tests passed.

## 2. Data-integrity findings

### 2.1 Two missing-symbol rows

In 2022-01-03 / T2, two rows lacked `issueSymbolIdentifier`:

- One `OTC_W_SMBL_FIRM` row.
- One `OTC_W_SMBL` row.

The current validator labels both as `ROW_PARTITION_MISMATCH`, but the captured examples are missing-symbol problems, not incorrect week/tier values. The gate currently conflates two separate checks. The actual returned week/tier fields must be audited independently from symbol completeness.

### 2.2 Two LND coarse-key collisions

In 2025-01-06 / T2, two rows share each of these coarse keys:

- `LND / 2025-01-06 / T2 / OTC_W_SMBL / CTS`
- `LND / 2025-01-06 / T2 / ATS_W_SMBL / CTS`

The paired rows have different `lastReportedDate` values (2025-01-08 and 2025-01-10), while both show `initialPublishedDate=2025-02-10` and `lastUpdateDate=2025-02-10`. Their share quantities and trade counts differ.

These should not yet be called true duplicates. Phase 100 did not request `MPID`, `firmCRDNumber`, `marketParticipantName` or `issueName`, and its coarse key omitted `lastReportedDate`. The rows may be distinct reporting/update records or a source-quality defect. No row is silently selected, summed or discarded.

## 3. Publication and revision behavior

- `initialPublishedDate`, `lastUpdateDate` and `lastReportedDate` were non-null for 100% of symbol-level rows.
- Publication lag from `weekStartDate`: 21 calendar days for T1 and 35 for T2 in every sampled partition. This is consistent with the two-/four-week reporting delays measured from the end of the reporting week and the next-Monday publication convention.
- 1,882 of 108,444 symbol aggregates (1.735%) had `lastUpdateDate` later than `initialPublishedDate`.
- `lastReportedDate` is not the trading/event date; FINRA field documentation describes it as the last time a firm sent an update to underlying data contributing to the aggregate.

The current historical response contains latest values and update dates, not a demonstrated archive of original publication vintages. A conservative candidate knowledge date is the later of first publication and last update, followed by execution no earlier than the next trading session. This is a candidate rule, not proof that historical revisions can be reconstructed exactly.

## 4. Coverage interpretation

The 335-name overlap ranged widely by week and tier (approximately 20.9%–99.1%). This is a diagnostic only: the 335 names were manually/arbitrarily selected and are not a representative market universe. It is not a coverage gate and must not be used to claim broad-market coverage.

The source currently establishes symbol-level reporting for the sampled NMS T1/T2 partitions. It does not establish permanent security identity, inactive/delisted coverage, or a broad point-in-time listing universe. FINRA's historic weekly endpoint is a rolling four-year historical window one to five years before the current date; together with the production rolling 12-month endpoint, this is not a full 2016-present archive.

## 5. Gate decision

| Gate | Result |
|---|---|
| All 10 partitions retrieved | PASS |
| Exact `Record-Total` reconciliation | PASS |
| Symbol aggregates in every sampled week/tier | PASS |
| Non-negative numeric quantities | PASS |
| Initial publication date completeness / plausible delay | PASS |
| Week/tier validation | REVIEW: current validator conflates missing symbols with partition mismatch |
| Missing symbols in symbol-bearing rows | FAIL / INVESTIGATE (2 rows) |
| Coarse-key collisions | FAIL / INVESTIGATE (2 groups; natural key incomplete) |
| Original-vintage / correction history | NOT ESTABLISHED |
| Permanent security identity / inactive-delisted coverage | NOT ESTABLISHED |
| Forward-return / alpha test | NOT AUTHORIZED |

**Decision:** retain FINRA ATS/non-ATS weekly data as a public market-structure candidate, but do not construct a return feature or claim predictive value yet. The next step is a narrow full-field anomaly-resolution probe, not another broad return test.

## 6. Economic interpretation and controls

ATS and non-ATS aggregates describe reported off-exchange activity. They do not reveal aggressor direction, beneficial ownership, customer identity, or whether a participant was informed. They are not evidence of institutional or “smart money” behavior by themselves.

No forward returns were accessed, no alpha test was performed, no vendor was contacted, no data were purchased, and `F80_TOP20_PARTIAL50_BASELINE_C20` was not changed.

## References

- FINRA Weekly Summary API: https://developer.finra.org/docs/api-explorer/query_api-equity-weekly_summary
- FINRA Q1 2021 API update describing the rolling 12-month production and four-year historic datasets: https://developer.finra.org/news/q12021
- FINRA field definitions (secondary schema reference): https://finra.hawkberry.com/en/stable/reference.html
