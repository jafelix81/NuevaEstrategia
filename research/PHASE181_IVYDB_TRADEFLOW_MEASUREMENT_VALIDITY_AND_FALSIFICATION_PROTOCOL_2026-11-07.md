# Phase 181 — IvyDB TradeFlow Measurement Validity and Preregistered Falsification Protocol

**Date:** 2026-11-07  
**Status:** PREREGISTERED — DATA NOT ADMITTED  
**Scope:** Options order flow, participant proxies, microstructure, PIT and return-chasing controls  
**Frozen control:** `F80_TOP20_PARTIAL50_BASELINE_C20`

## Executive decision

Phase 180 established that IvyDB TradeFlow is a high-priority *conditional* candidate, not a research panel. Phase 181 converts the public documentation and relevant literature into a measurement contract and falsifiable test plan. It does not construct features or run returns.

The key methodological finding is that TradeFlow's participant labels are execution-style proxies, not investor identities; its buy/sell field is aggressor direction, not open/close position status; and the vendor's 99.9% midpoint-direction assignment is a coverage statistic from one SPY FOMC session, not an independently measured 99.9% accuracy rate.

A second PIT distinction is essential: the vendor launched TradeFlow on **2026-09-30** while advertising historical data from **2016-01**. Historical backfill may support retrospective predictive research if every classification input is event-time causal and the methodology is stable. It does not prove that the proprietary feature was delivered to a strategy in 2016. Operational PIT/deployability requires first-receipt and vintage evidence.

## 1. Measurement contract

### Direction is not position opening

TradeFlow signs buyer- versus seller-initiated executions. It does not state whether the trade opened, increased, reduced or closed a position. Therefore:
- Do not call positive flow "new institutional buying".
- Do not reproduce Pan–Poteshman buyer-initiated *opening-position* put/call ratios from TradeFlow alone.
- Do not infer beneficial ownership, account identity or ultimate client type from the participant proxies.
- Treat Institutional 2 as aggressive liquidity demand only. It excludes passive executions, midpoint prints, patient position-building and market-making.
- Institutional 1 is nested within Institutional 2; never add the two.
- Retail 1/2/3 are described as mutually exclusive by the vendor, but verify that on a raw sample before aggregating.

### Classification coverage is not classification accuracy

The methodology paper's 99.9% midpoint directional assignment and 0.10% overall unclassified share refer to one SPY session on 2026-06-17 (FOMC day). They show how much volume received a direction label in that example. They do not report precision/recall against independent ground truth, nor representative performance across symbols, conditions, venues, volatility regimes or historical years.

A raw-sample validation must separately report:
- coverage/assignment rate;
- directional agreement against independently labelled or independently reconstructable trades;
- precision/recall by condition, venue, NBBO location and midpoint status;
- stability across ordinary and event sessions;
- disagreement and unclassified rates by liquidity, DTE and moneyness.

### Avoid accounting overlap

- Midpoint volume is a subset of inside-NBBO volume. Total volume is at-NBBO + inside-NBBO + outside-NBBO; do not add midpoint a second time.
- Keep unclassified volume in the total denominator and report its share separately; do not inflate signed flow by renormalizing only classified trades.
- Each multi-leg leg is signed separately. Exclude multi-leg flow in the primary directional test or preregister a separate sensitivity; a spread's legs are not an outright directional bet.
- Venue-level totals must reconcile to series-level signed volume before venue concentration features are used.

## 2. Historical availability and PIT

TradeFlow advertises a 2016-01 history but launched as a product on 2026-09-30. This creates two distinct research claims:

1. **Retrospective event-time predictive content:** potentially testable only after verifying that the classifier uses solely information available by each trade/interval, the algorithm is stable or versioned, and no later corrections or future observations enter the classification.
2. **Live strategy availability:** not established without contemporaneous delivery/first-receipt records and historical file vintages. A 2026 backfill cannot be silently treated as a feature actually delivered in 2016.

The usable timestamp for a joined feature is the maximum of TradeFlow first receipt, required Greek/underlying-data first receipt and effective-dated identity availability. Nominal interval end is not delivery time. Preserve correction vintages. Do not difference or sum snapshots until exact interval boundaries and cumulative-versus-incremental semantics are documented.

For delta-equivalent flow, use only Greeks received by the feature decision time. IvyDB US Intraday advertises 10:00, 14:00 and 15:45 ET snapshots; a later 15:45 Greek cannot be used for an earlier 5-minute interval. If no valid contemporaneous or preregistered lagged Greek exists, retain contract-level flow rather than inventing delta exposure.

## 3. Competing economic hypotheses

The same observed imbalance may represent informed trading, intermediary hedging/inventory pressure, liquidity demand or temporary price pressure. The research must distinguish:

| Hypothesis | Expected pattern | Falsification |
|---|---|---|
| H1: information continuation | Forward underlying returns remain predictable after controls | Effect disappears after prior returns/IV/liquidity controls or is only contemporaneous |
| H2: hedging / temporary pressure | Same-session or next-session impact followed by reversal | No short-lived response/reversal after costs |
| H3: participant-proxy heterogeneity | Institutional 2 differs in persistence from Retail 1/2/3 | No stable difference or result depends on overlap/backfill |
| H4: flow × IV/skew | Flow adds information conditional on volatility surface | Effect disappears with time-aligned Greeks or IV repricing controls |
| H5: execution mechanism | Condition/NBBO/venue mix explains incremental variation | No incremental effect beyond total flow and liquidity |

Relevant literature motivates competing mechanisms rather than a presumed smart-money story:
- Pan and Poteshman (2006) find predictive information in buyer-initiated option volume used to open new positions. TradeFlow does not provide opening-position status, so its measure is not a direct replication: [RFS article](https://doi.org/10.1093/rfs/hhj024).
- Bryzgalova, Pavlova and Sikorskaya (2023) find retail option imbalance predicts next-day underlying returns in their sample, but not weekly/monthly returns; they interpret the short-lived pattern as more consistent with intermediary hedging/price pressure than informed retail trading: [Journal of Finance article](https://doi.org/10.1111/jofi.13285).
- Research on option order flow and expected option returns finds inventory-risk effects can dominate asymmetric-information effects in option prices. This is a different target from underlying equity returns and warns against equating imbalance with information: [Journal of Finance article](https://doi.org/10.1111/jofi.12380).

## 4. Preregistered candidate measurements

No feature has been computed. Definitions to be frozen before data access:

1. **All signed contract imbalance:** `(buyer_initiated - seller_initiated) / total_contracts`, where total includes unclassified contracts; report unclassified share separately.
2. **All signed delta-notional:** sum of `(buy_contracts - sell_contracts) × effective_delta × effective_multiplier × contemporaneous_underlying_price`. Only use time-aligned Greeks and effective multipliers. Otherwise stay at contract level.
3. **Institutional 2 aggressive delta flow:** same signed construction for Institutional 2 only; never add Institutional 1.
4. **Retail proxy flows:** Retail 1, Retail 2 and Retail 3 separately; aggregate only after raw-sample validation of mutual exclusivity and historical field coverage.
5. **Execution-quality/mechanism controls:** unclassified share, NBBO-location shares, condition mix, multi-leg share and venue concentration.

## 5. Controls, horizons and economic evaluation

Required controls include same-session and lagged underlying returns; realized volatility; IV level/skew/term structure; option volume and OI; spreads and underlying dollar ADV; DTE, delta/moneyness, call/put and multiplier; earnings/corporate-action/macro-event indicators; multi-leg and condition mix; venue concentration; market beta, size, sector and regime.

Evaluate remainder-of-session only where a receipt-time replay is valid, overnight/next session, and 5/20/60/120-session horizons. This is a test grid, not a prescribed holding period.

If data gates pass:
- compare incremental information against frozen LTM/F80 at identical exposure and costs;
- separate contemporaneous price impact from forward continuation and reversal;
- include spread/slippage, turnover, capacity and borrow where relevant;
- use chronological development/validation, date-block bootstrap and ticker/sector/year leave-one-out;
- apply multiple-testing controls and preserve the locked final holdout;
- do not random-split time series or choose horizons using the final holdout.

## 6. Data admission gates

All nine gates remain blocked: raw samples across 2016/2020/2023/2026 including inactive/delisted names; full dictionary and interval semantics; first receipt and latency; corrections/vintages; classifier version/backfill; per-field lot-size/participant history (2016 vs 2021); independent direction-label validation; effective-dated contract/underlying identity; and price/license/derived-data rights.

## Decision

**Keep TradeFlow as a conditional priority candidate, but do not admit features or authorize backtests.** Phase 181 is a preregistration and measurement guardrail, not evidence of alpha. No vendor contact, raw-data request, purchase, final-holdout use or production change occurred. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Sources

- [IvyDB TradeFlow product page](https://optionmetrics.com/ivydb-tradeflow/)
- [TradeFlow methodology paper, September 2026](https://optionmetrics.com/wp-content/uploads/2026/09/IvyDB-TradeFlow-A-Framework-for-Options-Volume-Classification-and-Microstructure-Analytics.pdf)
- [Legacy Signed Volume brochure, August 2024](https://optionmetrics.com/wp-content/uploads/2024/08/Signed-Volume-Brochure_v6.pdf)
- [IvyDB US Intraday](https://optionmetrics.com/united-states-intraday/)
- [Pan & Poteshman (2006)](https://doi.org/10.1093/rfs/hhj024)
- [Bryzgalova, Pavlova & Sikorskaya (2023)](https://doi.org/10.1111/jofi.13285)
- [Option order flow and inventory risk (2015)](https://doi.org/10.1111/jofi.12380)
