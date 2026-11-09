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

`ACTUAL_FILE_GATE_TRIGGERED_2026-10-30`

The Phase 43 workflow is present on `main` and a fresh main-branch content commit has now been issued to trigger the actual-file audit. No alpha work is authorized until the workflow validates the representative files and universe/PIT coverage. No alpha conclusion. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-05 execution reconciliation

The latest Actions history contained no completed or active run for this workflow, despite the earlier state note saying the actual-file gate had been triggered. That note was premature. The workflow is being made branch-runnable and re-executed from the Phase 99/100 research branch. This remains a parser/schema audit only; no forward-return test is included.


## 2026-11-05 — Actual-file revalidation completed (Phase 101)

Final successful run: [41970505481](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41970505481)  
Artifact: [SEC FTD parser audit](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41970505481/artifacts/13389273464)

The first download attempt was blocked with HTTP 403 because the request did not identify the organization/contact. The SEC request was updated to use the firm's existing contact identity. The next attempt exposed a changed path for the 2026 archive; the exact official page link was followed and the URL corrected. The final run downloaded and parsed both samples.

| Sample | Valid records | Unique symbols | Settlement dates | Trailer record count | Trailer quantity total | Result |
|---|---:|---:|---|---:|---:|---|
| Jan 2018 first half | 43,567 | 9,824 | 2018-01-02 to 2018-01-12 | exact match | exact match | PASS |
| Sep 2026 second half | 66,693 | 13,394 | 2026-09-15 to 2026-09-30 | exact match | exact match | PASS |

Both files had:
- Exact six-field header and one TXT member in the ZIP.
- Zero malformed data records after recognizing the two documented trailer lines.
- Zero invalid settlement dates, fail quantities, or prices.
- Trailer record counts equal to parsed record counts.
- Trailer total share quantities equal to the calculated sum of row quantities.

This validates the actual ZIP path, parser schema and internal record/quantity controls at two distant dates. It does not yet validate all intervening files, CUSIP lifecycle mapping, delisted return linkage, or point-in-time publication timestamps.

## Source interpretation and gates

The SEC's official page reports data from February 2004 through September 2026. Before September 16, 2008, only balances of at least 10,000 shares were included; from that date, all securities with a positive fail balance are included. Treat this as a structural break and do not pool the pre-2008 threshold regime without an explicit regime treatment.

The file contains the aggregate net fail-to-deliver balance as of each settlement date, not a daily flow and not the age of the fails. The SEC explicitly warns that fails can occur on both long and short sales and are not evidence by themselves of abusive or naked short selling. The series is therefore a settlement-pressure hypothesis, not a direct short-interest or informed-trading measure.

The stated release convention is first-half data at month-end and second-half data about the 15th of the next month; the SEC does not guarantee exact posting dates. A backtest must use an independently validated publication timestamp or a conservative lag after the scheduled release, not the settlement date.

Next gate: sample additional periods around 2008-09, 2018 and 2026; measure CUSIP/symbol collisions and ticker changes; link to a PIT security master including inactive securities; only then preregister a settlement-pressure hypothesis. No forward-return test or production feature is authorized by this audit.
