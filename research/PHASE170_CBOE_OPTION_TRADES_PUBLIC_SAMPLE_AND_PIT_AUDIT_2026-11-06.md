# Phase 170 — Cboe Option Trades active-catalog and public-sample PIT audit

**Date:** 2026-11-06  
**Decision:** **PROMOTE CBOE OPTION TRADES TO FIRST-PRIORITY OPTIONS DATA FEASIBILITY; SAMPLE SCHEMA GATE PENDING. OPTION SENTIMENT IS PARKED PENDING CURRENT PRODUCT CONFIRMATION.**  
**Scope:** Current DataShop catalog/orderability evidence, official file specification, trade-side reconstruction design, and a public sample audit workflow. No paid data, account, vendor contact, return test or production change.

## 1. Why the source ranking changed

A fresh review of Cboe's live DataShop pages found a material distinction:

- The current [Data Products catalog](https://datashop.cboe.com/data-products) lists Cboe Open-Close, Enhanced US Options Trade-by-Trade Execution Detail, Option EOD Summary, Option Quotes and Option Trades. It does **not** list Option Sentiment.
- The legacy [Option Sentiment route](https://datashop.cboe.com/option-sentiment) redirects to the DataShop home page.
- The current [FAQ](https://datashop.cboe.com/faqs) still advertises Option Sentiment history from January 2012, and the [v1.4 specification](https://datashop.cboe.com/Documents/Cboe_OptionSentiment_Specs.pdf) remains online.
- In contrast, the current [Option Trades product page](https://datashop.cboe.com/option-trades) is a live product detail page with Historical and Subscription purchase choices, All Symbols selection and a public sample link.

This does not prove Option Sentiment has been discontinued; it proves that current orderability is not established by the public catalog. Do not plan a purchase or model dependency around it without written product confirmation.

## 2. Option Trades: current documented data contract

The current product page and [Option Trades specification v1.3](https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf) describe:

- Every options print across the OPRA universe for U.S.-listed stocks, ETFs and indices.
- Global Trading Hours and Regular Trading Hours.
- Trade price, size, executing exchange, OPRA sequence number, trade condition, prevailing NBBO and option contract descriptors.
- Optional point-in-time trade IV and Greeks (Delta, Gamma, Vega, Theta, Rho).
- Daily file delivery; historical data advertised from January 2012.
- Per-day, per-month or per-year file grouping.
- Options on futures and non-U.S. markets are excluded.

The general DataShop FAQ says daily files are typically delivered the next day between 00:05 and 03:00 ET, but may be delayed until after the next market open. That is a general schedule, not an Option Trades historical first-receipt ledger.

The sample endpoint linked from the current product page is https://datashop.cboe.com/download/sample/216. Phase 170 downloads only this public sample in GitHub Actions, parses it in memory and stores only metadata, counts and hashes.

## 3. Why this is a better first-priority candidate than Option Sentiment

Option Trades exposes the underlying trade prints and NBBO rather than only the vendor's daily directional aggregates. It therefore permits a reproducible, independently specified trade-side reconstruction:

- At the contemporaneous NBBO ask: buyer-initiated candidate.
- At the contemporaneous NBBO bid: seller-initiated candidate.
- Midpoint and inside-spread prints: unclassified by the conservative base rule.
- Prints outside the NBBO, missing, locked/crossed or otherwise invalid quotes: quarantine or separate diagnostic.
- Complex, late, canceled, out-of-sequence and other trade-condition categories: classify only after pinning the official condition mapping and validating its effective dates.

This is a quote-based aggressor proxy, not a beneficial-owner label and not proof of informed trading. The quote at execution is market context; trade-condition filters and quote validity matter. Do not use a generic tick rule to force a side for ambiguous prints.

A small preregistered feature family, only after all data gates pass:
1. Signed option contract volume.
2. Signed option premium notional.
3. Delta-weighted signed notional using contemporaneous trade delta when valid.
4. Put/call side composition, separately by moneyness and DTE only if contract metadata supports it.
5. Persistence versus reversal after controlling for underlying return, option volume, volatility, liquidity and event calendar.

Do not use the vendor's midpoint classification as ground truth. Reconstruct it from the raw print/NBBO fields and compare as a separate sensitivity only if a licensed vendor field is available.

## 4. Important limitations

- **Trade timestamp is not knowledge time.** quote_datetime is the execution timestamp in U.S. Eastern time to milliseconds. It is not the time our strategy could have downloaded the daily file. Historical backfill must not be backdated to the trade timestamp.
- **First receipt is unproven.** Store actual first-received time, file hash, source filename and later revisions as separate immutable vintages. The general next-day delivery window is not enough for strict PIT.
- **Underlying identity is ticker-only in the documented file.** Require an effective-dated security master with inactive/delisted securities, ticker changes, mergers and share classes. Unresolved identities stay quarantined.
- **Option contract identity is not fully economic from root/expiry/strike/type alone.** Nonstandard roots may end in a digit; adjusted deliverables and contract multipliers must be resolved. Do not equate every root/expiry/strike/type tuple with a standard 100-share contract.
- **Trade conditions are essential.** Pin the exchange-ID and trade-condition mapping files and validate their date/effective semantics before excluding or including any condition. The mapping downloads are separate CSV/XLSX references on the product page.
- **Calcs zero is not necessarily a real zero.** The spec says IV/Greeks default to zero when model inputs are insufficient, the trade is below intrinsic value, or IV exceeds the acceptable upper limit. Keep these as unavailable/model-failure observations, not genuine zero Greeks.
- **Underlying bid/ask zero is a documented no-quote default** for some instruments, especially indices. Preserve missingness.
- **OPRA scope is not options-on-futures or non-U.S. options.** The product page states that full-market orders can still report unavailable dates/symbols; retain all exclusions in the coverage matrix.
- **License and economics remain open.** The product page exposes order options, but no price was obtained and no purchase or vendor contact occurred. Review internal-use, derived-data and redistribution terms before any licensed panel is built.

## 5. Comparison with other Cboe products

| Product | Scope/history | Information | Research role |
|---|---|---|---|
| Option Trades | OPRA-wide; advertised Jan 2012 | Every print, NBBO, optional trade-time IV/Greeks | **First-priority raw-flow reconstruction** |
| Enhanced TBT | C1 only; 2019-10-07 | Side, open/close, capacity, NBBO, execution IDs | Complementary high-quality C1 validation |
| Open-Close | Cboe venues; EOD/interval | Capacity × open/close aggregates | Complementary venue-specific state |
| Option Quotes | OPRA-wide; advertised Jan 2012 | Interval NBBO, volume, optional OI/IV/Greeks | Volatility/liquidity/OI context, not signed flow |
| Option Sentiment | FAQ says Jan 2012; absent from current catalog | Daily signed aggregates, IV/skew/OI/capacity | Park pending orderability confirmation |

Option Trades is not a substitute for TBT's open/close and capacity fields. The two products answer different questions and must be joined only on validated contract/time keys. Option Quotes can supply context but must not be mistaken for transaction flow.

## 6. Point-in-time protocol

1. Download a licensed sample or public sample; hash every raw archive/member before parsing.
2. Record actual retrieval time, source URL, final URL, HTTP Date/Last-Modified/ETag and filename. HTTP metadata are diagnostics, not historical first receipt.
3. Preserve each daily file and correction as a separate immutable vintage.
4. Use the later of actual file receipt and any required mapping/contract-reference receipt as feature knowledge time.
5. For a daily close decision, use only the file actually received before the decision; otherwise use the next tradable session after receipt. Do not infer receipt from quote_datetime.
6. Apply the official trade-condition mapping and quote-quality filters before constructing signed flow.
7. Resolve effective-dated underlying and option-series identity, including adjusted deliverables, corporate actions and delisted names.
8. Measure historical date/security coverage against a broad PIT universe, not only the legacy 335-name list.

## 7. Phase 170 implementation and decision gate

The workflow:
- downloads the public sample URL;
- validates ZIP/CSV integrity and the documented base/optional-Calcs schema;
- validates date/time, contract, trade, NBBO and legacy fields;
- records quote-side buckets only as diagnostics, not as a promoted signal;
- records missing/zero Calcs and underlying quote defaults;
- stores archive/member/header hashes and aggregate counts only;
- uploads the metadata artifact before enforcing the schema gate.

The audit does not retain raw rows, underlying symbols or contract identifiers.

**Admission decision:** Option Trades is the best currently orderable Cboe raw-flow candidate identified in this audit, but it remains **sample/schema feasibility only** until the public sample gate passes and historical first-receipt, revision, licensing, effective-dated identity and universe-coverage gates are completed. No forward-return, bootstrap/LOO, chronological OOS or final-holdout test is authorized yet.

## Official sources reviewed on 2026-11-06

- [Cboe Data Products catalog](https://datashop.cboe.com/data-products)
- [Cboe Option Trades product page](https://datashop.cboe.com/option-trades)
- [Option Trades File Specification v1.3](https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf)
- [Cboe DataShop FAQ](https://datashop.cboe.com/faqs)
- [Option Sentiment Specification v1.4](https://datashop.cboe.com/Documents/Cboe_OptionSentiment_Specs.pdf)
- [Enhanced US Options Trade-by-Trade Execution Detail](https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail)
- [Option Quotes](https://datashop.cboe.com/option-quote-intervals)
