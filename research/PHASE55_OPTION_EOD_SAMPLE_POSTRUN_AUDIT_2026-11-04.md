# Phase 55 — Option EOD sample post-run audit
Date: 2026-11-04

## Execution
- Initial run: [41762853231](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762853231) exposed an overly strict sample-coverage gate.
- Corrected canonical run: [41763011186](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763011186), job 126354812938 — success; artifact 13290668468 — `phase55-option-eod-summary-sample`.
- Parser tests and corrected base-schema/Calcs gates: PASS. The 335-ticker coverage gate is explicitly not tested by this four-underlying demonstration sample.
- The sample contains two product variants: `no_cgi_subscription` and `cgi_or_historical`. Both carry the same 2023-08-25 sample option universe.

## Actual sample facts

| Metric | Result |
|---|---:|
| CSV rows per variant | 32,672 |
| Underlyings in sample | 4 |
| Underlyings | ^SPX, SPY, TSLA, ^VIX |
| Frozen-universe tickers in sample | 1 (TSLA) |
| Base EOD fields non-null | 100% |
| Optional Calcs fields non-null | 100% |
| IV > 0, no-CGI variant | 92.75% |
| IV > 0, CGI/historical variant | 91.26% |
| OI > 0 | 77.20% |
| Trade volume > 0 | 40.35% |

The sample proves the file schema and optional Calcs payload, not 335-ticker coverage. The 1/335 overlap is not a coverage estimate because the sample is a four-underlying demonstration.

Zero IV/Greek values occur even when fields are present. They must not be treated as valid volatility observations without a separate validity filter. Open interest and volume are non-null but frequently zero, which is expected for inactive contracts.

The sample ReadMe explains that the no-CGI daily-subscription variant reports zero underlying index values, while historical purchases (T+1) and CGI-licensed daily subscriptions include ^SPX underlying values. ^VIX underlying bid/ask is not supplied by default.

## Documentation discrepancy

The current Option EOD product page states historical availability from January 2012. The Cboe FAQ table lists January 2010 for Option EOD Summary. Treat January 2012 as the conservative floor until Cboe confirms the discrepancy in writing.

## Decision

- Schema: PASS in corrected run 41763011186.
- Calcs/IV: PASS for field presence, but valid-IV rate must exclude zero/invalid rows.
- Universe coverage: NOT TESTED.
- Historical depth: documented, but exact floor needs confirmation.
- Price/licensing and PIT delivery: quote and delivery timestamp still required.
- No forward returns or alpha test.
