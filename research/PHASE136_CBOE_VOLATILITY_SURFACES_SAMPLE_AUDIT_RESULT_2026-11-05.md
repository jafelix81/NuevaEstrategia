# Phase 136 — Cboe Volatility Surfaces public-sample audit result

**Date:** 2026-11-05  
**Status:** **PASS_PUBLIC_SAMPLE_SCHEMA**; historical coverage, broad universe coverage and strict PIT remain unverified. No return test or paid-data access.

## 1. Execution and reproducibility

- Workflow [42115525546](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546) completed successfully. Auditor compiled, all six offline regression tests passed, the public sample was downloaded and the aggregate artifact was uploaded.
- Artifact [13455975956](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115525546/artifacts/13455975956), 2,425 bytes; ZIP SHA-256: `a0f3d7fd5dbde7302dbacdcc6cf368e342a5d7d2880af35535fa182fc790829a`.
- The exact public sample endpoint returned HTTP 200, `application/x-zip-compressed`, 53,058 bytes; sample ZIP SHA-256: `d3cb21be928dc1001a54f697aed5009e96da9c824d233a0978a4c8998e81a5e3`.
- The sample contained four CSV members dated 2025-04-07. Raw sample bytes and symbol names were not retained or uploaded.
- An intermediate run [42115519293](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42115519293) failed only because its test still expected negative extrapolation codes to count as low positive confidence. The auditor and regression expectation were corrected; the final run above passed. This was a test-definition correction, not a source-data failure.

## 2. Schema and sample coverage

All four documented file types were present and passed required schema, numeric, timestamp and duplicate-key checks.

| Surface file | Rows | Underlyings | IV cells valid | Confidence cells valid | Negative codes |
|---|---:|---:|---:|---:|---:|
| Constant maturity / delta | 44 | 1 | 660/660 | 660/660 | 60 |
| Constant maturity / price | 44 | 1 | 748/748 | 748/748 | 70 |
| Expiration specific / delta | 136 | 1 | 2,040/2,040 | 2,040/2,040 | 0 |
| Expiration specific / price | 136 | 1 | 2,312/2,312 | 2,312/2,312 | 559 |
| **Total** | **360** | **1 unique underlying** | **5,760/5,760** | **5,760/5,760** | **689** |

- All 360 row timestamps parsed successfully; no duplicate surface keys were found.
- All reported IV and strike cells were numeric and positive; all confidence cells were either in [0,1] or one of the documented negative status codes.
- The 689 negative confidence values are extrapolation/flat-lining status codes, not ordinary confidence scores. They must be excluded from IV feature construction.
- A further 32 positive confidence cells in the expiration-specific price-relative file were below 0.5. These also fail the specification's recommended reliability threshold.
- The 4 file types contain one underlying only. This validates the schema, not broad market or historical universe coverage.

The sample shows calculation timestamps clustered around approximately 09:40, 15:45, 16:00 and 16:15 ET, with millisecond differences across rows. The 16:15 snapshot is documented as index-only; the symbol was deliberately not retained in the aggregate artifact, so that specific row-level rule was not independently adjudicated.

## 3. Source interpretation and gates

The sample confirms that the public file is machine-readable and exposes the expected surface structures. It does **not** prove that files exist on every date from the product's advertised August 2011 start, that inactive/delisted underlyings are retained, or that the sample's single underlying is representative.

The calculation timestamp is not a publication or receipt timestamp. No `Last-Modified` or `ETag` was supplied by the sample endpoint, and the HTTP Date is only the time of this audit's retrieval. Historical first-publication and revision timing remain unverified.

The product is a Cboe Hanweck Volera interpolated surface derived from listed-option mid-volatility inputs. It is a volatility-context source, not raw trade flow, signed customer demand or participant identity.

**Decision:** retain Cboe Volatility Surfaces as the leading IV/skew context candidate, with a strict confidence filter and a hard PIT/coverage gate. Do not promote it to an alpha test yet.

## 4. Research implications

A future preregistered candidate family may include:
- downside/upside skew using price-relative 90% versus 110% IV, only where both points have acceptable confidence;
- constant-maturity ATM term structure, e.g. 30D versus 90D, only where both tenors exist and pass confidence checks;
- daily changes in these measures, not their level alone, to distinguish new information from persistent risk premia.

These are feature definitions to be frozen before any return analysis. They are not yet computed as time series and have no demonstrated predictive value.

Before alpha testing, require actual historical archive probes across early/middle/recent dates, multi-symbol coverage including inactive/delisted names, effective-dated underlying identity, missing-date/revision policy, and historical file-delivery evidence. If strict PIT cannot be demonstrated, any delay sensitivity must be labelled conditional rather than PIT-proven.

No forward returns, alpha, bootstrap or LOO tests were run. No vendor was contacted, no data purchased, no cart action or terms acceptance occurred, and no production setting changed. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
