# Phase 95 — DOOD dimensional units, source-history bridge, and independent reconstruction audit

**Date:** 2026-11-04 research cycle  
**Branch:** phase95-dood-units-and-independent-reconstruction-audit  
**Status:** source/methodology audit only. No vendor contact, purchase, raw-data acquisition, forward-return test, or alpha claim.

## Executive decision

DOOD remains a high-priority hypothesis, but three distinct questions must not be conflated:

1. Can the 2022 published DOOD calculation be reproduced from the exact historical Signed Volume fields used by the paper?
2. Can the newer TradeFlow fields be reconstructed with historically stable definitions and original point-in-time vintages?
3. Can an independent OPRA trade/quote reconstruction validate the directional-flow construct outside the vendor's own classification process?

The data gate is **not passed**. Phase 94's 12/12 synthetic arithmetic tests validate only the helper implementation.

## 1. Source-paper formula: exact expression and unresolved dimensional convention

The OptionMetrics paper's methodology section says to multiply option delta by net volume, defined as Total Ask Volume minus Total Bid Volume, sum across all option symbols in the underlying chain, and scale by underlying daily stock volume:

DOOD(s,t) = sum_i[Delta(i,t) * (TotalAskVolume(i,t) - TotalBidVolume(i,t))] / UnderlyingDailyShareVolume(s,t)

The paper does not show a contract multiplier in the published equation. The Phase 94 helper correctly keeps this literal formula separate from the multiplier-adjusted sensitivity.

However, the paper does not clearly state in the formula whether its ask/bid volume fields are expressed in contracts, shares, or a vendor-normalized unit. If volume is raw contracts and delta is per underlying share, the numerator is contract-delta units while the denominator is shares. A standard 100-share multiplier would multiply every standard-contract numerator by 100. If the same constant multiplier applies to all option rows and securities, it changes the scale but not cross-sectional ranks or decile membership. If adjusted/nonstandard contracts have different deliverables, a contract-specific multiplier can change relative security rankings.

Required written vendor clarification:
- exact units of Total Ask Volume and Total Bid Volume;
- whether adjusted contracts are represented in raw contracts, deliverable-equivalent units, or normalized volume;
- whether IvyDB delta is per share, per contract, or already adjusted for deliverables;
- how the 2022 paper treated nonstandard/adjusted series;
- whether the underlying stock-volume denominator is split-adjusted consistently with the option volume/delta fields.

Until answered, retain three explicitly different outputs:
- DOOD_PUBLISHED_LITERAL: literal paper formula, no multiplier;
- DOOD_STANDARD_X100: literal formula multiplied by 100 only as a unit-scale diagnostic for standard contracts;
- DOOD_DELIVERABLE_ADJUSTED: contract-specific historical multiplier/deliverable sensitivity, only when OCC history is resolved.

Do not choose the variant by which produces better returns. The literal paper formula remains the only primary replication target until the vendor clarifies field units.

## 2. Source-paper textual inconsistency

The paper consistently defines ask-side trades as buyer-initiated and bid-side trades as seller-initiated, and the displayed expression is Ask minus Bid. This implies positive DOOD for net buyer-initiated positive-delta demand.

One sentence on page 1 describes the operation as “subtracting buy from sell orders,” which reverses the verbal order. The displayed formula and the bullish/high-DOOD narrative support Ask minus Bid. Phase 94 follows the displayed formula. Preserve this textual inconsistency in the replication log; do not silently reverse the sign.

The paper also has an internal Sharpe discrepancy:
- Abstract: 1.08.
- Detailed Table 2 discussion: 1.03.
- Volatility-targeted result: 1.15.

The 1.08 and 1.03 claims must both be recorded until the original calculation/table is reconciled. No single preferred number is selected.

Primary paper: https://optionmetrics.com/wp-content/uploads/2023/05/Demand-for-Option-Order-Delta-DOOD.pdf

## 3. Signed Volume / TradeFlow historical bridge

Public-source evidence reviewed:

- OptionMetrics' current Signed Volume page says daily signed volume is available for every option every day since January 2016, with bid/ask/midpoint and five-/30-minute plus EOD snapshots: https://optionmetrics.com/signed-volume/
- OptionMetrics' current TradeFlow page calls TradeFlow an evolution of Signed Volume and says it covers every US option every day since January 2016. It adds trade-description codes, venue, VWAP-based classification, NBBO aggressiveness and proprietary retail/institutional analytics: https://optionmetrics.com/ivydb-tradeflow/
- The January 30, 2020 Signed Volume launch announcement described daily data on more than 10,000 underlyings **since March 2018**, and described quote-relative Lee–Ready-style buyer/seller classification: https://www.tradersmagazine.com/departments/options/optionmetrics-launches-ivydb-order-flow-tracker/
- OptionMetrics announced five- and 30-minute Signed Volume snapshots on August 7, 2024: https://optionmetrics.com/news/optionmetrics-releases-signed-volume-intraday-with-5-and-30-minute-snapshots-for-assessing-0dte-options-market-maker-inventory-hedging/
- TradeFlow launch publicity is dated September 30, 2026; it describes the product as an evolution with additional trade descriptions, venue, VWAP and participant-proxy analytics.

This is a material history/methodology discrepancy, not a minor marketing detail. The DOOD paper uses January 2016–March 2022, while the 2020 launch announcement describes Signed Volume history beginning March 2018. Current pages say January 2016. Possible explanations include an internal pre-launch history, a later backfill, a changed product definition, or an inaccurate launch-history description. None may be assumed.

The newer TradeFlow fields must not be treated as point-in-time historical labels from 2016 unless the vendor provides:
- field-by-field earliest effective date;
- algorithm/version history and exact change dates;
- backfill/restatement policy;
- historical archived delivery vintages or a correction ledger;
- confirmation that the legacy Ask/Bid/Midpoint fields reproduce the fields used in the 2022 paper.

The proprietary retail/institutional labels are model-derived participant proxies, not verified beneficial-owner identities. Do not apply a current classifier retrospectively without version and vintage evidence.

## 4. Independent OPRA reconstruction: Databento feasibility boundary

Databento's public OPRA documentation states:
- trades and selected OPRA history from 2013-04-01;
- CBBO-1m (one-minute consolidated BBO) from 2013-04-01;
- consolidated event schemas CMBP-1 and TCBBO from 2023-03-28;
- CMBP-1/TCBBO replaced older MBP-1/TBBO schemas in May 2025, with the new consolidated schemas available historically from March 28, 2023.

Sources:
- https://www.databento.tech/blog/opra-improvements-coming-soon
- https://www.databento.tech/blog/opra-migration
- https://www.databento.tech/docs/schemas/mbp-1

Implications:
- A 1-minute NBBO snapshot is not sufficient to reproduce exact trade-time quote-relative signing for every option execution; multiple quote changes may occur within a minute.
- TCBBO's pre-trade consolidated NBBO snapshot is a materially better independent input for a post-2023 reconstruction, subject to trade-condition, correction, sequence and timestamp checks.
- The documented TCBBO/CMBP-1 history begins 2023-03-28, so it cannot by itself independently reconstruct the paper's 2016–2022 period.
- Databento remains a candidate for an independent 2023-2026 OOS signed-flow reconstruction. Ask whether full regional quote-event history before 2023 can be supplied for a true historical NBBO rebuild; do not infer that it is available from the CBBO-1m history statement.

An independent OPRA reconstruction will still be a separate signal definition: quote-relative trade signing with explicit tie/midpoint/complex/auction handling. It is not automatically identical to OptionMetrics' proprietary implementation.

## 5. Preregistered source comparison matrix

| Source/construct | Potential role | Historical limit | Current decision |
|---|---|---|---|
| OptionMetrics legacy Signed Volume | Exact DOOD replication | 2016 vs March 2018 conflict | Highest priority; sample and written history proof required |
| OptionMetrics TradeFlow | Enhanced signed flow and participant proxies | New fields/version backfill unresolved | Separate versioned hypothesis; no retrospective identity assumption |
| Databento OPRA trades + TCBBO | Independent trade-time NBBO signing | TCBBO from 2023-03-28 | Candidate independent OOS check |
| Databento OPRA trades + CBBO-1m | Low-cost historical context / approximate signing | 2013-04-01; minute sampling | Not exact trade-time DOOD replication |
| Cboe Open-Close EOD | Position-side opening/closing and capacity | Four Cboe venues; not full OPRA; EOD delivery next day | Separate complementary construct, never merge with aggressor side |
| Cboe TBT | Rich venue-specific trade/quote/capacity/open-close | C1 from 2019-10-07; expensive | Park pending justified narrow sample |

## 6. Minimum vendor sample acceptance matrix

No purchase is authorized. A no-cost eligible sample or written quote may be considered only after confirming:

1. **History:** sample dates in Jan/Feb 2016, 2017, Mar/Apr 2018, 2019, 2021, 2022, 2023, 2025 and 2026.
2. **Universe:** representative frozen-F80 current names, low-liquidity names, predecessor/delisted securities and historically optionable securities, with identity mapping.
3. **Full chain:** all option symbols, including expired, adjusted and nonstandard contracts; no top-volume truncation.
4. **Field units:** delta, contract volume, multiplier, deliverable, ask/bid/midpoint/unknown and stock-volume units.
5. **Classification:** exact quote matching, trade conditions, complex orders, midpoint/tie logic, auctions, corrections and busted trades.
6. **Versioning:** legacy Signed Volume versus TradeFlow field-by-field history and methodology version dates.
7. **PIT:** exact daily cutoff, file creation/publication/delivery time, original vintage retention, late patches and restatements.
8. **Coverage:** at least 95% of historically optionable eligible issuer-days in each tested period, reported by year, issuer, liquidity and market-cap strata.
9. **License:** internal research, storage, derived-feature and model-output rights.

A modern downloaded historical file with no original-vintage evidence is not automatically point-in-time safe. If the provider cannot supply archived vintages or correction history, mark the historical PIT gate as unresolved and do not run an alpha backtest on it.

## 7. Test sequence after data gates

A. **Literal replication:** 2016–2022, exact published fields/filters, five-session equal-weighted deciles. Preserve the paper's Sharpe discrepancy and report gross results separately from investable results.

B. **Independent OOS reconstruction:** 2023-03-28 onward using Databento TCBBO if trade/quote quality, contract mapping and costs pass. Compare sign agreement, cross-sectional rank correlation and daily coverage against OptionMetrics only if both sources are licensed and aligned.

C. **Incremental F80 test:** only after A/B and PIT gates. Compare baseline and augmented F80/LTM under identical exposure, execution, costs, missing-data rules and universe. Control prior 1/5/20/60-session returns, volatility, liquidity, earnings, IV/skew, option-chain composition and market/sector exposures. Use chronological walk-forward, purging/embargo, block bootstrap, issuer-clustered uncertainty, LOO and multiple-testing correction.

No holding-period limit is imposed. Evaluate decay horizons only within nested chronological validation; do not select a horizon on final OOS.

## 8. Decision and audit boundary

- Phase 94's 12/12 tests passed; this validates arithmetic only.
- DOOD data-feasibility gate remains **NOT PASSED**.
- No vendor has been contacted.
- No data has been purchased or downloaded.
- No forward returns, alpha tests or portfolio changes were made.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

The next useful action is a tightly scoped sample/data-dictionary request (not a purchase) for legacy Signed Volume and TradeFlow history, alongside a Databento OPRA TCBBO sample for post-2023 independent reconstruction. This is a human/vendor-access dependency; continue other repository research while it remains unresolved.
