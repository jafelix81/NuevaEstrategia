# Phase 113 — Cboe Enhanced US Options Trade-by-Trade (TBT) sample feasibility

**Date:** 2026-11-05  
**Status:** sample parser passed; semantic convention flags remain unresolved  
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


The parser/workflow were revised after run 42023567791 to retain convention exceptions, add cross-tabs and exception-row samples, and always upload the raw public sample artifact. The next hosted run will distinguish successful file parsing from unresolved semantic conventions.


## Final hosted sample audit — run 42023896730

The corrected workflow completed successfully. All 9 offline tests passed; the public sample and official v1.1 PDF downloaded with HTTP 200; the raw ZIP and JSON artifact were retained.

- Artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42023896730/artifacts/13413280759
- Sample ZIP: 3,807,739 bytes; SHA-256 6c99e69e43d259e81bc31334574579cf9c623f5e77ff596cacf268712cd3262c.
- Current v1.1 PDF: 306,668 bytes; SHA-256 e70599e0829dc5d030ac2e47b73fbd12afd6b7b31047d3ae354bbd884e65dffa.
- Nested sample CSV: 113,018 rows; 16,486,601 bytes; SHA-256 24394a233dc20066b1fad675deb15cd99bf91e8620a69f6bf50f190dfda62ba0.
- Sample trade date: 2025-03-28; 1,250 underlyings; C1 only; sample filename says 3%.

### Reconciliation of sample v1.0 and current v1.1 conventions

The sample archive contains an embedded TBT v1.0 PDF dated 2026-01-12. Its field names are lowercase and its container is ZIP; the current v1.1 spec (2026-10-05) uses uppercase names and CSV.GZ. Both versions describe SIDE as B/S, OPEN_CLOSE as O/C, and the same trading-segment examples (1 prior-evening/overnight, 2 daytime). Thus the observed values below are not explained by a documented v1.0-to-v1.1 change.

### Sample exceptions and coverage

- SIDE: B 56,635; S 56,314; T 69. All 69 T rows also have blank OPEN_CLOSE. T occurs only with Complex Add (23), Complex Remove (28), COA Responder (9), COA Initiator (8), and Opening Cross (1). Do not interpret T as buyer or seller.
- OPEN_CLOSE: O 69,184; C 23,654; blank 20,180 (17.86%). Blank values span 19 trade types; the largest are Simple Add (6,007), Simple Remove (5,419), COA Responder (3,325), Complex Remove (2,614), AIM Responder - Complex (806) and AIM Responder - Simple (713). Do not impute O/C.
- CAPACITY: MarketMaker 58,293; Customer 49,989; ProCustomer 2,699; Firm 1,879; BrokerDealer 158. These are exchange capacity categories, not beneficial-owner identities.
- SESSION: RTH 111,240; GTH 1,671; Curb 107. TRADING_SEGMENT is 1 for every row, including all RTH rows; this conflicts with the spec's illustrative RTH2/GTH1 examples. Preserve SESSION, but do not rely on TRADING_SEGMENT for time segmentation until Cboe explains or an independently verified file resolves it.
- 306 transact_time/TRADING_DT calendar-date mismatches are all GTH; RTH and Curb have zero. This is consistent with the documented GTH cross-midnight caveat.
- NBBO: 111,756 valid; 45 locked; 12 crossed; 1,205 zero/missing. BBO: 109,410 valid; 3,608 zero/missing.
- FLOOR_ACTION_TS exists on 618 rows: 61 have transact_time minus floor_action_ts >=90 seconds; 557 are between 0 and 90 seconds; none are negative.
- EXEC_ID: 111,333 unique IDs over 113,018 rows; 1,685 repeated groups, all with both B and S sides. These are execution links, not duplicate records. COMPLEX_EXEC_ID has 46,350 unique IDs and 2,875 repeated groups (2,770 size 2; 103 size 3; 2 size 4). Exact duplicate rows: zero.

The run's data_gate is PASS_PARSE_WITH_UNRESOLVED_CONVENTIONS: structural parsing, numeric fields, timestamps, capacities and duplicate-row checks passed, but side/open-close/segment semantics remain unresolved. This is not a data-approval or alpha gate.

### Decision

Keep C1 TBT as the highest-information conditional options candidate because it explicitly carries side, open/close, capacity and execution type, with history advertised from 2019-10-07 and T+1 delivery. Do not yet use it for a directional/open-close feature. Exclude SIDE=T and blank OPEN_CLOSE from any such candidate feature unless the semantics are resolved; do not use TRADING_SEGMENT. C1-only coverage and the 3% sample are not sufficient to infer universe completeness or whole-market representativeness.

Next gates:
1. Compare C1 TBT against C1 Open-Close on the same dates/series and identical population or known sampling fraction.
2. Verify the 2019-10-07 archive boundary and missing-date/symbol coverage; a sample does not prove historical completeness.
3. Crosswalk all 1,250 sample underlyings and historical/delisted securities to the broad PIT security master.
4. Establish actual file availability/correction timing before a conservative T+1 feature timestamp.
5. Preregister a narrow feature set only after the above; no returns or alpha test yet.

No purchase, subscription, vendor contact, terms acceptance, or production change occurred. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
