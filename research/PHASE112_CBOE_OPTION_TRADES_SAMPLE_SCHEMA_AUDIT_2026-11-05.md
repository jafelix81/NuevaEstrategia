# Phase 112 — Cboe Option Trades: public sample schema and market-coverage audit

**Date:** 2026-11-05  
**Status:** public sample schema passed; sample timestamp representation does not match published specification  
**Scope:** data feasibility only; no forward returns, no alpha test, no purchase or vendor contact.

## Why this candidate is now prioritized

Cboe Option Trades is currently listed in DataShop and has a public sample-download link. The current product page describes a daily trade-by-trade feed across the entire OPRA universe, with trade price/size, executing exchange and prevailing NBBO at the time of each trade. The page lists historical data from January 2012 to present and supports all symbols or selected symbols.

This is a stronger independent options-flow candidate than the parked OCC account-type file because it provides trade-level price/size and contemporaneous NBBO across U.S. listed stock, ETF and index options. It is not itself a signed-flow signal: trade direction must be reconstructed conservatively from NBBO and trade conditions.

## Official references

- Product page: https://datashop.cboe.com/option-trades
- File specification v1.3: https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf
- Exchange ID mapping: https://datashop.cboe.com/documents/livevol_exchange_ids.csv
- Trade condition mapping: https://datashop.cboe.com/documents/livevol_trade_condition_ids.xlsx
- Cboe DataShop FAQ: https://datashop.cboe.com/faqs

The v1.3 specification defines:
- Underlying symbol, market date, Eastern trade timestamp to milliseconds, OPRA sequence number;
- option root, expiration, strike, call/put;
- executing exchange, trade size, trade price, trade-condition ID;
- prevailing NBB/NBO prices and sizes at trade time;
- optional trade-time IV and Greeks when the Calcs option is selected;
- underlying bid/ask, which may be zero for instruments without a disseminated underlying quote;
- legacy cancelled-condition and regional-quote fields that are always zero/empty.

The product page says the feed covers U.S.-listed stocks, ETFs and indices disseminated over OPRA, including all U.S. options exchanges; options on futures and non-U.S. markets are excluded. It also says Global Trading Hours trades are included.

## Point-in-time policy

Cboe's FAQ says daily files for a trade date are normally delivered the following day between 00:05 and 03:00 U.S. Eastern, but can be delayed until after the next market open. A conservative research availability rule is therefore the next regular session, with a further one-session delay sensitivity. Do not assume that the historical file's present-day delivery behavior proves every historical release timestamp.

No midpoint/quote classifier will be called “true aggressor side” until trade-condition exclusions, locked/crossed/zero NBBO, complex prints, late reports and corrections are handled. For a first-pass classifier:
- at/above valid NBO: buyer-initiated candidate;
- at/below valid NBB: seller-initiated candidate;
- inside spread, midpoint, invalid/crossed/zero NBBO: unclassified;
- exclude or separately model trade conditions after the official mapping is audited.

This phase only measures sample structure and NBBO quality; it does not classify flow for a return test.

## Live sample audit

The hosted audit downloads the public sample ZIP and the official exchange/condition mapping files, hashes them, extracts CSVs, checks required columns, parses timestamps and numeric fields, and reports:
- file names, sizes, hashes, row counts and market-date range;
- unique underlyings, option roots/series, exchange IDs and trade-condition IDs;
- sequence-key duplicates;
- invalid sizes/prices/strikes/Greeks;
- valid, zero, locked and crossed NBBO counts;
- trade-price location relative to valid NBBO (descriptive only);
- optional Calcs-field coverage.

A public sample can validate schema and basic quote/condition quality, but it does not establish full-market historical coverage, ticker/date availability, delisted-name coverage, file-size/cost feasibility or historical methodology continuity.

## Required gates before any purchase or alpha test

1. Sample schema and quote-quality audit must pass.
2. Compare Cboe sample rows against independent OPRA data on an overlapping date (Databento TCBBO since March 2023) using sequence/trade keys where available; measure trade/quote match rates and differences.
3. Audit trade-condition mappings and define exclusions before aggressor-side reconstruction.
4. Establish symbol/date coverage and missingness for the broad PIT universe, including inactive/delisted securities.
5. Verify historical start date and methodology continuity; distinguish product-page Jan 2012 from older FAQ references.
6. Obtain a price estimate only if needed; no purchase or vendor contact without explicit user authorization.
7. Preregister flow features and compare incremental information versus frozen LTM/F80 under identical exposure/costs, chronological OOS, bootstrap and issuer LOO.

No raw sample or derived data will be redistributed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## Hosted execution

The guarded sample audit has been triggered. It downloads only the public sample and public reference mappings; it does not add a product to cart, purchase data, contact Cboe or authenticate to a paid account.


The first workflow attempt stopped at the offline tests because the fixture's 1.05 trade price was exactly the NBBO midpoint (1.00/1.10), while the test expected the generic inside-spread bucket. The parser correctly classified it as exact_midpoint. The test was corrected and a new run triggered; no live download occurred in the failed attempt.


## First live attempt — run 42021426883

The public sample ZIP downloaded successfully (HTTP 200, 3,561,778 bytes, SHA-256 a02504e156db28b3f007d9d25a534e4c88ffd8d24ac43f3bf84885583a3d10b8). Both reference mappings also downloaded successfully: exchange IDs (1,703 bytes) and trade-condition IDs (26,854 bytes). The sample archive did not expose a top-level CSV to the initial parser, so the schema gate remained incomplete; no live data conclusion was drawn.

The parser has been extended to inspect nested ZIP/GZIP members and identify CSV payloads by their header, not merely by filename extension. Offline tests were corrected and the live audit is being retried. The first run did not fail because of Cboe data; it failed to recognize the sample's archive structure.


## Nested sample structure and parser correction

The second attempt identified two nested ZIP variants for the same sample date, 2026-01-07:
- Calcs included: nested ZIP 2,092,490 bytes; CSV 11,287,115 bytes; 74,999 data records.
- Calcs excluded: nested ZIP 1,471,241 bytes; CSV 7,923,505 bytes; 74,999 data records.

These are alternative schema variants for the same trade date, not independent trade populations and must not be added together. The current sample omits the legacy number_of_exchanges field described in the v1.3 PDF; the parser no longer requires that legacy field and now accepts ISO-formatted trade timestamps. A third run will validate the actual records and compare sequence-key hashes between the two variants.


## Sample schema discrepancy discovered

The nested CSVs expose two deviations from the published v1.3 layout:
- market_date is formatted as M/D/YYYY (for example, 1/7/2026), not yyyy-mm-dd;
- quote_datetime is represented in the sample as a compact two-component clock string (for example, 21:30.4), not the documented full YYYY-MM-DD HH:MM:SS.000 timestamp.

The parser now preserves and classifies these values without inventing a timezone or timestamp interpretation. This is a material schema/version issue: daily market-date research may still be feasible, but intraday sequencing/time-of-day analysis is not approved until the representation is explained or independently validated. OPRA sequence_number may provide an ordering key, but that too must be tested rather than assumed.


The next offline test attempt exposed a missing `re` import in the new timestamp-format classifier; the parser was corrected. The live sample was not downloaded in that failed attempt. A fresh run is now triggered.


The first sample-style timestamp test initially retained the old date prefix and therefore did not reproduce the actual time-only field. The fixture was corrected to the exact sample representation (market_date M/D/YYYY; quote_datetime HH:MM.fraction), and the next live audit is triggered. No live download occurred in the failed test run.


## Sample rows parsed — mapping and clock audit pending

The corrected parser now recognizes the two nested CSV variants and the current sample's M/D/YYYY market date and compact quote-clock field. The next run will also inspect the official exchange-ID CSV and trade-condition workbook, report the observed ID-to-description mappings, and measure whether the compact clock candidate is monotonic with OPRA sequence_number. No time-zone or clock semantics will be assumed from the compact field.


## Final hosted result — run 42022615770

The run completed successfully on 2026-11-05. All 11 offline tests passed. The public sample (HTTP 200; 3,561,778 bytes; SHA-256 a02504e156db28b3f007d9d25a534e4c88ffd8d24ac43f3bf84885583a3d10b8) contained two nested CSV variants for 2026-01-07:

- Calcs included: 74,999 rows, 11,287,115 bytes;
- Calcs excluded: 74,999 rows, 7,923,505 bytes.

The two variants have identical row counts and identical sequence-key hashes. They are alternate schema variants of the same sample population and must not be added together. The sample contains one underlying (AAPL), one root and 308 option series; this is not a full-market coverage test.

Both variants passed required-field, numeric, quote-state and duplicate-sequence checks. Across 74,999 rows:
- 74,218 valid NBBO, 625 locked, 5 crossed and 151 zero/missing;
- 24,765 trades at/above ask, 27,952 at/below bid, 8,739 exact midpoint and 12,762 inside the spread; these are descriptive locations, not yet validated aggressor-side labels;
- 15 observed trade-condition IDs all map to the downloaded official LiveVol condition workbook; 18 exchange IDs all map to the official exchange list;
- zero duplicate sequence keys.

**Critical schema discrepancy:** all 74,999 sample rows use a two-component quote_datetime such as 21:30.4. The published v1.3 specification requires the full trade date and U.S. Eastern time to milliseconds (YYYY-MM-DD hh:mm:ss.000). The sample clock is not interpretable from the available documentation and must not be converted to a time-of-day or used for intraday sequencing. The earlier adjacent-row sequence/clock nonmonotonic counter is not a valid test because file row order is not an established time or sequence order; it is not an acceptance metric.

The sample therefore passes structural schema/quote checks but fails the documented timestamp-conformance gate. Retain Option Trades only as a conditional daily trade/quote/IV context source until Cboe explains the sample discrepancy or a new sample conforms to the specification. Do not use it for signed flow or intraday event studies.

Artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42022615770/artifacts/13412861022  
Report decision: sample schema/quote-quality PASS; timestamp conformance FAIL/UNRESOLVED; broad market coverage not established; no alpha test.
