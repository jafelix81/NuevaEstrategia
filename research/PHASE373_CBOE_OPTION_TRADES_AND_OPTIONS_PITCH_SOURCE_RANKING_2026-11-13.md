# Phase 373 — Cboe Option Trades and Options PITCH source ranking

**Date:** 2026-11-13  
**Disposition:** **Option Trades becomes the highest-priority broad-coverage options-flow candidate; PITCH remains a high-cost microstructure candidate. Neither is PIT- or alpha-admitted.**  
**Research class:** public product/specification audit only. No sample bytes, subscription, trial, vendor contact, purchase, return test or production change.

## Executive decision

The fresh Cboe product/specification review changes the options-source ranking:

1. **Option Trades (OPRA)** — broadest historical trade-print coverage: all U.S. listed stock, ETF and index options disseminated over OPRA, advertised from January 2012, with trade-level NBBO and optional point-in-time IV/Greeks. It does not identify participant capacity, beneficial owner, or open/close position. Direction must be inferred conservatively from trade price versus contemporaneous NBBO and trade conditions.
2. **Open-Close EOD** — strongest direct participant-capacity and open/close cross-tab among the reviewed products, but limited to Cboe exchanges and subject to historical convention changes, third-party industry-volume/OI fields and PIT-vintage requirements.
3. **Cboe Options Multicast PITCH** — rich depth-of-book/execution/auction-update feed across C1, C2, BZX and EDGX options, with RTH/GTH sessions and archive from October 2019. It is a microstructure source, not a direct institutional-identity source; processing and licensing burden are high.
4. **TBT** — detailed C1 execution records with side, open/close, capacity and trade-type fields, but C1-only, costly, and its advertised 2019 archive is retrospective before the conservative public launch-documentation floor of 2026-02-20.

Option Trades is the best next source to test for breadth across the existing and expanded underlying universe. This is a source-priority decision only; no feature has been admitted.

## 1. Option Trades — product contract

Cboe's current product page and v1.3 file specification state:

- Every options print across the OPRA universe for U.S.-listed stocks, ETFs and indices; GTH trades are included.
- Options on futures and non-U.S. markets are excluded.
- Daily file delivery; historical data advertised from **January 2012 to present**.
- Files can be grouped per day, month or year; all symbols or selected underlying symbols can be requested.
- Trade-level fields include underlying symbol, market date, Eastern quote/trade timestamp to milliseconds, OPRA sequence number, option root, expiration, strike, call/put, executing exchange ID, size, price, trade-condition ID, and contemporaneous NBBO prices and sizes.
- Optional Calcs adds trade-time IV, delta, gamma, vega, theta and rho.

### What it enables

A broad OPRA options-flow hypothesis can be constructed using:
- signed premium/notional estimated from trade price versus NBBO;
- delta-adjusted premium/notional when valid Calcs are present;
- call/put and moneyness/tenor buckets;
- trade-condition and exchange stratification;
- unusual volume relative to effective-dated underlying liquidity and option-series history;
- IV/skew/term-structure changes from trade-time Greeks, with explicit missing/zero-calculation flags.

### What it does not enable directly

- No documented customer/pro-customer/broker-dealer/market-maker capacity cross-tab.
- No explicit open/close position field.
- No beneficial-owner, fund, account or unique trader identity.
- A trade print is not automatically an opening institutional purchase, an aggressor-side trade, or an informed bet.

Aggressor direction would be an estimate, not a source field. Midpoint/locked/crossed/complex/auction and other condition classes must be mapped and separately filtered or modeled. Do not classify every print as buy or sell. The sequence number, trade-condition mapping and exchange-ID mapping are mandatory for deduplication and interpretation.

### Data-quality caveats in v1.3

- `trade_iv` and Greeks are zero when the calculation model lacks sufficient inputs, the trade is below intrinsic value, or computed IV exceeds an upper limit. Zero is not a valid zero-volatility observation; retain a calculation-validity flag.
- Underlying bid/ask defaults to zero when no quote is disseminated, including many indices and OTC names.
- `canceled_trade_condition_id` is legacy and always zero; the trade-condition mapping must be used instead.
- `number_of_exchanges` and regional quote fields are legacy/empty.
- Underlying identity must be effective-dated. Current ticker strings are insufficient for historical share classes, symbol changes, mergers and delisted underlyings.

## 2. PIT and historical coverage ruling

The January 2012 archive is a historical-coverage claim, not a contemporaneous receipt ledger. The product page says daily delivery but the reviewed public page/specification does not establish:
- the exact first-available timestamp for each daily file;
- whether files are T+0 or T+1 in every historical era;
- correction, cancellation, bust and replacement-vintage history;
- whether the historical archive reproduces the original delivered file byte-for-byte.

Therefore:
- historical data before a verified live-delivery/receipt ledger are **retrospective backfill, not strict PIT**;
- no historical backtest is authorized from the archive alone;
- any prospective capture must record file date, first-received timestamp, immutable SHA-256, schema/spec version, correction lineage and effective-dated underlying identity;
- for any later test, use the first tradable session strictly after verified receipt, not the trade date by assumption.

The public sample link resolves to `https://datashop.cboe.com/download/sample/216`, but the current web/runtime download path rejected the ZIP content type and the container download attempt failed. **No sample bytes or parser validation are claimed.**

## 3. PITCH — order-book microstructure alternative

Cboe's Options Multicast PITCH product page states:
- daily end-of-day archive, typically available after 8 p.m. U.S. Eastern;
- historical coverage from **October 2019**;
- C1, C2, BZX and EDGX options exchanges;
- RTH and GTH sessions;
- one file per matching-engine unit per exchange and trade date, with multiple trading segments possible around holidays.

The linked Cboe Multicast PITCH specification describes real-time depth-of-book quotations, execution information and auction-update messages. This could support order-book imbalance, displayed-depth depletion/replenishment, execution intensity and liquidity/price-impact measures. It does not identify beneficial owners or prove that displayed orders were informed. Add/cancel/replace behavior, sequence-gap recovery, matching-engine segmentation and execution linkage must be validated against actual sample files.

PITCH is proprietary, external redistribution is prohibited, and the public page does not provide a usable current price in the reviewed content. No sample, purchase or trial was attempted.

## 4. Relative ranking

| Product | History advertised | Coverage | Direct participant/position fields | Main role |
|---|---:|---|---|---|
| Option Trades | 2012-01 | OPRA-wide U.S. stock/ETF/index options | No | Broad options-flow / IV hypothesis |
| Open-Close EOD | Exchange-specific; C1 2005, BZX/C2/EDGX 2018 | Four Cboe venues, not all OPRA | Yes: capacity × side × open/close | Participant-category context |
| Options PITCH | 2019-10 | C1/C2/BZX/EDGX | No beneficial-owner identity | Depth/order-flow microstructure |
| TBT | 2019-10-07 archive | C1 only | Side, open/close, capacity | Narrow execution-level study |

TBT's pre-launch archive remains retrospective. The earlier Phase 236 audit uses 2026-02-20 as the conservative public launch-documentation floor; actual first subscriber receipt is still unknown. Its last located C1 fee schedule (2026-04-21) listed $12,000/month subscription and $8,000 per month of ad-hoc history. Reconfirm current fees and rights before any acquisition.

## 5. Next feasibility gate — no alpha yet

If sample access becomes available without purchase or card authorization, test representative dates/eras (2012, 2019, 2023, 2025) and the existing/expanded underlying universe. The parser gate should report:
1. row count, file hashes, schema and sequence uniqueness;
2. trade-condition and exchange-ID distributions;
3. NBBO completeness, zero/locked/crossed markets and trade-price location versus NBBO;
4. IV/Greek zero/missing rates and underlying bid/ask coverage;
5. complex/auction/cancelled/late/condition-specific row handling;
6. underlying-symbol mapping to active and inactive securities with effective dates;
7. file availability and correction-vintage/first-receipt evidence.

Only after the data and PIT gates pass should features be compared incrementally with frozen LTM/F80 using identical exposure/costs, chronological training, clustered bootstrap, LOO, multiplicity controls and a new untouched holdout.

## 6. Controls

No sample bytes downloaded, no trial, no vendor contact, no purchase, no card authorization, no raw data retained, no forward returns, no alpha/OOS/holdout test, no signal admitted and no production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Official sources reviewed 2026-11-13

- Option Trades product page: https://datashop.cboe.com/option-trades
- Option Trades v1.3 file specification: https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf
- Options PITCH product page: https://datashop.cboe.com/cboe-us-options-multicast-pitch
- Cboe Multicast PITCH specification: https://www.cboe.com/document/tech-spec/content/technical-specifications/cboe-titanium-u.s.-equitiesoptions-multicast-pitch-specification
- Open-Close product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- TBT product page: https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail
- Phase 236 TBT feasibility/PIT audit: PHASE236_CBOE_TBT_EXECUTION_DETAIL_FEASIBILITY_AND_PIT_AUDIT_2026-11-09.md
