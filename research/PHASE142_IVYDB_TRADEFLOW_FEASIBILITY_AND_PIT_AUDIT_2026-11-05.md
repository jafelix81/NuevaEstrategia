# Phase 142 — IvyDB TradeFlow feasibility and point-in-time audit

**Date:** 2026-11-05  
**Scope:** public vendor documentation and methodology review only. No raw-data access, trial account, purchase, vendor contact or alpha test.

## Decision

**IvyDB TradeFlow is now the highest-priority options-flow candidate for a future all-venue study, conditional on historical PIT, version lineage and sample validation.** It is materially more promising for broad U.S. equity-option coverage than a C1-only flow series: OptionMetrics claims every U.S. option across all U.S. exchanges, with 5-minute, 30-minute and EOD data and historical coverage from January 2016.

This is a source-feasibility decision, not evidence of predictive alpha. The current TradeFlow product launched on **2026-09-30**. Its 2016 backfill must not be treated as if the current classification had been available to traders since 2016.

## 1. Product scope and data structure

The current product page and September 30, 2026 launch announcement describe:

- every U.S. option, every day, from January 2016;
- all U.S. options exchanges;
- 5-minute, 30-minute and end-of-day snapshots;
- buying/selling pressure, trade aggressiveness, lot-size distributions and venue activity;
- data that complements IvyDB US.

The vendor paper describes four relational tables, keyed by option symbol, SecurityID and date:

1. **Signed_Volume** — buyer-initiated, seller-initiated and unclassified volume by option series and interval;
2. **Trade_Conditions** — condition-code decomposition;
3. **Market_Structure** — execution location relative to NBBO;
4. **Signed_Exchange** — venue-level allocation of signed volume.

The paper says the component tables reconcile to Signed_Volume. This is a useful internal consistency property, but it still requires independent validation against raw OPRA or another all-venue source.

## 2. Directional classification: better than naive bid/ask, not ground truth

The vendor describes a sequential classifier:

1. identify trades executed against previously posted passive orders;
2. identify small price improvements through exchange auction mechanisms;
3. classify remaining trades nearer the offer as buyer-initiated and nearer the bid as seller-initiated;
4. resolve midpoint trades with supplementary market information said to be available at the time;
5. use direction relative to the prior trade for the remaining unresolved cases.

The product paper reports that 10.2% of SPY volume on 2026-06-17 printed at midpoint and that 99.9% of that midpoint volume received a direction. Across all locations, 0.10% remained unclassified.

**Important distinction:** 99.9% is reported classification coverage, not independently measured classification accuracy. The paper's demonstration is one SPY session (the June 17, 2026 FOMC day), written by the vendor. It is not an independent accuracy study or an out-of-sample return test.

The use of prior-trade direction appears potentially causal, but the vendor must confirm the exact event-time sequencing, quote synchronization, correction handling and that no post-trade information enters the classifier.

## 3. Retail and institutional labels are operational proxies

TradeFlow's proprietary buckets are based on trade condition, size, price location and notional value—not verified beneficial-owner identity.

- **Retail 1:** single-leg auction (SLAN) prints below 10 contracts; the strictest auction-based retail proxy.
- **Retail 2:** automatic executions below 10 contracts at the bid or offer; broader and potentially contaminated by institutional algorithms.
- **Retail 3:** automatic executions below 10 contracts and below $5,000 notional; intended to capture small price-improved executions.
- **Institutional 1:** intermarket sweep orders (ISO) at or through the prevailing quote.
- **Institutional 2:** Institutional 1 plus automatic executions above 10 contracts and above $5,000 notional.

Retail 1/2/3 are described as mutually exclusive. Institutional 1 is contained in Institutional 2; **do not add them**. Institutional 2 is an aggressive-liquidity-demand measure only. The paper explicitly excludes passive execution, midpoint prints, patient position-building and market-making activity from its institutional measures. It is not total institutional participation.

For our research, these should remain named hypotheses, not literal investor identities. In particular, large size or ISO execution does not prove that a hedge fund has directional information.

## 4. Coverage and useful complementary data

OptionMetrics' IvyDB US page claims complete EOD coverage of U.S. exchange-traded equity and index options, including ETFs and ADRs, from January 1996. It provides option volume, open interest, bid/ask, IV and Greeks, permanent SecurityIDs, ticker/name-change history and records for securities that no longer trade.

This makes the combination attractive:

- TradeFlow for all-venue signed volume, trade mechanisms and venue migration;
- IvyDB US for OI, IV, Greeks, option surfaces and historical security identity;
- Cboe Open-Close for a different view: capacity buckets and opening/closing activity on Cboe venues.

TradeFlow does not replace Cboe Open-Close: the public TradeFlow methodology does not claim to identify whether the customer's position is opening or closing. Conversely, Cboe Open-Close is not the full OPRA market. A joint feature may be complementary, but only after same-date, same-series reconciliation.

IvyDB US also provides daily patch files that can correct prior prices/calculations. The first-received file and every patch must be preserved; the current database value cannot automatically be assumed to have been known historically.

## 5. Version lineage and strict PIT

The public documentation exposes several product generations:

| Version/event | Public date | What is documented |
|---|---|---|
| Signed Volume 2.0 | 2021-03-07 | Added retail trade tracking and expanded signed-direction detail |
| Signed Volume intraday | 2024-08-07 | 5- and 30-minute snapshots alongside EOD |
| IvyDB TradeFlow launch | 2026-09-30 | New all-exchange classification framework, 5m/30m/EOD, history back to 2016 |

Current brochures advertise TradeFlow history from January 2016; the 2024 Signed Volume brochure also advertises history from January 2016 and says lot-size fields begin in 2021. These claims do not establish when each historical version, field or interval was first delivered, whether earlier dates were backfilled later, or whether the new TradeFlow algorithm was applied retrospectively.

**PIT ruling:**

- Treat TradeFlow's 2016 history as historical research data, not automatically as a 2016-2026 live-available signal.
- For strict executable OOS, use TradeFlow only after its actual first delivery and preserve the received file/version timestamps.
- Earlier Signed Volume versions may support a longer prospective history, but require exact first-availability dates, field/version changes, intraday backfill dates and revision logs.
- Do not splice legacy Signed Volume and TradeFlow as one homogeneous series without an overlap study and a preregistered regime break.
- If the vendor cannot supply historical first-publication/version timestamps, reconstruct the feature from raw contemporaneous OPRA data or restrict strict PIT validation to the verified prospective window.

The current product page and brochure do not provide a public raw-data sample, detailed delivery-time SLA, price schedule, immutable historical publication log or full revision methodology. These remain hard gates. No vendor contact or purchase was attempted.

## 6. Research priority and preregistered candidate families

If the access/PIT gates pass, evaluate a small, non-overlapping feature family:

1. total net signed volume, normalized by total option volume and/or prior OI;
2. delta-weighted signed volume, with Greeks timestamped no later than the flow interval;
3. Retail 1 (strict), Retail 1 + Retail 3 (intermediate), and Retail 1 + Retail 2 + Retail 3 (broad);
4. Institutional 2 aggressive flow, kept separate from total signed flow;
5. venue concentration and migration in net signed volume;
6. calls and puts separately, then maturity/moneyness buckets;
7. interaction with OI changes, IV level, skew and term structure.

Every candidate must be tested for return-chasing versus prediction: lag the feature to its first verified availability, control for contemporaneous underlying return/volatility and liquidity, and test whether it adds information beyond frozen LTM/F80. Use identical exposure/costs, chronological OOS, bootstrap and issuer LOO. Do not select the most profitable bucket after looking at the holdout.

## 7. Source ranking after Phase 142

| Source | Best use | Current status |
|---|---|---|
| IvyDB TradeFlow | All-venue signed flow, trade mechanisms, venue and aggressive retail/institutional proxies | **Top conditional candidate**; PIT/version/sample gates open |
| IvyDB US | Long-history OI, IV, Greeks, surfaces and permanent security identity | Strong complementary historical foundation; patch PIT must be preserved |
| Cboe Open-Close EOD | Capacity × side × open/close on Cboe venues | Conditional; correct one-sided volume units and venue-share limits |
| Cboe Option Trades | OPRA-wide raw daily denominator/trade context | Conditional; public sample timestamp mismatch and one-symbol coverage |
| Cboe TBT/GRK | Execution detail and Greeks | Secondary diagnostic; Phase 140 temporal-join restrictions remain |

**No alpha is demonstrated or claimed.** No forward-return test was run, no data was purchased, no vendor was contacted, and F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Official references

- [IvyDB TradeFlow product page](https://optionmetrics.com/ivydb-tradeflow/)
- [TradeFlow launch announcement — 2026-09-30](https://optionmetrics.com/news/optionmetrics-launches-ivydb-tradeflow/)
- [TradeFlow brochure (August 2026)](https://optionmetrics.com/wp-content/uploads/2026/08/TradeFlow-Brochure-1-1.pdf)
- [TradeFlow methodology paper (September 2026)](https://optionmetrics.com/wp-content/uploads/2026/09/IvyDB-TradeFlow-A-Framework-for-Options-Volume-Classification-and-Microstructure-Analytics.pdf)
- [IvyDB US product page](https://optionmetrics.com/united-states/)
- [IvyDB Signed Volume page](https://optionmetrics.com/signed-volume/)
- [Signed Volume intraday announcement — 2024-08-07](https://optionmetrics.com/news/optionmetrics-releases-signed-volume-intraday-with-5-and-30-minute-snapshots-on-directional-options-order-flows-for-assessing-0dte-options-market-maker-inventory-hedging/)
