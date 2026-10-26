# Phase 36 — FINRA ATS / off-exchange historical feasibility

Date: 2026-10-25

## Motivation
Phase 35 SEC 13D/13G failed the production universe-coverage gate (303/335 resolved issuers = 90.45% of the frozen universe in the corrected audit). The next Smart Money candidate should capture institutional/off-exchange behavior directly and have a reproducible historical publication boundary.

## Candidate source
FINRA Alternative Trading System (ATS) Transparency / OTC Transparency data.

FINRA documentation states that ATS weekly equity volume and trade-count information is published by security and ATS. Tier 1 NMS aggregate data are published with a two-week delay; other NMS/OTC categories with a four-week delay. FINRA's 2021 API update states that the production weeklySummary dataset was reduced to a rolling 12 months and weeklySummaryHistoric to a rolling 4 years; older historical data are not available from that API endpoint. The older OTC Transparency specification documents weekly reporting beginning April 25, 2016, so the 2016+ archive must be reconstructed from the downloadable/public archive rather than assumed to exist in the current API.

## PIT rule
The signal knowledge date must be the publication/download availability date, not the trading week itself. For any weekly report, only the first eligible trading session after the documented publication delay may enter the signal. `lastUpdateDate` is a revision diagnostic, not automatically a signal date; any later revision must not overwrite the originally available value in a PIT panel.

## Initial hypotheses (pre-registered, no threshold tuning)
1. Abnormal ATS share-volume ratio versus the stock's own recent history.
2. Abnormal ATS share-volume ratio relative to total consolidated volume.
3. ATS share-volume change plus subsequent price/volume confirmation.
4. Large ATS block activity as a separate hypothesis, not conflated with ordinary ATS volume.
5. ATS vs non-ATS divergence where both are available.

## Feasibility gates
- Frozen-universe coverage >= 90% in the core OOS window and >= 85% in earlier training periods.
- Historical reports available without survivorship filtering; unresolved symbols must be measured explicitly.
- Publication delay and revision fields reproducible.
- No use of revised weekly totals before their publication date.
- Enough weekly observations per issuer to support chronological OOS testing.
- Signal can be residualized against frozen LTM/F80 and tested with identical exposure.

## Fresh audit — 2026-10-26
The official FINRA Developer Center confirms `weeklySummary` contains ATS and non-ATS weekly aggregate trade data and exposes fields including `totalWeeklyShareQuantity`, `totalWeeklyTradeCount`, `summaryTypeCode`, `weekStartDate`, and `lastUpdateDate`. The current API is partitioned by week and tier and supports filtered asynchronous access, but `weeklySummaryHistoric` only retains a rolling four years and does not support general field filtering/sorting. Therefore an API-only reconstruction cannot satisfy a 2016+ OOS requirement today.

The older FINRA OTC Transparency specification independently documents weekly reports beginning April 25, 2016 and the two-week/four-week publication delays. This is enough to keep the source alive, but not enough to claim machine-reproducible full-history coverage until the archive files themselves are sampled and mapped against the frozen universe.

## Parallel Smart Money candidate — options
Cboe's official DataShop documentation confirms Option EOD Summary and Option Trades historical data from January 2012 to present. EOD Summary contains option OHLC, volume, VWAP, open interest and NBBO snapshots, with optional point-in-time IV/Greeks; Option Trades contains trade-by-trade OPRA prints, exchange, size, prevailing NBBO and optional point-in-time IV/Greeks. This is a much richer candidate for an informed-flow hypothesis, but it is commercial data and therefore remains access-gated. No alpha test is authorized until access and universe/timestamp feasibility are established.

## Research rule
Do not run an economic alpha test until the historical coverage/PIT audit passes. If coverage or publication timing fails, archive the source without forcing an alpha conclusion. For options, distinguish trade activity from position change: volume alone is not evidence of opening informed positions; open-interest changes and IV/skew context must be used to test that hypothesis.

## Current state
STAGED — feasibility only. FINRA ATS remains the strongest public-data candidate, but the current API does not provide the full 2016+ history. Options is the strongest information-density candidate but requires licensed historical access. No Smart Money signal has been admitted to the strategy.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
