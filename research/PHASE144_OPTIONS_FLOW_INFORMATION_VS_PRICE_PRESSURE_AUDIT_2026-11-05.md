# Phase 144 — Options-flow information versus inventory/price-pressure audit

**Date:** 2026-11-05  
**Input:** Phases 140–143; public academic literature on options order flow and retail options trading.  
**Mode:** literature and schema audit only. No raw vendor data, forward-return test, vendor contact, purchase or production change.

## Decision

**TradeFlow remains the leading conditional all-venue flow dataset, but its signed aggressor volume cannot by itself reproduce the best-known informed-options-flow measure.** The key missing distinction is whether the trade opened a new position or closed/reduced an existing one.

This is not a minor naming issue. The seminal stock-return result of Pan and Poteshman (2006) uses buyer-initiated volume to open new positions. TradeFlow's published four-table schema reports buyer-/seller-initiated volume, execution conditions, quote location and venue, but does not document an opening/closing field. Cboe Open-Close supplies opening/closing classification for Cboe venues, but not a whole-OPRA, trade-level combination of opening/closing and aggressor direction.

Therefore:
- Do not label TradeFlow buyer-initiated flow as “new buying”, “opening demand” or “informed accumulation”.
- Treat Cboe Open-Close as a complementary, venue-limited position-state source, not as a direct all-market replacement.
- Keep the exact “buyer-initiated to open” hypothesis gated until a source or a validated cross-source join provides both dimensions on the same trades/contracts.
- Separate information from intermediary inventory hedging and temporary price pressure in every return test.

## 1. The literature points to a specific mechanism, not generic flow

### Pan & Poteshman (2006): opening buyer-initiated positions

Pan and Poteshman, *The Information in Option Volume for Future Stock Prices*, Review of Financial Studies 19(3), 871–908 (2006), construct put/call ratios from option volume initiated by buyers **to open new positions**. Their abstract reports that low-ratio stocks outperformed high-ratio stocks by more than 40 basis points the next day and more than 1% over the next week in their historical sample.

The relevant unit is not simply buyer-initiated volume. It is buyer-initiated volume that creates new positions, separated by calls and puts. This prevents closing transactions and some position turnover from being interpreted as fresh demand.

**TradeFlow gap:** its public methodology describes aggressor direction but does not document open/close state. Signed calls/puts alone are therefore a weaker and different hypothesis. The original result cannot be assumed to transfer.

### Bryzgalova, Pavlova & Sikorskaya (2023): retail flow can predict briefly without being informed

The Journal of Finance paper *Retail Trading in Options and the Rise of the Big Three Wholesalers* uses OPRA price-improvement flags, particularly SLAN, and validates its retail proxy against broker outages and trading restrictions. Its sample covers 2019-11-04 through 2021-06-30.

The paper reports:
- retail options trades lose money on average, with losses concentrated in short-term contracts and substantial execution costs;
- retail options flow and call/put imbalances can predict next-day underlying returns;
- the authors interpret the short-horizon predictability as more consistent with **intermediary hedging demand and price pressure** than private information.

This is a critical warning for our project: a feature can forecast next-day returns and still not identify informed traders. For a swing strategy, we must test whether the effect persists, reverses or disappears after the immediate hedging/price-pressure window.

The paper's SLAN-based retail proxy is not identical to every vendor “Retail” bucket. Do not equate the categories or splice their definitions without an explicit mapping.

### Muravyev (2016): inventory risk is a first-order confound

Muravyev, *Order Flow and Expected Option Returns*, Journal of Finance 71(2), 673–708 (2016), decomposes option-trade price impact into inventory-risk and asymmetric-information components. The abstract reports that inventory risk has the larger impact and that inventory-related imbalance has a much larger effect on option prices than previously thought.

Thus an option imbalance can reflect dealer inventory/risk management rather than private information. A flow feature that predicts option prices or IV does not automatically predict the underlying stock's future direction.

### Kang, Kang & Lee (2022): institutional intraday evidence is not single-stock proof

Their Journal of Futures Markets study reports that option order imbalances in the first ten minutes predict the rest of the day for stock indices and index futures, with the predictability mainly driven by institutional traders rather than day traders. This is useful adjacent evidence for an opening-session/time-of-day hypothesis, but the market studied is index/index futures; it is not direct evidence for a cross-sectional single-stock swing strategy.

## 2. What our sources can and cannot identify

| Source | Aggressor direction | Open/close | Participant proxy | Market scope | Current ruling |
|---|---|---|---|---|---|
| IvyDB TradeFlow | Yes, vendor-classified | Not documented | Execution/size/condition buckets | All U.S. options exchanges, vendor claim | Best conditional broad signed-flow source; not opening-flow identity |
| Cboe Open-Close EOD | Buy/sell side by capacity, not the same as aggressor signing | Yes | Clearing-origin capacity | Cboe venues only | Complementary position-state panel |
| Cboe TBT + quotes | Trade/side fields; aggressor inference needs quote alignment | Open/close field exists in sample schema | Limited Cboe capacity fields | C1 only | Potential exact-event diagnostic; quote/side semantics and joins must be validated |
| IVolatility signed flow | NBBO-signed OPRA flow | Not documented in public endpoint announcement | Customer Greeks/filters are derived categories, not beneficial-owner identity | Broad OPRA-derived flow | Methodology robustness, not opening-position identification |

A Cboe Open-Close buy/open count is not the same thing as an aggressor-initiated buy/open trade. Do not join aggregate capacity/open-close counts to TradeFlow and call the result “informed opening flow”. At most, exact same-contract/date overlap can test whether broad signed flow and C1 opening/closing composition move together; it cannot identify the same trade unless stable event-level keys and both semantics are present.

## 3. Required experiment design if data access/PIT gates pass

Pre-register separate hypotheses rather than one generic “smart money” score:

1. **Aggressor imbalance:** TradeFlow buyer-initiated minus seller-initiated volume, calls and puts separately, scaled by total option volume and lagged OI. This is liquidity-demand flow, not necessarily position creation.
2. **Opening-position imbalance:** only if a validated source provides opening/closing and buyer/seller initiator on the same observation. This is the closest analogue to Pan–Poteshman.
3. **Retail auction flow:** SLAN and broader auction/size proxies separately. Test whether it creates short-lived pressure, not whether it is “smart”.
4. **Aggressive large flow:** ISO and large AUTO proxies separately. Interpret as urgent liquidity demand, not total institutional ownership or accumulation.
5. **C1 capacity/open-close:** use Cboe Open-Close to measure opening versus closing composition by capacity on covered venues; report C1 share and never extrapolate to whole OPRA without an all-venue denominator.
6. **Dealer/inventory pressure:** use IV/Greeks and market structure to control for hedging/inventory conditions. Do not assume dealer gamma sign is a stock-direction signal.

For every feature:
- feature knowledge time = interval end plus verified first availability; no use of a bar before it is actually received;
- compare next-session, 5-, 10- and 20-session outcomes (and, where intraday data are PIT-valid, remainder-of-day) to distinguish immediate pressure from persistence/reversal;
- control for preceding and contemporaneous underlying returns, realized volatility, option/underlying liquidity, spread, earnings and scheduled news, 0DTE share, moneyness and tenor;
- use identical exposure and transaction costs versus frozen F80/LTM;
- train chronologically, preserve untouched OOS and final holdout, block-bootstrap by date, issuer leave-one-out, and correct for multiple testing;
- report both underlying-return prediction and option-price/IV effects separately.

A result that exists only contemporaneously or at the next close, then reverses, is price-pressure evidence—not durable informed positioning. A result that survives controls and persists across horizons is still only a candidate until it clears OOS and economic-cost gates.

## 4. Research priority update

1. **TradeFlow raw sample and delivery/version evidence** — still the top data-access gate. Need same-date 5m/30m/EOD reconciliation, correction vintages, first receipt and exact open/close field inventory.
2. **Cboe Open-Close + TBT** — test whether exact contract/venue/date semantics can bridge position state and trade direction without invalid aggregate joins. Keep C1-only limitations explicit.
3. **IvyDB US OI/IV/Greeks** — complementary risk/contract context; first-received patches and adjusted deliverables remain mandatory.
4. **Independent OPRA reconstruction** — use only where timestamped quotes/trades and schema availability are contemporaneous; cross-vendor agreement alone is not independent validation.

FINRA short-flow stock selection remains killed under Phase 100; the Phase 31 flow × short-interest panel remains killed for the frozen universe under Phase 37 because joint short-interest coverage was only about 98/335 at best. Do not reopen either with cosmetic transformations. FINRA ATS/OTC remains a separate conditional market-structure source pending historical first-publication vintages and effective-dated security identity.

## 5. Final status

No alpha result is claimed. No forward-return experiment was run. No final holdout was touched. No vendor contact, trial, purchase or terms acceptance occurred. No production strategy or parameter changed.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## References

- [Pan & Poteshman (2006), Review of Financial Studies](https://doi.org/10.1093/rfs/hhj024); [NBER Working Paper 10925](https://www.nber.org/papers/w10925)
- [Bryzgalova, Pavlova & Sikorskaya (2023), Journal of Finance](https://doi.org/10.1111/jofi.13285); [author-hosted paper](https://www.sikorskaya.net/files/Bryzgalova_Pavlova_Sikorskaya_2023.pdf)
- [Muravyev (2016), Journal of Finance](https://doi.org/10.1111/jofi.12380)
- [Kang, Kang & Lee (2022), Journal of Futures Markets](https://doi.org/10.1002/fut.22301)
- [OptionMetrics TradeFlow methodology paper, 2026-09-28](https://optionmetrics.com/wp-content/uploads/2026/09/IvyDB-TradeFlow-A-Framework-for-Options-Volume-Classification-and-Microstructure-Analytics.pdf)
