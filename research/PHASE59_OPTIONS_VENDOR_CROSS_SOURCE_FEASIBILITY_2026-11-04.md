# Phase 59 — Historical options vendor cross-source feasibility
Date: 2026-11-04  
Branch: `phase59-options-vendor-cross-source-audit`  
Status: SOURCE FEASIBILITY REVIEW / NO DATA PURCHASE / NO RETURN TEST.

## Executive decision

A stronger options research stack has emerged than the prior Intrinio-only plan:

1. **OptionMetrics IvyDB US + Signed Volume** is the highest-priority candidate for historical options context plus signed buyer-/seller-initiated volume. It has the best documented continuity controls and a direct flow field, but price, exact field schema, historical lot-size scope, delivery timestamps and licensing require a vendor sample/quote.
2. **ORATS Near-EOD** is the leading low-cost/API candidate for broad option-chain, volume, OI, IV and Greeks context. It advertises 2007 history and 5,000+ symbols; a one-time historical archive is available via S3, while recurring files are delivered nightly. Price/entitlements for the one-time archive and historical retention of delisted underlyings still require confirmation.
3. **Intrinio Options** remains a secondary alternative. Its API/CSV supports historical chains and all expired/active contracts available for a ticker, but pre-2021-10-10 expirations require a separate subscription and historical delisted-underlying coverage is unproven.
4. **Databento OPRA** is a conditional independent reconstruction route for signed flow from trades plus consolidated BBO/CBBO-1m, with history from 2013-04-01. It does not directly provide open/close or participant identity; usage-based cost and required OPRA schemas/licensing need a sample estimate.
5. **Cboe Open-Close** remains the strongest candidate for exchange-specific participant-capacity and opening/closing labels; it is venue-limited. MIAX is an independent venue replication candidate but should not be purchased before a viable hypothesis/data stack exists.
6. **ThetaData** can support a small low-cost/limited-history pilot, but its public free-tier and flat-file terms do not yet support the long OOS panel required here.

No provider has passed a full 335-name point-in-time coverage audit. No source is promoted to alpha. No data was purchased or downloaded.

## 1. OptionMetrics IvyDB US + Signed Volume — priority quote/sample

Official sources:
- IvyDB US: https://optionmetrics.com/united-states/
- Signed Volume: https://optionmetrics.com/signed-volume/
- Signed Volume brochure: https://optionmetrics.com/wp-content/uploads/2024/08/Signed-Volume-Brochure_v6.pdf
- Data products: https://optionmetrics.com/data-products/

### Documented coverage and fields

IvyDB US advertises a complete history of US exchange-traded equity and index options from 1996-01 onward, including ETFs and ADRs. Fields include option symbol/date, closing bid/ask, volume, OI, underlying high/low/close, IV and Greeks. It supplies interest-rate, dividend and corporate-action information, handles ticker/name changes and split/spinoff adjustments, and assigns permanent instrument IDs that track securities even when option roots, strikes or deliverables change, including securities that no longer trade.

IvyDB Signed Volume is an add-on to IvyDB US:
- Daily option trading volume summarized by buyer-initiated and seller-initiated direction.
- Trade direction is assigned from trade price relative to the bid/ask quote at the time of trade.
- Tracks bid, ask and midpoint activity.
- Every option/every day is advertised from 2016-01.
- Intraday 5-minute and 30-minute snapshots are advertised in addition to EOD.
- Volume lot-size fields begin in 2021 and are described as helping distinguish retail/institutional flow.
- Symbols and security IDs link to IvyDB US.

### Why this is materially stronger

This is the first source found in this line that directly provides signed option demand while also offering a documented historical security identity/corporate-action framework. It is a better direct test of aggressor-side demand than unsigned call/put volume or venue-level aggregate volume.

However, buyer-/seller-initiated is **not** opening/closing. It does not identify beneficial owners. Lot size is not a verified investor-type label. A buyer-initiated put may be a hedge, a directional bearish position, or a closing/adjustment leg. No single call/put or participant label will be called “smart money”.

### Required vendor clarifications

Request a sample and written quote for IvyDB US + Signed Volume covering:
- The 335 current frozen tickers plus historical/delisted F80 names and ETFs.
- Dates in 2016, 2018, 2020, 2021, 2023, 2025 and 2026.
- All option series on those dates, including expired and adjusted contracts.
- EOD Signed Volume plus 5-minute and 30-minute snapshots; specify exact first date for each granularity.
- Field-level definitions for buyer-initiated, seller-initiated, midpoint, unclassified, trade count, contract volume, lot-size buckets and multiplier/deliverable.
- Timestamp for each snapshot and actual daily delivery/publication timestamp; revision/patch policy.
- Permanent ID mapping and historical underlying/ticker/delisting crosswalk.
- Internal-use, derived-feature and model-output licensing.
- One-time historical, recurring update and minimum-term pricing.

Until verified, KnowledgeDate is conservatively the next trading session and execution is no earlier than the next-session close. The data's trade timestamp or snapshot timestamp is not, by itself, proof that the file was available to the strategy at that time.

### Candidate flow definition (hypothesis only)

For participant-free signed-volume data, use a separate variable from Cboe/MIAX open-close flow:

`signed_delta_demand_t = Σ_i delta_i,t × multiplier_i,t × (buyer_initiated_volume_i,t − seller_initiated_volume_i,t)`

Label this **signed delta-equivalent demand**, not net opening delta or net position change. Retain call/put, expiry, delta/moneyness, size and time buckets separately. Exclude midpoint/unclassified volume from the directional numerator unless the vendor supplies a validated signed rule. Never assume a 100-share multiplier for adjusted contracts.

Lot-size stratification is a separate post-2021 hypothesis, not a historical institution classifier. The primary signed-flow test should not depend on it.

## 2. ORATS Near-EOD — preferred lower-cost context sample

Official sources:
- Product/API: https://orats.com/data-api
- Historical data delivery: https://orats.com/university/historical-data
- Historical API docs: https://orats.com/docs/historical-data-api
- Field definitions: https://orats.com/hard-drive-delivery

### Documented facts

- Historical Near-EOD options data advertised from 2007, with full US equity option chains and 5,000+ symbols.
- Snapshot is gathered 14 minutes before the close.
- Example historical records include call/put volume and OI, NBBO bid/ask prices and sizes, bid/mid/ask IV, smoothed IV (`smvVol`), Greeks, theoretical values, `quoteDate` and `updatedAt`.
- ORATS explicitly says its underlying stock/ETF/index prices are derived from options using put-call parity and are for internal reference only; use the project's independent equity-price source for returns, execution and ADTV.
- Historical Near-EOD data is available as a one-time purchase through an ORATS-hosted S3 archive. Access to the historical download lasts 14 days.
- Recurring Near-EOD files are delivered nightly at midnight for OPRA compliance. The recurring subscription does not include pre-purchase history.
- The delayed API plan currently advertises $199/month and 20,000 requests/month, including Near-EOD history endpoints. Exact entitlement and whether the one-time archive is separately priced must be confirmed in writing.

The `hist/strikes` endpoint requires ticker and tradeDate; up to 10 tickers may be comma-delimited per request. For 335 symbols, a full-date request is therefore at least 34 requests. At 20,000 requests/month, that is approximately 588 trading dates/month. A rough 2007-to-2026 backfill of about 4,800 sessions would require around 163,200 requests (about 9 monthly quotas), before retries/pagination. This is only an API-call estimate; a one-time S3 archive may be materially more practical.

### PIT interpretation

The option snapshot is taken 14 minutes before close, but recurring files are delivered at midnight. Use next-session KnowledgeDate and next-session close execution unless the vendor provides reproducible evidence of earlier availability for the exact plan. Do not use same-day tradeDate as availability date.

### Limitations

- No buyer-/seller-initiated volume, open/close status or participant identity in the documented EOD fields.
- Current symbol counts do not prove historical 335-name/delisted coverage.
- Need exact historical universe and contract retention, adjusted-root and multiplier checks.
- Historical bid/ask/IV/Greeks validity and zero/stale/crossed quote rates must be measured.

Decision: obtain a representative sample and quote. If it passes historical identity/coverage and PIT gates, use it as a full-chain volatility/OI context source; not as standalone smart-money flow.

## 3. Intrinio — secondary context alternative

Official sources:
- Pricing: https://intrinio.com/pricing
- EOD options guide: https://intrinio.com/how-to/how-to-query-eod-options
- Options Gold guide: https://intrinio.com/guides/options-gold
- Chain API: https://docs.intrinio.com/documentation/web_api/get_options_chain_eod_v2

Documented facts:
- Individual plan $150/month is personal-use only, one seat, no redistribution/display.
- Startup plan begins at $333/month and includes commercial-use/business-wide rights.
- The API guide says the ticker contract endpoint returns all expired and active contracts available for a ticker; historical contract prices can be paged from inception to expiration; chain EOD can return historical prices for all contracts in an expiration; CSV delivery is encouraged for bulk historical backfill.
- The Options Gold guide says historical expirations before 2021-10-10 require a separate subscription.

This partially addresses the prior expired-contract concern, but it does not prove retention for delisted underlyings or PIT F80 membership. Require a sample with known expired contracts, delisted underlyings, adjusted roots and dates before 2021-10-10. No participant signed flow/open-close is documented. Treat as a context alternative to ORATS, not an independent source from OPRA.

## 4. Databento OPRA — conditional flow reconstruction

Official sources:
- OPRA product announcement: https://databento.com/blog/opra-data
- Historical extension: https://databento.com/blog/opra-improvements-coming-soon
- OPRA schema changes: https://databento.com/blog/opra-migration
- Pricing: https://databento.com/pricing/

Documented OPRA history was extended to 2013-04-01 for trades, OHLCV, statistics, instrument definitions and CBBO-1m. OPRA covers consolidated US listed options across national exchanges. Databento announced more consistent historical releases within 10 hours of publication for licensed users. Pricing is usage-based for historical data; exact OPRA cost depends on schema, date range and selected symbols/records.

Potential value:
- Reconstruct buyer-/seller-initiated volume from trades against contemporaneous consolidated BBO/CBBO.
- Preserve exchange, timestamp, condition codes, contract definitions and quote freshness.
- Independently compare a transparent signing algorithm against OptionMetrics Signed Volume.

Limitations:
- This does not reveal open/close or beneficial owner.
- NBBO/tick-rule signing is noisy for midpoint, locked/crossed/stale quotes, complex orders and trade conditions.
- No direct OI/IV/Greeks are assumed; these must be sourced or calculated with a frozen model.
- Full history volume/cost and OPRA licensing must be estimated before a sample.

Decision: park until OptionMetrics Signed Volume or ORATS sample establishes a specific need for an independently reconstructed flow measure.

## 5. Other candidates / parked lines

### ThetaData
Official subscription docs: https://thetadata.net/docs/Articles/Getting-Started/Subscriptions.html  
Flat-file docs: https://thetadata.net/docs/Flat-Files/Getting-Started

Public docs advertise one year of free historical EOD options data; the table lists FREE EOD first access 2023-06-01, while OI/quotes require VALUE or higher and IV/Greeks require STANDARD or PRO. Options history is advertised from 2020-01 for 1-minute VALUE, 2016-01 for tick-level STANDARD and 2012-06 for tick-level PRO. Professional flat files cover only the latest seven calendar days; longer bulk history requires a sales inquiry. The free-tier date/retention statements need reconciliation. Keep as a sample/validation alternative, not the primary long-history panel.

### OptionMetrics IvyDB US Intraday
Official page: https://optionmetrics.com/united-states-intraday/  
Advertises timestamped option quotes/volume at 10:00, 14:00 and 15:45 ET from 2018-01. Could be useful for checking pre-close versus EOD surface changes. Price and actual release timestamp remain unknown; do not add until Signed Volume sample/quote is obtained.

### Cboe / MIAX
Continue to treat Open-Close as exchange-specific participant-capacity and open/close data, not full OPRA. Do not buy expensive multi-year Cboe/MIAX archives before broad OPRA context and/or OptionMetrics Signed Volume passes. MIAX remains a potential independent venue replication, not an assumed confirmation.

## 6. Comparative decision matrix

| Source | Historical depth advertised | Flow direction | Open/close | OI / IV / Greeks | Identity continuity | Cost visibility | Current decision |
|---|---:|---|---|---|---|---|---|
| OptionMetrics IvyDB + Signed Volume | IvyDB 1996; Signed Volume 2016 | Buyer/seller initiated | No | Yes | Permanent ID; corporate actions; delisted names | Quote required | **Priority 1 sample/quote** |
| ORATS Near-EOD | 2007 | No | No | Yes | PIT/delisted continuity unverified | API $199/mo; archive quote/price unclear | **Priority 2 sample** |
| Intrinio | Product/contract-dependent; pre-2021-10-10 expirations separate | No | No | Yes | Expired contracts by ticker; delisted coverage unverified | $150 personal / $333 commercial + add-ons | Secondary alternative |
| Databento OPRA | 2013-04 | Reconstruct from trades/BBO | No | Not assumed | Instrument definitions; PIT corporate action join required | Usage-based | Conditional independent reconstruction |
| Cboe Open-Close | C1 2005; other venues 2018 | Buy/sell by participant | Yes | Context from separate OPRA feed | OCC/PIT mapping required | Published, high historical cost | Complementary participant data |
| MIAX Open-Close | EOD 2021; 1m varies by venue from 2013 | Buy/sell by origin | Yes | Context separate | OCC/PIT mapping required | Published, high cost | Parked independent venue |
| ThetaData | EOD/free limited; paid tick from 2012/2016 | Trade/quote reconstruction possible | No | Paid tiers | PIT/delisted test needed | Subscription tiers | Limited sample only |

## 7. Preregistered next data gate

No return test is authorized until at least one context vendor and one signed-flow route pass:

### Sample design
- 40–50 names drawn before data review from frozen F80 history: large/small cap, high/low option volume, ETFs, delisted names, symbol changes, splits/spinoffs and adjusted option roots.
- At least 12 non-contiguous dates across 2016–2026, including 2016/2018/2020/2021/2023/2025/2026.
- All contracts, expiries and strikes for each sample name/date.
- Explicitly include contracts known to have expired and underlyings no longer trading.
- Keep current-universe coverage separate from PIT F80 membership and from historically optionable names.

### Required metrics
1. PIT optionable ticker/date coverage against the historical F80 denominator.
2. Contract-level completeness for volume, OI, bid/ask, IV and Greeks.
3. Expired contract and delisted-underlying retention.
4. Permanent identifier and adjusted deliverable/multiplier mapping.
5. Buyer/seller-initiated, midpoint and unclassified volume rates.
6. Lot-size field availability by date and exact definitions.
7. Timestamp/revision/late-file evidence and reproducible KnowledgeDate.
8. Licensing, internal use and derived-feature rights.
9. Total acquisition and ongoing cost for the exact requested scope.

### Economic hypotheses after data gate only
- Signed delta-equivalent demand (buyer-initiated minus seller-initiated) by call/put, delta and expiry bucket.
- Signed vega/premium demand as a separate volatility-demand measure.
- Large-lot versus small-lot flow only from 2021 onward, as a proxy hypothesis, never an investor identity.
- IV skew and term-structure state from IvyDB/ORATS as context, not flow.
- Interactions of signed flow with IV/skew/OI only after each component passes independently.

Control for prior 1/5/20-session underlying returns, realized volatility, liquidity, earnings, market/sector moves, optionability, and recent volume. Distinguish predictive information from return chasing. Use only data available by KnowledgeDate; execute at the next-session close under the existing end-of-day convention.

Validation must compare frozen LTM/F80 against each single feature and then pre-specified combinations, with identical exposure, costs, rebalance timing and universe; chronological train/validation and at least two untouched OOS regimes; block bootstrap, ticker/sector clustering and LOO. Do not select horizons or thresholds by maximizing backtest return. Failed hypotheses are archived, not rescued.

## 8. Current execution/repository state

- The latest Phase 53B OCC canonical run 41763113005 succeeded. OCC has 645/670 valid recent queries (96.27%), but explicitly fails the long-history gate (24-month retention) and lacks buy/sell/open/close.
- Phase 54 Cboe Open-Close sample schema passed; the EOD sample is a 20% C1 sample for one date, not full universe/history.
- Phase 55 Cboe Option EOD Summary sample schema/Calcs passed, but only TSLA of the 335 current names was present; universe coverage is NOT TESTED.
- Phase 50 global SEC Form 144 run 41761510120 is still marked in progress at its 2025Q1 global-index step; run 41761577180 is pending in the same concurrency group. The active job's log-download endpoint currently returns BlobNotFound and no artifact is available. Do not launch another Phase 50 run or infer source coverage. Recheck later; the step remains marked in progress.
- Phase 58 remains conditional; Phase 59 is a research-only branch. No data purchased, no forward returns, no alpha result.
- `main` and `F80_TOP20_PARTIAL50_BASELINE_C20` are unchanged/frozen.

## Sources reviewed (official vendor documentation)

- OptionMetrics IvyDB US: https://optionmetrics.com/united-states/
- OptionMetrics Signed Volume: https://optionmetrics.com/signed-volume/
- OptionMetrics Signed Volume brochure: https://optionmetrics.com/wp-content/uploads/2024/08/Signed-Volume-Brochure_v6.pdf
- ORATS pricing/API: https://orats.com/data-api
- ORATS historical data delivery: https://orats.com/university/historical-data
- ORATS historical API: https://orats.com/docs/historical-data-api
- ORATS field definitions: https://orats.com/hard-drive-delivery
- Intrinio pricing: https://intrinio.com/pricing
- Intrinio historical options guide: https://intrinio.com/how-to/how-to-query-eod-options
- Intrinio Options Gold: https://intrinio.com/guides/options-gold
- Databento OPRA: https://databento.com/blog/opra-data
- Databento OPRA history: https://databento.com/blog/opra-improvements-coming-soon
- ThetaData subscriptions: https://thetadata.net/docs/Articles/Getting-Started/Subscriptions.html

## Final decision

**Priority order: OptionMetrics Signed Volume sample/quote; ORATS Near-EOD sample/quote; Intrinio as backup.** Cboe Open-Close remains complementary for open/close and participant capacity. MIAX and Databento are deferred until a specific replication need is established.

No alpha claim. No forward-return test. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
