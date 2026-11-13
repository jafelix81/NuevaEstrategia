# Phase 352 — Cboe Open-Close 1-minute v1.8 specification and PIT audit

**Date:** 2026-11-13 UTC  
**Scope:** Reassess the intraday Cboe Open-Close candidate after the v1.8 specification became effective on 2026-11-08.  
**Mode:** Official-documentation audit only; no vendor contact, trial, purchase, raw-data acquisition, returns test or alpha test.

## Executive decision

**Retain Cboe Open-Close 1-minute as a high-priority conditional prospective participant-flow source. Do not admit historical PIT or alpha.**

The v1.8 specification materially improves the research design: the files are published on a real-time cadence and contain cumulative participant-specific opening/closing volume by option series. It also makes the correction problem explicit: later snapshots may include late-processed trades and remove trades subsequently broken or cancelled. The snapshots therefore must be preserved as received; a final corrected historical file cannot be backdated as the exact signal available earlier.

The data are cumulative day-to-date snapshots, not one-minute increments. The 1-minute schema also leaves fields 10–17 empty, including open interest, total exchange volume, total industry volume and EOD price fields. OI/IV/Greeks must come from a separately timestamped companion source.

No signal, return test or model change is authorized by this audit.

## 1. Official sources and version

- Cboe Open-Close product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- 1-minute file specification: https://datashop.cboe.com/documents/Open_Close_1m_Spec_v1.8.pdf
- Specification version/date: **v1.8, 2026-11-08**.
- Product page describes one file per exchange and interval timestamp, delivered minutes after each interval closes. The subscription is rolling monthly; a mid-month subscription begins from the subscription date.
- Raw data is proprietary and licensed for internal use. Raw redistribution is prohibited; external distribution of derived data requires additional licensing/approval.

The Phase 352 hosted audit downloads the official PDF, hashes it, extracts its text and verifies the semantic controls listed below. The artifact contains metadata only, not raw market data.

## 2. Snapshot and correction semantics

The v1.8 specification says:

1. Each 1-minute file contains trade counts and volume **aggregated throughout the day**, not only the latest minute.
2. Files are generated from real-time exchange streaming feeds and published on a real-time cadence.
3. A small number of trades may be processed late and appear in a later 1-minute snapshot.
4. Subsequent snapshots incorporate trade corrections; trades later broken or cancelled are removed from subsequent snapshots.

### Consequences for research

- Treat each file as a cumulative as-of snapshot, not as an independent one-minute bar.
- Preserve the exact bytes of every first-received file, with receipt UTC, exchange, market date, interval key, filename, schema version and SHA-256. Never overwrite a previously received snapshot.
- Derive interval changes only by comparing successive snapshots for the same exchange/date/series. Preserve negative changes: they can represent corrections/removals and must not be clipped to zero or relabelled as sell flow.
- A signal at time t may use only the snapshot actually received by t. A later snapshot must not rewrite the earlier feature or historical signal.
- The specification documents cadence and correction behavior, but does not supply an immutable historical first-receipt ledger or historical file-version vintages. Therefore the current historical archive is **not admitted as strict PIT** by this audit.

A prospective PIT archive is technically feasible only if exact snapshots are captured append-only at first receipt. No such capture has been activated.

## 3. Venue, session and historical coverage

The product page documents:

| Venue | 1-minute historical start | Session coverage |
|---|---:|---|
| C1 | 2019-10-07 | RTH and GTH |
| BZX | 2019-03-01 | RTH only |
| C2 | 2019-03-01 | RTH only |
| EDGX | 2019-03-01 | RTH only |

C1 Global Trading Hours coverage begins 2023-12-11. The v1.8 specification describes 405 RTH interval files from 09:31 through 16:15 for C2/BZX/EDGX, with separate C1 GTH/RTH handling.

This is **four Cboe venues, not all OPRA**. The product page says files include option series with trading volume on selected exchanges. Neither the documented history start nor a public sample establishes exact coverage of the frozen 335-name universe, inactive/delisted underlyings, historical option roots or the fraction of all-market option activity.

## 4. Participant and contract dimensions

The 1-minute file identifies option series by underlying, option symbol, expiration, strike, call/put and days to expiry. It reports participant-category trade counts and volume for:

- Firm: origin codes F, L, J.
- Broker-Dealer: B.
- Market Maker: M, N.
- Customer: C.
- Professional Customer: U, W.

Customer and Professional Customer activity is split into trade-size buckets below 100, 100–199 and at least 200 contracts. These are exchange origin/capacity classifications, not beneficial-owner identities or proof of informed trading. In particular, Customer and Professional Customer categories may mix retail, professional and institutional participants.

The data supports separate opening and closing measures by capacity. It does not justify calling any category “smart money” before predictive evidence.

## 5. Missing intraday fields and companion data

The v1.8 1-minute specification marks fields 10–17 as empty/not included in 1-minute files. These fields include first/high/low/last trade price, total exchange volume, total industry volume, open interest and previous open interest.

Consequences:

- Do not normalize intraday participant flow by Open-Close OI or total-industry volume from the 1-minute file; those values are not populated there.
- Do not infer IV or Greeks from this file. Use a separately validated Option Quotes/Option EOD source and its own point-in-time availability.
- For a daily swing signal, an EOD Greek snapshot may be simpler, but it must be available before the signal's execution time. For an intraday signal, any delayed companion quote/Greek feed needs a separate latency and alignment audit.
- Do not treat zero-filled missing fields as true zero.

## 6. Product-specific trading-segment convention

The v1.8 Open-Close 1-minute specification describes C1 segment 1/2 through the file/session structure: normal RTH and normal GTH examples use segment 1; segment 2 is used when a GTH session spans a market holiday and the second trading segment begins. \`TRADING_SEGMENT\` is null for C2, BZX and EDGX.

Do not generalize this convention to Cboe TBT. TBT v1.1 has its own explicit segment definition and examples; Phase 351's TBT sample still has an unresolved RTH/segment discrepancy. This audit does not resolve or reinterpret that separate TBT issue.

## 7. Sample and PIT limitations

The product page links new 1-minute/10-minute sample data alongside the v1.8 release. The surfaced 1-minute sample filename is \`Cboe_OpenClose_2026-09-30_15_20_1.csv.gz\`, whose market date precedes the 2026-11-08 effective date. The binary header and post-cutover behavior were not inspected in Phase 352; this link alone is not accepted as proof that the sample demonstrates the v1.8 schema/correction regime.

The product page's "minutes after each interval closes" delivery description is not an exact per-file SLA. A strict prospective KnowledgeTime must use the observed first-receipt timestamp, not the filename interval or trade date.

## 8. Preregistered hypotheses — not yet testable

Only after coverage, licensing, schema and prospective/historical PIT gates pass:

- Participant-specific opening net volume: \`open_buy_volume - open_sell_volume\`, separately for Firm, Broker-Dealer, Market Maker, Customer and Professional Customer; never combine open and close.
- Keep calls and puts separate, and stratify by expiry/delta/moneyness buckets only where the companion quote/Greek data is available at the same or earlier KnowledgeTime.
- Treat closing net volume as a distinct unwind/cover hypothesis.
- Compare large Customer/Professional Customer size buckets with smaller buckets; do not infer beneficial ownership from size.
- Test whether flow leads subsequent underlying returns or changes in IV/skew after controlling for prior 1/5/20-day returns, realized volatility, implied volatility, liquidity, earnings, market beta, optionability and dealer/market-maker hedging.
- Compare the feature alone and as an incremental addition to frozen LTM/F80 under identical exposure, rebalance timing, position sizing, transaction costs and liquidity constraints.

No thresholds or holding periods are selected here. No return, bootstrap, LOO, chronological OOS or holdout test is authorized.

## 9. Required next gates

1. Inspect a verifiably post-v1.8 1-minute sample and confirm the actual headers, row grain, cumulative behavior and correction behavior. The surfaced sample file's market date predates the cutover.
2. Quantify per-symbol/per-date coverage against the frozen 335 universe, including inactive/delisted securities and corporate-action option roots.
3. Reconcile four-venue activity against full-OPRA volume using a separate valid denominator; never treat Cboe share as total-market flow.
4. Establish exact first-receipt UTC and immutable snapshot/correction history. If only a prospective archive can satisfy this, do not backtest pre-capture dates as PIT.
5. Confirm price, internal-use and derived-feature licensing before any trial or data acquisition. No vendor contact, trial request or purchase was made or authorized.
6. Only then authorize a preregistered chronological test with a fresh untouched OOS period, matched costs/exposure, block bootstrap, ticker/sector clustering, LOO and multiplicity controls.

## 10. Controls and disposition

- **Source disposition:** high-priority conditional prospective candidate; historical PIT not admitted.
- **Alpha admission:** false.
- **Return test authorized:** false.
- **Holdout used:** false.
- **F80:** \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
- No vendor contact, trial request, purchase, licensing acceptance, production/universe/capital/parameter change or PR merge.
