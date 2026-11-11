# Phase 236 — Cboe Trade-by-Trade (TBT) execution-detail feasibility and PIT admission audit

**Date:** 2026-11-09  
**Disposition:** **HIGH-VALUE C1 EXECUTION-LEVEL MEASUREMENT CANDIDATE; NOT STRICT-PIT OR ALPHA ADMITTED**  
**Research class:** source feasibility, field semantics, product chronology, licensing/cost gate. No data purchase, raw sample parsing, forward-return test, or production change.

## Executive decision

Cboe's Enhanced US Options Trade-by-Trade Execution Detail (TBT) is materially richer for directional/opening-flow research than the 80-field Option Sentiment daily aggregate and the Open-Close summary. Its documented row-level fields include buy/sell side, open/close, order capacity, trade type, size, execution timestamp, NBBO/local BBO, and execution identifiers that can link simple sides and complex legs.

This resolves several *measurement-design* limitations found in Phase 233: the TBT schema exposes side, open/close, capacity, and size on the same trade-level record rather than only as separate daily aggregates.

It does **not** establish a smart-money signal. Capacity is not beneficial-owner identity; side is not automatically aggressor direction; an opening flag is not a unique investor's net position; C1 is not all-OPRA; and complex trades can be double-counted if execution IDs are ignored.

The key historical correction is that the product page advertises archive data from **2019-10-07**, but the first public Cboe launch documentation located in this audit is the **2026-02-20** Traders Weekly, which says the TBT dataset had launched. Therefore the 2019–pre-launch archive is retrospective backfill, not evidence that a live TBT signal was available at those historical dates. The first possible live-product window is short (under nine months as of this audit), and actual first-receipt logs remain unavailable. No historical row is strict-PIT admitted.

The C1 price is also substantial: the last located C1 fee schedule (dated 2026-04-21) lists **$12,000/month** for subscription and **$8,000/month** for an ad-hoc historical request, with an eligible one-month trial. No trial was requested and no purchase was made.

## 1. Official product and field contract

The current Cboe product page states:
- one trade-level record for each C1 options execution;
- underlying and OSI details, timestamp, price and size;
- buy/sell side, opening/closing position, participant capacity and trade type;
- NBBO and executing-exchange BBO context;
- execution identifiers for simple and complex trades;
- T+1 overnight delivery;
- C1 only at present, with C2, BZX and EDGX described as planned;
- historical archive start of 2019-10-07.

The v1.1 specification dated 2026-10-05 defines 22 fields. Material fields include:
- `TRANSACT_TIME`: time processed/booked in the electronic system;
- `TRADING_DT`: assigned trade/market date, which can differ from the calendar date of `TRANSACT_TIME` around GTH midnight;
- `FLOOR_ACTION_TS`: floor-agreement timestamp; a trade is described as late when the difference from `TRANSACT_TIME` is at least 90 seconds;
- `SIDE` (`B`/`S`), `OPEN_CLOSE` (`O`/`C`), and `CAPACITY`;
- `NBBO_BID/ASK` and executing-exchange `BBO_BID/ASK`;
- `EXEC_ID`, which links simple buy and sell orders;
- `COMPLEX_EXEC_ID`, which links buy/sell legs for a complex-to-complex trade;
- `SESSION` and `TRADING_SEGMENT` for RTH/GTH/Curb and prior-evening/daytime segmentation.

Capacity categories are `MarketMaker`, `Customer`, `ProCustomer`, `BrokerDealer`, and `Firm`. The documented code mapping is F/L/J → Firm, B → Broker-Dealer, M/N → Market Maker, C → Customer, U → Professional Customer.

The trade-type taxonomy includes auctions, QCC, compression, routed trades, floor executions, complex-order activity and a `Provisional` category subject to future update/review. Trade types must be preserved and separately analyzed; they should not be collapsed into one signed-flow bucket by default.

## 2. Measurement advantage — and what it does not solve

| Research dimension | Option Sentiment v1.4 | TBT v1.1 |
|---|---|---|
| Buy/sell side | Daily directional aggregates | Per trade |
| Open/close | Not available as a complete directional cross-tab | Per trade |
| Capacity × side × open/close × size | Not available in the documented 80-field schema | Directly observable at row level |
| Trade type / auction / complex context | Not at execution level | Per trade |
| NBBO and local BBO at execution | Not a trade-level field | Included |
| Execution/complex linkage | No | IDs provided |
| History advertised | 2012-01 | 2019-10-07 |
| Current venue coverage | OPRA-disseminated options scope claimed | C1 only |

The TBT file can support a more precise *C1 venue* hypothesis, for example customer/pro-customer opening-side imbalance in non-complex, non-routed, non-provisional executions, normalized by underlying liquidity. That is only a candidate design; no feature is defined or tested in this phase.

Non-inferences that are mandatory:
1. `SIDE=B/S` is documented as Buy/Sell. Do not call it aggressor-side or order-initiator direction without a separate, source-backed rule and sample validation.
2. `CAPACITY` is an exchange order-capacity category, not an account, fund, beneficial owner, or proof of informed trading.
3. `OPEN_CLOSE` is not open interest and does not identify the unique beneficial owner's net position.
4. C1 executions are not all U.S. options executions. Do not scale C1-only volume into all-OPRA flow without a separately validated coverage denominator.
5. `EXEC_ID` and `COMPLEX_EXEC_ID` may connect multiple sides/legs. Do not sum raw rows as independent trades until row grain, paired-side behavior and complex-leg cardinality are empirically reconciled.
6. The `Provisional` trade type is explicitly subject to later update/review and should be quarantined or versioned separately.

## 3. Historical archive versus live product chronology

Cboe's current product page advertises TBT history beginning 2019-10-07. That is an archive-availability claim, not proof of contemporaneous delivery.

The first public launch evidence located here is Cboe Traders Weekly dated **2026-02-20**, which says Cboe launched the TBT dataset. The March 6, 2026 newsletter repeats that it had launched. The SEC rule filing SR-CBOE-2025-088 (filed 2025-12-11; published 2025-12-19) described the product and required Cboe to announce its implementation date within 90 days after the operative date. The February 20 newsletter is used only as a conservative *public documentation floor*, not as an exact first subscriber receipt.

**PIT ruling**
- Trade dates before 2026-02-20: `RETROSPECTIVE_BACKFILL_NOT_STRICT_PIT`.
- Trade dates on/after 2026-02-20: `LIVE_PRODUCT_WINDOW_RECEIPT_REQUIRED`; no row is admitted until actual first-received timestamps, raw hashes, schema/version lineage, correction history, effective-dated underlying identity and licensing are present.
- TBT files are described as T+1, typically 00:30–01:30 a.m. Eastern the next morning. The actual first receipt for each file/version remains required; a typical delivery window is not a historical receipt ledger.
- Use `TRADING_DT`, not the calendar date of `TRANSACT_TIME`, around GTH midnight.
- For this project's end-of-day execution discipline, earliest execution is the close of the first regular session whose open is strictly after actual receipt. A file received after that session's open rolls to the next session.

As of 2026-11-09, the documented live window is less than nine months. That is not enough to claim multi-regime or independent OOS robustness. The 2019–2026 backfill cannot be silently promoted to PIT history.

## 4. Venue expansion is not yet available

C1 is the only currently documented TBT venue. Cboe's product page lists C2, BZX and EDGX as planned.

C2 and BZX filed separate expansion proposals on 2026-10-27, with SEC notices published 2026-11-06. Those notices do not make those feeds part of the current C1 product on 2026-11-09; the filings state an operative delay. EDGX remains only a planned venue in the current product page. Do not claim multi-venue coverage until each venue's actual product implementation, first-receipt logs and data contract are verified.

## 5. Cost and licensing gate

The Cboe C1 fee schedule dated 2026-04-21 lists:
- TBT subscription: **$12,000 per month**;
- historical ad-hoc request: **$8,000 per month of data**;
- eligible free trial: up to one month, for TPHs and non-TPHs that have not previously purchased or received the trial.

The current product page states the data are proprietary and external redistribution is prohibited. Before any acquisition, confirm internal-use rights, derived-feature restrictions, retention, trial eligibility, and whether research-derived signals may be used in the intended account/business context. The fee schedule is the last located C1 schedule in this audit, not a guarantee that fees remain unchanged after 2026-04-21.

No contact, trial request, purchase, or redistribution was made.

## 6. Sample and implementation status

The product page exposes a public sample link, but this audit did not obtain the sample bytes. Therefore:
- no row-level sample parse is claimed;
- no paired-side or execution-ID reconciliation is claimed;
- no real C1/OPRA coverage ratio is measured;
- no inactive/delisted underlying coverage is measured;
- no schema-vintage or correction-vintage history is verified.

Added a documentation-backed fail-closed audit module and tests. The module classifies pre-launch archive dates as retrospective, requires an aware first-receipt timestamp, immutable raw SHA-256, vintage ID, schema version, resolved effective-dated security identity and confirmed internal-use licensing, and rejects manual/non-scheduled receipts. Its row validator checks documented categorical fields but explicitly does not infer aggressor direction or beneficial-owner identity.

Local regression suite: **15/15 passed**. This is a static feasibility/guardrail suite, not a live-data test or hosted CI run.

## 7. Admission decision

| Gate | Result |
|---|---|
| Official schema/product documentation | PASS |
| Trade-level side/open-close/capacity/size fields | PASS |
| Execution/complex IDs documented | PASS |
| Historical archive start documented | PASS |
| Live-product documentation floor identified | PASS, conservative public floor only |
| Pre-launch archive strict PIT | FAIL / retrospective only |
| Post-launch per-file first-receipt ledger | NOT ESTABLISHED |
| Immutable correction/revision lineage | NOT ESTABLISHED |
| Row-grain / paired-side / complex-leg sample reconciliation | NOT ESTABLISHED |
| Effective-dated underlying identity incl. inactive/delisted | NOT ESTABLISHED |
| C1 share of all-OPRA volume | NOT MEASURED |
| Licensing / internal-use / derived-feature rights | NOT CONFIRMED |
| Alpha / OOS test | NOT AUTHORIZED |

**Decision:** keep TBT as a **high-priority conditional C1 execution-measurement candidate**, ahead of Option Sentiment for hypotheses that require crossed side × open/close × capacity × size fields. Do not call it an institutional or smart-money signal. Do not buy it. The next useful gate is a lawful representative sample or eligible trial, followed by row-grain/ID/correction validation and an actual prospective receipt ledger. Only after those gates should one preregistered C1-specific flow hypothesis be compared against LTM/F80 under identical exposure/costs, with prior-return controls and chronological OOS discipline.

No returns, no signal, no bootstrap/LOO, no OOS, no final holdout, no vendor contact, no purchase, no production/universe change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; `CONSUMED_NOT_PRISTINE` remains unused.

## Official source references

- Cboe TBT product page: https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail
- Cboe TBT File Specification v1.1 (2026-10-05): https://datashop.cboe.com/documents/TBT_Spec_v1.1.pdf
- Cboe Traders Weekly (2026-02-20): https://cdn.cboe.com/resources/trader_news/2026/Cboe-Traders-Weekly-for-Friday-February-20-2026.pdf
- Cboe Traders Weekly (2026-03-06): https://cdn.cboe.com/resources/trader_news/2026/Cboe-Traders-Weekly-for-Friday-March-6-2026.pdf
- SEC SR-CBOE-2025-088 / Release 34-104415: https://www.sec.gov/files/rules/sro/cboe/2025/34-104415.pdf
- Cboe C1 Fee Schedule (2026-04-21): https://cdn.cboe.com/resources/membership/Cboe_FeeSchedule.pdf
- Cboe C2 TBT notice (published 2026-11-06): https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-c2-2026-029
- Cboe Open-Close product page (comparison): https://datashop.cboe.com/cboe-options-open-close-volume-summary
