# Phase 135 — Cboe U.S. Options Multicast PITCH microstructure feasibility audit

**Date:** 2026-11-05  
**Branch:** `phase99-broad-pit-universe-charter`  
**Status:** official-source feasibility review; no historical feed purchased/downloaded, no vendor contact, no return test, no production change.

## 1. New candidate and decision

The current Cboe DataShop product page documents a daily historical archive of the Cboe U.S. Options Exchanges' depth-of-book real-time feed with execution information for Regular Trading Hours (RTH) and Global Trading Hours (GTH). Historical availability is advertised from **October 2019 to present**. The selectable exchanges are C1, C2, BZX and EDGX. Files are delivered per exchange and Matching Engine (ME), typically after 8 p.m. U.S. Eastern.

Decision: **PROMOTE TO CONDITIONAL MICROSTRUCTURE CANDIDATE — HIGH INFORMATION, ACCESS / COVERAGE / PIT GATED.**

This is a materially different source from Open-Close. Open-Close is a daily participant-capacity/open-close summary; PITCH is an event stream that can reconstruct visible order-book state and order lifecycle. It is not a participant-identity feed and must not be described as "smart money" data.

Official product page: https://datashop.cboe.com/cboe-us-options-multicast-pitch

## 2. What the feed can measure

The current Cboe Titanium Multicast PITCH specification describes full depth-of-book quotations and execution information. It documents sequenced messages, per-unit sequence numbers, Time/Time Reference messages, and options symbol mapping from a compact feed symbol to the OSI option symbol and underlying.

Relevant event families include:
- Add Order (long, short, expanded);
- Order Executed and Order Executed at Price/Size;
- Reduce Size, Modify Order and Delete Order;
- Trade, expanded Trade and Trade Break;
- Unit Clear, Trading Status, Time / Time Reference and Symbol Mapping.

The event Time Offset is nanosecond precision relative to the latest Time message. Sequence numbers are maintained per symbol unit and begin at one each day. C1 Options Time/Time Reference messages support the Eastern-time midnight boundary and an epoch/midnight reference. These fields make event-time and sequence-integrity reconstruction technically feasible, subject to complete archives and correct handling of all message types.

Official specification: https://www.cboe.com/document/tech-spec/content/technical-specifications/cboe-titanium-u.s.-equitiesoptions-multicast-pitch-specification

## 3. Economic hypotheses — not participant labels

If the archive is complete and the option-symbol mapping is recoverable, candidate features include:
1. displayed depth imbalance by option contract and side;
2. event-level order-flow imbalance from additions, executions, reductions, modifications and cancellations;
3. cancellation-to-add and execution-to-add ratios;
4. displayed-order lifetime / replenishment / queue-depletion measures;
5. book resilience after aggressive executions;
6. option-contract flow aggregated to the underlying, first without Greeks and later with a separately validated contemporaneous delta/vega source.

These are market-microstructure hypotheses. They may reflect liquidity supply, inventory management, market making, hedging, mechanical execution or price discovery. They do not identify beneficial owners or establish informed trading.

Important interpretation constraints:
- The side on an Add Order is the resting quote side, not the aggressor side.
- The Trade message's side indicator is documented as B regardless of the resting side; it must not be treated as buyer-initiated flow.
- Execution-side inference is possible only when the referenced visible order and its full lifecycle are reconstructed. Hidden/non-displayed executions and obfuscated order IDs cannot be treated as fully attributable to a visible resting order.
- The specification says the feed is anonymous. Do not assume that an order ID identifies a firm, customer or institution.

## 4. Coverage and identity gates

PITCH is **Cboe-venue-only**, not a consolidated OPRA feed. It covers the Cboe-affiliated options exchanges selected in the order (C1, C2, BZX, EDGX), not every U.S. options venue. The 2019-10 start provides roughly seven years of potential history as of this audit, but the product page does not establish per-date completeness, historical inactive-underlying retention, or symbol coverage against our broad PIT equity universe.

Options symbol mapping is central. The specification describes unsequenced Symbol Mapping messages that map the six-character feed symbol to OSI and underlying; they are sent continuously during the day. Before any research panel is built, a sample archive must prove that the daily files preserve sufficient mapping information (or that an independently archived, effective-dated mapping file exists). Adjusted options, root changes, corporate actions, delistings, mergers and symbol reuse must remain explicit; unresolved mappings are quarantined.

The product page states one file per Matching Engine per exchange and trade date, with segment indicators for certain C1 GTH/RTH calendar-crossing sessions. A proper audit must enumerate expected ME/segment files, verify hashes, decompress every file, and check sequence continuity per unit. Missing ME files, sequence gaps, unhandled trade breaks or unit resets invalidate book-state reconstruction for the affected unit/date.

No public historical PITCH sample link is exposed on the current product page. Therefore the message decoder, archive naming, compression, file sizes, symbol mapping retention and sequence completeness have not been empirically validated in this phase.

## 5. Point-in-time availability

The current product page says daily archives typically become available after 8 p.m. ET. This is current delivery guidance, not a historical per-file first-publication log. The event timestamps inside a file are not the time the research user first received that file.

Until historical SFTP delivery logs or equivalent immutable publication evidence are available:
- do not use the same-day PITCH archive as if it were available at the event or market close;
- any preliminary sensitivity should use the next trading session as the earliest possible use and test additional one-session delay;
- do not call the resulting historical panel strictly point-in-time proven;
- preserve the distinction between EventTime, FileDeliveryTime and KnowledgeTime.

A future daily pipeline can retain actual receipt timestamps prospectively, but that does not repair unknown historical delivery times.

## 6. Data volume, licensing and practical feasibility

The product is proprietary Cboe data and is distributed through DataShop SFTP. The page does not provide public price, archive size estimates or a downloadable sample. Files are partitioned by exchange and ME, which implies materially more storage and compute than a daily EOD summary. A sample day from each exchange and representative ME/segment is required before estimating full-history storage, decode throughput and usable symbol breadth.

No order was placed, no cart was used, no terms were accepted, no vendor was contacted and no credentials or paid data were requested.

## 7. Comparison with existing candidates

| Source | Main information | History advertised | Current role |
|---|---|---:|---|
| Cboe C1 Open-Close EOD | Capacity × buy/sell × open/close | Jan 2005 | Leading participant/open-close summary; venue and PIT gated |
| Cboe Volatility Surfaces | Model-fitted IV/skew/term structure + confidence | Aug 2011 | Leading IV/skew context; sample/coverage/PIT gated |
| Cboe Options PITCH | Visible order-book lifecycle and executions | Oct 2019 | New conditional microstructure candidate |
| Cboe Complex Order Flow | RevCon, box, jelly roll, tied outright/spread legs | Current page offers subscription only | Prospective-only unless historical archive is confirmed |
| Databento multi-venue L2/L3 | Broader multi-venue order/trade data | Prior Phase 32 review | Broader primary concept; commercial access blocked |

Cboe Complex Order Flow's current page lists five daily zipped CSV strategy files but only exposes a subscription purchase type, not historical purchase. Its leg-level records could be economically informative (including paired stock executions), but it is not promoted for long OOS until historical orderability is confirmed. Product: https://datashop.cboe.com/complex-order-flow. Specification: https://datashop.cboe.com/documents/Complex_Order_Flow_Specifications_v1.0.pdf.

The prior Phase 32 market-microstructure audit remains relevant: Databento was the broader multi-venue historical candidate, but commercial access was blocked. Cboe PITCH is a narrower exchange-specific alternative, not a replacement for consolidated coverage.

## 8. Required next gates before any alpha test

1. Obtain a public sample or authorized sample day from each relevant Cboe options exchange and a representative ME.
2. Validate compression/container layout, every message length/type, Time Reference / Time Offset reconstruction, sequence continuity, Unit Clear, Trade Break and GTH segment handling.
3. Prove historical OSI-to-underlying mapping coverage, including adjusted options and inactive/delisted underlyings.
4. Quantify per-underlying Cboe venue share and sample coverage against the broad historical equity universe; never extrapolate Cboe-only activity to OPRA.
5. Record actual file receipt timestamps prospectively; obtain historical publication evidence or keep historical PIT explicitly unverified.
6. Preregister a small feature set and cutoffs. Use only events before the signal cutoff, then make the feature available no earlier than verified file receipt / conservative next-session sensitivity.
7. Compare each microstructure feature incrementally with frozen LTM/F80 under identical exposure and costs; use chronological walk-forward OOS, block bootstrap and ticker/sector leave-one-out. Separate price-chasing, liquidity/inventory effects and predictive behavior.

No forward returns or alpha were tested in Phase 135. No strategy or production setting changed. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
