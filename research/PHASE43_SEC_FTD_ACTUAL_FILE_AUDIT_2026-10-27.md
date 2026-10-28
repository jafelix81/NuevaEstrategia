# Phase 43 — SEC FTD actual-file audit

## Objective

Advance the SEC fails-to-deliver (FTD) hypothesis from feasibility to an actual-file gate without touching the frozen F80/LTM baseline.

## Source verification

SEC's official Fails-to-Deliver page currently documents coverage from February 2004 through September 2026. From July 2009 onward, each month is split into two files: first half available at month-end and second half around the 15th of the following month. The raw file is pipe-delimited and contains settlement date, CUSIP, ticker, issuer, fails quantity, and prior-day closing price.

The SEC explicitly defines the quantity as an aggregate balance outstanding at a settlement date, not a daily flow. FTD can arise from both long and short sales and is not evidence by itself of naked short selling.

Representative official files selected for parser validation:
- `https://www.sec.gov/files/data/fails-deliver-data/cnsfails201801a.zip`
- `https://www.sec.gov/files/data/fails-deliver-data/cnsfails202609b.zip`

The 2018 file tests a mature historical period; the 2026 file tests the current format.

## PIT rule

For a settlement date `D`, the earliest defensible knowledge date is the SEC publication/availability date of that half-month file, not `D`. For July 2009 onward:
- first-half file: use a conservative month-end knowledge date;
- second-half file: use a conservative 15th-of-next-month knowledge date;
- never use the settlement date as the information date.

Pre-July-2009 data remain secondary because SEC states that the monthly files are quarterly archives and accuracy is not guaranteed. Pre-2008-09-16 observations also have a 10,000-share reporting threshold.

## Required gate

1. Download representative official files.
2. Parse ZIP/text without relying on current web-page formatting.
3. Validate exact six-field schema and numeric/date types.
4. Confirm duplicate behavior and settlement-date ordering.
5. Confirm ticker/CUSIP fields are populated at usable rates.
6. Record publication/knowledge-date metadata separately from settlement date.
7. Only after the parser gate passes, measure frozen-universe coverage and ticker/CUSIP continuity.
8. Only after universe/PIT coverage passes, construct FTD hypotheses and test incremental information versus frozen LTM/F80 with identical exposure/costs and chronological OOS validation.

## Candidate features (not yet tested)

- FTD level scaled by price-implied market value or shares outstanding when an ex-ante share denominator is available.
- log(1 + FTD) level and percentile within each symbol's own history.
- change in FTD balance between successive observations.
- persistence / consecutive reporting periods with elevated FTD.
- acceleration or reversal in FTD balance.
- divergence between FTD and FINRA short interest / short flow where both are PIT-valid.

No feature will be interpreted as directional short pressure a priori.

## Decision state

`ACTUAL_FILE_GATE_PENDING_RUN`

The Phase 43 workflow exists on `main`, but the prior trigger commit did not produce a corresponding Actions run. A fresh push-trigger is therefore being issued now; no alpha work is authorized until the actual-file audit completes. No alpha conclusion. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
