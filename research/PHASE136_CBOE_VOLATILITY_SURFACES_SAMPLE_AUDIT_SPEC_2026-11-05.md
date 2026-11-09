# Phase 136 — Cboe Volatility Surfaces public-sample schema audit

**Date:** 2026-11-05  
**Status:** preregistered public-sample audit only. No paid historical download, return test, vendor contact or production change.

## Question

Does the current public Cboe Volatility Surfaces sample provide a machine-readable, internally coherent example of all four documented surface files, with usable calculation timestamps, IV values, strikes and confidence fields?

## Source

- Product: https://datashop.cboe.com/volatility-surfaces
- Public sample link exposed by the current page: https://datashop.cboe.com/download/sample/281
- File specification (v1.0, April 2025): https://datashop.cboe.com/documents/VolatilitySurfacesSpecifications%20(1).pdf

The product page advertises daily EOD files and historical data from August 2011. The sample is public and does not require a data purchase. This audit downloads only that sample and emits aggregate metadata; it must not upload raw market data or a list of sample symbols.

## Expected files and schema

The product page/specification describes four files:
1. Expiration Specific Delta Relative
2. Expiration Specific Price Relative
3. Constant Maturity Delta Relative
4. Constant Maturity Price Relative

Common fields include underlying symbol, calculation timestamp and underlying price. Expiration-specific files should contain expiry; constant-maturity files should contain maturity. Delta-relative files contain IV/strike/confidence columns by delta. Price-relative files contain IV/strike/confidence columns by percentage of underlying price.

Confidence values in [0,1] are valid; the specification also documents negative extrapolation/flat-lining codes -1, -2, -5 and -6. Confidence below 0.5 is a quality warning, not a parse failure.

## Fixed audit rules

- Download the exact public sample URL with bounded retries and a 60-second request timeout.
- Verify ZIP integrity and inventory all CSV members, including nested ZIP members if present.
- Infer each file type from its filename and/or schema.
- Validate required fields, numeric IV/strike/underlying-price cells, timestamp format, duplicate surface keys and confidence domain.
- Report row counts, unique underlying count, timestamp counts, IV/confidence completeness, negative confidence codes and hashes. Do not emit raw rows or sample symbol lists.
- Tests use synthetic fixtures only and do not depend on the network.
- If the public sample does not include all four files, record the exact gap; do not extrapolate sample coverage to the full product.

## Explicit non-goals / gates not resolved

A public sample does not establish:
- actual date-by-date history back to August 2011;
- broad universe coverage or retention of inactive/delisted underlyings;
- historical file-delivery/first-publication timestamps;
- revisions, missing-date policy, full pricing or licensing terms;
- predictive information or incremental alpha.

The calculation timestamp is not a file-publication timestamp. No historical PIT claim is authorized. The next-session/extra-session delay sensitivities remain provisional until actual historical receipt evidence exists.

No return data, forward returns, alpha, model or production settings are used or changed. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
