# Phase 169 — Cboe Option Sentiment historical source and PIT feasibility audit

**Audit date:** 2026-11-06  
**Decision:** **CONDITIONAL HIGH-INFORMATION CANDIDATE; CURRENT ORDERABILITY UNCONFIRMED; STRICT PIT NOT APPROVED.**  
**Scope:** Official Cboe specification and FAQ review, field-contract reconstruction, delivery-time reconciliation, and fail-closed feature/knowledge-time rules. No sample download, paid data, account/trial, vendor contact, forward-return test, or production change.

## 1. Why this source merits investigation

Cboe's Option Sentiment specification describes a daily and historical product assembled from trade-level information, with proprietary initiating-side classification of nearly five million executions per day. It exposes daily aggregates for each underlying, including directional premium, net option delta, directional percentage, volatility/skew, implied borrow, open interest, clearing-capacity volumes, size and days-to-expiration buckets, and exchange-level volumes.

The Cboe FAQ currently lists **January 2012** as the historical start date for Option Sentiment. This is materially longer than the one-day public samples previously audited for Open-Close and Volatility Surfaces, and the fields could provide a useful multi-venue directional-flow hypothesis.

Official sources:
- Specification v1.4 (May 2025): https://datashop.cboe.com/Documents/Cboe_OptionSentiment_Specs.pdf
- Cboe FAQ, historical start dates and delivery guidance: https://datashop.cboe.com/faqs
- Current DataShop product listing: https://datashop.cboe.com/data-products
- Legacy product route checked: https://datashop.cboe.com/option-sentiment

## 2. Important availability qualification

The FAQ still lists Option Sentiment with a January 2012 start date, but the former product route /option-sentiment redirected to the DataShop home page during this audit, and the current public Data Products listing did not show Option Sentiment. No public Option Sentiment sample was located.

Therefore:
- The historical start date is an advertised FAQ entry, not proof of complete daily coverage.
- Current orderability, current product support, price, and access to a sample are **unconfirmed**.
- Do not infer that the product is purchasable merely because the PDF and FAQ remain online.
- No account was opened, no cart action was taken, no vendor was contacted, and no purchase was authorized.

This is a discovery candidate, not an admitted data source.

## 3. Reconstructed 80-field contract

The v1.4 specification defines 80 fields. The auditor records the exact field order and types, with 18 named exchange-volume fields.

| Family | Fields | Interpretation |
|---|---|---|
| Total activity | call/put/total volume and trade counts; underlying volume | Daily activity and denominator controls |
| Vendor baselines | avg_call_volume, avg_put_volume, avg_total_volume, avg sizes | 20-session moving averages; window endpoint/inclusion is not specified |
| Directional flow | net_option_delta; call/put premium bought/sold; calls/puts bought/sold; directional_pct | Proprietary midpoint-relative directional classification, not independently verified aggressor side |
| Risk context | iv30, iv90, hv20, norm_25d_skew_30, implied_borrow, vega_total | Volatility, skew, borrow and sensitivity context; not flow identity |
| OI state | oi_calls, oi_puts, otm_call_oi, otm_put_oi | Previous-night OCC OI at the start of the trading day |
| Clearing capacity | cust_volume, firm_volume, mkt_mkr_volume | OCC clearing classifications; not beneficial owners or a complete institutional taxonomy |
| Venue activity | 18 exch_vol_* fields | Exchange-level volume context across the venues named in the specification |
| Composition | size buckets, DTE buckets, ITM/ATM/OTM call/put volumes | Activity composition, not individual trade records |
| Underlying | spot_close, split_adj_close, spot_chg, underlying_symbol, underlying_security_type | Ticker-level underlying context; no permanent security identifier is specified |

The exact schema is encoded in the Phase 169 auditor; tests enforce 80 unique fields, exact header matching, and the documented optional-blank list.

### Interpretation safeguards

- **directional_pct** is reported in percentage points (the specification example is 98.011, not 0.98011). Convert to a fraction only by dividing by 100 after range validation.
- Directional side is relative to the midpoint: above midpoint is treated as a buy and below midpoint as a sell. Spread, late and tied trades are excluded. This is a vendor classification rule, not a verified beneficial-owner or informed-trader label.
- **net_option_delta** is limited to directional trades under that same methodology.
- **call_premium_bought/sold** and **put_premium_bought/sold** can support a preregistered signed premium proxy. Calls bought and puts sold are positive-delta directions; calls sold and puts bought are negative-delta directions. The resulting proxy is still an aggregate flow estimate.
- **oi_calls**, **oi_puts**, and OTM OI are previous-night OCC open interest at the start of the day, static during the session until the next morning update. They are not same-day opening volume, buyer direction, or a closing OI observation.
- **cust_volume**, **firm_volume**, and **mkt_mkr_volume** are OCC clearing-capacity categories. They do not identify the beneficial owner, and the specification does not provide a distinct professional-customer category.
- The 20-session moving-average endpoint is not documented. Recompute all rolling baselines using prior sessions only; do not use the vendor average as an ex-ante denominator until its window convention is verified.
- **split_adj_close** may incorporate later corporate-action adjustments. Do not use it as a historical point-in-time price without adjustment vintages; prefer an as-traded close joined to an effective-dated security master.
- The output is daily underlying-level aggregation, not contract-level flow. It cannot reconstruct option series, strikes, expirations, or complex-order legs.

## 4. Delivery and knowledge-time conflict

The product specification says:
- Subscription preliminary file: after the market close on trade date, with a target arrival around 8–9 PM ET.
- Subscription complete file: by approximately 5–6 AM ET the next morning.
- Historical orders: complete files delivered at end of day, without a precise historical receipt timestamp in the specification.

The general DataShop FAQ says daily files are typically uploaded the following day between 00:05 and 03:00 ET, but may be delayed until after the market opens.

These statements are not a reliable historical first-publication ledger. A scheduled delivery time is not an observed receipt time. Preliminary and complete files may differ; the specification says the first subscription day can produce preliminary and complete files with identical content, but that does not establish all later-day revision behavior or historical vintages.

**PIT rule:** use an immutable first-received file, SHA-256, actual timezone-aware first_received_at, source filename, version, and any later complete/revision file as a separate vintage. The feature cannot be used before actual receipt. The Phase 169 helper also rejects same-trade-date decisions and requires the decision timestamp to follow first receipt. It does not yet implement an exchange calendar; next-tradable-session mapping remains a separate gate.

Without actual receipt logs, a historical backfill remains descriptive/conditional, not strict PIT. A conservative next-session delay sensitivity would not transform it into PIT-proven data.

## 5. Small preregistered candidate family — not yet computed

Only after access, history, identity and first-receipt gates pass, consider:

1. Signed directional premium: (call_premium_bought - call_premium_sold) - (put_premium_bought - put_premium_sold).
2. Vendor net option delta, with its documented midpoint-relative exclusions.
3. Directional activity share, converting percentage points to a 0–1 fraction.
4. Volatility context: IV30/IV90 term structure, 25-delta skew, HV20 and implied borrow.
5. Beginning-of-day OI state and changes only with the correct one-session knowledge lag.
6. Clearing-capacity mix as a descriptive customer/firm/market-maker control, never as a Smart Money identity label.

Recompute rolling baselines using only prior sessions. Freeze definitions before any forward-return analysis. Do not tune thresholds on the final holdout.

## 6. Universe, survivorship and economic gates

The FAQ's January 2012 start does not establish complete daily files for every trading date, historical underlying coverage, inactive/delisted retention, permanent security IDs, coverage of all U.S. options venues, or historical first-receipt vintages.

The underlying ticker must be mapped through an effective-dated security master, including ticker changes, mergers, splits, ADRs, ETF changes and delistings. Unresolved identities stay quarantined.

Before alpha testing, require a licensed sample or authorized access, a multi-date/multi-regime history probe, a coverage matrix against the broad PIT stock universe, a receipt/vintage ledger, and reconciliation of core activity fields. Compare any candidate against frozen LTM/F80 and momentum controls using identical exposure, costs, chronological OOS, bootstrap and LOO. Control explicitly for recent underlying returns, option volume, volatility, liquidity and scheduled events to distinguish prediction from return-chasing.

## 7. Decision and next step

**Retain as a conditional high-information candidate; do not promote to feature or alpha testing.** The breadth of directional, volatility, OI and venue fields is attractive, but current orderability, sample access, historical completeness, first receipt and underlying identity remain unresolved.

If an authorized sample becomes available, the next phase should first validate actual 80-field headers and optional blanks, row uniqueness/date coverage, volume/count reconciliations, percentage scaling, preliminary/complete differences, missing/delisted coverage and actual receipt/vintage metadata.

No forward returns, bootstrap/LOO, OOS or final-holdout test was run. No data were purchased, no vendor was contacted, and no production or F80 setting changed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
