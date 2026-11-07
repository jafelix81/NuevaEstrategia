# Phase 170 — Cboe Option Trades active-catalog and public-sample PIT audit

**Date:** 2026-11-06  
**Decision:** **OPTION TRADES REMAINS FIRST-PRIORITY RAW-FLOW FEASIBILITY. HEADER SCHEMA PASSES, BUT THE FIRST FULL ROW PARSE FAILED ON ALL 197,158 ROWS. PHASE 170 IS NOT A VALIDATED SAMPLE YET; ROW-LEVEL DIAGNOSTICS ARE BEING ADDED BEFORE ANY PARSER RELAXATION. OPTION SENTIMENT REMAINS PARKED PENDING CURRENT PRODUCT CONFIRMATION.**  
**Scope:** Current DataShop catalog/orderability evidence, official file specification, sample retrieval, schema correction and trade-side design. No paid data, vendor contact, return test or production change.

## 1. Why the source ranking changed

A fresh review of Cboe's live DataShop pages found a material distinction:

- The current [Data Products catalog](https://datashop.cboe.com/data-products) lists Cboe Open-Close, Enhanced US Options Trade-by-Trade Execution Detail, Option EOD Summary, Option Quotes and Option Trades. It does **not** list Option Sentiment.
- The legacy [Option Sentiment route](https://datashop.cboe.com/option-sentiment) redirects to the DataShop home page.
- The current [FAQ](https://datashop.cboe.com/faqs) still lists Option Sentiment history from January 2012, and its v1.4 specification remains online.
- The current [Option Trades product page](https://datashop.cboe.com/option-trades) is a live product detail page with Historical and Subscription purchase choices, All Symbols selection and a public sample link.

This does not prove Option Sentiment has been discontinued; it proves that current orderability is not established by the public catalog. Do not plan a purchase or model dependency around it without written product confirmation.

## 2. Option Trades: current documented data contract

The current product page and [Option Trades specification v1.3](https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf) describe:

- Every options print across the OPRA universe for U.S.-listed stocks, ETFs and indices.
- Both Global Trading Hours and Regular Trading Hours.
- Trade price, size, executing exchange, OPRA sequence number, trade condition and prevailing NBBO at execution.
- Optional point-in-time trade IV and Greeks (Delta, Gamma, Vega, Theta, Rho).
- Daily file delivery, with historical data grouping per day, month or year.
- Options on futures and non-U.S. markets are excluded.
- Exchange ID and Trade Condition ID mapping files are linked separately from the product page.

**Historical-start conflict:** the current Option Trades product page says data are available from January 2012, while the general FAQ history table says January 2010. Both are official Cboe pages currently accessible. Do not silently select one. The exact purchasable start date and per-symbol availability must be verified through the actual order-availability matrix or written confirmation. The script records both claims and leaves the start unresolved.

## 3. Public sample retrieval and first schema finding

The product-page sample endpoint is https://datashop.cboe.com/download/sample/216.

Hosted run [42302934895](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42302934895) successfully downloaded the public ZIP and uploaded metadata artifact [13545021423](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42302934895/artifacts/13545021423).

- Compressed archive: 3,561,778 bytes.
- Archive SHA-256: a02504e156db28b3f007d9d25a534e4c88ffd8d24ac43f3bf84885583a3d10b8.
- Two members, both dated 2026-01-07:
  - UnderlyingOptionsTradesCalcs_2026-01-07.csv: 25 columns.
  - UnderlyingOptionsTrades_2026-01-07.csv: 19 columns.
- Member SHA-256 values are recorded in the metadata artifact.
- HTTP Date was present; ETag and Last-Modified were absent.
- No raw rows, symbols or contract identifiers were persisted.

The first strict schema gate failed because the parser required number_of_exchanges in both files. The official specification labels that field legacy and says it is always zero; the associated regional-exchange quote fields are also legacy and always empty. The public sample omits the number_of_exchanges column entirely. This was an auditor expectation error, not a failed download or evidence that the source lacks trade data.

The corrected parser now treats number_of_exchanges as an optional legacy column, accepts the documented 19-column base layout and 25-column Calcs layout, and records its presence/absence. A blank canceled_trade_condition_id is also treated as an unpopulated legacy field. Optional quote and Calcs blanks are retained as missing; zero IV/Greeks are counted as model-unavailable cases, not valid zero values. Zero trade prices are recorded as a diagnostic rather than used as signed flow. The corrected offline suite covers these cases. Final hosted sample parsing and row-quality results are still pending; the first attempt parsed zero rows because the strict header gate stopped before row iteration.

## 4. Why Option Trades is the best current raw-flow candidate

Option Trades exposes raw prints and the contemporaneous NBBO, allowing a reproducible quote-based aggressor proxy:

- At the contemporaneous NBBO ask: buyer-initiated candidate.
- At the contemporaneous NBBO bid: seller-initiated candidate.
- Midpoint and inside-spread prints: unclassified by the conservative base rule.
- Prints outside the NBBO, missing, locked/crossed or otherwise invalid quotes: quarantine or separate diagnostic.
- Complex, late, canceled, out-of-sequence and other trade-condition categories: classify only after pinning the official condition mapping and validating its effective dates.

Only exact at-ask/at-bid prints are candidate sides in the base rule. A trade above/below the displayed NBBO is not automatically signed; it may reflect stale quotes or special conditions. This is a quote-based aggressor proxy, not beneficial-owner identity and not proof of informed trading.

A small preregistered feature family, only after all data gates pass:
1. Signed option contract volume.
2. Signed option premium notional.
3. Delta-weighted signed notional using contemporaneous trade delta when valid.
4. Put/call side composition, separately by moneyness and DTE only if contract metadata supports it.
5. Persistence versus reversal after controlling for underlying return, option volume, volatility, liquidity and event calendar.

Do not use a generic tick rule to force a side for ambiguous prints. Do not treat customer/professional/dealer labels as beneficial-owner identity; Option Trades does not include participant capacity or open/close classification.

## 5. Point-in-time and identity limitations

- **Trade timestamp is not knowledge time.** quote_datetime is the execution timestamp in U.S. Eastern time to milliseconds. It is not when our strategy could download the daily file.
- **Daily delivery is variable.** The general DataShop FAQ says daily trade-date files are normally available the following day between 00:05 and 03:00 ET, but delays can push delivery past the next market open. This is a general SFTP schedule, not an Option Trades historical first-receipt ledger. Capture actual first receipt and file hash; use only files received before the strategy decision.
- **SFTP retention is only 30 days** after order completion. Any licensed feed must be archived immediately as received, with immutable correction/replacement vintages.
- **Underlying identity is ticker-only.** Require an effective-dated security master with inactive/delisted securities, ticker changes, mergers and share classes. Unresolved identities stay quarantined.
- **Option contract identity is not fully economic from root/expiry/strike/type alone.** The FAQ says roots containing digits identify non-standard adjusted contracts after splits, special dividends, spin-offs or mergers, with deliverables other than the standard 100 shares. Resolve adjusted deliverables and multipliers; do not equate every root/expiry/strike/type tuple with a standard contract.
- **Trade conditions are essential.** Pin the linked exchange-ID CSV and Trade Condition ID XLSX, hash each mapping version, and establish effective dates before excluding or including any condition.
- **Calcs zero is not necessarily a real zero.** The specification says IV/Greeks default to zero when model inputs are insufficient, the trade is below intrinsic value or IV exceeds the model's upper limit. Keep these as unavailable/model-failure observations, not genuine zero Greeks.
- **Underlying bid/ask zero is a documented no-quote default** for some instruments, especially indices and OTC names. Preserve missingness. Certain index values also depend on Cboe Global Indices licensing.
- **OPRA scope is not options-on-futures or non-U.S. options.** The order UI warns that some symbols/dates may be unavailable even in an All Symbols selection; retain the exclusions in the coverage matrix.
- **License and economics remain open.** The product page exposes order choices, but no price was obtained and no purchase or vendor contact occurred. Review internal-use, derived-data and redistribution terms before building a licensed panel.

## 6. Comparison with other Cboe products

| Product | Scope/history | Information | Research role |
|---|---|---|---|
| Option Trades | OPRA-wide; product page says Jan 2012, FAQ says Jan 2010 | Every print, NBBO, optional trade-time IV/Greeks | **First-priority raw-flow reconstruction** |
| Enhanced TBT | C1 only; 2019-10-07 | Side, open/close, capacity, NBBO, execution IDs | Complementary C1 validation |
| Open-Close | Cboe venues; EOD/interval | Capacity × open/close aggregates | Complementary venue-specific state |
| Option Quotes | OPRA-wide; product page says Jan 2012, FAQ says Jan 2010 | 1-minute/custom intervals, NBBO, optional OI/IV/Greeks | Volatility/liquidity/OI context, not signed flow |
| Option Sentiment | FAQ says Jan 2012; absent from current catalog | Daily signed aggregates, IV/skew/OI/capacity | Park pending orderability confirmation |

Option Trades is not a substitute for TBT's open/close and capacity fields. The two products answer different questions and must be joined only on validated contract/time keys. Option Quotes can supply context but must not be mistaken for transaction flow; its product page says intraday snapshots are delayed 15 minutes and daily files are delivered overnight/early the following day.

## 7. Point-in-time protocol and admission decision

1. Download a licensed sample or public sample; hash every raw archive/member before parsing.
2. Record actual retrieval time, source URL, final URL, HTTP Date/Last-Modified/ETag and filename. HTTP metadata are diagnostics, not historical first receipt.
3. Preserve each daily file and correction as a separate immutable vintage.
4. Use the later of actual file receipt and any required mapping/contract-reference receipt as feature knowledge time.
5. For a daily close decision, use only the file actually received before the decision; otherwise defer to the next tradable decision after receipt. Do not infer receipt from quote_datetime.
6. Apply the official trade-condition mapping and quote-quality filters before constructing signed flow.
7. Resolve effective-dated underlying and option-series identity, including adjusted deliverables, corporate actions and delisted names.
8. Measure historical date/security coverage against a broad PIT universe, not only the legacy 335-name list.

**Admission decision:** Option Trades is the best currently listed Cboe raw-flow candidate identified in this audit. The public sample download works, but final schema/row-quality validation, historical first-receipt/revision history, exact earliest date, licensing/price, effective-dated identity and universe coverage remain gates. No forward-return, bootstrap/LOO, chronological OOS or final-holdout test is authorized yet.

## Official sources reviewed on 2026-11-06

- [Cboe Data Products catalog](https://datashop.cboe.com/data-products)
- [Cboe Option Trades product page](https://datashop.cboe.com/option-trades)
- [Option Trades File Specification v1.3](https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf)
- [Cboe DataShop FAQ](https://datashop.cboe.com/faqs)
- [Option Sentiment Specification v1.4](https://datashop.cboe.com/Documents/Cboe_OptionSentiment_Specs.pdf)
- [Enhanced US Options Trade-by-Trade Execution Detail](https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail)
- [Option Quotes](https://datashop.cboe.com/option-quote-intervals)


## 2026-11-06 — hosted row-parser diagnostic correction

Run [42303680951](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42303680951) confirmed that the corrected 25-column and 19-column headers pass, but all 98,579 rows in each member were marked invalid. Because the parser did not preserve field-level error reasons, the prior artifact cannot identify the cause. Zero contracts, underlyings, trade keys or volume were accumulated; the 98,579 duplicate-key count per member is therefore a consequence of zero parsed keys, not evidence of actual duplicate trades.

The parser now records only non-identifying diagnostics: row field-count distribution, extra/short-field counts, sanitized parser error codes, and the first error code/field name. It does not store row values, symbols, contract identifiers or raw trades. The workflow treats a completed diagnostic with a failed row gate as a successful diagnostic run, not as a passing sample. The explicit status `DIAGNOSTIC_COMPLETE_ROW_GATE_FAIL` means schema passed but row-level validity did not; it is not alpha admission or data validation.

Added regression tests for extra CSV fields, short rows, value-free parse errors and the diagnostic-vs-pass status. The next decision depends on the actual error distribution from the hosted sample. No date/number parser has been loosened without evidence.


## 2026-11-07 — hosted row-diagnostic result and date-shape follow-up

- Final-head diagnostic run [42316681940](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42316681940) passed compile, **32/32 offline tests**, public sample download, metadata-only artifact upload and the diagnostic-status gate. Artifact [13550443768](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42316681940/artifacts/13550443768), archive SHA-256 unchanged at `a02504e156db28b3f007d9d25a534e4c88ffd8d24ac43f3bf84885583a3d10b8`.
- Both members still have valid headers and exact row widths: 98,579 rows × 25 columns (Calcs) and 98,579 × 19 columns (no Calcs); no extra or short field rows.
- **All 197,158 rows fail first at `market_date`**: `invalid_market_date` = 98,579 in each member. The parser therefore has zero parsed contracts, underlyings and trade keys. This is a date-format mismatch, not a failed download or a header-schema failure.
- The artifact's `duplicate_trade_key_rows=98,579` per member is mechanically wrong because the prior formula used total rows minus zero parsed keys. It is not evidence of duplicates. The staged correction counts duplicates only among successfully parsed trade keys.
- The next diagnostic revision adds value-free `market_date` and `quote_datetime` shape distributions, field-specific first-error labels and valid-key denominators. It does not store raw date strings, symbols, contracts or trades. Date parsing remains strict until the actual shape is observed.
- Current status remains `DIAGNOSTIC_COMPLETE_ROW_GATE_FAIL`; no sample admission, flow feature or alpha test is authorized.

## Phase 149 — latest OpenFIGI rerun adjudication (2026-11-07)

- Run [42316322780](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42316322780) and identical-input final-head rerun [42316681966](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42316681966) both completed successfully with 553 CUSIPs, 437 exact 9-character primary mappings, 116 primary no-matches, 7 unique 8-character fallback recoveries, 109 remaining no-matches, zero API errors and one cross-CUSIP shareClassFIGI pair (two CUSIPs).
- The preceding run [42302934940](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42302934940) had 438 primary mappings and 6 fallback recoveries, with the same 444/553 total. The exact-vs-fallback split moved by one across current API snapshots; preserve request/response hashes and retrieval timestamps, and do not treat OpenFIGI's current response as an immutable historical security master.
- The 109 unmatched CUSIPs and lack of effective dates remain unresolved. No ticker or issuer mapping may be backdated; Phase 149 remains a manual identity cross-check only.
