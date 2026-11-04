# Phase 53B — OCC Volume Query full-universe preliminary results
Date: 2026-11-04

## Execution reviewed
- Initial full-universe run: [41762473953](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762473953), artifact 13291422118.
- Unit tests passed and 670 ticker/date queries completed.
- The run's schema gate was overly strict: it required `contractDate`, which the all-series response does not return. The artifact was independently re-audited using the actual returned fields; a corrected parser/gate is running in [41763109144](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763109144), with a latest-commit run queued as 41763113005.

## Correct interpretation of the response

With `contractDt` omitted, OCC returns aggregate options volume by underlying/root, account type, call/put and exchange. The returned schema is:

`quantity, underlying, symbol, actype, porc, exchange, actdate`

It does **not** return strike, expiry/contractDate, buy/sell side, open/close status or OI. Therefore this is an underlying-level account-type call/put volume feature, not contract-level flow.

## Preliminary full-universe coverage

| Report date | Valid ticker responses | Exact frozen-335 coverage |
|---|---:|---:|
| 2025-01-03 | 325/335 | 97.01% |
| 2026-11-02 | 320/335 | 95.52% |
| Combined | 645/670 | 96.27% |

The independent artifact reparse found valid account-type values C/F/M, call/put values C/P, and Activity Date matching the requested date in all valid rows.

The 2024-01-03 boundary probes for AAPL, NVDA and TSLA returned OCC's explicit `Report date cannot be prior to 2 years` message. This confirms the Volume Query's approximately 24-month retention limit.

## Decision

- Preliminary recent ticker coverage: PASS.
- Data depth for multi-cycle OOS: FAIL (24-month limit).
- PIT publication timestamp: NOT VERIFIED.
- Economic information: aggregate call/put volume by account type; no trade direction, opening/closing, strike, expiry or OI. It can be retained only as a recent complementary hypothesis, not a standalone Smart Money signal.
- Corrected parser/gate run remains in progress; no forward returns or alpha test.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
