# Phase 295 — SEC Form 4 daily-index and acceptance-time real-data pilot

**Date:** 2026-11-11  
**Branch:** `phase295-sec-form4-daily-index-pit-pilot`  
**Commit:** `4e661b6ae9cfa20c7a4849849a34d4aa84c5bb19`  
**Workflow:** [43087726733](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43087726733) — success  
**Artifact:** [13887641760](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43087726733/artifacts/13887641760), SHA-256 `89c9904d9bdd8f4cbde2706c40111a3e5ddeabed79788b77ed76b6a1e92390ed`

## Scope and method

A purposive sample of 18 Form 4 accessions was selected as the first, middle and last deterministic record from each Phase 294 archive quarter: 2006Q1, 2012Q1, 2023Q1, 2023Q2, 2025Q3 and 2026Q3. For each accession, the workflow queried the SEC historical daily `form.YYYYMMDD.idx` files over a five-calendar-day window and downloaded the complete-submission text file. The raw response bytes, response headers, SHA-256 hashes and parsed manifest were staged in the Actions artifact.

## Result

- 18/18 SEC-HEADER records reconciled accession, Form 4 type, bulk `FILING_DATE` and `ACCEPTANCE-DATETIME`.
- 18/18 first observed daily-index sightings matched the expected issuer identity and had index-date lag 0.
- 57/88 daily-index requests returned valid files and parsed with zero parser errors. The remaining 31 returned HTTP 403: 27 weekend dates and four U.S. federal holidays. They were non-SEC business dates, not parse failures.
- 15/18 acceptances occurred at or after 16:00 ET; 8/18 at or after 17:00 ET; 5/18 at or after 18:00 ET; 2/18 at or after 20:00 ET. All 18 acceptance timestamps had a New York local date matching the SEC filing date.
- Total bytes downloaded: 60,334,796. The artifact contains 18 raw submission text files, 57 raw daily-index files and the JSON audit manifest.
- Offline tests: 11/11 passed.

## Parser correction

The initial implementation reused the N-PORT submission-header parser, which expected a colon-delimited `ACCEPTANCE-DATETIME:` field. The actual Form 4 complete-submission text uses the SGML tag `<ACCEPTANCE-DATETIME>YYYYMMDDHHMMSS`. A Form 4-specific parser now handles that format, reconciles accession/form/filed date, converts acceptance time to America/New_York and UTC, and records whether acceptance date equals filing date without treating a date difference as a parser failure. Raw submission files are persisted before parsing so diagnostic evidence is retained if a later parse fails.

## Interpretation and limitations

This validates the real retrieval and parsing path across six eras, not strict point-in-time availability. The 18 accessions are purposive, not random. All 18 daily-index dates matched the filing date; this sample did not observe a later index-date sighting or a post-acceptance correction. The index is date-granular and built nightly; its date does not prove the exact time the index became public. Acceptance time is not itself the first-public timestamp. The after-close acceptances reinforce the need for a conservative execution rule.

**Trading-clock rule for any future test:** do not enter on the filing date. Use no earlier than the next full XNYS session after the SEC acceptance timestamp, with a separate first-index-date ledger and no backdating. Strict PIT remains unadmitted until a broader after-hours/PAC sample and first-public timing adjudication pass.

## Controls

`email_secret_present=true`; the secret was used only in the SEC User-Agent contact string and was not logged or emailed. `first_public_timestamp_verified=false`, `strict_pit_admitted=false`, `alpha_test_authorized=false`, `return_test_run=false`, `bootstrap_loo_run=false`, `holdout_used=false`, `f80_frozen=true`, and no production, universe, capital or parameter changes occurred.
