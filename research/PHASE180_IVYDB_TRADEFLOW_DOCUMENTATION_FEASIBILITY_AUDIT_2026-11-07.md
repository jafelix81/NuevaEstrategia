# Phase 180 — IvyDB TradeFlow Documentation and Data-Feasibility Audit

**Date:** 2026-11-07  
**Status:** CONDITIONAL CANDIDATE — NOT FEATURE-ADMITTED  
**Research line:** Options order flow / participant-capacity proxies  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Executive decision

A material product change justifies reopening the OptionMetrics Signed Volume source review: OptionMetrics launched **IvyDB TradeFlow on 2026-09-30**, describing it as the evolution of Signed Volume. The vendor advertises every U.S. option across all U.S. options exchanges, daily history from January 2016, and 5-minute, 30-minute and end-of-day aggregates. The new methodology adds trade-condition, venue, VWAP/NBBO-location and proprietary retail/aggressive-institutional proxy fields.

This is a stronger candidate for broad cross-exchange order-flow research than the earlier Signed Volume specification. It is **not yet a usable research panel**. The public material does not establish first receipt, revisions, historical coverage of inactive/delisted contracts, uniform backfill of the new participant fields, exact interval semantics, a representative raw sample, or commercial terms. No feature, backtest or alpha claim is admitted.

## What the vendor now documents

### Product scope and structure

The product page and launch announcement advertise all U.S. options exchanges, every U.S. option every day since January 2016, and 5-minute, 30-minute and EOD intervals. The vendor methodology paper describes four relational tables:

- `Signed_Volume`: buyer-initiated, seller-initiated and unclassified volume, buy/sell VWAP and lot-size distribution.
- `Trade_Conditions`: direction and lot-size counts by exchange-reported condition code.
- `Market_Structure`: execution location relative to the NBBO.
- `Signed_Exchange`: venue-level signed volume.

The paper says each record aggregates one option series over a reporting interval and retains unclassified volume. Exact interval boundaries, the full interval key, cumulative-versus-incremental behavior and revision handling still require a raw sample and data dictionary.

### Direction classifier

The documented sequence is: passive-order/condition screening; exchange-auction price-improvement screening; comparison with the prevailing quote; supplementary contemporaneous market information to resolve midpoint prints; then prior-trade price direction for the remaining unresolved trades. The paper does not publish full production code or every threshold/tie-break rule.

The vendor's headline 99.9% midpoint-direction assignment and 0.10% overall unclassified share come from **one SPY session, 2026-06-17 (FOMC day)**: 12,932,090 contracts, of which 1,321,280 (10.2%) printed at midpoint. This is an illustrative one-day vendor example, not a general historical accuracy estimate or independent evidence of predictive value.

### Participant fields: proxies, not identities

The vendor defines three mutually exclusive retail proxies and two nested institutional proxies:

- **Retail 1:** SLAN single-leg auction prints below 10 contracts; the strictest proxy.
- **Retail 2:** automatic executions below 10 contracts at bid/offer; the paper explicitly notes some institutional-algorithmic contamination.
- **Retail 3:** automatic executions below 10 contracts and below $5,000 notional inside the NBBO; described as consistent with wholesaler internalization.
- **Institutional 1:** ISOs executing at or through the prevailing quote.
- **Institutional 2:** Institutional 1 plus automatic executions at/through the quote exceeding both 10 contracts and $5,000 notional.

Retail 1/2/3 are mutually exclusive and may be combined only after their definitions are validated. Institutional 1 is contained in Institutional 2 and **must not be added to it**. Institutional 2 captures aggressive liquidity demand, not all institutional participation: passive execution, midpoint prints, patient position-building and market-making activity are outside the proxy. None of these fields identifies a beneficial owner or account. The labels must not be treated as ground-truth “smart money.”

### Important reconciliation and overlap rules

- In `Market_Structure`, midpoint volume is a **subset** of inside-NBBO volume. Total volume is at-NBBO + inside-NBBO + outside-NBBO; adding midpoint separately double-counts it.
- The vendor says `Signed_Exchange` venue rows reconcile to `Signed_Volume`; this must be tested on a sample.
- Multi-leg executions have each leg signed individually. Primary analysis must either isolate/exclude multi-leg flow or preregister a separate sensitivity; do not assume a spread's legs have a common directional sign.
- TradeFlow is aggressor-side, not open/close position status. It does not replace Cboe Open-Close.

## Historical-field and PIT gaps

The 2024 Signed Volume brochure says volume lot-size fields begin in **2021**. The 2026 TradeFlow brochure advertises the overall product from January 2016 and includes lot-size/participant analytics, but does not state whether every new lot-size and participant-proxy field is backfilled uniformly to 2016. This is an unresolved per-field historical-coverage conflict. Do not backdate Retail/Institutional proxy features to 2016 without explicit evidence.

The following remain blocked:

1. Per-year, per-underlying, per-contract coverage, including inactive/delisted underlyings and expired option series.
2. Exact 5-minute/30-minute boundaries and interval-only versus cumulative semantics.
3. First-publication and first-receipt timestamps, actual delivery latency and time-zone conventions.
4. Late trades, busts/cancellations, corrections, reprocessing and immutable revision vintages.
5. Historical methodology versioning and whether the 2026 classifier is uniformly backfilled to the 2016 start.
6. Historical availability of lot-size buckets and each participant proxy (2016 versus the 2021 legacy field start).
7. Raw sample, complete field dictionary, exchange-condition-code effective dates and reconciliation keys.
8. Pricing, internal-use licensing and rights for derived data.

The product's security identifiers are cross-referenced to IvyDB US, which is helpful but does not by itself prove TradeFlow's historical inactive/delisted coverage or effective-dated identity availability.

## Complementary Greek/volatility data

OptionMetrics advertises IvyDB US Intraday from January 2018 with option bid/ask, volume, IV, Greeks and volatility surfaces at 10:00, 14:00 and 15:45 ET; permanent IDs and ticker-change history are also advertised. Its 2025 brochure says nightly FTP updates. This could provide delta/IV/skew marks for EOD TradeFlow research, but three snapshots do not supply exact trade-time Greeks for every 5-minute interval. Any delta-equivalent flow must use contemporaneously available or preregistered lagged Greeks; never use a later 15:45 mark for an earlier interval.

Cboe Open-Close remains complementary: it supplies participant-capacity and open/close position-side buckets on Cboe venues, whereas TradeFlow supplies aggressor-side classification across all U.S. options exchanges. Their definitions are not interchangeable.

## Candidate hypotheses — not tested

1. Aggressive Institutional 2 net delta-equivalent demand, kept separate from Institutional 1 and weighted only with time-aligned Greeks.
2. Retail 1, Retail 2 and Retail 3 net flow, analyzed separately before any mutually exclusive aggregate.
3. All signed net flow with unclassified volume retained as a quality/coverage field.
4. Condition-code, NBBO-location and venue concentration/dispersion as execution-mechanism and liquidity controls.
5. Flow × IV/skew interactions to distinguish information from hedging/volatility repricing.

These are hypotheses, not presumed alpha. They must be tested against same-day and prior underlying returns, IV/skew, liquidity, event calendar, DTE/moneyness, option volume and OI to distinguish predictive information from return-chasing or hedging demand.

## Admission protocol

Before feature construction, require a hashed sample spanning 2016, 2020, 2023 and 2026; active and inactive/delisted underlyings; all four tables; per-year/per-name/per-contract coverage; condition-code and lot-size effective dates; exact interval and first-receipt timestamps; correction/revision policy; historical methodology/backfill version; identity continuity; and price/license/derived-rights review.

If those gates pass, preregister interval/EOD semantics, signed premium versus delta-equivalent measures, multi-leg treatment and participant-proxy definitions. Compare incremental information against frozen LTM/F80 using identical exposure and costs, chronological development/validation, block bootstrap, leave-one-out and the locked final holdout. Evaluate multiple holding horizons; do not impose a fixed holding period. Do not unlock or inspect the final holdout during this feasibility phase.

## Decision

**Keep IvyDB TradeFlow as a conditional priority candidate; do not admit features, run returns, purchase data or contact the vendor in this phase.** Its all-exchange 2016+ claim and richer decomposition make it worth pursuing before paying for narrower or less auditable flow products, but the current public documentation is insufficient for PIT research. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; no alpha has been demonstrated.

## Sources

- [IvyDB TradeFlow product page](https://optionmetrics.com/ivydb-tradeflow/)
- [Launch announcement, 2026-09-30](https://optionmetrics.com/news/optionmetrics-launches-ivydb-tradeflow/)
- [IvyDB TradeFlow methodology paper, September 2026](https://optionmetrics.com/wp-content/uploads/2026/09/IvyDB-TradeFlow-A-Framework-for-Options-Volume-Classification-and-Microstructure-Analytics.pdf)
- [TradeFlow brochure, August 2026](https://optionmetrics.com/wp-content/uploads/2026/08/TradeFlow-Brochure-1-1.pdf)
- [Legacy Signed Volume brochure, August 2024](https://optionmetrics.com/wp-content/uploads/2024/08/Signed-Volume-Brochure_v6.pdf)
- [IvyDB US Intraday product page](https://optionmetrics.com/united-states-intraday/)
- [IvyDB US Intraday brochure, July 2025](https://optionmetrics.com/wp-content/uploads/2025/07/OM_IvyDB-US_Intraday_Flyer_WEB.pdf)

**No vendor contact, purchase, raw-data request, feature construction, return test, holdout use or production change was made.**
