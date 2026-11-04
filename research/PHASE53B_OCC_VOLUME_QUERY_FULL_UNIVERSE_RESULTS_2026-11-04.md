# Phase 53B — OCC Volume Query full-universe results
Date: 2026-11-04

## Canonical corrected execution

- Corrected run: [41763113005](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763113005), job 126356693552, artifact 13292225481.
- Three parser tests passed; all 670 ticker/date requests completed; zero HTTP/query errors.
- The run's completed job log was inspected directly. The output's `volume_query_data_gate` is PASS; its separate `historical_depth_gate` is FAIL_FOR_LONG_OOS.
- Earlier run 41763109144 is superseded for final metrics by this latest-commit run.

## Correct interpretation of the response

With `contractDt` omitted, OCC returns aggregate options volume by underlying/root, account type, call/put and exchange. The returned schema is:

`quantity, underlying, symbol, actype, porc, exchange, actdate`

It does **not** return strike, expiry/contractDate, buy/sell side, open/close status or actual open interest. This is an underlying-level account-type call/put volume feature, not contract-level directional flow.

## Corrected full-universe coverage

| Report date | Valid ticker responses | Exact frozen-335 coverage | Schema-valid rate |
|---|---:|---:|---:|
| 2025-01-03 | 325/335 | 97.01% | 97.01% |
| 2026-11-02 | 320/335 | 95.52% | 95.52% |
| Combined | 645/670 | 96.27% | 96.27% |

Additional log facts:
- No query errors across the 670 requests.
- Activity Date matched the requested report date in 100% of valid rows.
- Customer account type C was present for 325/325 valid tickers in 2025 and 318/320 in 2026.
- Firm account type F was present for 229/325 and 222/320, respectively.
- Market Maker account type M was present for 325/325 and 320/320, respectively.
- Call/put codes C/P were valid in all parsed rows.

The 2024-01-03 boundary probes for AAPL, NVDA and TSLA returned OCC's explicit `Report date cannot be prior to 2 years` message. This confirms the approximately 24-month retention limit.

## Decision

- Recent response/schema coverage: PASS at the two tested dates.
- Long-history/multi-cycle OOS depth: FAIL (24-month limit).
- Historical PIT publication timestamp: NOT VERIFIED. Do not treat reportDate as KnowledgeDate; if ever tested, use a conservative next-session availability rule.
- Economic information: aggregate call/put volume by account type and exchange, without trade direction, opening/closing, strike, expiry or OI.
- Retain only as a recent complementary hypothesis; do not use as standalone Smart Money flow or as a substitute for Cboe/MIAX open-close data.
- No forward returns or alpha test.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Reproducibility

The corrected parser is `research/phase53_occ_volume_query_universe_audit.py`; tests are `research/test_phase53_occ_volume_query_universe_audit.py`. The run artifact contains the ticker-date coverage CSV, sample rows and summary JSON. The log facts above are from the canonical corrected run, not the preliminary 41762473953 artifact.
