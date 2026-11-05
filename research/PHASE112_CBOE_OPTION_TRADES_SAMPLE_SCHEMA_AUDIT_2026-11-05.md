# Phase 112 — Cboe Option Trades: public sample schema and market-coverage audit

**Date:** 2026-11-05  
**Status:** live sample audit pending  
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
