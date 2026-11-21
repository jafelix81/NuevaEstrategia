# Phase 540 — CFTC TFF prospective net-position / open-interest feature audit

**Audit date:** 2026-11-21 UTC  
**Disposition:** normalized positioning ratios computed from the two available prospectively captured vintages; directions remain mixed. Descriptive feature-construction check only. No alpha test or signal admission.

## 1. Scope and point-in-time controls

Compared the two prospectively captured CFTC Traders in Financial Futures (TFF) observations currently present in the append-only event ledger:

| Report date | First receipt UTC | Capture run |
|---|---|---:|
| 2026-11-10 | 2026-11-18 03:44:57Z | [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204) |
| 2026-11-17 | 2026-11-21 03:17:36Z | [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977) |

The latest capture contains one new report per contract for four U.S. equity-index futures contracts. The total historical archive has 3,043 rows, but historical backfill is excluded from derived-feature eligibility. Only these prospective first-receipt events were used.

The latest report was received after the Friday, 2026-11-20 U.S. equity close. Its earliest executable regular equity session is Monday, 2026-11-23. Do not use its 2026-11-17 report date as the feature-availability date.

## 2. Feature definition

For each TFF trader category and contract:

`NetPosition = Long - Short`

`NormalizedNet = NetPosition / OpenInterest`

The change is computed between consecutive prospectively captured reports:

`DeltaNormalizedNet = NormalizedNet(t) - NormalizedNet(t-1)`

This normalizes the scale across contracts and partially accounts for changes in total open interest. It is not a direct measure of capital, beneficial ownership, directional stock exposure or an individual trader's intent. TFF categories are regulatory reporting classifications, not a verified “smart money” label.

## 3. Latest normalized net positioning

<small>Values are percentages of contract open interest, using report date 2026-11-17.</small>

| Contract | Asset managers | Dealers | Leveraged funds |
|---|---:|---:|---:|
| E-mini S&P 500 | +42.68% | -37.55% | -11.21% |
| Nasdaq Mini | +27.97% | -30.25% | -3.69% |
| DJIA x $5 | -9.24% | +1.27% | +4.13% |
| Russell E-mini | +6.67% | +2.71% | -9.21% |

## 4. Change versus prior prospective report

<small>Percentage-point change in normalized net positioning from report date 2026-11-10 to 2026-11-17.</small>

| Contract | Asset managers | Dealers | Leveraged funds | Open-interest change |
|---|---:|---:|---:|---:|
| E-mini S&P 500 | -2.62 pp | -1.11 pp | +3.82 pp | +3.93% |
| Nasdaq Mini | +2.76 pp | +4.42 pp | -8.52 pp | +2.67% |
| DJIA x $5 | -11.74 pp | +9.85 pp | +2.55 pp | +0.34% |
| Russell E-mini | +2.21 pp | -2.34 pp | +0.87 pp | +4.35% |

The signs differ by index and category. The largest move is the DJIA asset-manager net/OI ratio, which fell 11.74 percentage points, while the dealer ratio rose 9.85 points. Leveraged funds moved in opposite directions across Nasdaq and the other contracts. This is not a uniform risk-on or risk-off positioning pattern.

## 5. Research interpretation and limitations

- There are only **two** prospectively observed reports per contract. No stable rolling percentile, z-score, persistence or reversal estimate can be formed.
- The first observation is a prospective baseline, not a license to backfill historical features from the 3,043-row archive.
- The report date is the position snapshot date, not public availability. The next-session rule uses the first-receipt timestamp.
- Index-futures categories are broad market-regime context. They cannot identify which individual equities were accumulated or distributed.
- Net/OI ratios do not distinguish new opening positions from closing/rolling activity and are affected by contract composition and reporting-category definitions.
- Any future feature must be calculated using only prior prospectively received events, with category/contract-specific scaling and a timestamped session calendar.
- Before a test, preregister whether the hypothesis concerns crowding, change in positioning, divergence across categories, or persistence. Do not select among these after inspecting forward returns.

## 6. Decision

**Retain as a prospective market-regime feature candidate; no alpha claim.** Continue accumulating natural weekly TFF observations. Do not backfill feature history, create a trading signal, or run a return test yet.

A future evaluation must use the earliest executable session after each first receipt, compare incremental information against frozen LTM/F80 at identical exposure and costs, and use chronological OOS, block bootstrap and leave-one-report/event-block-out controls. It must also distinguish a regime filter from a stock-selection signal.

## Frozen controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` unchanged.
- No signal admitted; no backtest, OOS, bootstrap or LOO performed.
- Universe, parameters, holding period, exposure, costs, holdout and production unchanged.
