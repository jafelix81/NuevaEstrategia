# Phase 372 — FINRA short-flow next-session-open retest: data gate blocked

**Date:** 2026-11-13  
**Disposition:** **NOT RUN — fixed-universe price-history gate failed. No corrected pseudo-OOS return result exists.**

## 1. Purpose

Phase 20C originally selected FINRA short-flow factors using chronological prior-signal data, but its diagnostic used close-to-close forward returns from the same close at which the daily FINRA file becomes available after the regular session. That entry convention is not executable.

Phase 372 pins the historical price window to **2016-10-24 through 2026-10-24**, preserves the original 335-name configured universe and requires the same 329 valid names as the original Phase 20C run. It is designed to enter at the next session open and use fixed close exits at 5/10/20 sessions. The six consumed Phase 20B final-OOS dates remain excluded.

## 2. Result

The code compiled and its offline tests passed. The hosted run then failed before any FINRA signal panel or return calculation:

- Expected valid universe: 329.
- Retrieved: 328.
- Remaining failures: AVB, EA, EQR, LPRO, ROKU, WBD and WBS.
- Recovery attempts: 0 additional names recovered.
- A targeted ROKU retry beginning on its actual first trading date, **2017-09-28**, also returned no Yahoo/yfinance price data.

The 2017-09-28 listing date is independently documented by Nasdaq's IPO announcement and Roku's subsequent SEC filing; the provider failure is therefore not evidence that ROKU was unlisted during the requested sample.

## 3. Decision

Do not:
- silently drop ROKU and run a 328-name sample;
- substitute another ticker;
- mix a different price vendor for one name without a documented reconciliation against the frozen price source;
- alter the 12 pseudo-OOS dates, six-date consumed holdout, LTM/F80 or production universe.

The next step, if Phase 20C remains worth pursuing, is a **targeted ROKU provider diagnostic** (e.g., Yahoo `period=max` and chart/history endpoint variants) before another full-universe run. Given the already weak 12-date Phase 20C evidence, do not spend repeated full-universe runs until the one-name retrieval issue is resolved.

## 4. Controls

No pseudo-OOS returns were calculated in Phase 372. No artifact with results was produced. No holdout used, no signal admitted, no universe/parameter/capital/production change. F80 remains frozen.

Runs:
- https://github.com/jafelix81/NuevaEstrategia/actions/runs/43481196468
- https://github.com/jafelix81/NuevaEstrategia/actions/runs/43481200906

Original Phase 20C run and artifact:
- https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254
- https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254/artifacts/12562171831

Public listing-date references:
- Nasdaq announcement: https://www.globenewswire.com/news-release/2017/09/28/1134533/6948/en/Nasdaq-Welcomes-Roku-Inc-Nasdaq-ROKU-to-The-Nasdaq-Stock-Market.html
- Roku SEC filing: https://d18rn0p25nwr6d.cloudfront.net/CIK-0001428439/4597eb6b-9817-4c7a-9924-67b722918717.pdf
