# Phase 61 — ORATS Near-EOD public sample audit results

Date: 2026-11-04  
Run: [41787946992](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41787946992)  
Job: `126434320461` — success  
Artifact: [13301409440 — phase61-orats-near-eod-public-sample](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41787946992/artifacts/13301409440)  
Branch: `phase61-orats-near-eod-sample-audit`

## 1. Download and sample coverage

The public sample ZIP downloaded successfully on the first attempt.

| Metric | Result |
|---|---:|
| HTTP status | 200 |
| ZIP bytes | 66,808,802 |
| SHA-256 | `e04a37310b0f453fedc03a000c55adfc517a119279150173916ebdc5fb514570` |
| CSV members | 1 |
| Trade date | 2024-01-03 |
| Rows | 716,822 |
| Unique underlyings | 5,787 |
| Current frozen-candidate tickers present | 324/335 |
| Current candidate-list coverage | 96.72% |

The 11 absent current tickers were ALAB, AMTD, DJT, GEV, HAPN, LOT, RDDT, TELFY, TEM, WAY and XYZ. This is not evidence of missing historical coverage: several may not have been listed or optionable on 2024-01-03. The 335-name list is current, not a point-in-time F80 universe.

## 2. Schema result

<badge>PASS — one-date sample schema</badge>

The 39-column file includes:
- `ticker`, `trade_date`, `expirDate`, `strike`.
- OPRA symbol fields `cOpra` and `pOpra`.
- Call/put volume and prior-night OI: `cVolu`, `pVolu`, `cOi`, `pOi`.
- Bid/ask prices and IVs for calls and puts.
- `smoothSmvVol`, `delta`, `gamma`, `theta`, `vega`, `rho`, `phi`.
- `stkPx` and `spot_px`, both derived from option prices rather than independent underlying stock prices.

All required core fields were present and 100% non-null in the sample.

### Zero values are not missing values

| Field | Positive rate | Zero rate |
|---|---:|---:|
| Call volume | 16.41% | 83.59% |
| Put volume | 13.36% | 86.64% |
| Call OI | 50.61% | 49.39% |
| Put OI | 41.45% | 58.55% |
| Call bid | 78.95% | 21.05% |
| Put bid | 73.22% | 26.78% |
| Call bid IV | 45.88% | 54.12% |
| Put bid IV | 41.77% | 58.23% |
| Smoothed IV | 100.00% | 0.00% |

Ask IV was positive on 97.86% of call observations and 97.31% of put observations. Delta was positive on 94.15% of rows and gamma on 86.24%; vega was positive on 100%.

The high zero rates for volume, OI and bid-side IV are not schema missingness. They require economic/quote-quality filters; they must not be silently converted to missing or treated as valid positive liquidity.

## 3. Contract and PIT limitations

- No explicit multiplier, deliverable, shares-per-contract or contract-size field was found in the 39-column sample. The `cOpra`/`pOpra` symbols may support an external OCC contract-reference join, but that mapping remains untested. Do not assume a universal multiplier of 100.
- `stkPx` and `spot_px` are option-implied reference values, not independent stock prices.
- ORATS documents the snapshot at approximately 3:46 p.m. ET; volume is cumulative only through that snapshot.
- Call/put OI is OCC data updated the previous night.
- The sample's HTTP Last-Modified header is 2024-03-12, while the data trade date is 2024-01-03. This is a sample-file hosting timestamp, not evidence of the historical daily publication time.
- A single date cannot validate the claim that delisted tickers are retained from 2007 or that expired contracts and adjusted deliverables remain queryable.

## 4. Gate decision

| Gate | Result |
|---|---|
| Download and ZIP integrity | PASS |
| Core schema | PASS |
| One-date current-list coverage | 96.72%, measured only |
| Historical PIT F80 coverage | NOT TESTED |
| Delisted/expired retention | NOT TESTED |
| Contract multiplier/deliverable | External reference required |
| Historical publication timestamp | NOT VERIFIED |
| Forward-return / alpha test | NOT AUTHORIZED |

ORATS is now the preferred low-cost candidate for historical options context (quotes, volume, OI, IV and Greeks). It does not classify buyer/seller aggressor flow or participant identity, so it cannot be the directional Smart Money signal on its own. Pair it with OptionMetrics TradeFlow only after TradeFlow's sample and classification methodology pass.

## 5. Decision and next work

Before any purchase:
1. Ask ORATS whether it can provide a custom 335-symbol historical extract instead of the full ~500 GB archive.
2. Request sample dates across 2015, 2018, 2020, 2022, 2024 and 2026, including known delisted issuers and expired/adjusted option roots.
3. Confirm professional/institutional licensing if the research will be used in a business context.
4. Resolve `cOpra`/`pOpra` to point-in-time OCC contract terms and multipliers.
5. Verify file corrections and historical delivery timestamps.

No data purchased, no forward returns or alpha tests run, and no strategy change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
