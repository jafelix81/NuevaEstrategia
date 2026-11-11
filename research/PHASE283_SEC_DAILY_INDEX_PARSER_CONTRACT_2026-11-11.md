# Phase 283 — SEC daily-index parser contract and accession-ledger guardrails

**Date:** 2026-11-11 UTC  
**Status:** OFFLINE_PARSER_IMPLEMENTED_RAW_INDEX_VALIDATION_PENDING  
**Branch:** phase231-cboe-option-quotes-full-row-reparse  
**Control:** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## 1. Why this phase exists

Phase 281 identified the SEC historical daily form.YYYYMMDD.idx archive as the best available public route for reconstructing a conservative daily Form 4 knowledge date. Phase 282 rejected paid PDS as a superior first-publication clock. Neither phase downloaded raw daily-index bytes or validated the accession/path join.

This phase implements the offline parser and fail-closed ledger contract before any SEC request is made. It does not claim that the live SEC index format has passed a raw-byte test.

## 2. Implemented contract

The parser:
- accepts only a filename matching form.YYYYMMDD.idx;
- requires the documented five-column pipe-delimited header;
- retains only Form 4 and Form 4/A rows, as distinct accessions;
- validates the accession path, path CIK and accession CIK prefix; requires the index date not to precede the filing date, while retaining later index sightings with explicit lag metadata;
- counts exact duplicate rows but excludes conflicting duplicate accessions;
- builds one accession ledger while preserving every daily-index sighting, the earliest observed index date, and first/maximum index lag relative to FILING_DATE;
- quarantines malformed, mismatched and cross-index-conflicting records without copying raw row text;
- computes the next full XNYS session close only from explicit timezone-aware session timestamps, skipping early-close sessions.

There is no fallback to FILING_DATE, ACCEPTANCE-DATETIME, current submissions feeds, or PDS receipts when the daily-index match is missing.

## 3. Regression coverage

The synthetic suite covers:
- Form 4 versus Form 4/A accession separation;
- non-Form-4 filtering;
- CIK/path and accession-prefix mismatches;
- index date preceding filing date (quarantined) and later index-date sightings (retained as lagged observations);
- malformed/unrecognized paths;
- exact and conflicting duplicate rows;
- earliest-date and multi-sighting ledger behavior;
- cross-index identity conflicts;
- timezone-aware next-full-session logic and early-close skipping;
- fail-closed PIT/alpha controls.

The GitHub Actions workflow compiles the parser and runs the Phase 283 tests alongside the existing Phase 231 sample gate. No network request is added to the Phase 283 parser tests.

## 4. What is not established

- No SEC daily-index bytes were downloaded or parsed.
- The SEC live header, delimiter, accession path and same-day PAC behavior remain unverified against raw files.
- No six-quarter accession join has been performed.
- No exact first-public timestamp exists in the SEC documentation.
- Owner-level transaction attribution and effective-dated security/class identity remain unresolved.
- No return, alpha, bootstrap/LOO, chronological OOS or holdout test was run.

The daily-index date remains a conservative candidate knowledge date, not strict PIT admission. The earliest permitted daily strategy execution remains the close of the next full XNYS session after the first verified daily-index date.

## 5. Next gates

1. Configure the authorized SEC_CONTACT_EMAIL GitHub Actions secret before automated SEC retrieval; do not invent a contact address or send a request without the declared User-Agent.
2. Use the six Phase 279 strata (2006Q1, 2012Q1, 2023Q1, 2023Q2, 2025Q3 and 2026Q3) to retrieve only the daily Form index files needed for deterministic sampled accessions.
3. Preserve each raw index file's SHA-256, filename, retrieval timestamp and source metadata; never upload raw index contents to CI artifacts.
4. Measure missing, duplicate, multi-date, malformed, index-date-lag and same-day-PAC cases. Reconcile a stratified subset to original Form 4/Form 4-A headers and body accessions.
5. Keep all amendments as separate accessions/vintages. Resolve joint/group owner attribution and effective-dated security/class identity before any returns join.

## 6. Controls

- Raw SEC requests: 0.
- Raw SEC index bytes downloaded: 0.
- Strict PIT admitted: false.
- Alpha test authorized: false.
- Holdout used: false.
- F80 frozen: true.
- Production, universe, capital and parameters changed: false.
- No vendor contacted, no trial requested, no data purchased, no terms accepted and no PR merged.

This is a reproducibility/engineering prerequisite only. It does not increase demonstrated economic edge.


## Phase 283 refinement — delayed ownership-form index sightings

A code review found an unreachable synthetic path: the parser rejected every row whose index filename date differed from `Date Filed`, while the ledger/test contract explicitly claimed to preserve multi-date sightings. SEC documentation also notes that some Forms 3/4/5 submitted after 10 p.m. ET are disseminated on the next business day and appear in the following business day's index. Equality was therefore too strict for the conservative knowledge clock.

The parser now:
- quarantines only an index date that precedes `Date Filed`;
- retains later index dates and records `index_date_lag_days`;
- preserves all sightings and reports first/max lag in the accession ledger;
- never substitutes `Date Filed` for a missing daily-index sighting.

The regression suite now exercises a real parser-produced later sighting, multi-date ledger aggregation and the no-backdating rule. This remains synthetic validation only; raw SEC index bytes and actual late Form 4/PAC frequencies have not been inspected. The next permitted knowledge date remains based on the earliest verified daily-index date, followed by the next full XNYS session close.

Source semantics: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
