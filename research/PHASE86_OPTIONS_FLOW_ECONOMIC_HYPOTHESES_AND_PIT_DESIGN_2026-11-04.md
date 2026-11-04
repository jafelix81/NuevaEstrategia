# Phase 86 — Options-flow economic hypotheses, taxonomy and PIT design

**Date:** 2026-11-04  
**Branch:** phase85-cboe-options-flow-source-feasibility  
**Status:** research-design addendum only. No vendor data purchase, no forward-return test, no alpha claim.

## Executive decision

Retain two distinct options-flow candidates, but do not collapse them into one generic "smart money" measure:

1. **Cboe Open-Close EOD** measures exchange-specific position-side activity by capacity and open/close status. It is the better source for *capacity and whether exposure is being opened or closed* on four Cboe venues.
2. **OptionMetrics IvyDB Signed Volume** measures inferred buyer- versus seller-initiated trade direction from trade price relative to bid/ask. It is the broader historical signed-flow candidate, but does not itself provide Cboe-style open/close or participant-capacity identity.

The sources measure different things. Agreement between them may be informative; disagreement is also a testable result. Neither is presumed to identify informed investors.

## 1. Verified Cboe EOD data semantics

Primary sources:
- [Cboe Open-Close DataShop product page](https://datashop.cboe.com/cboe-options-open-close-volume-summary)
- [Cboe Open-Close EOD file specification v1.3](https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf)
- [Cboe Open-Close factsheet](https://datashop.cboe.com/documents/Cboe_Open-Close_Factsheet.pdf)

### Coverage and file timing

- Exchanges: C1, C2, BZX and EDGX. This is four Cboe venues, **not full OPRA market-wide participant flow**.
- EOD history: C1 from 2005-01-03; BZX/C2/EDGX from 2018-01-02. Thus 2016–2017 can only be C1 for this product; a consistent four-venue panel begins in 2018.
- Historical EOD: one zipped CSV per trade date and exchange.
- Subscription: a preliminary and a final file are typically delivered around 00:30–01:00 U.S. Eastern the next morning.
- The preliminary file sources total-industry-volume and open-interest fields from OPRA; the final file sources authoritative values from OCC and may update them. Use the **final** file for a canonical daily panel and retain file/version/retrieval timestamps.
- Conservative KnowledgeDate is the next trading session. For the existing end-of-day execution convention, the first comparable execution is the close of that next session. Do not use the signal-date close.

The factsheet's "approximately 98%" statement is not evidence of 98% of all U.S. OPRA volume. Do not use it as a market-wide coverage claim.

### Capacity taxonomy — not beneficial-owner identity

The EOD specification maps trade origin/capacity codes as follows:

| Cboe bucket | Origin codes | Interpretation limit |
|---|---|---|
| Firm | F, L, J | Proprietary firm / affiliate / joint-back-office capacity; not a named institution |
| Broker-Dealer | B | Broker/dealer capacity; not necessarily proprietary or directional information |
| Market Maker | M, N | Liquidity-provider capacity; inventory and hedging effects may dominate |
| Customer | C | Public customer; factsheet says this includes both retail and institutional clients |
| Pro-Customer | U, W | Professional customer capacity; factsheet describes professional traders and institutional participants |

Customer and Pro-Customer are further split by **per-trade** contract-size buckets (<100, 100–199, >=200). These are not account-level AUM or beneficial-owner classifications. A large trade is not automatically institutional, and Customer is not synonymous with retail.

The data's buy/sell and open/close dimensions are position-side classifications:
- Opening Buy initiates/increases a long option position.
- Opening Sell initiates/increases a short option position.
- Closing Buy reduces/eliminates a short option position.
- Closing Sell reduces/eliminates a long option position.

Do not relabel Cboe buy/sell as buyer-/seller-aggressor flow. That is a different concept from OptionMetrics' quote-relative signed-volume classification.

### Schema and historical convention breaks

- security_type: 1=Equity, 2=ETF, 3=Index, 4=WCO. Keep instrument types separate.
- series_type: S=standard; N=nonstandard. From 2024-10-16, F is added for FLEX. Earlier N values include nonstandard roots; retain the raw root and series type.
- Adjusted/nonstandard contracts require historical OCC multiplier and deliverable resolution. Never assume a 100-share multiplier. Exclude unresolved adjusted contracts from delta-equivalent features.
- C1 OI fields were shifted one day ahead through 2019-10-04; C2 through 2018-05-11. BZX/EDGX use consistent start-of-day convention.
- C2 total-industry-volume values were doubled through 2018-05-11.
- C1 total-exchange-volume convention changed through 2019-10-04 from (buy + sell)/2 to buy + sell.
- Previous-close conventions also differ historically for C1 and C2 through those dates.
- Total industry volume and OI are value-add fields with third-party/OCC provenance, not raw Cboe execution measures. Preserve raw and normalized values separately; do not use uncorrected historical denominators.

The 2026-11-08 announced schema changes apply to intraday 1-minute/10-minute files, not the EOD file used as the first candidate. If intraday files are ever added, version the schema and normalize pre/post-change records explicitly.

## 2. OptionMetrics Signed Volume semantics

Primary sources:
- [IvyDB Signed Volume](https://optionmetrics.com/signed-volume/)
- [Signed Volume brochure](https://optionmetrics.com/wp-content/uploads/2024/08/Signed-Volume-Brochure_v6.pdf)

Public materials state:
- Daily option signed volume for every option since January 2016.
- Trades are classified as buyer-initiated or seller-initiated using trade price relative to the contemporaneous bid/ask quote; bid, ask and midpoint are tracked.
- 5-minute and 30-minute snapshots are available in addition to EOD.
- Symbols/security IDs link to IvyDB US.
- Volume lot-size fields begin in 2021 and are described as useful for retail/institutional-flow analysis.

Limitations still open:
- Exact trade/quote matching, midpoint/ambiguous handling, complex-order and trade-condition rules.
- Whether classification methodology and historical corrections are stable back to 2016.
- Historical inactive/delisted underlying and expired-contract retention.
- Exact snapshot cutoffs, file publication times, restatements and correction policy.
- Meaning and historical consistency of the lot-size fields. They are not verified beneficial-owner labels and do not exist in the same form before 2021.
- Pricing, business-use license and derived-data rights.

Until publication timing is documented, use next-session KnowledgeDate and next-session-close execution.

## 3. What the literature suggests — and what it does not

These papers motivate specific, competing hypotheses; their historical results do not establish current F80 incremental value.

- **Pan & Poteshman (2006), [The Information in Option Volume for Future Stock Prices](https://doi.org/10.1093/rfs/hhj024):** buyer-initiated opening put/call volume ratios predicted stock returns in their historical sample; low put/call ratios outperformed high ratios by more than 40 bp next day and more than 1% over the next week. This motivates opening-position decomposition, not a blanket "call buying = smart money" rule.
- **Ge, Lin & Pearson (2016), [Why Does the Option-to-Stock Volume Ratio Predict Stock Returns?](https://doi.org/10.1016/j.jfineco.2015.08.019):** call purchases that open new positions were the strongest predictor in their study, followed by call sales that close existing purchased-call positions. Their interpretation emphasizes embedded leverage; predictive flow need not uniquely imply private information.
- **Han & Kim (2017), [Informed Trading in the Options Market and Stock Return Predictability](https://doi.org/10.1002/fut.21837):** the negative relation between options volume and future stock returns was concentrated in stocks with steep volatility smirks. This motivates a preregistered skew interaction, not post-hoc sign selection.
- **Muravyev (2016), [Order Flow and Expected Option Returns](https://doi.org/10.1111/jofi.12380):** market-maker inventory risk had a first-order impact on option prices and was larger than the asymmetric-information component in the studied decomposition. This is a direct warning that order flow and price impact can reflect inventory/hedging rather than informed trading.
- **Bernile, Gao & Hu (2019), [Center of Volume Mass: Does Options Trading Predict Stock Returns?](https://ink.library.smu.edu.sg/lkcsb_research/6568/):** the volume-weighted strike/spot distribution (VWKS) was reported to predict underlying returns and anticipate fundamental information. Treat this as a separate, secondary hypothesis requiring strike-level coverage and independent replication.

## 4. Preregistered candidate features — not yet authorized for return testing

Keep source constructs separate:

### A. Cboe position-side flow

For issuer/security s and information date t, construct separately by capacity, call/put, DTE and moneyness:

**NetOpenContracts = OpenBuyVolume - OpenSellVolume**

Then, only after historical OCC multiplier/deliverable and a timestamped Greek mark are validated:

**NetOpenDeltaShares = sum(delta_15:45 × multiplier × NetOpenContracts)**

Label this **15:45-marked delta-equivalent opening flow**, not exact trade-time delta. Keep unweighted contracts as a separate primary diagnostic. Closing flow remains separate; do not net opening and closing before the component tests.

Candidate normalizations are separately named:
- raw contracts;
- prior-available OI;
- full-OPRA option volume;
- underlying prior-20-session dollar ADV.

Do not use same-day OI or an unverified total-industry-volume denominator.

### B. OptionMetrics signed flow

First reproduce the vendor's documented DOOD definition from its data dictionary and source paper, preserving unknown/midpoint trades separately:

**SignedDeltaDemand = sum(delta × multiplier × (ask_initiated_volume - bid_initiated_volume))**

The exact denominator and trade filters must match the preregistered replication before any alternative is tested. Lot-size buckets are a separate sensitivity from 2021 onward, not a backfilled historical identity label.

### C. Cross-source hypotheses

1. Opening call demand versus opening put demand, with closing flow separate.
2. Cboe capacity heterogeneity: Firm, Pro-Customer, Customer, Broker-Dealer and Market Maker tested separately.
3. Signed aggressor flow from OptionMetrics versus Cboe position-side flow.
4. Skew/IV interaction and VWKS as separately preregistered secondary hypotheses.
5. Cross-source agreement/disagreement as a diagnostic, not an ex-post filter.

No category is labelled "smart money" in advance.

## 5. Competing explanations and required controls

- **Information hypothesis:** flow predicts future underlying returns after prior-return, volatility, liquidity, event and market/sector controls.
- **Return-chasing hypothesis:** flow follows recent stock/option price moves; predictive value weakens after 1/5/20/60-session returns and same-day trend are controlled.
- **Dealer inventory/hedging hypothesis:** market-maker flow and price impact reflect inventory adjustment or delta/gamma hedging rather than private information.
- **Leverage hypothesis:** call-opening demand predicts returns because options embed leverage, without identifying a privileged participant.
- **Volatility hypothesis:** flow predicts IV/skew or realized volatility more consistently than return direction.

Controls include prior returns (1/5/20/60), realized volatility, IV level/skew/term, option liquidity, prior OI, moneyness, DTE, 0DTE share, earnings/event windows, market/sector exposure, market cap and underlying ADV. Report contemporaneous and lagged flow separately.

## 6. Data gates before any economic test

1. Obtain a representative Cboe EOD sample for all four exchanges, including a full (not 20%) date and dates spanning 2018, 2019, 2021, 2023, 2025 and 2026. Report per-exchange, per-date and per-underlying availability.
2. Reconcile Cboe EOD to full-OPRA Option EOD for the same symbols/dates. The existing four-underlying Option EOD sample does not establish 335-name coverage.
3. Resolve historical OCC series roots, multiplier, deliverables, adjustments, expiration and underlying mapping; no fuzzy joins.
4. Obtain an OptionMetrics sample with the full dictionary, methodology versions, inactive/delisted retention, lot-size definition, snapshot cutoffs, corrections and exact delivery timestamps.
5. Confirm data license, internal use, storage/retention and derived-data permissions before acquisition.
6. Reconstruct the point-in-time optionable security universe. Do not use the current 335-name list as a survivorship-free historical universe; Phase 70 remains a hard blocker.
7. Require at least 95% of historically optionable F80 issuer-days in each tested period, with per-year/per-name missingness and optionability denominators. A pooled average cannot hide a weak year or issuer.
8. Preserve raw files, hashes, vendor/schema versions, delivery/retrieval timestamps and KnowledgeDate. Use the final Cboe EOD file, not preliminary, for the canonical panel.

## 7. Economic validation if and only if the data gates pass

- Follow Phase 60's chronological framework: development 2016–2019, validation 2020–2022, locked OOS 2023–2026 (last fully available date). Cboe four-venue tests begin in 2018; disclose the shorter four-venue history and do not backfill absent venues.
- Execute both frozen baseline and augmented model at the same next-session close after overnight data availability. Identical exposure, costs, turnover and missing-data treatment.
- First reproduce the vendor/literature definition exactly. Any alternative is a separately registered test.
- Evaluate horizons 1, 2, 5, 10, 20 and 40 sessions and event-time exits only inside nested chronological validation; there is no fixed holding-period assumption.
- Test incremental value versus frozen LTM/F80, not just standalone equal-weight decile spreads.
- Use issuer-clustered/block-bootstrap uncertainty, leave-one-issuer-out, regime tests, realistic costs, liquidity/optionability controls and multiple-testing correction.
- Kill if signal is contemporaneous/return-chasing, depends on one issuer/regime, loses significance after controls, or adds no robust OOS portfolio value.

## Decision

Cboe Open-Close EOD remains the first practical capacity/open-close candidate; OptionMetrics Signed Volume remains the first broad aggressor-flow candidate. The Cboe one-date 20% C1 sample (288/335 current tickers) is a schema/reach diagnostic only. Neither source has passed full historical PIT coverage, licensing and optionable-universe gates. No vendor was contacted, no data were purchased, no forward returns were calculated and no production changes were made.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
