# Phase 42 — Market-center / off-exchange volume feasibility audit — 2026-10-31

## Purpose
Evaluate whether publicly documented market-center volume history can provide a reproducible off-exchange / market-microstructure research input without pretending it is a stock-level Smart Money signal.

## Fresh source verification
Cboe's current U.S. equities historical market-volume archive states that it provides daily, monthly and yearly historical market-center statistics for all U.S. equities exchanges and trade-reporting facilities, broken down by Tape A/B/C, with history dating to January 2009. The daily files contain total shares traded, total notional value traded and total number of trades for each market center.

## What this enables
The source is potentially useful as a **market-center / regime descriptor** and as a denominator for broader off-exchange research. It can support questions such as:

- whether aggregate TRF/market-center share shifts contain regime information;
- whether changes in off-exchange market share alter the interpretation of stock-level volume signals;
- whether market-wide execution-location regimes interact with an independent stock-selection signal.

## What it does NOT enable by itself
The public historical market-volume archive is aggregated by market center, not security. It therefore cannot directly produce a 335-name stock-selection signal or be treated as a substitute for the missing historical security-level FINRA ATS panel.

A stock-level test using this dataset alone would violate the research design. Any eventual use must be explicitly framed as a market/regime control or interaction variable.

## PIT / availability
The archive is historical and reproducible, but the current page describes the files rather than a historical publication timestamp for each daily file. Before any economic test, record the actual publication/availability convention used by the research pipeline and ensure the feature is lagged to a demonstrably available date.

## Relationship to Phase 36
Phase 36 already killed FINRA `blocksSummary` as a direct stock-alpha source because it has no ticker dimension. This Phase 42 candidate is different: it may provide a broad market-center state variable or denominator, but it does not repair the security-level coverage problem in the FINRA ATS panel.

## Candidate hypotheses
H1: market-wide off-exchange share changes predict subsequent broad-market risk/return regimes.
H2: market-center concentration changes modify the efficacy of an independent stock-selection signal.
H3: market-center regime variables explain apparent stock-level off-exchange relationships that would otherwise be mistaken for Smart Money activity.

These are hypotheses only. No assumption is made that off-exchange volume represents informed trading.

## Required gates before testing
1. Verify exact historical file coverage and publication/availability timing.
2. Normalize market-center names and Tape A/B/C definitions across 2009-present.
3. Freeze transformations before any OOS selection.
4. Test only chronological OOS and compare incremental information against frozen LTM/F80.
5. Use identical exposure/cost assumptions and bootstrap/leave-one-date-out sensitivity.
6. Explicitly distinguish market-regime information from stock-selection alpha.

## Decision
**KEEP AS SECONDARY FEASIBILITY CANDIDATE; DO NOT RUN STOCK-LEVEL ALPHA.**

Priority remains:
1. Cboe Open-Close/OI/IV/skew for security-level options research, subject to commercial data access and coverage audit.
2. FINRA security-level ATS/off-exchange archive reconstruction.
3. SEC Form 4 after frozen-universe ticker coverage and transaction-code filtering.
4. Market-center historical volume as a possible broad regime/control variable.

No change to `F80_TOP20_PARTIAL50_BASELINE_C20`.
