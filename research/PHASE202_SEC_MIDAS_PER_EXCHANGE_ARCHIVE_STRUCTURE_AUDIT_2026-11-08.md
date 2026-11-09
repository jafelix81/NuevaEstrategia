# Phase 202 — SEC MIDAS per-security/per-exchange archive structure

**Audit date:** 2026-11-08  
**Disposition:** archive structure verified in three quarterly samples; full row reconciliation, first-publication PIT and alpha remain **NOT ADMITTED**.  
**Hosted run:** [42436593124](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42436593124)  
**Artifact:** [phase202-sec-midas-per-exchange-structure, ID 13600180470](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42436593124/artifacts/13600180470), SHA-256 36a5742afc26f5e929e46f7194eb17d3ffee822a4aac7c57023f859e1debb1ba.

## 1. Result

The SEC's official *Metrics by Individual Security and Exchange* index returned **58 quarterly archives**, from 2012 Q1 through 2026 Q2. The audit downloaded and inspected the full ZIP containers for three samples:

| Quarter | ZIP bytes | ZIP SHA-256 | Members | Monthly data members |
|---|---:|---|---:|---:|
| 2016 Q2 | 93,597,355 | 69113781212297bf73c9b352a625f4735b99110f4e54f85bfe23b1de252f84b6 | 4 | 3 |
| 2017 Q2 | 91,406,464 | 56015592f4e64aee718e9a2fd648693c150d7dce216cf13c12a7b20138b9a061 | 4 | 3 |
| 2019 Q4 | 126,219,647 | 7a3f9c008889c4972a4adda37e7ac84d1553335a471063262f509e817fec6db1 | 4 | 3 |

Each archive contains **three monthly CSV files plus one README**, with no nested ZIP:
- 2016 Q2: apr16.csv, may16.csv, jun16.csv.
- 2017 Q2: apr17.csv, may17.csv, jun17.csv.
- 2019 Q4: oct19.csv, nov19.csv, dec19.csv.

The exchange dimension is **an explicit Exchange column inside each monthly CSV**, not a separate file per exchange. The observed schema has 20 columns, including Date, Security, Ticker, Exchange, rank fields and the trade/order/hidden/odd-lot activity fields. Sample rows include Arca, Bats-Y and Bats-Z; the complete exchange set and row counts were not yet enumerated.

## 2. Why this matters

The archive is not merely a quarterly aggregate by ticker. It preserves a venue dimension that may let us:
- reconcile exchange-level activity against the SEC's aggregate individual-security dataset;
- attribute negative Hidden/HiddenVol residuals to specific venues;
- test venue concentration and exchange-coverage changes;
- distinguish documented feed/methodology breaks from actual changes in market behavior.

This is still market-structure activity, not institutional identity, aggressor-side flow, dark-pool activity or proof of informed trading.

## 3. Limitations

- Phase 202 inspected archive/member structure and CSV headers/sample rows; it did **not** perform a full ZIP CRC test or parse/reconcile all rows.
- The three archive HTTP Last-Modified values are all 2020-12-19. They are not the first public release dates of the 2016/2017/2019 observations.
- The 58-quarter archive index does not establish when each quarterly file first became available. The three release anchors previously identified still cover only 3/58 quarters (5.17%).
- Historical security identity, delisted coverage and daily-calendar completeness remain separate gates.

## 4. Next gate — Phase 203

Reconcile a deterministic ticker sample from the per-exchange monthly files to the corresponding aggregate per-security quarterly file for the same three quarters. Compare additive activity fields, derive TradesForOddLots and TradeVolForOddLots from the README's date-effective order-based venue set, inspect duplicate activity keys, and attribute negative Hidden/HiddenVol values by exchange. Do not deduplicate conflicting rows or infer publication time from HTTP headers.

## 5. Decision and controls

**Retain MIDAS only as a slow market-structure context candidate.** Do not authorize forward-return or alpha testing until release-vintage PIT, permanent historical identity and a defensible row/field reconciliation gate pass.

No return test, holdout use, data purchase, vendor contact or production change occurred. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
