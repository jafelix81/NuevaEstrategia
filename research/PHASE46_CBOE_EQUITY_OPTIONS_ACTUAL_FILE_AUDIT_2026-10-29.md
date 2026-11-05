# Phase 46 — Cboe equity-option volume actual-file audit

**Date:** 2026-10-29  
**Status:** audit pending CI  
**Scope:** source/schema/coverage feasibility only; no alpha test and no baseline change.

## Hypothesis

Equity-option volume may contain incremental information about attention, positioning, hedging pressure, or informed activity. We do **not** equate high option volume with "smart money" and will not use it as an alpha feature unless it survives chronological incremental testing versus frozen F80/LTM.

## Public source

Cboe's official historical options page states that historical equity-option volume is available through the archive through August 2019 and through the historical-options download interface from September 2019 onward. The archive exposes monthly symbol-level files. The official page also documents a much richer Open-Close dataset with customer/professional customer/broker-dealer/market-maker capacity, buy/sell and open/close fields, but that dataset is licensed and is therefore not assumed to be reproducibly available here.

## Audit design

Representative monthly files are checked for:

1. actual download success;
2. spreadsheet/schema readability;
3. symbol-level coverage against the frozen 335-symbol universe;
4. consistency across 2018 and 2019 samples.

## PIT rule

The archive labels files by month but does not expose a historical release/acceptance timestamp. Therefore month-end is **not** treated as the knowledge date. If the source survives coverage, any later signal test must use a conservative fixed publication lag that guarantees ex-ante availability.

## Decision rule

- Coverage <70% in any representative file: kill the public-volume candidate for the frozen-universe research line.
- Coverage >=70%: proceed only to a PIT-lag gate and then an incremental OOS test.
- No alpha test is authorized from this audit alone.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
