# Phase 429 — ThetaData v3 options access, extraction scale and licensing reconciliation

**Audit date:** 2026-11-16 UTC  
**Disposition:** retain ThetaData as a strong conditional independent raw-OPRA candidate; documentation feasibility improved, but no sample, PIT, full-universe or alpha admission.  
**Relationship to prior work:** additive update to Phase 391, not a replacement. Phase 391 remains the source-ranking and initial OPRA-methodology record.

## Executive finding

A fresh review of ThetaData's current official v3 documentation clarifies that the historical options endpoints can expose OPRA trades, NBBO quotes, trade/quote pairs and open interest by subscription tier. The trade/quote endpoint supports a strict prior-quote match (exclusive=true), and the dated contract-list endpoint can enumerate contracts traded or quoted on a historical date. These are useful building blocks for a point-in-time raw-flow panel.

The same review exposes meaningful implementation and commercial constraints:

1. Historical full-market flat files are **not** available through the ordinary public workflow beyond the most recent seven calendar days. Historical reconstruction is per underlying/contract request, not one market-wide archive download.
2. Tick-level option requests should generally be chunked to one week, and to one day for very liquid names, keeping each response below roughly one million ticks. A one-month endpoint limit is not a safe recommended chunk size.
3. Pro concurrency is eight requests account-wide, not eight per endpoint. This is throughput concurrency, not a guarantee of complete historical coverage or unlimited compute/storage.
4. The detailed subscription matrix says Options Pro first-access is 2012-06-01, while the retail pricing page advertises 12 years and the business page advertises 14 years. This is a documentation discrepancy requiring written confirmation before purchase.
5. The business-use options package is listed at $1,600/month billed annually (startup discounts advertised from $500/month). The retail Options Pro page is for individual/personal use only. No plan, trial, key, sample or vendor contact was obtained.

The result is a stronger engineering-feasibility case, not evidence that the source covers the frozen 335-name universe or predicts equity returns.

## 1. Subscription and endpoint matrix

The current official subscription documentation lists:

| Options tier | First-access date | Granularity | Historical endpoints relevant to this project |
|---|---|---|---|
| FREE | 2023-06-01 | EOD, one-day delayed | EOD only |
| VALUE | 2020-01-01 | 1 minute | EOD, quote, open interest, OHLC |
| STANDARD | 2016-01-01 | Tick | Above plus trade, trade_quote, IV and first-order Greeks |
| PRO | 2012-06-01 | Tick | Standard endpoints plus higher-order and trade Greeks |

This is the vendor's tier-level access matrix, not an empirical coverage audit by ticker, contract or date. The general availability page separately says options trades, EOD and OHLC extend to 2012-06-01. The public retail pricing page currently advertises Options Pro at $160/month and 12 years of history, while the commercial page advertises 14 years. These statements are not perfectly aligned with the detailed 2012-06-01 tier matrix. Before any paid decision, require written confirmation of the actual first date for **trade, quote, trade_quote, OI, IV and Greeks separately**, for the exact account/license being quoted.

Official references:
- https://www.thetadata.net/docs/Articles/Getting-Started/Subscriptions.html
- https://www.thetadata.net/docs/Articles/Data-And-Requests/Making-Requests.html
- https://www.thetadata.net/subscribe
- https://www.thetadata.net/commercial-use

## 2. Raw OPRA trade/quote reconstruction

The v3 option/history/trade_quote endpoint returns OPRA trades paired with the last OPRA NBBO quote. For historical data, matching is timestamp-based. Explicitly set exclusive=true so the quote timestamp must be strictly earlier than the trade timestamp; retain both timestamps and calculate quote age.

The endpoint accepts expiration=* for all expirations of a specified underlying. Multi-day requests are limited to one month and require an expiration parameter. The historical quote endpoint has the same one-month multi-day limit and supports tick through coarser intervals.

**Interpretation limits:** a strict prior quote prevents using a quote timestamped at or after the trade, but it does not establish that the quote was fresh, valid, uncrossed, or free of later correction. It also does not establish when the vendor first delivered that historical row to a customer.

If a lawful sample is later available, the parser must:
- retain raw trade and quote timestamps, sequence, condition, exchange, size, price and NBBO fields;
- quarantine stale, locked, crossed, zero-sided and otherwise invalid quotes;
- decode OPRA trade conditions and isolate complex, auction, late, out-of-sequence, corrected and cancelled prints where the feed permits;
- classify only clearly buyer-/seller-initiated trades; leave midpoint and ambiguous prints unclassified rather than forcing a side;
- avoid calling large prints or any flow bucket “institutional” or “smart money” without identity evidence;
- preserve source bytes, request parameters, response hashes, retrieval time and parser version.

Official references:
- https://www.thetadata.net/docs/operations/option_history_trade_quote.html
- https://www.thetadata.net/docs/operations/option_history_quote.html
- https://www.thetadata.net/docs/Articles/Data-And-Requests/Symbology.html

## 3. Historical contract universe and extraction scale

The option/list/contracts endpoint is documented to list contracts traded or quoted on a specified date, optionally filtered by underlying. This provides a possible date-specific optionability census and is preferable to using today's option chain as a historical universe. It still requires a real historical sample to verify completeness, adjusted contracts, duplicate roots and ticker changes.

The regular history endpoints require an underlying symbol; there is no market-wide wildcard for historical options trades/quotes/EOD/OI. expiration=* expands expirations for one underlying, not all underlyings.

ThetaData's request-sizing guidance recommends:
- options tick-level: one week;
- one day for very liquid underlyings such as AAPL/SPX/SPY;
- keep responses below approximately one million ticks.

The Pro tier supports eight concurrent requests account-wide. Requests beyond that can queue (default queue size 16); a queue that grows too large may produce HTTP 429. Thus the one-month endpoint maximum should not be treated as the normal chunk size. A 335-name, multi-year tick panel is a substantial extraction, storage, retry and reconciliation project. Exact workload cannot be estimated until a small representative sample establishes rows/ticks per underlying-day.

The full-market option trade_quote flat file is approximately 1.2 GB per day and the open-interest flat file approximately 50 MB, but the documented flat-file interface is limited to the most recent seven calendar days. It is not a historical market-wide backfill mechanism. The historical path remains per-underlying API requests.

Official references:
- https://www.thetadata.net/docs/operations/option_list_contracts.html
- https://www.thetadata.net/docs/Articles/Data-And-Requests/Request-Sizing.html
- https://www.thetadata.net/docs/Articles/Data-And-Requests/Concurrent-Requests.html
- https://thetadata.net/docs/Flat-Files/Getting-Started.html
- https://www.thetadata.net/docs/operations/option_flat_file_trade_quote.html

## 4. Open-interest and availability clocks

ThetaData states that OPRA normally reports open interest around 06:30 ET and that the value represents the end of the **previous trading day**. A new message may be absent when the contract has no open interest.

Rules:
- Never align the 06:30 ET message to the current session's closing OI.
- Treat it as prior-session OI and use it only after the actual message is received.
- Missing OI messages are missing observations, not zero.
- Do not infer that high volume/OI means new opening positions; volume is intraday turnover and OI is a later net outstanding-position measure.

The public documentation does not establish a historical first-vendor-receipt ledger, complete correction/bust/replacement vintages, or historical delivery latency for each endpoint. Historical backfill therefore remains retrospective unless a defensible vendor vintage is provided. A prospective capture must record actual first receipt, raw response hash, request parameters, endpoint/version and subsequent corrections. For daily portfolio use, do not trade on same-session option flow before the source is received and reconciled.

Official reference:
- https://www.thetadata.net/docs/operations/option_history_open_interest.html

## 5. Coverage and underlying-data caveats

The vendor's “every U.S. option ticker” / full-coverage language is not a measured pass against the frozen 335-name diagnostic universe. Required sample gates remain:
1. Historical contract-list coverage by underlying and date, including inactive/delisted names.
2. Adjusted/non-standard contract handling and deliverable/multiplier history.
3. Historical root-to-underlying and corporate-action identity.
4. Actual trade/quote/OI/IV availability by tier and date.
5. Missingness and no-data reconciliation by symbol, date, expiration and contract.
6. Underlying price coverage if any delta-/gamma-adjusted feature is used.

ThetaData separately documents that its historical equity price/Greek coverage is UTP-dependent for older dates; CTA-only examples such as SPY and GE lack pre-2020 underlying history in that stock feed. This does not invalidate raw option trade/quote observations, but it can invalidate vendor-calculated historical Greeks or delta-weighted flow for affected names. Do not silently mix this with the frozen strategy's price source. Either use a separately validated, point-in-time underlying source or keep the initial flow measure unweighted by Greeks.

Official reference:
- https://www.thetadata.net/docs/Articles/Data-And-Requests/Making-Requests.html

## 6. License and cost gate

The commercial-use page lists Options Data at $1,600/month billed annually, with startup pricing advertised as low as $500/month. It describes the commercial offering as for business use. The retail page lists Options Pro at $160/month but expressly restricts that page to individual/personal use and disallows redistribution/business use.

No purchase, free-account creation, trial, API key, vendor contact or license acceptance occurred. The retail plan must not be used for business/commercial research or redistribution. If the eventual use case is strictly personal research, obtain the exact retail terms and first-date guarantee; if commercial, obtain a written business quote and data-use rights before any sample is retained or shared.

Official references:
- https://www.thetadata.net/subscribe
- https://www.thetadata.net/commercial-use

## 7. Proposed research design after all data gates pass

Treat the source as **raw options-market microstructure**, not verified institutional ownership.

Candidate daily underlying-level features:
- signed premium/notional flow using only valid, strictly prior NBBO;
- signed volume divided by total classifiable premium/contract volume;
- separate call/put, DTE and moneyness buckets;
- volume/OI as a descriptive turnover measure, with OI aligned to its prior-session report date;
- changes in IV/skew only after the corresponding quote/IV observation is available;
- separate unclassified/complex/auction/late/correction buckets.

Do not make size alone an institutional classifier. Do not assume call buying is bullish or put buying bearish without controlling for opening/closing, spreads, hedges and underlying exposure.

Before any return test:
1. Freeze a representative sample and reconcile raw rows, contracts, conditions, quote ages, hashes and corrections.
2. Measure historical coverage against the full frozen universe and inactive/delisted names; do not reduce the denominator to obtain a pass.
3. Establish a prospective first-receipt ledger and conservative feature-availability time.
4. Reconcile a subset independently against OptionMetrics TradeFlow and Cboe Open-Close, respecting their different coverage and participant semantics.
5. Preregister one or a small fixed family of features and controls for LTM/F80 score, momentum, volatility, liquidity, market/sector exposure and event risk.
6. Use identical portfolio exposure, execution timing and transaction costs; test only incremental information over frozen LTM/F80.
7. Apply chronological discovery/validation/OOS, block bootstrap, leave-one-out and multiplicity controls. The consumed legacy holdout remains unavailable.

## 8. Decision

**CONDITIONAL — DO NOT PURCHASE OR ADMIT YET.**

ThetaData remains the strongest independent raw-OPRA reconstruction candidate because it offers trade/quote pairs, prior-quote matching, dated contract enumeration and historical OI. Phase 429 improves the extraction and license map, but no sample bytes or account-level coverage were obtained. Historical first-receipt/correction vintages and point-in-time universe coverage remain unverified.

No Smart Money source or signal is admitted. No forward-return, alpha, OOS, bootstrap, LOO or holdout test was run. F80, universe, parameters, capital, exposure and production remain frozen.
