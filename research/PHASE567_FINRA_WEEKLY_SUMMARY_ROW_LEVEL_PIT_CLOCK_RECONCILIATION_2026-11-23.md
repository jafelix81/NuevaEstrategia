# Phase 567 — FINRA Weekly Summary row-level PIT clock and schema reconciliation

**Audit cutoff:** 2026-11-23 03:23 UTC  
**Main HEAD before this report:** `c280930ffd7060e57b7acce8627b6c06940076e2`  
**Disposition:** official metadata clarifies the Weekly Summary row grain and revision fields. A conservative final-value availability proxy is now definable, but strict PIT admission remains blocked pending live first-receipt reconciliation, exact identity/universe coverage and row-key re-audit. No signal or alpha test.

## 1. New official metadata finding

FINRA's official Developer Center describes:

- `weeklySummary`: rolling 12 months.
- `weeklySummaryHistoric`: rolling four-year historical window beginning one year before the current date; older-than-one-year data are static and should not be repeatedly re-downloaded.
- Historical requests must specify exactly one of `weekStartDate`, `historicalWeek` or `historicalMonth`, with optional `tierIdentifier`; no symbol filter is supported by this endpoint. Large partitions should use the asynchronous API and reconcile `Record-Total`.

The repository's existing Phase 518 work already captured **259 consecutive weeks, 2021-11-15 through 2026-10-26**, across the historical and production datasets. This is a roughly five-year weekly panel, not a 2014+ archive. Phase 535 separately established that the ATS Transparency archive route returned HTTP 530 from GitHub Actions; this phase does not retry or bypass that route.

Sources:
- [FINRA Developer Center — Weekly Summary](https://developer.finra.org/docs)
- [FINRA Weekly Summary metadata schema](https://api.finra.org/metadata/group/otcMarket/name/weeklySummaryMock)
- [Phase 535 archive/API/PIT reconciliation](PHASE535_FINRA_ATS_ARCHIVE_ACCESS_AND_PIT_RECONCILIATION_2026-11-20.md)

## 2. Row grain and participant semantics

The official metadata lists these `summaryTypeCode` values:

- `ATS_W_FIRM`, `ATS_W_SMBL`, `ATS_W_SMBL_FIRM`, `ATS_W_VOL_STATS`
- `OTC_W_FIRM`, `OTC_W_SMBL`, `OTC_W_SMBL_FIRM`, `OTC_W_VOL_STATS`

It exposes `issueSymbolIdentifier`, `firmCRDNumber`, `MPID`, `marketParticipantName`, `tierIdentifier`, `productTypeCode`, weekly share/trade totals, and the three date fields below.

This confirms that the source can distinguish symbol aggregates from symbol-by-ATS/firm aggregates. A ticker can legitimately appear in separate ATS and OTC summary types. Therefore a duplicate check keyed only by week/tier/symbol is too coarse. The proposed composite key must include `summaryTypeCode` and, for participant-level rows, `MPID` or `firmCRDNumber`. This is a schema-derived key proposal, not yet a validation of the two historical LND groups; those raw rows must be re-audited before either is accepted or discarded.

An ATS MPID or OTC reporting firm is a reporting venue/entity, not the beneficial owner or ultimate investor. The data do not identify aggressor side or prove institutional accumulation/distribution.

## 3. Official date-field semantics and conservative PIT proposal

The FINRA metadata defines:

- `initialPublishedDate`: initial publication date, described as the first Monday or next business day after the reporting delay — two weeks for NMS Tier 1 and four weeks for NMS Tier 2 and OTC.
- `lastUpdateDate`: most recent date on which total trades were updated based on data received from the ATS/OTC.
- `lastReportedDate`: the date a firm last sent an update to underlying data contributing to the aggregate.

Phase 100 found 1,882 symbol-aggregate rows with `lastUpdateDate` later than `initialPublishedDate`. Thus the current final value cannot be backdated to the initial publication date.

For a final/current snapshot, the candidate conservative date floor is:

`knowledge_date_proxy = max(initialPublishedDate, lastUpdateDate)`

Because these fields are date-only and do not contain an intraday dissemination timestamp, a historical return test would not execute on that date. The candidate first executable point is the next regular trading session after the proxy date, subject to validation that `lastUpdateDate` corresponds to public dataset update rather than merely source receipt.

**This is not yet a certified PIT clock.** The API metadata does not preserve each intermediate revision value or its exact public timestamp. Prospective first-seen capture and a bounded authorized live sample must reconcile the date fields to actual receipt before any feature is admitted. Rows with either date missing, contradictory dates, unresolved identity or unvalidated revisions remain ineligible.

## 4. Reconciliation with prior coverage and integrity results

Existing evidence is retained; no data were re-extracted:

- Phase 100: 10 week/tier partitions, 968,139 rows, every sampled `Record-Total` reconciled; `initialPublishedDate` was present on 100% of symbol-aggregate rows in that sample.
- Phase 100: observed initial-publication lags were 21 calendar days for T1 and 35 days for T2 in the five sampled weeks. These are sample observations, not a substitute for row-level date fields.
- Phase 100: 1,882 rows had later `lastUpdateDate`; two rows lacked a symbol; two LND groups were flagged when ATS and OTC symbol aggregates shared a coarse key. The LND groups remain unresolved pending re-keying with `summaryTypeCode` and inspection of the raw rows.
- Phase 518: 259 consecutive weekly partitions from 2021-11-15 to 2026-10-26. This establishes a useful recent panel, not a complete broad-market or survivorship-safe universe.
- The sampled 94.63%–99.10% overlap against the manually selected 335-name F80 list is only a diagnostic. It does not establish active-universe coverage, delisted-name completeness or valid zeros.

The API's documented 5,000 synchronous / 100,000 asynchronous record limits and 500,000 offset limit mean any future complete extraction must be partitioned by week and tier, use asynchronous retrieval when appropriate, and reconcile every response header. Do not repeatedly download static history older than one year.

## 5. Hypotheses to retain — not assumptions

Only after the data gates pass:

1. Abnormal ATS share of a symbol's reported weekly activity may contain information beyond LTM/F80.
2. Changes in ATS share may add information beyond its level.
3. Concentration across ATS MPIDs or OTC reporting firms may add information beyond aggregate ATS participation.
4. ATS-versus-OTC divergence may describe venue-routing or liquidity-state changes.
5. Any apparent effect may disappear after controlling for recent returns, total volume, liquidity, size, volatility and market regime; if so, classify it as return/volume chasing, not informed activity.

No direction is inferred from venue participation. Any surviving hypothesis must be tested against frozen LTM/F80 with identical exposure and costs, strict chronological splits, a pristine future OOS period, bootstrap and leave-one-out robustness. No minimum or maximum holding period is imposed.

## 6. Remaining gates and decision

1. Re-audit the two LND groups with the full composite key; separately classify missing-symbol rows rather than converting them to zero.
2. Validate `lastUpdateDate` against one authorized live sample and prospective first-seen receipts. Do not create a new workflow or re-extract the 259-week panel for this metadata-only phase.
3. Build effective-dated security identity and historical active-universe coverage, including delisted securities.
4. Keep participant-level rows distinct from symbol aggregates and do not treat MPID/CRD as investor identity.
5. Only then build a feature panel and compare incremental information against frozen LTM/F80.

FINRA's Developer Center states that Individual API users are intended for their own purpose and that Individual access is not intended for commercial purposes. Credential ownership, accepted terms and the actual project-use category have not been verified here. No new credential was created, no terms were accepted and no API request was made in this phase.

**Research disposition:** new signals admitted 0; no forward-return/event/backtest/OOS/bootstrap/LOO test; no universe, exposure, cost, holding-period, holdout or production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
