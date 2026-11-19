# Phase 503 — Cboe Option Sentiment daily order-flow source/PIT feasibility audit

**Date:** 2026-11-19 UTC  
**Branch:** `phase501-cboe-opra-trades-quotes-pit-feasibility` (supplement to PR #157 / Phases 501–502)  
**Baseline main:** `408a8fdfaeac81408760b90b2c0ecff2c34ae7b2`  
**Disposition:** **high-priority conditional daily options-flow candidate; not admitted**. Public documentation describes unusually rich daily directional-flow and volatility aggregates, but current product availability, symbol coverage, license, and historical PIT remain unverified.

## 1. New finding

Cboe's official Option Sentiment specification (v1.4, marked 0525) describes a daily/historical dataset built from trade-level information and proprietary systems intended to identify the initiating side of nearly five million executions per day. It supplies up to 80 underlying-level fields, including directional call/put premium and volume, net option delta, open interest, IV30/IV90, 25-delta 30-day put-call skew, implied borrow, trade-size and days-to-expiration buckets, and OCC clearing participant-volume aggregates.

This may be more directly useful for a daily swing-trading hypothesis than raw interval quotes alone: it packages a broad set of daily option-flow, volatility, and positioning summaries without requiring us to reconstruct every contract. It is also a black-box aggregate. It does not provide the raw prints, contract-level strike/expiry rows, participant-by-side cross-tabs, or exact trade timestamps needed for independent reconstruction.

Official sources:
- Option Sentiment specification v1.4: https://datashop.cboe.com/Documents/Cboe_OptionSentiment_Specs.pdf
- Cboe DataShop FAQ: https://datashop.cboe.com/faqs
- TBT product: https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail
- Open-Close product: https://datashop.cboe.com/cboe-options-open-close-volume-summary

The current FAQ lists Option Sentiment historical availability from January 2012. The dedicated public product URL/active purchase page could not be verified; the guessed `/option-sentiment` route redirects to the DataShop home page. This may be a retired, renamed, or non-indexed product. Do **not** assume it can currently be ordered.

## 2. What the 80-field specification actually provides

The specification is a daily row keyed by `trade_date` and `underlying_symbol`, with aggregate fields such as:

### Activity and normalization
- Total call, put, and option volume; call/put/total trade counts.
- 20-day average call, put, and total volume fields (exact calculation cutoff/inclusion convention is not specified in the public spec).
- Average call/put trade size, underlying volume, call/put premium, spot close, split-adjusted close and spot change.

### Directional flow
- `net_option_delta` for directional trades.
- Call/put premium bought and sold, and calls/puts bought and sold.
- `directional_pct`, the percentage of option volume classed as directional (non-complex, not late).
- Size buckets from 1 contract through more than 1,000 contracts.
- DTE buckets: <=1, 2–5, 6–30, 31–90, 91–180, 181–360 and >360 days.

### Volatility, OI and stock-loan context
- `iv30`, `iv90`, `hv20`, total dollar vega traded.
- Normalized 30-day 25-delta put-call skew.
- Call/put OI and OTM call/put OI.
- Near-term implied borrow cost for options with >7 DTE.

### Participant and venue aggregates
- OCC clearing customer, firm and market-maker volume.
- Exchange-volume fields for Cboe and multiple U.S. options venues.

**Important semantic limits**
- The spec says direction is relative to the option midpoint: a trade above midpoint is a Buy and below midpoint a Sell; spread, late and tied trades are excluded from the directional net-delta calculation. This is a midpoint-based initiating-side proxy, not beneficial-owner intent or proof of informed trading.
- `directional_pct` is expressed as a percentage (e.g. 98.011, not 0.98011).
- Customer/firm/market-maker volumes are OCC clearing participant-category aggregates. The spec does not provide signed buy/sell flow separately for each participant category. Do not infer “firm net buying” or label customer as retail.
- Cancelled trades are stated to be backed out from totals. Preliminary-versus-complete revision behavior still requires verification.
- OI timing/meaning for this specific product should be confirmed. The general Cboe FAQ says options OI uses the previous night's OCC EOD OI at start of day and remains static during the day; do not silently assume every Option Sentiment OI field follows that convention without vendor confirmation.
- The 20-day averages' lookback cutoff is unspecified. Recompute all rolling baselines from prior observations only until the provider confirms exact ex-ante construction.
- The dataset has no trade-level timestamp, OSI, strike, expiry, or per-contract side rows. It cannot independently rebuild a full IV surface or distinguish opening from closing positions.

## 3. Historical coverage and point-in-time availability

### Historical coverage
- Cboe's current FAQ table lists Option Sentiment from January 2012.
- The public specification is v1.4 (0525); its publication is not proof that the product remains actively orderable in November 2026.
- The FAQ's general Option Data scope is U.S.-listed stock, ETF and index options disseminated over OPRA. Product-specific all-symbol coverage, exact date gaps, underlying exclusions, delisted names, and 335-name coverage have not been demonstrated.
- No per-symbol/date availability matrix, sample file, or actual row count was obtained.

### Delivery and PIT
The specification says:
- Historical orders deliver complete files at the end of the day when the order is fulfilled.
- Subscriptions produce a preliminary file after the same day's market close, targeted for 8–9 PM ET, and a complete file the next day by 5–6 AM ET.
- On the first day of a subscription, preliminary and complete files may be generated at approximately the same time with the same content.

Implications:
- Historical archives have no documented original first-delivery/vintage ledger in the reviewed public material. Strict historical PIT is **not certified**.
- A prospective subscription could support a valid daily PIT ledger if every preliminary and complete file is captured with actual first receipt UTC, filename, remote metadata, byte count, SHA-256, parse result, and revision lineage.
- The decision timestamp must be actual receipt, not trade_date, market close, or the nominal 8–9 PM target. Use the first executable underlying session strictly after receipt; never backdate the signal.
- Compare preliminary and complete files for every date. Preserve both vintages; do not overwrite a preliminary file with the complete version or treat the final file as if it had been available earlier.
- If the preliminary file is missed or arrives after the next session opens, use the next executable session after actual receipt.

## 4. Feasibility comparison with other Cboe options sources

| Source | Scope / detail | Advertised history | Main advantage | Main limitation |
|---|---|---|---|---|
| Option Sentiment | Daily underlying aggregates, directional side proxy, IV/skew/OI, participant-volume aggregates | FAQ: Jan 2012 | Feature-rich daily summary for swing horizons | Product orderability, exact coverage, units, PIT and license unverified; no raw contracts |
| Option Trades + Option Quotes | OPRA-wide prints + interval quotes | Product pages: Jan 2012; FAQ: Jan 2010 | Transparent reconstruction from prints/NBBO and separate IV/Greeks/OI | No vendor aggressor label in quote intervals; daily trade delivery; large data and correction/PIT gates |
| Enhanced Options TBT | Trade-by-trade C1 only, side, open/close, capacity, trade type, execution IDs, NBBO/local BBO | 2019-10-07 | Direct participant-capacity and position fields for C1 | One exchange only; T+1; proprietary licensing |
| Open-Close Summary | Cboe BZX/C1/C2/EDGX participant type, buy/sell, open/close; EOD and interval | C1 EOD Jan 2005; other exchanges EOD Jan 2018; intervals vary by venue | Participant and open/close dimensions | Cboe venues only, not OPRA-wide; historical OI/volume convention breaks and recent format changes |

TBT is a useful independent venue-level cross-check, not a market-wide substitute. Open-Close is a complementary participant/position aggregate, not a complete OPRA tape. Option Sentiment's directional classification should be validated against TBT/Open-Close on overlapping C1/Cboe dates before it is treated as reliable.

## 5. Preregistered hypotheses if the product is confirmed and data pass gates

These are hypotheses, not assumptions about “smart money”:

1. **Directional delta pressure:** `net_option_delta` and directional call/put flow predict next-session-to-multiweek returns after controlling for same-day underlying return, momentum, realized volatility, liquidity and event windows.
2. **Directional premium imbalance:** separately test call premium bought-minus-sold and put premium bought-minus-sold; test a combined signed score only after preserving both legs and their gross activity. Normalize by gross directional premium and underlying liquidity.
3. **Flow quality:** test whether `directional_pct` and the share of volume excluded as non-directional/complex/late alter the predictive value. Do not assume high directional share means informed activity.
4. **Participant composition:** test customer, firm and market-maker volume shares as unsigned composition features only. The public schema does not supply participant-by-side net flow.
5. **Volatility/borrow:** test changes in IV30, IV90, normalized 25-delta skew and implied borrow, separately from directional flow and after controlling for realized volatility and same-day price moves.
6. **Positioning:** test OI and OTM OI ratios/concentration only after OI timestamp semantics are confirmed. OI changes are not signed opening/closing flow.
7. **Size/tenor composition:** test size and DTE bucket shifts, normalized by total volume and underlying liquidity; avoid interpreting large contracts as institutional without validation.

Use own prior-only rolling baselines; do not rely on the vendor's 20-day averages until the inclusion cutoff is confirmed. Keep missing/zero values distinct from true zero activity. Avoid duplicate hypotheses and control the multiple-testing burden.

## 6. Validation path

Before any return test:
1. Obtain written confirmation that Option Sentiment remains orderable and get the current specification/version.
2. Obtain firm-use, internal retention, derived-data and redistribution terms, plus price.
3. Confirm exact universe/date coverage for the frozen 335-name panel, including delisted/acquired underlyings and symbol changes.
4. Obtain a lawful sample with old/new dates, liquid/illiquid symbols, missing/zero fields, corrections and preliminary/complete pairs.
5. Confirm units/sign conventions for `net_option_delta`, premiums, vega, implied borrow, skew, OI timing, participant-volume categories and the vendor's 20-day average cutoff.
6. Start a prospective first-receipt ledger for preliminary and complete files; use actual receipt times and immutable vintages.
7. Cross-check directional classification against C1 TBT and Open-Close where definitions and coverage overlap.

Only after these gates pass should features be built. Compare incremental information against frozen LTM/F80 with identical universe, exposure, costs, turnover and execution timing; use chronological discovery/validation/OOS, block bootstrap, LOO and multiple-testing control. Separate contemporaneous return-chasing from forward prediction.

## 7. Disposition

**CONDITIONAL HIGH-PRIORITY DAILY OPTIONS CANDIDATE — NOT ADMITTED.**

The schema is unusually rich for a daily swing strategy and is worth pursuing before committing to large raw OPRA files. However, the current public product page/orderability is unresolved, strict historical PIT is not certified, per-symbol/delisted coverage is unverified, and licensing/price are unknown.

No sample was downloaded, no vendor was contacted, no data was purchased, and no feature/backtest/event study/OOS/bootstrap/LOO was run. No signals were admitted.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen: universe, parameters, exposure, costs, holdout and production unchanged.
