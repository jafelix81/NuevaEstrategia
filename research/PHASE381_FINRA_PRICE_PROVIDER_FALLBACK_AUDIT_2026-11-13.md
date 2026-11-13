# Phase 381 — FINRA Phase 20C price-provider fallback feasibility audit

**Status:** completed — hosted diagnostic and deterministic tests passed.ntation added; hosted provider probes pending.  
**Parent:** Phase 372 next-session-open retest, blocked at 328/329 valid symbols.  
**Scope:** data availability only; no returns, alpha or universe change.

## Problem

Phase 372 pinned the exact 2016-10-24 to 2026-10-24 window, retained the original 335-ticker universe and attempted Yahoo download plus Yahoo history retries. It returned 328 valid histories; the same seven symbols failed repeatedly: AVB, EA, EQR, LPRO, ROKU, WBD and WBS. The script correctly stopped rather than silently dropping names or altering the universe.

The run log shows the errors were returned as “possibly delisted; no price data found” even for symbols that may still be active. The underlying Yahoo HTTP/chart error was not exposed by yfinance, so a direct provider probe is needed.

## Method

Probe Yahoo chart endpoints (query1/query2), Stooq daily CSV and Nasdaq historical API for the seven missing symbols plus four control tickers (AAPL, MSFT, NVDA, SPY). Preserve the exact price window. Retain only provider availability, row counts, first/last dates and cross-provider daily-return agreement metrics; no raw price rows are persisted.

A provider fallback is not admitted merely because it returns data. It must have at least 220 observations, suitable listing-history coverage and independent-provider return concordance. Mixing providers is prohibited until a separate reconciliation phase approves adjustment and corporate-action treatment.

## Controls

No universe changes, no imputation, no mixed-source prices, no forward returns, alpha, OOS, bootstrap, LOO or holdout use. No changes to F80, production, capital, parameters or exposure.

## Hosted result — completed 2026-11-13

Run [43500356535](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500356535) passed; metadata-only artifact [14073108228](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500356535/artifacts/14073108228).

- All four controls (AAPL, MSFT, NVDA, SPY) returned 2,514 daily rows from both Yahoo query1 and query2.
- Both Yahoo chart endpoints returned HTTP 200 but zero timestamps for each of AVB, EA, EQR, LPRO, ROKU, WBD and WBS.
- Stooq returned no parseable Date/Close table in this runner.
- Nasdaq historical API returned empty rows for all 11 symbols, including controls; therefore this attempt did not validate Nasdaq as a working alternative endpoint.
- No missing ticker had 220 or more rows from any tested provider. No cross-provider comparison was possible and no fallback was admitted.

**Disposition:** Phase 20C remains blocked at 328/329 valid histories. The provider probe confirms the Yahoo failure is reproducible outside yfinance for these seven symbols, but Stooq/Nasdaq access methods still need endpoint/schema diagnosis. Do not drop tickers, alter the 335-symbol universe, impute or mix providers. No return/alpha test was run.
