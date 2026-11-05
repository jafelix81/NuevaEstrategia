# Phase 113 — Cboe Enhanced US Options Trade-by-Trade (TBT) sample feasibility

**Date:** 2026-11-05  
**Status:** live public-sample audit triggered  
**Scope:** data feasibility only; no forward returns, alpha test, purchase, subscription or vendor contact.

## Why this source is materially different

Cboe's current DataShop catalog lists Enhanced US Options Trade-by-Trade Execution Detail. Its published v1.1 specification (2026-10-05) provides transaction-level fields not present in the broad OPRA Option Trades file:

- SIDE (Buy/Sell);
- OPEN_CLOSE (Open/Close);
- CAPACITY (MarketMaker, Customer, ProCustomer, BrokerDealer, Firm);
- TRADE_TYPE (auction, floor, complex, routed and other execution classifications);
- EXEC_ID and COMPLEX_EXEC_ID for linkage;
- transaction time, trade date, floor-action time, NBBO and local BBO.

The product is currently C1 only, with BZX, C2 and EDGX listed as future releases. Historical availability starts 2019-10-07. Files are delivered T+1, typically 00:30–01:30 ET the next morning. The spec says historical files are one compressed CSV per trade date and exchange.

This is potentially the most direct public-documentation evidence so far for participant-capacity × buy/sell × open/close behavior. It still does not identify beneficial owners or establish that Customer/ProCustomer/Firm activity is informed. C1 venue coverage is not the whole OPRA market.

## Official references

- Product page: https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail
- TBT File Specification v1.1: https://datashop.cboe.com/documents/TBT_Spec_v1.1.pdf
- Related Cboe Open-Close Volume Summary: https://datashop.cboe.com/cboe-options-open-close-volume-summary

The TBT spec defines TRANSACT_TIME as the time the trade was processed/booked; TRADING_DT as the assigned trade/market date, which may differ from calendar date around midnight due to GTH; FLOOR_ACTION_TS as the time a floor trade was agreed, with a late trade defined as a difference of at least 90 seconds; and EXEC_ID/COMPLEX_EXEC_ID as execution linkage fields. Repeated execution IDs are therefore not automatically duplicate rows.

## Preregistered sample audit

The live workflow downloads only Cboe's public sample and the public TBT v1.1 specification. It recursively inspects ZIP/GZIP members, hashes the source files, parses the published required schema, and reports:

- sample date and underlying/series coverage;
- row counts and exact duplicate rows;
- side, open/close, capacity, trade type, session and trading-segment distributions;
- transaction/trading-date clock parsing and calendar-date differences;
- NBBO/BBO valid, locked, crossed and missing states;
- floor-action lag counts;
- execution-ID and complex-execution-ID repetition/linkage diagnostics.

It will not infer a timezone where the file does not explicitly supply one, equate capacity with investor identity, or use the sample as evidence of market-wide coverage.

## Gates before any economic test

1. Public sample schema and key semantics must pass.
2. Verify actual daily file availability and the historical 2019-10-07 boundary without purchase; a public sample alone does not prove archive completeness.
3. Establish symbol/date coverage for a broad PIT universe, including inactive/delisted underlyings.
4. Reconcile C1 TBT buy/sell/open/close/capacity totals against Cboe C1 Open-Close EOD or intraday aggregates on overlapping dates and series; do not compare TBT to all-venue totals.
5. Establish a conservative T+1 knowledge timestamp and account for late files, corrections and trade-condition semantics.
6. Define features ex ante, including treatment of complex trades, auctions, floor trades, routed trades and provisional/late reports.
7. Only then consider a preregistered incremental test versus frozen LTM/F80 with identical exposure/costs, chronological OOS, bootstrap and issuer LOO.

No purchase, subscription, vendor contact or acceptance of additional terms is authorized. No alpha test is authorized. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
