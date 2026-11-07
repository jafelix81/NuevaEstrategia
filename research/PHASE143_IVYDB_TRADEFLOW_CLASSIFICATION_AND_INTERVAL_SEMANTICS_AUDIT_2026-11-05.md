# Phase 143 — IvyDB TradeFlow classification and interval-semantics audit

**Date:** 2026-11-05  
**Branch:** `phase99-broad-pit-universe-charter`  
**Input:** Phase 142 TradeFlow feasibility/PIT audit; current OptionMetrics product documentation, methodology paper and 2026-09-28 retail-identification note.  
**Mode:** public-documentation audit only. No raw vendor data, account, trial, vendor contact, purchase, terms acceptance, forward-return test or production change.

## Decision

**Retain IvyDB TradeFlow as the leading conditional all-venue options-flow candidate, but narrow the interpretation of its participant fields and add hard interval/complex-order gates before any signal work.**

The new public methodology materially improves our understanding of the data structure, but it also reveals three risks that would make a naive “institutional flow” feature misleading:

1. Institutional 2 is an aggressive liquidity-demand subset, not total institutional activity.
2. Multi-leg option executions are signed leg by leg; they are not parent-strategy direction.
3. Retail classification is definition-sensitive, especially for 0DTE, and cannot be treated as investor identity.

The 5-minute/30-minute records appear to be aggregates for reporting intervals, but the public brochure calls them “snapshots” and does not define interval boundaries or delivery/knowledge timestamps. Do not apply the Cboe cumulative-snapshot differencing method to TradeFlow without a raw sample and reconciliation.

## 1. What the official methodology establishes

The OptionMetrics methodology paper dated 2026-09-28 describes TradeFlow as four relational tables keyed by option symbol, SecurityID and date:

- `Signed_Volume`: buyer-initiated, seller-initiated and unclassified volume by option series and reporting interval.
- `Trade_Conditions`: trade counts split by exchange condition and lot-size bucket.
- `Market_Structure`: volume by execution price location relative to NBBO.
- `Signed_Exchange`: signed volume by venue.

The paper says each `Signed_Volume` record aggregates all trades in one option series over a reporting interval, and directional plus unclassified volume reconciles to total traded volume. Venue rows also reconcile to the symbol-level total.

The sequential signing method is described as:
1. classify trades with characteristics of execution against a previously posted passive order;
2. classify small price improvements through exchange auction mechanisms;
3. compare remaining trades with the prevailing quote (near offer = buyer-initiated; near bid = seller-initiated);
4. resolve midpoint trades using supplementary market information said to be available at trade time;
5. classify remaining trades by price direction relative to the prior trade.

This is more informative than naive bid/ask signing, but the paper does not publish enough implementation detail to independently reproduce the full classifier. In particular, the exact quote synchronization, event sequencing, correction/bust treatment, tie handling and fallback eligibility need a raw sample and field-level specification.

The vendor's 99.9% midpoint-direction assignment is **classification coverage, not independently measured accuracy**. The supporting illustration is one SPY session, 2026-06-17, on an FOMC day. It is not a broad-market accuracy study.

## 2. Interval accounting: promising but not yet proven

The public paper says records aggregate trades “over a reporting interval”; the product page and brochure describe 5-minute and 30-minute “snapshots”. These descriptions are consistent with interval totals, but do not establish whether the delivered files contain:
- disjoint interval increments;
- cumulative-to-date snapshots;
- revised interval aggregates after late reports/corrections; or
- end-of-interval values published after a vendor processing delay.

**Required sample test before use:** for identical option series/date, sum all 5-minute rows and reconcile to the EOD `TradeVolume`; repeat for 30-minute rows; test missing intervals, overlapping boundaries, late corrections and duplicate keys. If interval rows are cumulative, do not sum them. Preserve each raw received file, hash, schema/version and receipt timestamp.

Until this passes, no intraday flow feature is approved. The EOD table can be assessed separately once its actual first availability and revision history are known.

## 3. Critical table semantics and double-counting controls

### Market Structure is not a flat partition

The paper explicitly states that midpoint volume is a subset of inside-NBBO volume. The additive identity is:

`TradeVolume = AtNBBO + InsideNBBO + OutsideNBBO`

Do **not** add Midpoint again. Midpoint is a diagnostic subset of InsideNBBO. A naive four-category sum would double-count midpoint volume.

### Multi-leg prints are signed per leg

Trade condition codes include single-leg auctions, multi-leg auctions, automatic executions, multi-leg electronic trades, ISOs and other conditions. The paper says each leg of a multi-leg execution is signed individually. Multi-leg prints were 8.2% of SPY option trades in the 2026-06-17 illustration.

This is contract-leg flow, not parent-order or package direction. A vertical spread or iron condor can contain legs with opposing delta and different risk exposures. If parent complex-order identifiers and package reconstruction are unavailable, do not describe summed multi-leg leg volume as net directional conviction.

For any later study, keep single-leg and multi-leg activity separate first. Only combine them after a pre-registered, economically coherent package-level reconstruction or after showing the result is robust to excluding multi-leg executions.

### Venue and condition tables

The paper's 18-venue SPY illustration and exact table reconciliation are useful schema checks, not proof of full historical venue coverage. Verify actual venue IDs and missingness across the whole sample. Condition-code meanings and mappings must be versioned; a code's meaning or prevalence can change with exchange rules.

## 4. Participant labels: use mechanism names, not investor identities

The paper's five proprietary buckets are based on condition, size, quote location and notional—not account or beneficial-owner identity.

| Field | Vendor rule | Research interpretation |
|---|---|---|
| Retail 1 | SLAN, fewer than 10 contracts | Strict single-leg auction proxy |
| Retail 2 | AUTO, fewer than 10 contracts, at bid/offer | Small marketable execution proxy |
| Retail 3 | AUTO, fewer than 10 contracts and under $5,000 notional | Small price-improved execution proxy |
| Institutional 1 | ISO at/through prevailing quote | Aggressive ISO execution proxy |
| Institutional 2 | Institutional 1 plus AUTO above 10 contracts and above $5,000 notional | Aggressive large-liquidity-demand proxy |

Retail 1/2/3 are described as mutually exclusive. Institutional 1 is contained in Institutional 2; **never add Institutional 1 to Institutional 2**. Institutional 2 excludes passive execution, midpoint prints, patient position-building and market-making. It therefore cannot represent total institutional participation or “smart money” inventory.

A separate OptionMetrics note on 2026-09-28 makes the definition risk concrete for 0DTE:
- its narrow SPX/SPY retail proxy includes SLAN/MLAT 1–10 lots and AUTO/MLET size 1;
- its broad proxy extends SLAN/MLAT to 1–50 lots while retaining one-lot AUTO/MLET;
- the note says retail 0DTE activity can include 11–50 contract clips and complex multi-leg strategies;
- for SPX 0DTE, its OPRA-condition-code method estimates 30–35% retail, versus a Cboe broker/account-identity estimate of 50–60%.

Those are different definitions, not a verdict that either estimate is ground truth. The gap demonstrates that participant shares are highly sensitive to the classification target. A fixed 1–10 lot rule cannot be assumed to transfer from longer-dated single-stock options to 0DTE index options.

**Feature naming rule:** use explicit names such as `SLAN_SMALL_AUCTION_FLOW`, `AUTO_SMALL_AT_QUOTE_FLOW`, `ISO_LARGE_AGGRESSOR_FLOW` and `LARGE_AUTO_AGGRESSOR_FLOW`. Do not name them “hedge-fund buying”, “institutional accumulation” or “smart money”.

## 5. Product lineage and strict PIT

Public vendor chronology now establishes:
- **2021-03-07:** Signed Volume 2.0 announced with retail tracking and expanded signed-direction detail.
- **2024-08-07:** Signed Volume 5-minute and 30-minute intraday snapshots announced.
- **2026-09-28:** TradeFlow methodology paper published.
- **2026-09-30:** IvyDB TradeFlow launched as the evolved all-exchange product.

The current product advertises history from January 2016. That backfill does not establish that the current classifier, current participant buckets, all four tables or intraday intervals were available at those historical dates.

PIT rules:
1. Treat the current TradeFlow methodology as a new data-generation regime no earlier than its verified first delivery; do not backdate it to 2016.
2. Keep 2016 EOD Signed Volume, the 2021 Signed Volume 2.0 generation, 2024 intraday extension and 2026 TradeFlow generation as separate regimes until a field-by-field overlap/reprocessing audit proves comparability.
3. A public announcement date is not a historical first-delivery timestamp. Strict PIT needs actual delivery/receipt logs, schema versions, correction vintages and the exact time each interval became usable.
4. If those records are unavailable, use historical backfill only for exploratory/descriptive analysis and reserve strict executable OOS for a verified prospective capture window.
5. Set feature knowledge time no earlier than interval completion plus verified first availability. A 5-minute bar ending at 10:05 cannot be traded at 10:05 unless its actual publication time supports that.

No historical release/vintage log or public raw sample was located. This remains a hard gate.

## 6. Candidate feature family — preregistration only, no alpha test

If the data gates pass, test a small set of non-overlapping hypotheses:

1. **All-flow imbalance:** buyer-initiated minus seller-initiated volume, scaled by total option volume and separately by lagged open interest.
2. **Mechanism-specific flow:** strict SLAN auction proxy; broader auction proxy including MLAT; small AUTO/MLET; large ISO/AUTO aggressor flow. Do not collapse into literal retail/institutional labels.
3. **Complex-order sensitivity:** single-leg only as primary; multi-leg separately; combined result only after package-level economic interpretation.
4. **Venue concentration/migration:** share and concentration of signed flow across venues, normalized by total market volume. Treat fee/routing changes as confounders.
5. **Option-risk weighting:** calls and puts separately first. Delta-weighted flow requires a contemporaneous IvyDB US Greek and deliverable mapping no later than the flow interval. A buyer-initiated put is not automatically bearish information; it can be insurance or a spread leg.
6. **OI/IV/skew interactions:** only after first-received OI/IV/Greek vintages and security/contract identity pass.

For every feature, test whether it predicts *future* underlying returns after the interval's verified knowledge time. Control for prior and contemporaneous underlying return, realized volatility, liquidity, market/sector exposure, earnings and major scheduled news. This separates information from options flow that merely chases an underlying move or hedges an existing exposure.

The economic comparison remains frozen F80/LTM versus F80/LTM plus one feature at a time, using identical exposure, portfolio constraints and transaction costs. Use chronological train/validation/OOS, date-block bootstrap, issuer leave-one-out, and an untouched final holdout. No threshold selection on the final holdout.

## 7. Source decision

| Source | Role after Phase 143 |
|---|---|
| IvyDB TradeFlow | **Top conditional all-venue flow source**; raw sample, interval accounting, first-delivery PIT and version lineage still block alpha tests |
| IvyDB US | Complementary OI/IV/Greeks/security-ID foundation; preserve patch and first-receipt vintages |
| Cboe Open-Close | Complementary capacity × side × open/close on Cboe venues; not full OPRA |
| Cboe Option Trades / Databento OPRA | Potential raw-market reconciliation; same-date, same-contract and schema/time gates required |
| IVolatility signed flow | Methodology robustness candidate, not independent raw-market validation because it also derives from OPRA |

**No alpha is demonstrated.** No forward-return test was run. No vendor contact, trial, purchase or terms acceptance occurred. No production change was made. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Official references

- [IvyDB TradeFlow product page](https://optionmetrics.com/ivydb-tradeflow/)
- [TradeFlow methodology paper, 2026-09-28](https://optionmetrics.com/wp-content/uploads/2026/09/IvyDB-TradeFlow-A-Framework-for-Options-Volume-Classification-and-Microstructure-Analytics.pdf)
- [OptionMetrics retail identification note, 2026-09-28](https://optionmetrics.com/blog/how-much-of-0-dte-is-really-retail-evidence-from-spx-and-spy-options/)
- [Signed Volume 2.0 announcement, 2021-03-07](https://optionmetrics.com/news/optionmetrics-releases-signed-volume-2-0-with-insights-on-retail-participant-activity-and-even-more-detail-on-directional-buying-in-options-order-flows/)
- [Signed Volume intraday announcement, 2024-08-07](https://optionmetrics.com/news/optionmetrics-releases-signed-volume-intraday-with-5-and-30-minute-snapshots-on-directional-options-order-flows-for-assessing-0dte-options-market-maker-inventory-hedging/)
- [TradeFlow launch announcement, 2026-09-30](https://optionmetrics.com/news/optionmetrics-launches-ivydb-tradeflow/)
