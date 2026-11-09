# Phase 173 — Cboe Option EOD Summary: OI temporal semantics and PIT adjudication

**Date:** 2026-11-07  
**Decision:** retain as a conditional full-OPRA volatility/OI context source; do not admit to predictive research until first-receipt vintages, broad point-in-time universe coverage and licensing are verified.

## 1. Why this phase exists

Phase 55 already audited the public Option EOD Summary sample on the separate branch `phase55-cboe-option-eod-summary-feasibility`. Its successful hosted run was [41763011186](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763011186), with artifact [13290668468](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763011186/artifacts/13290668468). This phase does **not** redownload or repeat that sample audit. It recovers the result into the current research line and resolves a material temporal-semantic issue from Cboe's current FAQ.

## 2. Source and historical coverage

Official sources:

- Product page: https://datashop.cboe.com/option-eod-summary
- DataShop FAQ: https://datashop.cboe.com/faqs

The product page describes daily OPRA-wide U.S. stock, ETF and index option data, with two quote snapshots (15:45 ET and product-dependent EOD), EOD OHLC, trade volume, VWAP and open interest, plus optional 15:45 implied volatility and Greeks. Options on futures and non-U.S. markets are excluded.

The product page states historical availability from **January 2012**; the FAQ's historical-start table states **January 2010**. Until Cboe resolves the discrepancy in writing, use January 2012 as the conservative research floor. Neither statement proves that every symbol/series is continuously available or that inactive/delisted underlyings are covered.

## 3. Recovered public-sample evidence (Phase 55)

The prior successful sample audit found:

| Metric | Result |
|---|---:|
| Sample date | 2023-08-25 |
| Product variants | 2 |
| Rows per variant | 32,672 |
| Underlyings | 4: ^SPX, SPY, TSLA, ^VIX |
| Legacy 335-universe overlap | 1 ticker (TSLA) |
| Base EOD field non-null rate | 100% in both variants |
| Optional Calcs field non-null rate | 100% in both variants |
| Positive IV rate | 92.75% / 91.26% |
| Positive OI rate | 77.20% |
| Positive trade-volume rate | 40.35% |

The sample proves that the documented base and Calcs columns can be populated. It does **not** estimate universe coverage: four demonstration underlyings are not a representative sample of the 335-name legacy list or the broader PIT universe. Zero IV/Greek values must remain invalid/unavailable observations for volatility calculations; zero OI and volume may be legitimate inactive-series observations.

## 4. Critical open-interest temporal semantics

Cboe's FAQ says DataShop uses the previous night's OCC "end of day open interest" at the **start of the trading day**. That value remains static throughout the session and is replaced the following morning with a new OCC value.

Therefore:

- For quote date (t), the OI field is a **start-of-day snapshot sourced from the prior night's OCC EOD OI**, not a measurement of positions newly open at the close of (t).
- (OI_t - OI_{t-1}) is a change between consecutive start-of-day snapshots. It reflects the prior overnight OCC update and must not be labelled same-day intraday opening flow.
- A valid point-in-time knowledge timestamp is the latest of (i) the OCC value's actual availability, (ii) the first receipt of the exact Cboe file/vintage, and (iii) availability of the contract and underlying identity mappings used by the feature.
- The FAQ's semantic description does not prove that a historical Cboe file was delivered before a particular decision. Historical first-receipt timestamps, corrections and replacement vintages remain unavailable in this audit.

A backtest must not infer file receipt from quote date, 15:45 snapshot time, EOD time or trade date. If first receipt cannot be evidenced, the affected historical feature remains PIT-ineligible. For a daily strategy, the conservative fallback is to use the file only at the first documented decision after its actual receipt.

## 5. Snapshot timing and feature boundaries

- 15:45 NBBO and optional IV/Greeks are same-session market observations. They are not available to a strategy before the 15:45 snapshot.
- EOD NBBO, OHLC, volume and VWAP are same-session closing observations and must be used only after the applicable market close.
- The product page describes daily file delivery but this audit has no historical first-receipt ledger. The actual file receipt, not the nominal snapshot time, controls feature availability.
- Underlying bid/ask is supplied for stocks and ETFs; index underlying quotes are not generally included without the relevant Cboe Global Indices license.
- Option EOD Summary contains no participant capacity, aggressor side or open/close classification. It is context, not signed institutional flow.

## 6. Complementarity, not substitution

A future complementary test may align Option EOD Summary with Cboe Open-Close by date and validated option-series identity:

- Option EOD Summary: OPRA-wide NBBO, volume, start-of-day OI and optional 15:45 IV/Greeks.
- Open-Close: participant-capacity, buy/sell and open/close aggregates on Cboe venues only.

The join must preserve the narrower Cboe-venue coverage and missingness. It must not extrapolate Cboe participant composition to the entire OPRA market. Participant categories are not beneficial-owner identities and do not prove informed trading.

## 7. Admission gates and decision

| Gate | Status |
|---|---|
| Product exists in current catalog | PASS |
| Public sample base/Calcs schema | PASS (Phase 55 sample only) |
| Conservative historical floor | CONDITIONAL: Jan 2012 pending written resolution of Jan 2010 FAQ conflict |
| Broad PIT universe / inactive-name coverage | NOT TESTED |
| Historical first-receipt and correction vintages | BLOCKED |
| OI temporal semantics | RESOLVED: prior-night OCC EOD at start of quote date |
| Exact price and internal-use licensing | NOT CONFIRMED |
| Predictive / incremental alpha | NOT TESTED |

**Decision:** keep Option EOD Summary as a plausible daily options-volatility/OI context source, potentially complementary to Open-Close. Do not construct a predictive feature panel or run forward-return tests until first-receipt/vintage handling and point-in-time security/contract coverage are demonstrated. No vendor contact, purchase, return test, bootstrap/LOO, OOS, final-holdout use or production change was made.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
