# Phase 174 — Cboe Option Quotes / Option Quote Intervals public-sample and PIT feasibility

**Date:** 2026-11-07  
**Decision:** promote Option Quotes to a conditional OPRA-wide interval/IV/OI context candidate; do not admit it to predictive research until the public sample, first-receipt vintages, historical schema regimes, universe coverage and licensing are verified.

## 1. Source identification and historical coverage

Official sources:

- Product page: https://datashop.cboe.com/option-quote-intervals
- File specification v1.1: https://datashop.cboe.com/documents/Option_Quotes_Layout.pdf
- DataShop FAQ: https://datashop.cboe.com/faqs
- 2020 product-replacement notice: https://datashop.cboe.com/data-product-replacement-option-intervals-combines-nbbo-bbo-quotes-calcs-into-one-product
- 2022 regional-BBO deprecation notice: https://datashop.cboe.com/data-product-update-regional-bbo-by-exchange-deprecated

The current catalog calls the product Option Quotes; the page URL and descriptive text use Option Quote Intervals. It provides 1-minute or custom N-minute summaries for listed U.S. stock, ETF and index options disseminated over OPRA. Options on futures and non-U.S. markets are excluded.

The product page advertises historical availability from **January 2012**, while the FAQ table says **January 2010**. Use January 2012 as the conservative history floor until Cboe resolves the discrepancy. Neither statement establishes continuous series coverage, inactive/delisted-underlying coverage or availability of every requested symbol on every date.

## 2. Information content and temporal semantics

The v1.1 specification defines:

- NBBO bid/ask and size as a snapshot at the interval timestamp.
- quote_datetime as the **end of interval** timestamp in U.S. Eastern wall-clock time (yyyy-mm-dd hh:mm:ss).
- OHLC and trade volume as activity **since the prior interval record through the current timestamp**; they are interval increments, not cumulative daily values.
- Optional Calcs: active underlying price, implied volatility and Greeks.
- Optional open interest as OCC **start-of-day** OI.

The DataShop FAQ separately confirms that OI is the previous night's OCC EOD OI at the start of the trading day and remains static through that session. Therefore, intraday rows must not be interpreted as intraday OI updates or new opening flow. Any ΔOI between dates is a change between consecutive start-of-day OCC snapshots.

The source is not signed flow: it does not identify aggressor side, participant capacity or beneficial owner. It can supply option-market context (NBBO, interval volume, IV/Greeks and SOD OI) to complement, not replace, Open-Close or a validated signed-flow source.

## 3. Delivery and point-in-time constraints

- Intraday subscription files are described as delayed by 15 minutes after each snapshot.
- Daily files are delivered overnight/early morning the following day. The FAQ says typical SFTP upload is 00:05–03:00 ET, but delays can push the prior day's file past the next market open.
- SFTP retention is 30 days.
- The product page does not provide a historical first-receipt ledger or immutable preliminary/final/correction vintages. A scheduled delivery window is not proof of actual availability.

Strict PIT therefore requires an archived first-received timestamp, exact file hash/version, correction lineage, exchange calendar and effective-dated contract/underlying identity. Historical features without those facts remain PIT-ineligible. For intraday use, knowledge time must be at least the later of the interval end and actual 15-minute-delayed file receipt; for overnight use, actual file receipt controls.

## 4. Structural breaks and field caveats

- **July 10, 2020:** Cboe announced that Option Intervals combined NBBO, BBO Quotes and Calcs into a replacement product, while legacy Option Quotes Intervals variants were removed from the catalog. Historical files may therefore span a format/product-regime boundary; a single parser must not be assumed valid back to 2012 without versioned sample checks.
- **September 28, 2022:** regional BBO by exchange was deprecated for new orders; legacy headers may remain but fields are zero/empty. Regional-BBO fields must not be treated as populated venue depth.
- **June 22, 2026:** NBBO bid/ask size semantics changed. Before that date, size reflected the latest price and size in the interval; after that date, size is captured at the time of the most recent price change. Size-derived features need a regime flag and must not be compared naively across the boundary.
- The specification marks implied_underlying_price deprecated and defaulted to zero.
- IV is zero when model inputs are insufficient, the option price is below intrinsic value or IV exceeds an acceptable limit. The FAQ notes midpoint-based IV has no fallback, so zero IV can coexist with non-zero Greeks. Zero IV is unavailable for volatility features, not a valid 0% volatility observation.
- Underlying bid/ask may be zero when no source quote is disseminated. Index underlying fields are generally absent; ^SPX/^OEX underlying quotes require the relevant CGIF license.
- A root containing a digit denotes a non-standard adjusted option. Effective-dated deliverables and multipliers are required; root alone is not a sufficient contract identity.

## 5. Operational economics

Cboe's published annual disk-space estimates for all symbols with Calcs are approximately:

| Interval | Compressed | Uncompressed |
|---|---:|---:|
| 1 minute | 2,300 GB | 16,300 GB |
| 15 minutes | 155 GB | 1,100 GB |
| 60 minutes | 40 GB | 285 GB |

Without Calcs, the 1-minute estimate is still approximately 1,200 GB compressed per year. These are data-volume estimates, not prices. The product page exposes a purchase calculator, but no actual price was confirmed in this audit.

For a daily-to-monthly swing strategy, 1-minute all-market history is not justified at this stage. If the source survives other gates, begin with a representative 15-minute or 60-minute sample and compare its incremental information against a simpler 390-minute/EOD snapshot before considering full-market 1-minute data.

Early-close handling is also required: 390/405-minute subscription files may still be delivered at 16:00/16:15 ET while reflecting the actual 13:00/13:15 close, depending on symbol. Use the official exchange calendar and actual interval timestamp, not the nominal filename/delivery time.

## 6. Public sample audit and admission decision

The public sample is linked from the current product page at https://datashop.cboe.com/download/sample/215. Phase 174 adds a hosted downloader and metadata-only auditor. It records schema, row, timestamp, contract-key, duplicate, interval, quote-crossing, zero-IV/Greek, zero-OI/volume and within-session SOD-OI consistency diagnostics. It does not persist raw rows, underlying symbols, option roots, strikes, expirations or contract keys.

The hosted sample result is pending at report creation. A schema pass on one demonstration sample will establish parser compatibility only; it will not establish historical coverage or PIT.

| Gate | Status |
|---|---|
| Product exists in current catalog | PASS |
| Product-page historical floor | CONDITIONAL: Jan 2012; FAQ says Jan 2010 |
| Documented interval timestamp and OHLC/volume semantics | RESOLVED |
| OCC SOD OI semantics | RESOLVED |
| Public sample schema | PENDING HOSTED AUDIT |
| 2012–2020 format bridge | NOT TESTED |
| 2022 regional-BBO regime | DOCUMENTED; historical field population not tested |
| June 22, 2026 size regime | DOCUMENTED; sample coverage across boundary not tested |
| Broad PIT / inactive-name coverage | NOT TESTED |
| Historical first receipt and correction vintages | BLOCKED |
| Exact price / internal-use license | NOT CONFIRMED |
| Predictive / incremental alpha | NOT TESTED |

**Decision:** retain Option Quotes as a conditional full-OPRA interval/IV/OI context candidate. Do not build a predictive panel or run forward-return tests until sample/schema compatibility, historical coverage, first-receipt vintages, contract identity and licensing pass. No vendor contact, purchase, alpha test, bootstrap/LOO, chronological OOS, final-holdout use or production change.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
