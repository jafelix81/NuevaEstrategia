# Phase 267 — FINRA Short Interest: Pagination, Settlement Calendar, Publication-Time and Vintage Audit

**Date:** 2026-11-10  
**Scope:** Re-adjudicate the historical FINRA consolidated short-interest inputs used by Phases 25B and 25C. This is a data/PIT audit only; it is not a new return test.

## Decision

**Phase 25B and Phase 25C are not admissible as point-in-time evidence.** Their original diagnostic return summaries must not be used to select or promote a FINRA short-interest feature.

The source itself remains a **prospective research candidate**. FINRA documents the dataset as a consolidated view across exchange-listed and OTC equity securities and states that it is available by **4:40 p.m. ET on the publication date**. That creates a usable prospective knowledge clock, but only if we preserve first receipt, revisions, complete API pagination, and the next-session execution rule.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No production, universe, capital, parameter, or holdout changes were made.

## Evidence reviewed

- Phase 25B workflow run 39389135458, artifact 12248259525.
- Phase 25C workflow run 40088483325, artifact 12558485136.
- Both artifacts contain the **same** feature file SHA-256: 9be52a5522edfa3230657351cffb76f7ea3b0af419b26b9efaab07ca76845602. They are therefore not independent data replications.
- Phase 25B raw file SHA-256: eba8312fbfa041e310191a3e884e829f7d1bf4ea452433c898e622948393817e.
- Phase 25B and 25C download-audit SHA-256 values are pinned in phase267_finra_short_interest_audit_input.json.
- Legacy code:
  - [Phase 25B](https://github.com/jafelix81/NuevaEstrategia/blob/phase25b-finra-short-interest-research/Nueva_Estrategia_Fase25B_FINRA_ShortInterest_Research.py)
  - [Phase 25C](https://github.com/jafelix81/NuevaEstrategia/blob/phase25c-finra-short-interest-walkforward/Nueva_Estrategia_Fase25C_FINRA_ShortInterest_WalkForward.py)

## 1. The historical fetcher stops at FINRA's 5,000-record synchronous ceiling

The legacy fetchers request limit=10000 and stop paging when len(batch) is less than the requested limit. FINRA's official API documentation sets the synchronous maximum at **5,000 records per request**, and documents the Record-Total, Record-Limit, and Record-Max-Limit response headers for complete pagination. It also imposes a 3 MB synchronous payload ceiling.

The archived audit shows:

| Measure | Result |
|---|---:|
| Settlement-date queries | 57 |
| Successful responses | 55 |
| Failed responses | 2 |
| Successful responses containing exactly 5,000 rows | 55/55 |
| Requested page limit | 10,000 |
| Actual documented synchronous ceiling | 5,000 |
| Recorded page offsets | 0 only |
| Response-total headers preserved | No |

Because 5,000 is less than the requested 10,000, the old break condition exits after the first response. It never requests offset 5,000. The old artifacts do not preserve Record-Total, so we cannot prove how many records were omitted on each historical date; the correct classification is **first-page-only / completeness unverified**, not a fabricated exact truncation count.

This alone prevents us from admitting the 98-ticker / 5,115-row feature panel as complete. The 88–96 universe hits per settlement date are not a validated coverage measure.

**Required correction:** read and persist the FINRA pagination headers, request pages up to the current platform limit, advance by the actual number of records returned, and continue until Record-Total is satisfied. If the headers or page accounting are inconsistent, fail closed.

## 2. Settlement dates were adjusted for weekends, not XNYS holidays

The old schedule generated the 15th and month-end, moving dates for weekends but not exchange holidays. Two of the 57 requests therefore targeted non-settlement dates and failed:

| Queried date | Reconstructed correct XNYS settlement |
|---|---|
| 2024-01-15 | 2024-01-12 |
| 2024-03-29 | 2024-03-28 |

The second date was Good Friday. The first was the Martin Luther King Jr. Day market holiday.

A historical XNYS calendar reconstruction was performed for all 57 queried dates. The two mismatches are reproducible in the Phase 267 result JSON. Future retrieval must use the official FINRA schedule or a validated exchange-calendar mapping rather than weekend-only date arithmetic.

## 3. The old knowledge clock is early on 19 of 55 successful cycles

Both legacy phases calculate:

KnowledgeDate = settlementDate + pandas BDay(7)

Pandas business days skip weekends but do not skip exchange holidays. Comparing that rule with the seventh XNYS session after settlement shows:

- 19/55 cycles: old knowledge date is one XNYS session early (the calendar-date difference is one or three days depending on the weekend).
- 36/55 cycles: dates coincide.
- 0/55 cycles: old date is late.

The original price-label construction then uses the first daily close on or after KnowledgeDate (close.index.searchsorted(kd, side="left")). This is not a valid execution anchor: FINRA says the consolidated short-interest data is available by **4:40 p.m. ET on the publication date**, after the regular 4:00 p.m. close. Across the 55 unique settlement-cycle snapshots, the old price anchor precedes safe next-session entry. Phase 25B used 14 valid training snapshots per signal (84 repeated training-snapshot uses across six folds); Phase 25C used 3, 6, 13, 25, 33, 36, 42, and 50 (208 uses across eight folds). All 292 training-snapshot uses inherit pre-release price anchors. These repeated uses are not independent observations.

A conservative close-based implementation must use the **next XNYS session after the publication date**. Relative to that safe entry, the old anchors are one session early for 38 cycles and two sessions early for 17 cycles.

This contaminates the feature/forward-return correlations used to select the Phase 25B/25C factors, even where the later OOS signal date itself was after publication. The audit distinguishes 55 unique settlement-cycle anchors from 292 repeated valid training-snapshot uses across the two walk-forward procedures; the corrected counts are covered by the Phase 267 regression tests.

## 4. Phase 25C has one direct OOS availability error

For the 2022-11-25 Phase 25C signal:

- Old rule admitted the 2022-11-15 settlement report using an old knowledge date of 2022-11-24.
- The reconstructed publication date is 2022-11-25, and FINRA's documented availability is by 4:40 p.m. ET that day.
- The signal and price lookup use the 2022-11-25 close, which precedes the data release.
- Rebuilding the latest available snapshot removes that settlement cycle: 11 old snapshot dates become 10, and 89 ticker-level latest rows change.

The other Phase 25C signal dates and the six Phase 25B signal dates do not show this same latest-snapshot membership mismatch under the reconstructed calendar. That does **not** rescue the studies: all training labels still use pre-release closes, and the historical retrieval remains incomplete/unverified.

## 5. Revisions are present in the historical panel

The Phase 25B raw artifact contains 5,115 rows across 55 settlement dates and 98 tickers. Of these:

- 102 rows have revisionFlag = "R";
- those rows cover 63 tickers and 9 settlement dates;
- one settlement cycle contains 45 such rows.

FINRA's field description says revisionFlag = "R" indicates that the **prior cycle's short position was revised**. The model uses prior-cycle comparison fields such as previousShortPositionQuantity, changePreviousNumber, and changePercent, but the old artifacts do not contain the originally published values or immutable first-receipt vintages.

Consequently, current historical values cannot be assumed to equal the values available to an investor at the original publication time. Prospective capture must preserve original response bytes, headers, receipt timestamp, and later revisions as separate states.

## 6. Original return summaries are invalidated, not promoted

The archived Phase 25B summary was:

| Horizon | Mean | Median | Positive signals |
|---|---:|---:|---:|
| 5 sessions | +0.3672% | +0.4910% | 4/6 |
| 10 sessions | +0.8886% | +1.2565% | 4/6 |
| 20 sessions | -0.5012% | +0.5683% | 4/6 |

The archived Phase 25C summary was:

| Horizon | Mean | Median | Positive signals |
|---|---:|---:|---:|
| 5 sessions | +0.0309% | +0.2674% | 5/8 |
| 10 sessions | -1.8232% | -1.7304% | 1/8 |
| 20 sessions | -1.4466% | -1.3929% | 2/8 |

These are historical diagnostic outputs only. They are not valid PIT/OOS evidence because of the pagination, settlement-calendar, publication-time, and revision-vintage defects. The Phase 25B and 25C samples share the same feature file, so they are not independent replications. No new alpha test was run in Phase 267.

## 7. Current reporting regime

The SEC records that proposed FINRA rule change SR-FINRA-2026-012, which would have increased short-interest reporting frequency and granularity, was **withdrawn on 2026-08-05**. Do not assume weekly reporting has commenced. Continue using the official twice-monthly FINRA publication schedule until FINRA/SEC publish a new effective rule and schedule.

## 8. Current API authentication contract

The current FINRA Developer Center documentation lists Public, Firm, and Organization credential types for Consolidated Short Interest and states that Query API requests require an OAuth 2.0 Bearer token. The Phase 25B/25C client sends only Accept and Content-Type headers and contains no token flow. Although the historical GitHub runs returned data, that does not establish that the old unauthenticated request is a reproducible current access method.

A future live capture must first verify the current Public-credential onboarding and terms. No FINRA credential was created, no API terms were accepted, and no live request was made in Phase 267. This becomes a user-authorized setup step only if we decide to deploy prospective FINRA capture.

## Rebuild path

1. Correct the historical API fetcher and prove full pagination with response-header accounting.
2. Reconstruct settlement and publication dates from the official FINRA calendar / XNYS sessions.
3. Re-anchor training labels to the next XNYS session after the 4:40 p.m. ET publication.
4. Treat the current historical API as revised-current data unless original vintages can be proven.
5. Build prospective append-only first-receipt capture before any new PIT inference.
6. Resolve permanent security identity, inactive/delisted coverage, and corporate-action-adjusted prices.
7. Only then run a new chronological study against frozen LTM/F80, with identical costs/exposure, bootstrap/LOO, and genuinely unused OOS data.

## Official sources

- [FINRA Developer Center — Query API documentation](https://developer.finra.org/docs): Consolidated Short Interest is available by 4:40 p.m. ET on publication date; the dataset supports Public/Firm/Organization credentials; Query API requests require OAuth 2.0 Bearer authorization; synchronous requests max out at 5,000 records and 3 MB; pagination headers include Record-Total, Record-Offset, Record-Limit, and Record-Max-Limit.
- [FINRA — Short Interest Reporting](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest): official settlement, due, and publication schedule.
- [SEC — SR-FINRA-2026-012](https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-finra-2026-012): withdrawn August 5, 2026.

## Guardrails

- No live FINRA API call or credential creation in this phase.
- No data purchase, vendor contact, or acceptance of new terms.
- No production, universe, capital, or parameter change.
- No use of the consumed legacy holdout.
- F80 remains frozen.


## Hosted validation

- Corrected push validation: [run 42881252812](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42881252812), job 130057796963; 8/8 deterministic tests passed. Metadata artifact [13793872685](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42881252812/artifacts/13793872685), ZIP SHA-256 16aa3d969b3e22c5b294919579b6a4fcfdf825d2ff42d6e5a081518cf56dcdf7.
- Corrected pull-request validation: [run 42881264303](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42881264303), job 130058005392; 8/8 deterministic tests passed. Metadata artifact [13794116684](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42881264303/artifacts/13794116684), ZIP SHA-256 a921459af6ba610104fd189571f5fd2d9fba840abe22dfd3aabf8264f0111d24.
- Both corrected runs produced identical result JSON SHA-256 41f72d9c92e98f6aa91071525fd1330d44aaaf35c432aaa7cb961e0d2ad55371. The corrected output distinguishes 55 unique snapshot anchors from 292 repeated valid training-snapshot uses (84 Phase 25B; 208 Phase 25C).
- Initial runs 42880053761 and 42880064173 validated the first version of the audit and are superseded by the corrected accounting above.
- Both corrected workflows are offline/deterministic: no live FINRA API request, credential use, or market-data download occurred.
