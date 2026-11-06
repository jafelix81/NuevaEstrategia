# Phase 141 — Cboe OPRA denominator and venue-share audit

**Date:** 2026-11-05  
**Branch:** phase99-broad-pit-universe-charter  
**Scope:** re-audit existing public artifacts from Phases 112, 114 and 55. No new data purchase, subscription, vendor contact, authentication, forward-return test or production change.

## Decision

**Cboe Option Trades is a conditional daily OPRA-wide denominator candidate, but not yet approved for intraday use or strict historical PIT.** The public sample gives one empirical venue-share observation: on AAPL, 2026-01-07, C1 represented 10.47% of reported OPRA contract volume and Cboe's four Open-Close venues together represented 21.04%. This is one underlying on one day, not a market-wide estimate.

The audit also formalizes an important volume-unit rule: Cboe's total_exchange_vol counts both sides of a trade. It must not be divided directly by total_industry_vol and called a market-share percentage.

## Artifacts and reproducibility

- Phase 112 Option Trades sample artifact: [run 42022615770 / artifact 13412861022](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42022615770).
  - Public ZIP SHA-256: a02504e156db28b3f007d9d25a534e4c88ffd8d24ac43f3bf84885583a3d10b8.
  - The Calcs/no-Calcs variants have the same 74,999 valid trade rows and identical sequence-key hashes. They are alternate schema variants, not separate populations.
- Phase 114 C1 Open-Close EOD sample artifact: [run 42027724358 / artifact 13415230222](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42027724358).
  - Public sample ZIP SHA-256: 445cd9d658dc06028c286e09d4ac4818bd5884d7da8addd7509f3a0fa4840552.
  - Nested EOD sample SHA-256: 1c960e9a7b8b25311d2c8f012c36ea2c43087fe756335e57ffc952699a393ff6.
- Phase 55 Option EOD Summary sample artifact: [run 41762979543 / artifact 13291207023](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762979543).
- Raw market-data files are not committed or redistributed. Only aggregate audit results and the parser are retained.

## 1. OPRA-wide Option Trades sample

The sample is trade date **2026-01-07** and contains:

- 74,999 valid AAPL option trades;
- 308 option series and one underlying;
- 18 observed exchange IDs, among 20 option-exchange IDs in the downloaded official LiveVol mapping;
- 531,227 contracts summed from trade_size;
- no parse/identity/size errors, no duplicate sequence keys in the Phase 112 audit, and no non-zero legacy canceled_trade_condition_id values.

The raw CSV also contains 23,580 all-empty padded rows (23.9% of physical data rows). They are not trades and are counted separately by the Phase 141 parser.

| Venue | Exchange ID | Contracts | Share of sample |
|---|---:|---:|---:|
| CBOE / C1 | 5 | 55,612 | 10.47% |
| C2 | 42 | 17,174 | 3.23% |
| BZX | 60 | 16,431 | 3.09% |
| EDGX | 65 | 22,577 | 4.25% |
| **Cboe four-venue group** | — | **111,794** | **21.04%** |

The remaining 78.96% of this AAPL sample traded on other OPRA venues. The mapping lists 20 option venues; 18 appear in this one-symbol sample. Absence of prints from two venues on one symbol/date is not evidence of a feed-coverage gap.

**Interpretation:** C1-only participant flow can be a narrow view of whole-market option activity. Even all four Cboe Open-Close venues represented only about one fifth of this AAPL sample. Do not generalize these percentages beyond AAPL on 2026-01-07.

### Timestamp/schema gate

The official Option Trades v1.3 specification describes market_date as yyyy-mm-dd and quote_datetime as a full U.S. Eastern timestamp to milliseconds (yyyy-mm-dd hh:mm:ss.000). The public sample instead uses market_date like 1/7/2026 and quote_datetime like 21:30.4 for all 74,999 valid rows.

- Daily volume aggregation can use the parsed market_date; it does not require an intraday clock.
- Intraday event studies, time-of-day features and sequencing from quote_datetime are **not approved** until this sample/spec discrepancy is explained.
- canceled_trade_condition_id is legacy and the current specification says it is always zero; it is not a usable corrections feed.
- Trade conditions are retained without exclusions. No aggressor direction is inferred from NBBO location in this phase.

## 2. Correcting the C1 Open-Close volume denominator

The Phase 114 sample is a 20% C1 series sample for **2025-03-28**: 23,179 option-series rows across 1,553 underlyings. The participant buckets reconcile exactly:

- one-sided buy volume: 2,253,420;
- one-sided sell volume: 2,253,420;
- total_exchange_vol: 4,506,840;
- total_industry_vol: 12,228,281.

The EOD specification explicitly defines total_exchange_vol as electronic volume on the exchange **counting both sides of a trade**. It also states that the preliminary file sources total_industry_vol from OPRA while the final file uses OCC-authoritative values. The sampled file is the final version. Therefore the correct one-sided C1 proxy in this sample is:

\[
\frac{\sum \text{buy-side C1 volume}}{\sum \text{total industry volume}}
=\frac{2{,}253{,}420}{12{,}228{,}281}
=18.43\%.
\]

For comparison, the unadjusted total_exchange_vol / total_industry_vol ratio has median 0.50 and 90th percentile 2.00. That is a two-sided ratio, not market share. After using one side, the series-level proxy median is 25% and p90 is 100%; the volume-weighted sample proxy is 18.43%.

This remains **descriptive only** because the file is a 20% series sample. Preserve preliminary/final file versions because Cboe specifies OPRA-sourced total_industry_vol in preliminary files and OCC-authoritative values in final files. The proper denominator for future work should be OPRA-wide Option Trades or another independently reconciled all-venue feed.

The legacy 335-symbol universe appears in this sample for 288 names (85.97%). This is a historical coverage diagnostic only; 335 is not the research universe and must not cap future discovery. The eventual universe must include historical optionable securities, ticker changes and delisted names.

## 3. Why there is no direct cross-source reconciliation yet

The Option Trades sample is AAPL on 2026-01-07. The Open-Close sample is 2025-03-28. They share AAPL but **not a trade date**, so no same-day contract-level venue-share comparison is possible.

The separate Option EOD Summary sample is 2023-08-25, with 32,672 rows across only four underlyings (SPY, TSLA, ^SPX and ^VIX); only TSLA overlaps the legacy 335-symbol benchmark. It is useful for schema feasibility, not proof of broad universe coverage.

No cross-date ratios are treated as independent validation.

## 4. Historical coverage and availability

The current Cboe FAQ lists Option EOD Summary and Option Trades from January 2010, while the product-page audits previously recorded January 2012. Use **January 2012 as the conservative advertised start** until the discrepancy and actual archive boundaries are resolved.

Cboe says daily option files for a trade date are normally delivered the following day, typically 00:05–03:00 U.S. Eastern, but can be delayed until after the next market open. The Open-Close EOD specification separately describes preliminary and final files the next morning, typically 00:30–01:00 ET; the final file can update Total Industry Volume and Open Interest from OCC. For strict PIT, retain actual first-received timestamps and file versions. Do not assign a universal 00:05 or 00:30 historical availability time.

## 5. Source decision and next gates

| Source | Current role | Decision |
|---|---|---|
| Cboe Open-Close EOD | Cboe-venue capacity × buy/sell × open/close | Conditional daily source; one-sided volume normalization mandatory |
| Cboe Option Trades | All-venue daily denominator and trade/quote context | Conditional; one-symbol sample only; intraday timestamp gate unresolved |
| Cboe Option EOD Summary | OPRA-wide volume, OI, 15:45 IV/Greeks context | Conditional; current public sample too narrow for coverage approval |
| Cboe TBT / GRK | Execution and trade-time Greeks | Secondary; retain Phase 140 limitations |

Before any alpha test:

1. Obtain same-date, same-underlying, same-contract data across Open-Close and OPRA-wide Option Trades, with full-population and series-key reconciliation.
2. Verify historical availability and missing dates, including delisted and inactive underlyings; do not limit the universe to 335.
3. Preserve actual file first-received timestamps, preliminary/final versions and corrections.
4. Resolve Option Trades timestamp conformance before intraday use.
5. Preregister trade-condition handling before calculating directional flow.
6. Compare any future flow feature incrementally against frozen LTM/F80, with identical exposure/costs, chronological OOS, bootstrap and issuer LOO.

**No alpha result is claimed.** No forward returns were used, no purchase or vendor contact occurred, and F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Official references

- [Cboe Option Trades v1.3 specification](https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf)
- [Cboe DataShop FAQs](https://datashop.cboe.com/faqs)
- [Cboe Open-Close EOD v1.3 specification](https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf)
- [Cboe Open-Close factsheet](https://datashop.cboe.com/documents/Cboe_Open-Close_Factsheet.pdf)
