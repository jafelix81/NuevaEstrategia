# Phase 284 — SEC daily-index delayed ownership-form sighting correction

**Date:** 2026-11-11 UTC  
**Branch:** `phase231-cboe-option-quotes-full-row-reparse`  
**Status:** `SYNTHETIC_CONTRACT_CORRECTION_RAW_SEC_VALIDATION_PENDING`  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Finding

A code review of Phase 283 found an internal contradiction. The parser required the daily index filename date to equal the row's `Date Filed`, but the accession-ledger contract and a synthetic test claimed to preserve the same accession across multiple daily-index dates. That test bypassed the parser and therefore did not prove the advertised behavior.

The SEC's EDGAR access guidance says some ownership filings (Forms 3/4/5) submitted after 10 p.m. ET are disseminated on the next business day and appear in the following business day's index. Equality between the index filename date and `Date Filed` is therefore too strict for a conservative knowledge-date parser.

## Correction

- Reject and quarantine an index date earlier than `Date Filed`.
- Retain a later index date as an observed delayed sighting and record `index_date_lag_days`.
- Preserve every accession sighting; report the earliest observed index date plus first and maximum lag.
- If only a later sighting is present, use that observed index date; never backdate to `Date Filed`.
- Keep Form 4 and Form 4/A as separate accessions and retain CIK/path, accession-prefix and duplicate/conflict controls.

## Validation

The existing Phase 231 workflow already runs the Phase 283 parser tests, so no duplicate workflow was created. The synthetic suite was strengthened to test:
1. an index date before filing date is quarantined;
2. a later index date is parsed and tagged with its lag;
3. a multi-date accession ledger uses the earliest observed index date and records maximum lag;
4. a later-only sighting is not backdated to `Date Filed`.

No SEC network request, raw-index download, PAC reconstruction, alpha test, return test, holdout use, vendor contact or purchase occurred. Hosted validation is pending until the existing path-filtered PR workflow runs on the new commit.

## Limitations and next gate

The correction aligns the parser with the documented delayed-dissemination possibility, but does not prove the raw SEC index bytes actually exhibit later-date sightings or establish their frequency. After the authorized `SEC_CONTACT_EMAIL` is configured, the six-quarter sample must measure index-date lag distributions, missing accessions, PAC behavior and original-content reconciliation before any PIT admission.

Official reference: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data

**Economic disposition:** engineering/data-contract progress only. No Smart Money alpha or incremental economic edge has been demonstrated.
