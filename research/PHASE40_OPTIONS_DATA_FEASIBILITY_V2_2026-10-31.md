# Phase 40 — Historical options data feasibility V2 — 2026-10-31

## Status
**DATA FEASIBILITY STRENGTHENED; PURCHASE/COVERAGE GATE STILL OPEN. No alpha authorized.**

## Fresh official-source verification
Cboe DataShop's current FAQ states historical availability beginning:
- Open-Close Volume Summary EOD C1: January 2005.
- Option Quotes: January 2010 in the FAQ.
- Option EOD Summary: January 2010.
- Option Trades: January 2010 in the FAQ.
- Option Sentiment: January 2012.

Current product pages are more conservative for some products: the current Option Trades and Option Quotes pages advertise historical data from January 2012 onward. For research reproducibility, the product-specific purchase page and actual delivered files must govern the final usable start date, not the FAQ alone.

Option Quotes currently supports 1-minute/custom intervals with NBBO, OHLC, volume, optional open interest, and optional implied volatility/Greeks. Daily files are delivered overnight/early morning; intraday files are delayed 15 minutes after the snapshot. This gives a defensible ex-ante timestamp for daily and interval studies, subject to the exact subscription/purchase terms used.

Option Trades currently provides trade-by-trade records across the OPRA universe, including trade price/size, exchange, prevailing NBBO, and optional point-in-time IV/Greeks. The current product page advertises historical availability from January 2012.

Cboe's Option Sentiment specification describes daily historical order-flow analytics, including call/put volume, trade counts, average trade size, premiums, and open-interest-supported concentration analysis. It states that complete subscription files are delivered the following morning, generally by 5–6 a.m. ET. The dataset should be treated as a candidate analytical product until current purchase availability and field-level coverage are verified.

## Revised hypotheses
H1: abnormal directional options activity by non-market-maker capacities contains incremental information beyond frozen LTM/F80.
H2: flow combined with prior-night/opening open interest is more informative than raw volume alone.
H3: IV/skew changes add information conditional on underlying momentum, volatility and liquidity.
H4: any apparent predictive power must survive controls for prior returns, underlying volume, volatility, and explicit return-chasing tests.

## Critical PIT rule
Open interest that is only known after the close must not be used for a same-close decision. For daily signals, use the latest OI demonstrably available before the decision timestamp (e.g. prior-night/start-of-day OI when the product provides it). For end-of-day sentiment files delivered the next morning, the earliest permitted trading decision is the next session unless a historical delivery timestamp proves earlier availability.

## Required remaining gates
1. Obtain a reproducible historical sample from Cboe or another documented source.
2. Measure coverage on the frozen 335-name universe across multiple historical windows, including delisted/name-change cases where available.
3. Record exact product, purchase date, delivery timestamp, and missing-symbol/date behavior.
4. Freeze field definitions before testing, including participant capacity and open/close interpretation.
5. Build only features that would have been available at the intended decision time.

## Decision
The source is now technically credible enough to justify a concrete data-purchase/coverage audit, but not enough to authorize alpha testing. No change to `F80_TOP20_PARTIAL50_BASELINE_C20`.
