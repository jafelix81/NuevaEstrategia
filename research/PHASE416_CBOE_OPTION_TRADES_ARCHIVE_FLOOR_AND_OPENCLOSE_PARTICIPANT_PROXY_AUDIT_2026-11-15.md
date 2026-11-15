# Phase 416 — Cboe Option Trades archive-floor discrepancy and Open-Close participant-proxy audit

**Audit time:** 2026-11-15 12:44 UTC  
**Disposition:** Keep January 2012 as the conservative Option Trades historical floor until Cboe reconciles its conflicting public documentation. Cboe Open-Close is the strongest currently documented direct participant-capacity/open-close proxy, but only for Cboe venues and subject to historical convention and first-receipt gates. No data sample was obtained, no purchase/contact occurred, and no signal or return test is admitted.

## 1. Actions and repository preflight

- Main HEAD at audit start: `01d85972cc1551ab3983d3cc87f620aae16b35ef`.
- Rechecked the latest 100 Actions runs, latest 20 run records, latest 100 branch records, branch search for Phase 416, all 63 workflow files, 56 open PRs, current research state, relevant capture workflows, jobs, logs and artifacts.
- No run was queued or in progress at 2026-11-15 12:44 UTC. No Phase 416 branch existed. Existing options PR #48 remains a draft on its stacked base; this note is an addendum, not a duplicate PR or workflow.
- SEC Form 144 run [43709012759](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43709012759) is the latest scheduled capture. Both jobs succeeded; offline regression passed 15/15. The live log records 50 Form 144 + 5 Form 144/A feed observations, zero new accessions/events/candidate matches/XML resolutions, and no detected feed-window gap. Receipt: 2026-11-15 11:28:22 UTC. Artifact [14159294388](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43709012759/artifacts/14159294388), SHA-256 `29f3d2b6ddcd78b7a7f46fdf86a534beedcc4c78f2e965da4a187a514b80c442`.
- The next configured SEC :37 slot (12:37 UTC) was not visible in Actions by 12:44 UTC. With GitHub schedule best-effort behavior, classify this as not yet observed, not a proven missed/disabled trigger. Do not manually dispatch, change cron or create a parallel poll.
- CFTC Phase 384 remains on the existing weekday 22:15 UTC schedule. No Sunday capture was due; next expected capture is Monday 2026-11-16 at 22:15 UTC, after the CFTC calendar's delayed 20:30 UTC release. Keep weekly TFF semantics until prospective TFF report dates and first-receipt timestamps demonstrate a cadence change.
- FINRA Phase 20C remains blocked at 328/329 valid price histories; unresolved symbols remain AVB, EA, EQR, LPRO, ROKU, WBD and WBS. Massive remains a conditional provider candidate only.

## 2. Cboe Option Trades — conflicting official archive start dates

The current Option Trades product page says:
- Complete trade-by-trade records across the OPRA universe for U.S.-listed stock, ETF and index options; options on futures and non-U.S. markets are excluded.
- Daily files; GTH trades are included.
- Trade price/size, executing exchange and prevailing NBBO are included; optional Calcs add trade-time IV and Greeks.
- Historical archive is available from **January 2012**.
- The file specification v1.3 includes underlying, market date, Eastern timestamp to milliseconds, OPRA sequence number, option root, expiration, strike, put/call, exchange ID, size, price, trade-condition ID, NBBO prices/sizes and optional IV/Greeks.

However, the current Cboe DataShop FAQ's archive-start table says **Option Trades — January 2010**. This conflicts with the live product page's January 2012 statement. No primary-source evidence located in this audit resolves the two-year difference.

**Conservative ruling:** use January 2012 as the earliest admissible archive date for feasibility planning. Do not claim January 2010 coverage until Cboe confirms the product-specific availability and the order-date selector or a lawful sample proves actual files exist.

### What Option Trades can and cannot identify

- It can support independent OPRA-wide trade-side reconstruction using trade price relative to contemporaneous NBBO, subject to condition-aware classification and explicit midpoint/locked/crossed/complex/auction/late/extended-hours treatment.
- It does **not** supply a documented customer/pro-customer/broker-dealer/market-maker capacity, open/close position, beneficial-owner, account or trader identity.
- Aggressor side is inferred, not an observed source field. Do not label signed prints as institutional flow.
- `trade_iv` and Greeks can be zero when the calculation lacks inputs, the trade is below intrinsic, or IV exceeds the model's upper limit. Zero is a calculation-invalid/missing state, not zero volatility.
- Underlying bid/ask can default to zero for indices and OTC underlyings. Retain calculation/quote validity flags.
- `canceled_trade_condition_id` is legacy and always zero; use the mapped `trade_condition_id` and preserve sequence/exchange IDs for deduplication and condition filtering.

### Sample and PIT status

The product page exposes a public “Download sample” link. The web download path returned an unsupported ZIP content type and the container download attempt failed; no sample bytes were obtained or parsed. The v1.3 PDF was inspected, but specification inspection is not row-level validation.

Cboe's FAQ says daily subscription files are delivered the following day through SFTP, typically between 00:05 and 03:00 U.S. Eastern, but may be delayed until after the next session opens. Therefore, archive coverage does not establish a historical first-receipt ledger. A prospective test must record actual first receipt, raw hash, schema version and correction/replacement lineage, then enter only after the first tradable session strictly following receipt.

## 3. Cboe Open-Close — stronger participant proxy, narrower venue scope

The current Open-Close page documents volume by:
- participant capacity: Customer, Professional Customer, Broker-Dealer, Firm and Market Maker;
- action: buy/sell;
- position: open/close;
- customer and professional-customer size buckets: <100, 100–199 and >199 contracts.

The product covers Cboe's BZX, C1, C2 and EDGX options exchanges, with files delivered separately per exchange. It is **not consolidated OPRA-wide coverage**.

The factsheet's definitions prevent simplistic institutional labels:
- Customer/Individual includes retail investors **and institutional clients**.
- Professional Customer includes professional traders and institutional participants, described as averaging 390+ daily volumes.
- Thus Professional Customer is a useful execution-capacity proxy, not verified institutional beneficial ownership; Customer is not a pure retail category.

### Historical coverage by venue and grain

| Exchange(s) | EOD | 10-minute | 1-minute |
|---|---:|---:|---:|
| C1 | 2005-01-03 | 2011-01-03 | 2019-10-07 |
| BZX, C2, EDGX | 2018-01-02 | 2019-03-01 | 2019-03-01 |

C1 EOD had a format change in 2011. C1 GTH coverage begins 2023-12-11. EOD files are delivered overnight after midnight Eastern; actual first-receipt timestamps remain necessary for strict PIT.

### Historical convention breaks that must remain explicit

- C1 Open Interest / Previous Open Interest was shifted one day ahead through 2019-10-04.
- C2 Open Interest / Previous Open Interest was shifted one day ahead through 2018-05-11.
- C2 Total Industry Volume was doubled through 2018-05-11.
- C1 Total Exchange Volume used (Buy + Sell) / 2 through 2019-10-04, versus Buy + Sell under the later convention.
- C1/C2 Previous Close historically referred to the last traded price on that exchange only through their respective convention dates.

These are not cosmetic adjustments: uncorrected values can manufacture false volume or OI changes and distort opening/closing imbalance features. Keep the already documented Phase 355/356/357 corrections and separate parser/convention regimes.

## 4. Research hypothesis and ranking

No source ranking is promoted to signal admission. For the next lawful sample-level feasibility work:

1. **OptionMetrics IvyDB TradeFlow** remains the conditional all-venue signed-flow hypothesis, with historical classifier-version, first-delivery, revision, sample, license and universe gates unresolved.
2. **Cboe Open-Close** is the strongest currently documented direct capacity × side × open/close complement. It can test whether Professional Customer opening-buy/sell imbalance differs from Customer, Firm or Market Maker activity, but only within the covered Cboe venues and only after convention corrections and PIT receipt controls.
3. **Cboe Option Trades** is the independent OPRA-wide raw trade/NBBO validation source for directional reconstruction and coverage reconciliation. Its January 2010 vs January 2012 archive floor is unresolved; use 2012 conservatively.
4. **Cboe Options PITCH** remains a separate depth/order-book microstructure candidate (October 2019 onward), not a direct institutional-identity source.

Any eventual hypothesis must distinguish prediction from return-chasing, normalize by underlying liquidity and option-series coverage, avoid double-counting nested participant buckets, and test incremental information versus frozen LTM/F80 with identical exposure, costs, chronological OOS, bootstrap/LOO and untouched holdout. No minimum/maximum holding period is imposed.

## 5. Decision and controls

- Do not use January 2010 Option Trades history until the archive-floor discrepancy is resolved.
- Do not treat Option Trades signed prints as identified institutional trades.
- Treat Open-Close Professional Customer as a capacity proxy, not beneficial-owner identity; Customer includes institutional clients.
- No Cboe sample bytes, subscription, trial, vendor contact, purchase or card authorization occurred.
- No return, alpha, OOS, bootstrap, LOO or holdout test was run.
- No source or signal admitted. `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged.

## Official sources checked 2026-11-15

- Option Trades product page: https://datashop.cboe.com/option-trades
- Option Trades FAQ archive-start table and delivery FAQ: https://datashop.cboe.com/faqs
- Option Trades v1.3 file specification: https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf
- Open-Close product page and historical convention table: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- Open-Close factsheet and participant definitions: https://datashop.cboe.com/documents/Cboe_Open-Close_Factsheet.pdf
- Options Multicast PITCH: https://datashop.cboe.com/cboe-us-options-multicast-pitch
