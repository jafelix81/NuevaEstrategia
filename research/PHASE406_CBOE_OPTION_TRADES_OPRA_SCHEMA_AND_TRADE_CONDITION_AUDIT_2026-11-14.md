# Phase 406 — Cboe Option Trades / OPRA schema, trade-condition and PIT feasibility audit

**Audit date:** 2026-11-14 UTC  
**Disposition:** STRONG CONDITIONAL INDEPENDENT RAW-OPRA RECONSTRUCTION / VALIDATION SOURCE; NOT PIT-ADMITTED; NO SAMPLE BYTES OR ECONOMIC TEST.  
**Scope:** Official Cboe product page and v1.3 file specification, plus published academic evidence on OPRA trade-condition flags. The public sample link was located, but its ZIP bytes could not be retrieved in this audit environment; no sample rows were inspected.

## Executive decision

Cboe Option Trades materially improves the options-source map. Cboe describes a trade-by-trade file covering the OPRA universe of U.S.-listed stock, ETF and index options, with history from January 2012. The v1.3 specification exposes trade price/size, exchange, OPRA sequence number, millisecond Eastern trade time, trade condition, and the prevailing NBBO prices/sizes at the trade. Optional Calcs add trade-time IV and Greeks.

This makes the product a strong candidate for independent reconstruction and validation of signed options flow, and for separating single-leg auction/cross/floor executions from complex and stock-option trades. It does **not** identify beneficial owners or verified institutional/customer capacity. The special OPRA trade-type flags used in the academic retail-flow literature were implemented on 2019-11-04, so the broad 2012 history does not imply that this participant-behavior segmentation exists throughout the entire history.

No sample, subscription, vendor contact, trial, purchase, price quote, business-use license or data acquisition occurred. No alpha test is authorized.

## 1. Product coverage and delivery

Official Cboe product page:
- https://datashop.cboe.com/option-trades
- Public sample link shown on the product page: https://datashop.cboe.com/download/sample/216
- Historical availability advertised from 2012-01 to present.
- Daily file delivery; historical orders can be grouped by day, month or year.
- Product description claims every print on every option traded on U.S. exchanges across the OPRA universe.
- Coverage includes U.S.-listed stocks, ETFs and indices; options on futures and non-U.S. markets are excluded.
- GTH and RTH trades are included in file specification v1.3.
- Intraday delivery requires a separate contact with Cboe.

The sample link is publicly visible, but the ZIP response was not retrievable by the audit environment. Treat the sample as available for a human/browser or licensed download, not as inspected evidence.

## 2. File schema — v1.3

Official specification: https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf

| Field | Meaning | Research implication |
|---|---|---|
| underlying_symbol | Underlying stock/ETF/index | Must be joined through an effective-dated security master; dot-form share classes are used |
| market_date | Trade market date | Session/calendar key |
| quote_datetime | Eastern trade timestamp to milliseconds | Intraday ordering; not a first-public-delivery timestamp |
| sequence_number | OPRA trade sequence | Preserve for ordering/deduplication and correction diagnostics |
| root, expiration, strike, option_type | Option-series identity | Contract-level reconstruction |
| exchange_id | Executing options exchange | Venue segmentation |
| trade_size, trade_price | Executed quantity and price | Notional and signed-volume features |
| trade_condition_id | Trade/sale condition | Separate regular, auction, cross, floor, complex, late and cancellation-related records |
| best_bid_size, best_bid, best_ask, best_ask_size | Prevailing NBBO at trade | Quote-rule/midpoint classification and spread-quality filters |
| trade_iv, trade_delta/gamma/vega/theta/rho | Optional Calcs | Trade-time risk measures; zero can mean unavailable/invalid, not a true zero |
| underlying_bid, underlying_ask | Underlying quote | Defaults to zero when unavailable; zero is missing, not a valid quote |

Important schema limitations:
- The file provides the NBBO prevailing at trade time, but does not list a separate NBBO quote-event timestamp. Quote age cannot be measured from this file alone.
- The legacy `canceled_trade_condition_id` is always 0; the legacy `number_of_exchanges` is always 0 and regional quote fields are empty.
- Cboe states trade IV/Greeks may default to 0 when model inputs are insufficient, the trade is below intrinsic value, or computed IV exceeds the allowed limit. Preserve explicit missing/invalid flags; never interpret zero as a valid IV or Greek.
- Underlying bid/ask may be zero for indices and some OTC-market names. Do not use zero as a real underlying quote.
- Exact correction/bust replay and original-trade linkage remain unverified without sample bytes and the full trade-condition mapping workbook.

## 3. OPRA trade-condition regimes and participant-behavior hypotheses

The academic paper by Bryzgalova, Pavlova and Sikorskaya, *Retail Trading in Options and the Rise of the Big Three Wholesalers* (2022), reports OPRA trade types implemented on 2019-11-04 and their LiveVol condition IDs. It identifies:
- 114 = SLAN, single-leg auction non-ISO;
- 115 = SLAI, single-leg auction ISO;
- 116 = SLCN, single-leg cross non-ISO;
- 117 = SCLI, single-leg cross ISO;
- 118 = SLFT, single-leg floor;
- 119–126 = multi-leg electronic, auction, cross, floor and against-single-leg categories;
- 127–133 = stock-option electronic, auction, cross, floor and proprietary multi-leg categories;
- 40–43 = cancellation-related OPRA condition types;
- 2/13 = out-of-sequence/late reports; 6/7 = late opening reports; 21 = reopening; 95 = ISO.

The paper uses SLAN as a proxy for single-leg non-ISO price-improvement-mechanism flow associated with retail broker/wholesaler execution. It is **not** a direct beneficial-owner label and does not capture all retail trading. The paper also finds that naive small-trade filters can misclassify institutional trades split into small prints.

Source: https://www.aeaweb.org/conference/2023/program/paper/5N8FE6RZ (see Internet Appendix A.2, Table A2).

**Critical economic interpretation:** the paper reports that retail options imbalances can predict next-day underlying returns, but argues the short-horizon effect is more consistent with intermediary hedging demand/price pressure than with informed retail trading. It also reports aggregate retail-option losses after trading costs. This is exactly why a raw positive return association must not be labeled “smart money.”

## 4. Pre-registered reconstruction design if a lawful sample is later obtained

Keep the source decomposition explicit rather than creating one undifferentiated “institutional flow” variable:

1. **Single-leg regular flow:** exclude complex and stock-option combo conditions; classify aggressor conservatively using trade price versus contemporaneous NBBO midpoint. Midpoint/ambiguous trades remain unclassified or separate.
2. **Auction/cross/floor controls:** separately aggregate SLAN, SLAI, SLCN, SCLI and SLFT. Treat SLAN as a retail/wholesaler-auction proxy, not customer identity.
3. **Complex and stock-option flow:** retain separate buckets (119–133) because a leg-level quote-rule sign can misrepresent a package hedge or spread.
4. **Cancellation/late regime:** quarantine 40–43 and separately audit late/out-of-sequence/opening conditions. Do not count a cancellation record as fresh directional volume. Establish whether and how the original print is removed/replaced before building net volume.
5. **Quote quality:** quarantine zero/negative/crossed NBBO, nonpositive trade price/size, trade prints outside defensible quote bounds, and unavailable underlying quotes. The file lacks quote-event timestamps, so quote-age tests require an independent quote feed.
6. **Contract identity:** preserve root, expiration, strike, right, exchange, market date and sequence; handle adjusted deliverables, corporate actions, symbol changes, share classes and inactive/delisted underlyings.
7. **Time regime:** do not backcast OPRA trade-type segmentation before 2019-11-04. The 2012–2019 data may support basic trade/NBBO reconstruction only, subject to condition-map/version proof.
8. **PIT delivery:** daily delivery is documented, but exact first-delivery and correction-vintage timestamps are not. Historical backfill is not a contemporaneously available signal. Capture actual first receipt and raw-file hash prospectively before any daily feature is eligible.

## 5. Role relative to other options sources

| Source | Best role | Main limitation |
|---|---|---|
| OptionMetrics IvyDB TradeFlow | Primary conditional ready-made signed-flow panel | Historical classifier vintage/first-delivery and license gates remain open |
| Cboe Option Trades | Independent raw-OPRA reconstruction and validation | No participant capacity/beneficial owner; no quote-event timestamp; sample not inspected |
| ThetaData Pro | Second raw-OPRA reconstruction with trade/quote pairing | Historical delivery/correction vintage and inactive-underlying coverage unverified |
| Cboe Open-Close | Complementary capacity × side × open/close on BZX/C1/C2/EDGX | Four-venue scope, not consolidated OPRA |
| Cboe PITCH/TBT | Deeper venue microstructure/queue and execution analysis | More complex, proprietary and potentially expensive |

Cboe Option Trades and ThetaData are independent vendor implementations of substantially the same OPRA market-data source, not independent economic sources. Agreement between them validates reconstruction, not the hypothesis itself.

## 6. Admission gates still closed

Before any economic test:
1. Obtain and hash a representative sample ZIP and confirm exact CSV schema/encoding, row grain, file completeness and daily coverage.
2. Obtain the official Cboe Trade Condition ID workbook and reconcile it to the academic LiveVol mapping; do not rely solely on a third-party mapping.
3. Test cancellations/busts/corrections, sequence ordering, duplicates, late reports and complex-leg behavior.
4. Measure coverage across the frozen diagnostic universe and historical inactive/delisted underlyings, including adjusted contracts and corporate actions.
5. Establish daily first-delivery and correction-vintage policy prospectively; preserve raw bytes and receipt timestamps.
6. Confirm commercial/business-use rights and cost before any acquisition.
7. Freeze the feature definitions before forward returns are opened.

No return test, OOS, bootstrap, LOO, holdout or production use is authorized. No Smart Money signal is admitted.

## Decision

**Retain Cboe Option Trades as a strong conditional raw-OPRA validation source, not as an institutional-identity feed.** The most useful incremental contribution is its OPRA trade-condition field: it allows the research to separate single-leg price-improvement/auction activity from complex and stock-option package activity, helping distinguish information from retail demand and dealer-hedging price pressure. The data-feasibility gate remains incomplete until sample bytes, delivery-vintage and licensing are verified.

## References

- Cboe Option Trades product: https://datashop.cboe.com/option-trades
- Cboe Option Trades file specification v1.3: https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf
- Bryzgalova, Pavlova & Sikorskaya (2022), *Retail Trading in Options and the Rise of the Big Three Wholesalers*: https://www.aeaweb.org/conference/2023/program/paper/5N8FE6RZ
- ThetaData v3 trade_quote documentation: https://www.thetadata.net/docs/operations/option_history_trade_quote.html
