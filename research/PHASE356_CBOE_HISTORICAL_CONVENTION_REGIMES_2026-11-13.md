# Phase 356 — Cboe Open-Close EOD historical convention regimes

**Date:** 2026-11-13 UTC  
**Branch:** `phase356-cboe-historical-convention-regimes`  
**Status:** `DOCUMENTED_REGIME_MATRIX_ONLY_NO_HISTORICAL_FILES_VALIDATED`  
**Parent:** Phase 355, draft PR #42

## Objective

Translate Cboe's published historical convention notes into an explicit exchange/date/field policy before any multi-year Cboe Open-Close EOD feature construction. The purpose is to prevent a historical backtest from treating different field definitions, OI dates, or session scopes as homogeneous.

## Official documentation reviewed

1. [Cboe Open-Close Volume Summary product page](https://datashop.cboe.com/cboe-options-open-close-volume-summary), accessed 2026-11-13. It documents historical start dates, overnight EOD delivery, C1 session coverage, and field-specific historical convention breaks.
2. [C1 Open-Close and Optsum Data Availability Change](https://datashop.cboe.com/c1-open-close-and-optsum-data-availability-change), published 2020-11-23. C1 Open-Close/Optsum is available from 2005-01-01.
3. [Cboe Option EOD Summary](https://datashop.cboe.com/option-eod-summary), accessed 2026-11-13. It documents OPRA-listed U.S. stock, ETF and index options; daily 15:45 and EOD snapshots; optional 15:45 IV/Greeks; and historical availability from January 2012.

## Documented historical regimes

| Field / property | Exchange | Documented regime | Research treatment |
|---|---|---|---|
| Historical start | C1 | 2005-01-03 | Separate legacy and modern schema handling |
| Historical start | BZX, C2, EDGX | 2018-01-02 | Common four-venue history cannot start before this date |
| File format | C1 | Format change in 2011 | Pre-2011 requires the legacy C1 parser; exact effective trading date is not stated on the product page |
| Open Interest / Previous Open Interest | C1 | Shifted one day ahead through 2019-10-04 | Quarantine from PIT features until the historical alignment direction is validated against files |
| Open Interest / Previous Open Interest | C2 | Shifted one day ahead through 2018-05-11 | Same quarantine rule |
| Open Interest / Previous Open Interest | BZX, EDGX | Start-of-day convention throughout history | Still require file-level and first-receipt validation |
| Total Industry Volume | C2 | Values doubled through 2018-05-11 | Candidate scale factor 0.5; do not apply until historical sample validation |
| Total Exchange Volume | C1 | Calculated as (B + S) / 2 through 2019-10-04; current convention is B + S | Candidate scale factor 2.0; do not apply until historical sample validation |
| Previous Close | C1 | C1-only last trade through 2019-10-04 | Not industry-wide; exclude from cross-venue price features or independently rebuild |
| Previous Close | C2 | C2-only last trade through 2018-05-11 | Same |
| Previous Close | BZX, EDGX | Industry-wide convention | File validation still required |
| Session scope | C1 | GTH coverage begins 2023-12-11; C1 files include RTH and GTH | Split or explicitly control pre/post-GTH regimes; do not compare blindly to RTH-only venue files |
| EOD availability | All Open-Close EOD | Overnight after midnight U.S. Eastern | This is a schedule, not proof of exact first receipt or immutable historical vintages |

The product page states that Total Industry Volume and Open Interest are supplied by third-party vendors as best-effort value-adds. These fields therefore need separate quality, revision and lineage controls.

## Conservative interpretation

- The field-specific breaks are not one global “Cboe history starts in 2005” regime. C1 has a longer history, while the other three exchanges begin in 2018.
- **2019-10-07 is the earliest candidate common four-venue date after the documented C1/C2 OI timing, C1 exchange-volume formula, C1 previous-close, and C2 previous-close breaks have ended.** This is a convention-based candidate window only; it is not a claim that actual files are available or complete on every date.
- The C1 GTH change on 2023-12-11 creates a later session-scope break. Any RTH-comparable analysis must split the sample there or prove that session components can be separated.
- The C1 pre-2011 format break must be handled by a separate parser. The vendor page identifies the year, not an exact effective trading date.
- Do not propagate the C1 `total_exchange_vol` scale factor to the 34 participant-side volume fields. Phase 355 validated their arithmetic on one 2025 sample only; historical participant-field units remain unverified.
- Do not shift historical OI automatically from the phrase “shifted one day ahead.” Validate the exact mapping direction using adjacent-date raw files and an independent as-of reference first.
- Do not assume a next-day delivery schedule is an exact first-receipt timestamp. Historical first-receipt UTC and correction-vintage archives remain unproven.

## Automated policy matrix

The Phase 356 module and 17 offline tests encode the published date boundaries and reject dates before each venue's documented history start. The workflow produces a metadata-only JSON matrix.

- The matrix does not download or inspect historical subscription files.
- It applies **zero** numeric transforms.
- It admits no historical or prospective PIT data.
- It authorizes no return, alpha, bootstrap, LOO or holdout test.
- It leaves F80 frozen.

## Decision

**Pass the documentation-to-policy encoding gate only.** Retain Cboe Open-Close EOD as a conditional candidate, with 2019-10-07 as the earliest candidate common four-venue convention window for the listed core fields. Historical file availability, inactive/delisted underlying coverage, historical symbol/root identity, participant-field regime consistency, exact first-receipt times, correction vintages, session comparability and licensing remain unresolved.

The public C1 sample from 2025-03-28 cannot validate any of the historical breaks above. Next, if a permitted historical sample becomes available, validate each break with raw adjacent-day files and field-level identities before admitting even a diagnostic feature panel. Do not purchase data or contact Cboe without explicit authorization.

No alpha result, return test, production change, universe change, parameter change, capital change or F80 modification.
