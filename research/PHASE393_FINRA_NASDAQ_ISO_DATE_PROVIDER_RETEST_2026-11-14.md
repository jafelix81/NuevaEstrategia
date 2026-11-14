# Phase 393 — FINRA Phase 20C Nasdaq ISO-date provider retest

**Status:** hosted diagnostic completed; Nasdaq public quote endpoint rejected all seven missing symbols; no fallback admitted.  
**Parent:** Phase 372/381; Phase 20C remains blocked at 328/329 valid price histories.  
**Scope:** diagnose the prior Nasdaq endpoint failure only. No prices are persisted; no fallback, returns or alpha test is authorized.

## 0. Hosted outcome — 2026-11-14 07:52 UTC

Hosted run [43573077044](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43573077044) completed successfully. Job 132381464531 passed compilation, all 6 unit tests, provider diagnostics, research-only controls and artifact upload. Artifact [14105217368](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43573077044/artifacts/14105217368), SHA-256 `407e9b5b42567e317d27139a5a95c4d0766d0dab978481d7020907325858d712`.

**Observed results:**
- Three Nasdaq-listed equity controls (AAPL, MSFT, NVDA) each returned 2,499 rows, 2016-11-14 through 2026-10-23. Yahoo query1 returned 2,514 rows from 2016-10-24 through 2026-10-23. Nasdaq therefore omitted the first 15 requested sessions in this fixed window; it does not fully satisfy the Phase 20C control window.
- On the 2,499 common dates, daily-return concordance was very high: AAPL correlation 0.99999935, MSFT 0.999999998, NVDA 0.999999953. Median absolute return differences were below 0.000004%. These are diagnostics only; price-adjustment and corporate-action semantics are not independently certified.
- All seven unresolved symbols (AVB, EA, EQR, LPRO, ROKU, WBD, WBS) returned HTTP 200 but Nasdaq application code `rCode=400`, message `Symbol not exists.`, zero rows and no dates. This is an endpoint symbol-resolution failure, not proof that the securities lack historical prices.
- SPY also returned `Symbol not exists` because the script sent `assetclass=stocks`; SPY is an ETF. Its result is an invalid asset-class control and was not retested as `assetclass=etf`. The script's strict four-control flag therefore remains false. The three equity controls do establish that ISO dates and the parser work for those Nasdaq-listed names.
- No target symbol reached 220 rows. No prices were persisted; no forward returns, alpha, fallback, holdout or production changes occurred.

**Disposition:** close this public `api.nasdaq.com/api/quote/{symbol}/historical` route as a Phase 20C fallback candidate. Do not repeat the same request or infer coverage from HTTP 200. The ISO-date correction fixed the prior request-format defect for supported controls, but it did not resolve the seven missing names. Phase 20C remains blocked at its existing 328/329 price-history gate.

## 1. Why retest

Phase 381 tested seven unresolved symbols (AVB, EA, EQR, LPRO, ROKU, WBD, WBS) and four controls (AAPL, MSFT, NVDA, SPY) over the exact window 2016-10-24 through 2026-10-23 inclusive.

The Phase 381 implementation sent fromdate=10/24/2016 and todate=10/24/2026. Public examples of the Nasdaq quote-history endpoint use ISO dates (YYYY-MM-DD), including fromdate=2019-09-11 and todate=2019-10-11. The prior run returned empty rows for all eleven symbols, including every control. Because controls also failed, it did not establish that the endpoint was valid or that any symbol lacked coverage.

This is a concrete request-format defect candidate, not proof that it caused the empty responses. Phase 393 retests the same endpoint with ISO date parameters and captures response/schema diagnostics.

Reference examples:
- Nasdaq quote-history endpoint example using ISO dates: https://stackoverflow.com/questions/58331291/webscraping-assistance/58331383
- Nasdaq API endpoint examples and accepted date format: https://github.com/damiandelio/stocks-crawler
- Phase 381 original implementation and report are retained on phase381-finra-price-provider-fallback-audit.

## 2. Locked audit design

- Exact fixed window: fromdate=2016-10-24, todate=2026-10-24 (end-exclusive in our Yahoo control query; Nasdaq's endpoint date semantics will be recorded, not assumed).
- Same seven missing names and four positive controls.
- Use limit=5000, explicit offset, and deterministic pagination.
- Record HTTP status, content type, top-level/data/table keys, provider message, reported row count, parsed row count and first/last dates.
- Do not store price values or raw responses.
- Use Yahoo query1 only for the four controls to compute daily-return concordance diagnostics; no prices leave process memory.
- An endpoint is control-validated only if all four controls return at least 220 observations from both Nasdaq and Yahoo.
- A missing symbol with at least 220 rows is only a coverage candidate; identity, adjustment, delisting and cross-provider price reconciliation remain mandatory.
- No provider mix, no imputation, no ticker deletion and no universe change.

## 3. Stooq disposition

Phase 381's unauthenticated Stooq request did not return a parseable Date,Close series. This is not evidence that the symbols have no Stooq history. Stooq is not retested here because no API key has been configured and the prior response was not diagnostically preserved. Do not treat the old Stooq result as a coverage failure.

## 4. Acceptance and stop rules

- If all four controls still fail, classify the Nasdaq endpoint as unvalidated and stop; do not infer missing-symbol coverage.
- If controls pass but any missing symbol is below its listing-date-appropriate minimum, keep Phase 20C blocked.
- If all seven missing symbols return sufficient rows, classify Nasdaq as a coverage candidate only. Require a separate corporate-action/adjustment and independent-provider concordance audit before any use.
- Never admit a fallback from this feasibility-only phase.

## 5. Research-only controls

raw_prices_retained=false; forward_returns_used=false; alpha_test_authorized=false; holdout_used=false; f80_changed=false; production_changed=false; fallback_accepted=false.

F80_TOP20_PARTIAL50_BASELINE_C20, the 335-name diagnostic universe, capital, exposure and production parameters remain unchanged.
