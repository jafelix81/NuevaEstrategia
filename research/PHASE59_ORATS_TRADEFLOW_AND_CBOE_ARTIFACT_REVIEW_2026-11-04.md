# Phase 59 — Options vendor audit update: ORATS, OptionMetrics TradeFlow, and Cboe sample review

Date: 2026-11-04  
Branch: `phase59-options-vendor-cross-source-audit`  
Status: preferred sample candidates identified; no data purchase authorized.

## 1. ORATS Near End-of-Day — materially improved feasibility

The current official ORATS product page documents a complete US equity-options snapshot taken at approximately 3:46 p.m. ET, 14 minutes before the close, with every strike and expiration for more than 5,000 symbols and history from 2007.

Documented fields include:
- Calls and puts: volume and open interest.
- NBBO bid/ask and sizes.
- Theoretical values, smoothed implied volatility, and Greeks.
- Trade date, expiration, strike, DTE, rates and dividend assumptions.

Important timing and semantics:
- Call/put volume is the total traded volume at the snapshot time, not necessarily the final close-of-day total.
- Call/put OI is updated by OCC the previous night; it is not same-day final OI.
- The underlying value is derived from options via put-call parity and is not a substitute for an independent stock-price series.
- Daily recurring files are delivered via FTP around midnight. Use the next trading session as conservative KnowledgeDate unless historical release evidence supports an earlier time.
- The historical archive is approximately 500 GB, delivered via S3 with a 14-day access window. No AWS account or AWS transfer/storage charges are stated for this near-EOD archive.

Official individual pricing on the current product page:
- One-time history, 2007–present: $599.
- Recurring daily delivery: $99/month.
- Professional/institutional licenses are quoted separately.
- A full sample file is available through ORATS University; the sample is publicly listed, but it was not ingested in this run.

The page states that delisted tickers are retained from 2007-01-01. This materially improves its fit for historical-universe research, but the claim still needs to be verified against known delisted names and old contract roots in a sample.

Sources:
- https://orats.com/near-eod-data
- https://orats.com/data-api

## 2. OptionMetrics — prioritize TradeFlow, not the legacy Signed Volume label

The current OptionMetrics product is IvyDB TradeFlow, described as an evolution of IvyDB Signed Volume.

Official documentation states:
- Every US option, every day since January 2016.
- 5-minute, 30-minute, and end-of-day snapshots.
- Buy/sell pressure and whether trades occur at bid, ask, or midpoint.
- Lot-size information.
- Trade-description codes, exchange-venue data, VWAP, and aggressiveness relative to SEC NBBO.
- Classification/analytics described as retail versus institutional activity.

IvyDB US, the companion base dataset, begins in January 1996 and documents permanent instrument IDs, ticker/name changes, split/spinoff adjustments, and coverage of securities that no longer trade.

Interpretation guardrails:
- TradeFlow is a directional/aggressor-flow product, not proof of beneficial-owner identity or a record of opening versus closing positions.
- Retail/institutional labels must be treated as vendor classifications/proxies until OptionMetrics documents the exact variables, thresholds, trade-condition handling, and historical methodology.
- Do not assume the classifications are stable back to 2016 merely because the dataset begins in 2016.
- Request TradeFlow and IvyDB US together; do not purchase legacy Signed Volume separately unless the vendor confirms a material field not present in TradeFlow.

Sources:
- https://optionmetrics.com/ivydb-tradeflow/
- https://optionmetrics.com/signed-volume/
- https://optionmetrics.com/united-states/

## 3. Databento OPRA — useful reconstruction/validation source, exact price is usage-based

Official documentation states that OPRA historical trades, OHLCV aggregates, statistics, instrument definitions and CBBO-1m are available from 2013-04-01. Consolidated CMBP-1 and trade-conditioned TCBBO start 2023-03-28. Databento stated historical OPRA release within 10 hours of real-time-feed publication for licensed users after its 2025 upgrade.

Historical pricing is usage-based per uncompressed data size; exact cost is produced by a customized dataset/schema/date request. New accounts receive $125 in historical-data credits. Do not assume the general $199 Standard subscription headline is an OPRA quote; the public pricing table is product/dataset-specific and must be checked in the OPRA catalog.

Databento is a potential independent reconstruction of aggressor flow from trades and consolidated quotes, but it does not provide the participant categories in Cboe Open-Close or the TradeFlow retail/institutional labels.

Sources:
- https://databento.com/blog/opra-improvements-coming-soon
- https://databento.com/pricing/
- https://databento.com/docs/faqs/usage-pricing-and-data-credits

## 4. Reinspection of downloaded Cboe/OCC artifacts

The latest successful artifacts were downloaded and inspected, not just their run summaries.

### Cboe Open-Close EOD sample — artifact 13290264681

| File | Rows | Candidate tickers present | Coverage |
|---|---:|---:|---:|
| C1 EOD 20% sample | 23,179 | 288/335 | 85.97% |
| C1 1-minute sample | 87,322 | 305/335 | 91.04% |
| C1 10-minute sample | 78,468 | 302/335 | 90.15% |

The EOD sample has non-null underlying, series, expiry, strike, call/put, total exchange volume, total industry volume, current/previous OI, and participant-volume fields. This is a promising one-date schema/coverage result, not a historical-coverage pass.

Two issues were recorded:
1. The sample header contains the typo `cust_gt_199_clsoe_buy_qty`; its volume counterpart is correctly named. Preserve raw headers and map this alias explicitly rather than silently dropping the field.
2. The raw `total_exchange_vol / total_industry_vol` ratio has median 0.5, 90th percentile 2.0, maximum 2.0, and exceeds 1 in 32.7% of rows. It is not a valid market-share proxy without reconciling Cboe's count-both-sides convention, OCC/OPRA industry volume definitions, and sample/final-file semantics. Do not use it as a normalization denominator.

The EOD specification states that final files typically arrive 00:30–01:00 ET the next morning. Use next trading session as conservative KnowledgeDate. Preliminary files may source total industry volume and OI from OPRA; final files source authoritative values from OCC.

### Cboe Option EOD Summary sample — artifact 13290668468

The sample has 32,672 rows per variant but only four underlyings (SPY, TSLA, SPX, VIX); only TSLA belongs to the 335-name candidate universe. It validates schema, not universe coverage. Positive IV was 92.75% in the no-CGI sample; positive OI was 77.20%; positive volume was 40.35%. Keep explicit zero/invalid-value filters.

### OCC Volume Query — artifact 13292225481

Coverage was 325/335 (97.01%) on 2025-01-03 and 320/335 (95.52%) on 2026-11-02, with a hard 24-month retention boundary. It aggregates by account type and call/put/underlying but does not provide aggressor side, opening/closing status, strike-level positions, or actual OI in the reviewed response. It remains a recent complement, not a long-OOS source.

## 5. Revised vendor ranking

| Role | Preferred candidate | Reason |
|---|---|---|
| Historical options context (IV/OI/skew/quotes) | ORATS Near EOD | 2007 history, delisted retention claim, broad chain snapshot, $599 individual historical archive |
| Directional / retail-institutional proxy flow | OptionMetrics TradeFlow | All US options, 2016+, 5/30-minute/EOD, trade descriptions, venue, VWAP, NBBO aggressiveness |
| Independent order-flow reconstruction | Databento OPRA | Trades + consolidated quote schemas from 2013/2023; usage-based sample |
| Exchange-specific opening/closing validation | Cboe Open-Close | Participant origin and open/close categories, but Cboe venue subset only |
| Recent aggregate complement | OCC Volume Query | High recent ticker coverage but only 24 months and no signed/open-close data |

## Decision

First inspect ORATS public sample and request a small historical sample plus quote for OptionMetrics TradeFlow. Require exact data dictionary, PIT delivery/correction timestamps, expired/delisted coverage, contract identifiers, lot-size and retail/institutional classification methodology, and commercial-use terms before purchase. No vendor spend is authorized. No forward-return test or alpha claim is authorized. F80 remains frozen.
