# Phase 47 — Options coverage gate design — 2026-11-01

## Status
**FEASIBILITY CONFIRMED; COVERAGE/PIT PURCHASE GATE NOT YET PASSED. No alpha authorized.**

## Purpose
Convert the Phase 40 options-source review into a falsifiable coverage gate before any options alpha test. The objective is to determine whether Cboe historical options products can support a reproducible point-in-time panel on the frozen 335-name universe without silently changing the universe or using information unavailable at the decision time.

## Fresh source audit
Cboe's current DataShop documentation confirms:
- Option Trades: trade-by-trade U.S. listed options across the OPRA universe, with trade price/size, exchange, prevailing NBBO and optional point-in-time IV/Greeks; current product page advertises history from January 2012.
- Option Quotes: 1-minute/custom intervals with NBBO, OHLC, volume, optional open interest and optional IV/Greeks; current product page advertises history from January 2012 and daily files are delivered overnight/early morning.
- Open-Close Volume Summary EOD C1: historical availability from January 2005; participant capacity, buy/sell and open/close are explicit dimensions. Cboe's rule filing states this is proprietary exchange data and does not include other exchanges.
- Open-Close therefore has the best economic fit for the Smart Money hypothesis, but it is exchange-specific and cannot be treated as OPRA-wide coverage.

## Coverage gate
Before alpha testing, the delivered historical sample must report, by calendar window and by ticker:
1. first and last usable date;
2. fraction of trading sessions with usable observations;
3. fraction of sessions with non-zero option volume;
4. fraction with non-missing OI where OI is required;
5. continuity around ticker changes/delistings;
6. missing-date and missing-symbol counts;
7. exchange/product scope;
8. exact delivery/availability convention used for every feature.

Required windows should include at least 2005–2010, 2011–2015, 2016–2020, 2021–2023 and 2024–present for C1 Open-Close, plus 2012–2015, 2016–2020 and 2021–present for OPRA-wide trades/quotes.

A source passes only if coverage is sufficient across the frozen universe without introducing survivorship selection. If coverage is materially lower for historical periods, those periods must remain in the denominator and the source is rejected for the production experiment rather than replacing the universe with today's survivors.

## PIT gate
No same-close signal may use information delivered after the close. For daily features:
- prior-day/start-of-day OI may be used only when its timestamp is demonstrably available before the decision;
- EOD flow/sentiment delivered the next morning belongs to the next trading session;
- trade-level data may use a trade only after its timestamp, with no future aggregation leakage;
- documented historical OI shifts and convention breaks must be corrected before feature construction.

## Preferred initial feature family
Do not begin with a broad factor search. If the coverage gate passes, freeze a small test set:
1. Customer/Pro-Customer directional opening volume imbalance;
2. same imbalance normalized by underlying option volume;
3. opening flow relative to prior OI;
4. closing flow imbalance as a separate hypothesis;
5. optional IV/skew change conditional on the flow signal.

Market-maker volume should be retained as a control, not automatically interpreted as informed or uninformed. No label of 'smart money' is assigned ex ante.

## Anti-return-chasing controls
Every candidate must be tested conditional on:
- prior 1d/5d/20d underlying returns;
- abnormal return versus market/sector;
- underlying volume and realized volatility;
- option liquidity/spread proxies.

A signal that disappears after these controls is classified as return-chasing or a liquidity/momentum proxy, not incremental smart-money information.

## OOS protocol
If the data gate passes, use chronological train/validation/OOS periods with all feature definitions and thresholds frozen before final OOS. Compare against `F80_TOP20_PARTIAL50_BASELINE_C20` using identical exposure and costs. Require issuer/ticker-clustered bootstrap where appropriate, leave-one-name-out diagnostics, and robustness across historical subperiods.

## Decision
Do not purchase or model around an assumed coverage level. The next action is a concrete delivered-file audit. If Cboe cannot provide a reproducible historical sample with sufficient coverage over the frozen 335-name universe, this line should be archived rather than substituted with a smaller survivor universe.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
