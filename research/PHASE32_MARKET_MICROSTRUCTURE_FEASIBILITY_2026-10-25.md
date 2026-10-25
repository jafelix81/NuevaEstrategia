# Phase 32 — Market Microstructure / Institutional Flow Feasibility Audit

Date: 2026-10-25

## Objective

Identify a historical, point-in-time-safe source capable of measuring informed/institutional behavior at stock level, without assuming that any observed flow is inherently "smart money".

The candidate must have:

- ex-ante timestamps or availability dates;
- sufficient historical depth for chronological OOS testing;
- broad US-equity universe coverage;
- reproducible identifiers and corporate-action handling;
- enough granularity to define a signal before the return window;
- feasible access for both research and eventual production use.

Frozen control remains `F80_TOP20_PARTIAL50_BASELINE_C20` / LTM. Phase 30 showed MOM120 is not established incremental alpha and therefore remains a control only.

## Candidate audit

### 1. SEC MIDAS — high information quality, poor research accessibility

The SEC states that MIDAS collects posted orders, modifications/cancellations, trade executions and off-exchange executions from the national equity exchanges, with microsecond timestamps. It also processes equity options and futures. This is exceptionally strong conceptually for order-flow research.

However, MIDAS is an SEC analytical system; the public material describes the system and methodology but does not provide a public historical event-level download/API suitable for our reproducible GitHub pipeline.

Decision: **DO NOT PURSUE AS PRIMARY DATA SOURCE** unless a reproducible public extract becomes available.

### 2. FINRA ATS / OTC — economically relevant, but access uncertainty remains

FINRA documents historical weekly-summary datasets with roughly four years of rolling history. The existing Phase 26 audit already found the relevant OTC/ATS route conceptually promising but blocked by unauthenticated HTTP 405 / authenticated 401 behavior.

Decision: **KEEP AS SECONDARY CANDIDATE**, but do not spend further research cycles until access can be reproduced programmatically.

### 3. Direct-feed / order-book data — strongest executable research candidate

Databento currently advertises historical US-equity data across exchanges and ATSs, including trades, quotes, L1/L2/L3 order-book data and auction imbalance. Its US-equities coverage includes Nasdaq TotalView-ITCH and multiple other venues; historical coverage for the core Nasdaq TotalView feed begins in 2018. It also offers historical equity-options data and multiple US options venues.

This is materially better aligned with our objective than another low-frequency proxy because it can support hypotheses such as:

- aggressive buy/sell imbalance;
- signed volume / order-flow imbalance;
- depth imbalance;
- cancellation/quote-lifetime behavior;
- auction imbalance;
- abnormal off-exchange/ATS activity where venue classification permits it;
- options IV/skew/open-interest changes using the same PIT framework.

The principal limitation is **commercial access**. Historical data are usage-priced, although Databento currently advertises $125 in free credits for new accounts. No project credential is currently available to this research runtime, so an actual historical pilot cannot be executed yet.

Decision: **PROMOTE TO NEXT PRIMARY RESEARCH CANDIDATE, ACCESS-BLOCKED**.

### 4. Cboe public options history — insufficient for the desired stock-level test

Public Cboe historical pages provide useful aggregate options statistics, but the contract-level historical dataset needed for stock-specific OI/IV/skew/flow reconstruction is commercial. The earlier Phase 24 audit therefore remains valid.

Decision: **ARCHIVE AS PUBLIC-ONLY ROUTE**; revisit through a licensed historical dataset, preferably a unified source that also supplies PIT identifiers.

## Recommended Phase 32 hypothesis family

Do not start by optimizing a single microstructure metric. First run a pre-registered feasibility/control experiment on a fixed sample:

1. Select a broad liquid-US universe that overlaps the frozen strategy universe.
2. Construct daily or near-close features from order/trade data using only events available by signal cutoff.
3. Candidate features, fixed before OOS evaluation:
   - signed-volume imbalance;
   - trade-size imbalance;
   - quote/depth imbalance;
   - cancellation-to-add ratio;
   - abnormal auction imbalance;
   - venue/off-exchange share where reliably identified.
4. Neutralize/condition on LTM/F80 and, where useful, MOM120 so that any result is genuinely incremental.
5. Use chronological OOS only; no pooled random train/test split.
6. Evaluate IC, top-minus-bottom spread, residualized return, block bootstrap and LOO.
7. Only if an individual family survives should we combine complementary microstructure features.

## Important economic distinction

These features are **proxies for market behavior**, not labels for "smart money." A positive result could arise from liquidity provision, inventory effects, price discovery, mechanical rebalancing, or short-term reversal rather than informed trading. The research therefore tests whether the information is economically useful, not whether a story about institutional traders sounds plausible.

## Current decision

**Phase 31 FINRA flow × short-interest divergence: killed as an independent alpha hypothesis.**

**Phase 32 microstructure: feasibility passed conceptually, but executable historical testing is blocked by commercial-data access.**

No change to the frozen F80/LTM baseline is authorized.

## External evidence reviewed

- SEC MIDAS description: https://www.sec.gov/securities-topics/market-structure-analytics/midas-market-information-data-analytics-system
- FINRA historical weekly-summary documentation: https://developer.finra.org/news/q12021
- Databento US equities: https://databento.com/equities
- Databento historical market data: https://databento.com/historical
