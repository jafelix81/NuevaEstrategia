# Phase 265 — FINRA short-flow calendar, knowledge-time and execution audit

**Date:** 2026-11-10 UTC  
**Disposition:** Phase 20C remains a chronological diagnostic, but it is **not strict PIT**. The reported 1,382/2,020 file ratio is not a valid market-session coverage rate. No feature or alpha admission.  
**Scope:** source-code, run-log and artifact-metadata audit only. The 145.9 MB Phase 20C archive was not downloaded or rehashed in this phase; its ZIP digest below is the upload digest recorded in the completed GitHub Actions log. No new FINRA download, return test, holdout use, provider contact, purchase or production change.

## Executive decision

A fresh line-by-line audit of the actual Phase 20C script found two issues that were not made explicit in the 2026-10-24 FINRA audit:

1. **Knowledge-time mismatch.** Phase 20C includes the FINRA row for the signal trade date, while the forward-return denominator is that same date's closing price. The script does not record the first time the FINRA file was received, and its download audit contains only Date and Status. Therefore it does not prove that the same-day feature was available before the same-day close used as the entry price. The pseudo-OOS selection is chronological, but the feature/entry pairing is not strict PIT.
2. **Invalid coverage denominator.** Phase 20C builds its requested-file set by iterating every calendar date from D−100 through D inclusive. FINRA files are trade-date files, not daily calendar files. The reported 1,382/2,020 = 68.416% is a calendar-date success ratio, not XNYS-session coverage. Weekends and exchange holidays are included in the denominator. Actual expected-session coverage is unmeasured until the exact XNYS calendar is supplied.

The prior audit's statement that the artifact was PIT is superseded. The correct classification is **chronological selection / non-PIT feature availability / market-session coverage unknown**.

## 1. Immutable run and source-code evidence

- Phase 20C run: [40098425254](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254)
- Job: 120885427795
- Artifact: [12562171831](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254/artifacts/12562171831)
- Artifact ZIP SHA-256 from the completed job log: c15f75340bdedfbb37c82f79bb563a450dd1da11989d09e18bb745d93b7d3a5c
- Audited source: [Nueva_Estrategia_Fase20C_FINRA_WalkForward_OOS.py](https://github.com/jafelix81/NuevaEstrategia/blob/phase20c-finra-walkforward/Nueva_Estrategia_Fase20C_FINRA_WalkForward_OOS.py)
- Source Git blob SHA: 6974d4b70a63c5e4b8dc460d6f90dfd652f16fa7

The run log reports 329 valid names from the configured 335, 20 FINRA-eligible training signals, 12 pseudo-OOS test dates, six final holdout signals left untouched by that run, 2,020 requested dates and 1,382 successful/cached files. The 335-name universe is a selected legacy list, not a representative or survivorship-free universe.

## 2. Same-day knowledge-time mismatch

The code path is explicit:

- The raw FINRA panel is filtered to dates less than or equal to the signal date.
- The cross-sectional builder then selects the row whose Date equals the signal date.
- The forward-return builder locates that same signal date and uses its Close as the return denominator.

The download audit writes only Date and Status. The source does not persist a per-file first-received UTC timestamp, raw SHA-256, original first-publication bytes, or later correction vintages.

FINRA's official page describes the source as daily short-sale volume and directs users to downloadable daily/monthly files and the query API for history beyond the interactive 365-day grid. FINRA's Information Notice explains that the files include publicly disseminated trades, are not consolidated with exchange data, and may omit offsetting purchases associated with facilitation. It expressly distinguishes this flow measure from short-interest positions.

Because the actual first-receipt clock is absent, the same-day close cannot be certified as an executable entry after observing that day's file. We do not need to assume an exact FINRA publication time to reach this conclusion: the required evidence is missing.

**Required future rule:** preserve each raw response, request URL, response metadata, first-received UTC timestamp, SHA-256 and every changed version. Use the first XNYS session strictly after verified first receipt. If only the FINRA trade date is known, use the next XNYS session after that trade date. Do not use the same-day close.

## 3. Calendar-denominator correction

The legacy code constructs the download set by incrementing one calendar day from D−100 through D inclusive. It does not use an XNYS session calendar for this request set.

Consequently:

- 2,020 is a count of requested calendar dates across overlapping windows.
- 1,382 is a count of files fetched or found in the local cache.
- 638 is not a count of missing trading sessions.
- 68.416% must not be quoted as the FINRA trading-session coverage rate.

The correct denominator is the explicit set of expected XNYS sessions for each signal window, with exchange holidays excluded. Coverage must be measured against that set, with a missing expected-session file remaining UNKNOWN/missing rather than being filled with zero. Phase 265 supplies a deterministic session-coverage contract, but the actual session-level rate remains NOT MEASURED because the full date/status ledger has not been re-adjudicated against the authoritative calendar.

## 4. Economic diagnostic — no promotion

The existing 2026-10-24 audit reports 12 pseudo-OOS dates:

| Horizon | Mean delta vs blocked control | Median | Positive dates |
|---|---:|---:|---:|
| 5D | +0.141% | -0.049% | 5/12 |
| 10D | -1.686% | -1.837% | 3/12 |
| 20D | -0.858% | -0.333% | 5/12 |

The selected factor also migrated across the 12 dates: SHORT_RATIO_Z20 six times, SHORT_EXEMPT_RATIO five times, and SHORT_RATIO_PERSIST20 once.

This is not evidence of incremental alpha. The 5D mean is modest while its median is negative; 10D and 20D mean deltas are negative; the sample has only 12 pseudo-OOS dates; the universe is selected; the coverage denominator was not session-normalized; and the same-day entry is not proven PIT. No confidence interval, bootstrap, LOO or independent OOS claim is made here.

## 5. Correct source semantics

FINRA's Information Notice dated 2019-05-10 states that daily short-sale volume files are not consolidated with exchange data and that offsetting facilitation purchases may not appear in the daily file. FINRA separately explains that short-sale volume is not short interest. These are trade-flow aggregates, not beneficial-owner positions or a direct measure of informed institutional activity.

Official sources:
- [FINRA Short Sale Volume Data](https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data)
- [FINRA Information Notice 5/10/19 — Understanding Short Sale Volume Data](https://www.finra.org/sites/default/files/2019-07/information-notice-051019.pdf)
- [FINRA — Short Interest: What It Is, What It Is Not](https://syndication.finra.org/content/short-interest-what-it-what-it-not)

## 6. Implemented controls and tests

Added a fail-closed offline contract for:
- measuring coverage against an explicit XNYS session list;
- excluding weekends/holidays from the denominator by supplying only expected sessions;
- choosing the next XNYS session strictly after the trade/knowledge date;
- requiring training labels to end strictly before test entry;
- requiring timezone-aware first receipt, entry time, raw SHA-256 and immutable vintage preservation for strict PIT admission.

The deterministic suite contains 21 tests. It does not fetch data or calculate returns. The committed result intentionally records XNYS coverage as NOT MEASURED.

## 7. Hosted validation

- Phase 265 GitHub Actions: [run 42865680262](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42865680262), job 130003254392.
- Result: **21/21 deterministic tests passed**; the workflow regenerated the committed JSON and its byte-for-byte comparison passed.
- Metadata-only artifact: [13787227070](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42865680262/artifacts/13787227070), ZIP SHA-256 `430c9344619d5af2060d81b4532e531766ecc419fa81acac6d881fb3ec9a1208`.

## 8. Final disposition

| Gate | Result |
|---|---|
| Chronological feature selection | PASS as implemented |
| Same-day feature availability before same-day close | NOT PROVEN |
| Per-file first receipt UTC | FAIL / ABSENT |
| Raw hash and immutable revision vintages | FAIL / ABSENT |
| 1,382/2,020 as XNYS-session coverage | REJECTED |
| Actual XNYS-session coverage | NOT MEASURED |
| Strict PIT | NOT ADMITTED |
| Economic alpha | NOT DEMONSTRATED |
| Holdout used | NO |
| F80 change | NO |

Phase 20C is archived as a **chronological but non-PIT diagnostic**. Do not rerun or retune the same dates. A new prospective study requires immutable daily-file receipt capture, XNYS-normalized coverage, next-session execution, point-in-time prices and inactive-security coverage, then a preregistered incremental comparison against frozen LTM/F80 with identical exposure and costs.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. The legacy holdout remains CONSUMED_NOT_PRISTINE.
