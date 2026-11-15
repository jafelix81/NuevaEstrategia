# Phase 412 — FINRA Phase 20C price-provider access and fallback recheck

**Audit date:** 2026-11-15 UTC  
**Disposition:** **No acceptable no-credential fallback was established. Phase 20C remains blocked at the fixed 329-valid-history requirement; no provider mixing or universe reduction is authorized.**  
**Research class:** data-access / reproducibility gate only. No return or signal test.

## 1. Actions and repository state checked first

- Main HEAD at audit start: `1a168ca7914907356bba975dc32c76f480110e4d`.
- The latest 100 Actions runs were inspected. The newest runs were Phase 411 pull-request regressions [43681298839](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43681298839) and [43681270194](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43681270194), both SUCCESS. The latest actual SEC scheduled run remained [43670461605](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43670461605), SUCCESS. Explicit Actions queries returned zero queued and zero in-progress runs at 2026-11-15 07:06 UTC.
- Phase 411's latest regression completed 17/17 tests; no artifact and no CFTC request.
- Phase 403 SEC jobs and artifact [14143174642](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43670461605/artifacts/14143174642) were inspected. The downloaded `summary.json` confirms 55 feed observations appended (50 Form 144 + 5 Form 144/A), zero new accessions/events, zero eligible observations, and no feed-window gap. The last successful receipt remains 2026-11-15 03:02:02Z; no later schedule run is present in the inspected run set. Do not manually dispatch or duplicate the poll.
- Phase 384's last run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) and artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705) were inspected. It is a push/bootstrap, not a scheduled capture: 3,035 historical rows, zero signal-eligible historical rows, no event written. The next weekday schedule is Monday 2026-11-16 22:15 UTC.
- Open draft research PRs remain stacked. In particular #57 is the Phase 381 provider audit, #61 is the Phase 385 FINRA publication-clock branch, #59 is the original CFTC bootstrap branch (not the mainline activation), and #48 is the Cboe source-ranking branch. No stacked PR was merged.

## 2. Reconciliation of the Phase 372 and Phase 381 failures

### Phase 372 — next-session-open retest

Run [43481200906](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43481200906) passed its seven offline unit tests, then stopped before the research calculation:

`Valid universe drift: expected 329, got 328; recovered=0; remaining_failures=['AVB', 'EA', 'EQR', 'LPRO', 'ROKU', 'WBD', 'WBS']`

The fixed 2016-10-24 to 2026-10-24 price window and original diagnostic universe were preserved. The failure is a price-history completeness failure, **not a negative FINRA signal result**. No forward-return metrics, alpha, pseudo-OOS, bootstrap, LOO or holdout calculation was produced. The six final holdout signals remain untouched.

### Phase 381 — provider fallback probe

Run [43500356535](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500356535) completed successfully. Its metadata-only artifact [14073108228](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500356535/artifacts/14073108228) was downloaded and inspected.

- Yahoo query1 and query2 each returned 2,514 rows for all four controls (AAPL, MSFT, NVDA, SPY), but zero timestamps for all seven missing symbols.
- Stooq returned no parseable Date/Close table for any control or missing symbol. The Phase 381 request did not supply an API key and the artifact does not retain the response body/status, so this is an unauthenticated access failure, **not proof that Stooq lacks historical coverage**.
- Nasdaq's `api.nasdaq.com/api/quote/{symbol}/historical` endpoint returned HTTP 200 but empty rows for all 11 symbols, including controls. This endpoint was not established as a documented, supported public API; it is not accepted as a reproducible provider contract.
- No source supplied the required >=220 observations for any missing symbol. No cross-provider return concordance could be calculated. No fallback was admitted.

## 3. External provider-contract recheck

- The Stooq Q API's current machine-readable third-party specification lists `apikey` as required and describes a CAPTCHA-gated key; this is not a first-party Stooq contract, so the conclusion is limited to: **the unauthenticated Phase 381 probe cannot certify Stooq coverage**. See [Stooq Q API profile/specification](https://apis.io/apis/stooq/stooq-q-api/) and [query-parameter schema](https://apis.io/schemas/stooq/stooq-query-parameters/). The first-party endpoint currently presents a JavaScript verification page to this audit environment; no key was obtained.
- Nasdaq's first-party [Data Link API documentation](https://www.nasdaq.com/products/data/data-link/api) describes the Bars API as a subscriber service and advertises 10+ years of history across U.S.-listed and OTCBB securities. Nasdaq's public [Historical Data page](https://www.nasdaq.com/market-activity/quotes/historical) describes up to 10 years of daily prices, but the unauthenticated quote endpoint used by Phase 381 is not a documented stable API contract. The commercial Data Link route is a possible vendor path, not a free fallback.
- The legacy Nasdaq WIKI Prices dataset is discontinued and not recommended for investment/analysis; it is not a current replacement for the 2016–2026 panel. See [Nasdaq Data Link WIKI Prices](https://data.nasdaq.com/databases/WIKIP).

## 4. Decision and exact unblock gate

1. Keep the original 335-name diagnostic universe and the frozen 329-valid-history requirement. Do not silently drop AVB, EA, EQR, LPRO, ROKU, WBD or WBS.
2. Do not mix Yahoo with Stooq/Nasdaq or splice price vendors without an independent adjusted-price, corporate-action and daily-return reconciliation.
3. Phase 20C remains blocked until one approved source supplies a complete, reproducible daily OHLC/adjusted-price panel for the exact window and universe, including IPO start dates, symbol/class changes, delisted/predecessor names, split/dividend treatment and terminal returns. The source must also permit the intended research use.
4. A licensed provider or valid Stooq/Nasdaq Data Link credentials may be necessary. No key, vendor account, trial, purchase, contact or license acceptance was made in this phase.

## 5. Research controls

- FINRA ATS remains venue/firm concentration, not investor identity.
- FINRA short-flow features remain hypotheses; Phase 372 did not produce a test result.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No new signal admitted; no forward-return, alpha, OOS, bootstrap, LOO or holdout test completed.
- No changes to universe, parameters, capital, exposure, production or holdout.
