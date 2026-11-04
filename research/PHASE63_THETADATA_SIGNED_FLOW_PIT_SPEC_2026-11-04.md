# Phase 63 — Signed OPRA flow: PIT construction and classification specification
**Status:** Preregistration for data validation only. No returns or strategy parameters were inspected.

## Objective

Reconstruct a transparent, reproducible buyer-/seller-initiated options-flow measure from trade-level OPRA records paired with contemporaneous NBBO. Test whether it contains incremental information about the underlying's future returns after controlling for price momentum and other known drivers. Treat informed trading, dealer hedging, volatility demand and momentum chasing as competing hypotheses.

## Required raw fields

- Contract identity: underlying/root, expiration, strike, right, and PIT OCC series/reference key.
- Trade: timestamp, sequence, exchange, condition, size, price.
- NBBO: quote timestamp, bid/ask, bid/ask sizes, exchanges and quote conditions.
- Greeks: trade-time Delta, IV and underlying timestamp/price, or sufficient raw inputs to reproduce them.
- PIT multiplier/deliverable and corporate-action lineage.
- OI: timestamp and prior-session reference date.
- Vendor delivery/publication time or conservative next-session KnowledgeDate.

## Primary quote-match rule

Use the vendor's historical trade/quote join with strict prior-quote semantics (`exclusive=true`), requiring:

1. quote_timestamp < trade_timestamp;
2. bid > 0 and ask > bid;
3. positive bid/ask sizes;
4. firm quote condition; primary eligible codes to be confirmed against date-specific OPRA condition mappings;
5. no locked, crossed, halted or non-firm quote;
6. quote age no greater than 1,000 milliseconds.

Freeze a sensitivity grid before any return analysis: maximum quote age 250 ms, 500 ms, 1,000 ms and 2,000 ms. Report eligible volume and rejected volume at each threshold.

## Aggressor-side classification

For eligible outright trades:

- BUY: trade price >= ask.
- SELL: trade price <= bid.
- UNKNOWN: trade strictly inside the spread, including midpoint.
- INVALID: outside the valid NBBO, missing/stale quote, invalid condition, or unresolved correction.

Do not force midpoint/inside-spread trades into a side in the primary measure. A tick-rule or midpoint-sign sensitivity may be evaluated separately and must not replace the primary classifier.

## Trade-condition cohorts

Preserve raw condition codes and date-aware code descriptions. Do not infer participant identity from conditions.

- Primary outright cohort: regular and electronically executed trades only after sample validation.
- Complex cohort: spread, straddle, buy-write and combo conditions.
- Contingent/cross cohort: contingent orders, internal crosses and other linked executions.
- Late/out-of-sequence cohort: keep separate; exclude from primary directional flow unless timestamp/correction lineage is verified.
- Cancellation/correction cohort: reverse the original record only when the vendor supplies deterministic linkage (e.g., records_back or equivalent); otherwise block the affected trade-day from the primary signal or mark it incomplete.

The exact eligible code set is not frozen until a real option sample and date-specific condition-code version are inspected. The categories above are the initial taxonomy, not an assertion that every code is valid or stable across the full history.

## Trade-time Delta and contract adjustment

Primary Delta must be aligned to the option trade timestamp and a contemporaneous underlying observation no later than that trade. If vendor trade-Greeks are used:
- preserve underlying_timestamp and require underlying_timestamp <= trade_timestamp;
- explicitly set PIT rate and dividend inputs where available;
- compare Black-Scholes with binomial Delta for American-style contracts;
- retain IV error and exclude unstable solutions under a predeclared quality rule.

Join the option series to a point-in-time OCC contract reference. Apply the actual multiplier and deliverable for that series/date. If the multiplier or deliverable is unresolved, exclude the series from delta-equivalent flow and report its share of raw volume. Do not use a blanket multiplier of 100.

## Daily features

For each underlying/date, calculate separately:

- outright buyer-initiated and seller-initiated contract volume;
- signed premium flow;
- signed delta-equivalent flow;
- call and put components;
- DTE buckets and absolute-Delta buckets;
- complex/contingent/cross flow;
- unknown and invalid flow shares;
- eligible-trade and quote-quality coverage;
- prior-night OI by contract and underlying.

Primary feature:

[
SDD_{i,t}=\sum_j s_j\,size_j\,multiplier_{j,t}\,delta_{j,t}
]

where (s_j=+1) for BUY, (-1) for SELL and unknown trades are excluded from the signed numerator. Publish the numerator and eligible/unknown volume separately.

Primary normalization: divide by lagged 20-session median underlying share ADV (or a predeclared dollar-ADV alternative). Do not use same-day underlying volume as the primary denominator. OI-normalized variants are secondary and must use OI that was available before the relevant trade/session.

## PIT availability

- Trade/quote event timestamps are intraday, but the vendor's historical correction and publication schedule is not yet verified.
- Use the next trading session as KnowledgeDate until actual daily availability is documented.
- For the end-of-day strategy, execute at the next trading session close for both F80 and the augmented model.
- OPRA OI is normally disseminated around 06:30 ET and refers to the previous trading day's close. Preserve both report timestamp and economic reference date. A missing OI message is not automatically zero until retrieval completeness and zero-message semantics are verified.
- No current ticker/option symbol list may be used as a historical universe.

## Competing hypotheses

H1 — information: clean buyer-initiated signed delta demand predicts future underlying returns after controlling for past returns, volatility, liquidity, earnings and market/sector exposure.

H2 — dealer hedging: signed flow predicts contemporaneous or short-horizon continuation but loses power after controlling for prior intraday/daily price moves or dealer-hedging proxies.

H3 — return chasing: flow follows recent returns and has no incremental predictive value after momentum controls.

H4 — volatility/convexity demand: options flow predicts future IV/skew changes but not necessarily underlying direction.

H5 — complex-flow effect: complex/contingent/cross transactions contain different or more informative exposure than outright trades; they must be tested separately, not silently discarded.

## Data acceptance gates

No forward-return computation until all are met:
1. written license appropriate to intended use;
2. real historical options sample across liquid, illiquid, adjusted and delisted underlyings;
3. reproducible coverage by date for historical F80 membership;
4. cancellation/revision semantics verified;
5. PIT quote, trade, underlying, rate, dividend and OI timestamps validated;
6. PIT contract multipliers/deliverables resolved;
7. quote-quality and unclassified-volume coverage measured.

## Economic validation after data gate

Use the frozen DOOD/SDD research split unless the data-availability boundary requires a documented change:
- development: 2016–2019;
- validation: 2020–2022;
- untouched OOS: 2023–2026.

First reproduce the published/vendor-style DOOD benchmark without tuning. Then test the stricter raw-NBBO classifier. Control for prior 1/5/20/60-session returns, realized volatility, liquidity, earnings and market/sector effects. Test multiple horizons only under a preregistered family-wise correction or nested chronological selection. Compare against frozen LTM/F80 using identical universe, exposure, execution timestamp and costs. Use block bootstrap, issuer-clustered inference and leave-one-issuer-out. Kill the hypothesis if incremental OOS value is not robust or disappears after momentum controls.

No alpha promotion is authorized by this specification.
