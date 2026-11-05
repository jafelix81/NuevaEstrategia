# Phase 133 — OCC Flex Reports historical contract-level OI feasibility audit

**Date:** 2026-11-05  
**Status:** Preregistered public-endpoint feasibility audit only; no return/alpha test.  
**Scope:** OCC Flex Reports endpoint with reportType=OI and optionType=E. This is a separate endpoint from the Daily Open Interest monthly market-total report and from the 24-month Volume Query.

## Research question

Can OCC Flex Reports provide reproducible daily contract-level equity-option open interest over enough historical dates to support a long chronological study, and does the returned file expose an identifiable option series/underlying?

Official endpoint documentation: https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/flex-reports-batch-processing

The documented parameters are reportType=OI (open interest) or PR (price), optionType=E (equity) or I (index), and reportDate=YYYYMMDD. The page gives an endpoint example for PR but does not state historical retention, release time, revisions, or the OI record layout. Those are empirical gates.

## Fixed historical probes

- 2018-01-03
- 2020-01-03
- 2022-01-03
- 2024-01-03
- 2025-01-03
- 2026-01-05
- 2026-11-04

These are fixed calendar dates chosen to span multiple market regimes. A failed date is recorded as unavailable/invalid; it is not silently replaced with a nearby successful date.

## Required diagnostics

For every request preserve:
- exact URL and requested report date;
- HTTP status, content type, Last-Modified, ETag, Date and response bytes;
- SHA-256 of the exact response bytes;
- detected container/file format and inner member names;
- exact parsed header and schema classification;
- row count, non-null OI count/rate, unique contract keys, duplicate rows;
- unique underlying/root count and its extraction method;
- explicit parse/error status.

No fixed 335-ticker universe is used. The report measures the full returned underlying/root breadth and date-to-date persistence. It does not claim security-universe coverage until an independent effective-dated broad security master, including inactive/delisted securities, is available.

## Preregistered feasibility gates

1. At least 5 of 7 fixed dates return non-empty, parseable contract-level OI data.
2. Successful dates span at least five years.
3. At least 95% of returned contract rows have numeric non-null OI.
4. A contract/series identifier is present (or can be deterministically reconstructed from documented series fields); an underlying-only aggregate does not pass the contract-level gate.
5. Underlying/root breadth and missing-date patterns are reported, not hidden by a frozen ticker list.

These are source feasibility gates, not evidence of tradable information.

## PIT and economic limitations

- reportDate is the observation date, not the public knowledge timestamp.
- Last-Modified/ETag/Date headers are retrieval metadata, not proof of first dissemination.
- OI is outstanding contract inventory; a change does not identify buyer/seller, aggressor side, opening/closing intent, beneficial owner, or informed trader.
- OCC OI alone does not provide historical IV/skew or Greeks. A separate quote/volatility source is required.
- Contract roots, adjusted options, corporate actions and underlying identity require an effective-dated crosswalk.
- Any future use must model a conservative next-session availability boundary and be tested against frozen LTM/F80 with chronological OOS, identical exposure/costs, bootstrap and issuer LOO.

## Decision

If historical depth or contract-level schema fails, archive the endpoint as unsuitable for long-horizon stock-selection alpha. If it passes, retain only as a conditional OI-inventory source pending publication-time, revision, broad PIT identity and economic-incrementality gates. No paid data, purchase, vendor contact, terms acceptance, forward returns or production changes are authorized.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
