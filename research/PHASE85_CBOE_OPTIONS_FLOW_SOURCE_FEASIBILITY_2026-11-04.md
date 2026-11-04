# Phase 85 — Options-flow source feasibility: Cboe and OptionMetrics

**Audit date:** 2026-11-04  
**Branch:** phase85-cboe-options-flow-source-feasibility  
**Scope:** historical availability, universe coverage, point-in-time timing, field semantics, data conventions and cost. No performance test or purchase.

## Decision

**Promote Cboe Open-Close EOD to the first options-flow source for a controlled sample audit. Keep OptionMetrics IvyDB Signed Volume as a parallel high-priority candidate. Do not purchase full Cboe Trade-by-Trade (TBT) history yet.**

A material update appeared on 2026-11-03: Cboe filed proposals to extend TBT to C2, BZX and EDGX. Those filings specify historical availability beginning 2019-03-01 and free July 2022 samples, but the DataShop product page still describes TBT as C1-only with the other venues planned for future release. The SEC notices state that the fee changes are effective upon filing but become operative 30 days after filing (C2 filed 2026-10-27; BZX and EDGX filed 2026-10-21), subject to possible SEC suspension. The DataShop page still lists the other venues as future releases, so actual product launch/access timing is not verified. Treat the multi-venue product as announced/planned, not as currently verified live access.

## 1. Cboe Open-Close Volume Summary — first practical candidate

Official product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary

### Fields and coverage

- Covers options trading on Cboe BZX, C1, C2 and EDGX.
- EOD summaries cover every option series with trading volume on the selected exchanges.
- Participant capacity: customer, professional customer, broker-dealer and market maker.
- Side: buy/sell. Position: open/close.
- Customer and professional-customer activity is split into size buckets: under 100, 100–199 and over 199 contracts.
- EOD includes OHLC, total volume and open-interest fields. Files are delivered overnight after midnight U.S. Eastern; one file per exchange and day/month grouping.
- Historical starts: C1 EOD 2005-01-03; BZX/C2/EDGX EOD 2018-01-02. C1 10-minute history starts 2011-01-03; C1 1-minute starts 2019-10-07; BZX/C2/EDGX interval data starts 2019-03-01.

### Important limitations and normalization

- Open interest and total industry volume are third-party value-adds, supplied on a best-effort basis; they are not direct Cboe exchange measures.
- Historical OI / previous OI convention shifts: C1 through 2019-10-04 and C2 through 2018-05-11.
- C2 total-industry-volume values were doubled through 2018-05-11.
- C1 total-exchange-volume convention changed through 2019-10-04 from (buy + sell)/2 to buy + sell.
- Previous-close definitions also differ historically for C1 and C2 through 2019-10-04 and 2018-05-11 respectively.
- C1 Global Trading Hours coverage begins 2023-12-11.
- Intraday 1-minute/10-minute files exclude EOD fields 10–17 (OHLC, total volume, open interest). They are not interchangeable with EOD files.
- Intraday schema changes are scheduled for 2026-11-08: trade corrections/busts/cancellations, removal of indicative/unsettled trades, new trading-date/session fields, timestamp and column-name changes, and gzip compression. Version the schema and normalize pre/post data before combining it.

### Cost and sample

The Cboe Exchange 2026 fee exhibit lists C1 EOD Open-Close historical pricing at $600 per month for 1–4 years and $300 per month for five or more years; daily updates are $600/month. It also provides up to six months of EOD historical data as a free trial for eligible new users who have not previously purchased or received a trial. This is materially more feasible than full TBT history, but other exchange schedules and the actual 335-name coverage still need a quote/sample check.

Previous Phase 54 evidence found 288/335 current tickers in a one-date, C1-only sample. That is not a full-universe or multi-venue coverage result. The new four-exchange EOD product may improve coverage, but it must be re-audited across multiple dates and historical symbol states.

## 2. Cboe Trade-by-Trade (TBT) — richest microstructure, high cost

Current product page: https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail

- Current page describes C1-only availability, historical start 2019-10-07, T+1 delivery.
- Each trade includes timestamp, underlying/OSI contract details, price, size, side, open/close, participant capacity, trade type, NBBO/local BBO and (for the subscribing member) execution IDs. This is materially richer than aggregate Open-Close.
- Capacity is not beneficial-owner identity. A customer/professional/broker-dealer/market-maker flag does not identify a named institution or prove informed trading.
- C1 fee filing: $12,000/month subscription or $8,000 per month of historical data; one-month free trial for eligible new users.
- 2026-11-03 C2 filing (SR-C2-2026-029): historical start 2019-03-01, $5,000/month subscription, $3,000 per historical month, free July 2022 sample.
- 2026-11-03 BZX filing (SR-CboeBZX-2026-089): historical start 2019-03-01, $6,000/month subscription, $4,000 per historical month, free July 2022 sample.
- 2026-11-03 EDGX filing (SR-CboeEDGX-2026-074): historical start 2019-03-01, $6,000/month subscription, $4,000 per historical month, free July 2022 sample.
- The C2 and BZX fee exhibits state 2027-01-07 effective schedules; the live DataShop page still identifies C1 as the current venue and the others as future releases.

A rough full-history ad-hoc estimate across the four venues from their respective starts through 2026-11 is about **$1.71 million** before any discounts or other charges (assuming the quoted fee applies per historical month: C1 86 months × $8k; C2 93 × $3k; BZX 93 × $4k; EDGX 93 × $4k). This is not a purchase recommendation. Use only eligible free samples or a narrowly scoped quote unless a demonstrated economic benefit justifies more.

## 3. OptionMetrics IvyDB Signed Volume — broad directional-flow candidate

Official product page: https://optionmetrics.com/signed-volume/

- Add-on to IvyDB US.
- Daily signed option volume for every option since 2016-01, plus 5-minute and 30-minute snapshots.
- Assigns buyer-initiated or seller-initiated direction using trade price relative to the bid/ask quote; tracks bid, ask and midpoint.
- Links symbols and security IDs to IvyDB US.
- Unlike Cboe Open-Close/TBT, it does not classify participant capacity. It measures inferred trade direction, not institutional identity.
- Pricing, contract coverage for inactive/delisted underlyings, revision policy and exact daily publication timestamps remain unverified.

This may be the broader historical flow series, while Cboe capacity data provides a venue-specific participant-class cross-check. Their incremental information must be tested separately and jointly, not assumed.

## 4. Preregistered next feasibility work

1. Obtain only an eligible free sample or written quote; no purchase is authorized by this audit.
2. Audit the 335-name universe across all four Cboe exchanges on multiple dates spanning 2018, 2019, 2021, 2023, 2025 and 2026. Include delisted/inactive names where the original universe can be reconstructed.
3. Measure per-ticker and per-date availability, contract/underlying mapping, missingness, venue share, field completeness and historical symbol adjustments.
4. Reconcile OI and volume convention changes by venue/date; preserve raw values and normalized values separately.
5. Verify overnight delivery/public availability. Until verified, use next-session availability in any economic test.
6. Only after the data gate passes, define ex-ante capacity/side/open-close/size features. Compare them with signed-volume features and frozen LTM/F80 using identical exposure, costs, chronological OOS, bootstrap and leave-one-out tests.
7. Treat customer, professional customer, broker-dealer and market-maker flow as competing hypotheses. No capacity is labelled “smart money” by default.

## Research boundary

No vendor contact, trial request, purchase, data download, signal construction, forward-return test or production change was made. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## Primary source filings

- C1 TBT fee filing, SR-CBOE-2026-010: https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-cboe-2026-010
- C2 TBT expansion/fee filing, SR-C2-2026-029: https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-c2-2026-029
- BZX TBT expansion/fee filing, SR-CboeBZX-2026-089: https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-cboebzx-2026-089
- EDGX TBT expansion/fee filing, SR-CboeEDGX-2026-074: https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-cboeedgx-2026-074
