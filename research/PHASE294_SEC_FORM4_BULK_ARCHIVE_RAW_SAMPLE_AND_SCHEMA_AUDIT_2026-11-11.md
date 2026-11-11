# Phase 294 — SEC Insider Transactions bulk archive raw sample and schema audit

**Date:** 2026-11-11 UTC  
**Status:** SIX_ARCHIVES_RAW_RETRIEVED_SCHEMA_PASS  
**Branch:** `phase294-sec-form4-bulk-sample-acquisition`  
**Run:** [43083625013](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43083625013)  
**Artifact:** [13884014630 — raw ZIPs and audit manifest](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43083625013/artifacts/13884014630)  
**Control:** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Executive result

The repository secret `SEC_CONTACT_EMAIL` was successfully injected into GitHub Actions. The workflow made six authorized, sequential requests to the official SEC host; all six returned HTTP 200. The email value was not printed, logged, or written to the repository.

Six stratified quarterly archives were downloaded, ZIP CRC-checked, SHA-256 hashed, and inspected. All six passed the required-table/schema, primary-key, row-shape and accession-reconciliation gates. The archives total **72,767,570 bytes (about 69.4 MiB)**. They remain in the 90-day Actions artifact, not in the repository.

Across these six quarter samples:

- 353,212 SUBMISSION rows.
- 308,940 Form 4 and 8,327 Form 4/A submissions: **317,267 combined**.
- 568,055 NONDERIV_TRANS rows.
- 377,553 REPORTINGOWNER rows.
- 766,389 FOOTNOTES rows.
- 13,156 distinct issuer CIK values and 14,048 distinct as-filed ticker strings across the selected archives. These are descriptive counts, not effective-dated security-identity or frozen-universe coverage results.
- 7,769 accession-level submissions have more than one REPORTINGOWNER row. This confirms that an accession-only transaction-to-owner join would create false owner attribution; owner-specific features must use original XML/exhibits or exclude ambiguous accessions.

## Archive inventory and hashes

| Quarter | ZIP bytes | Form 4 | Form 4/A | AFF10B5ONE column | SHA-256 |
|---|---:|---:|---:|---|---|
| 2006Q1 | 17,306,804 | 68,520 | 3,159 | Absent | `62becdadbe5eaff68f03edefe2ba2357c8bb498a1f825b697003e087cf98e6ce` |
| 2012Q1 | 14,219,288 | 61,816 | 1,862 | Absent | `0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357` |
| 2023Q1 | 13,882,049 | 62,557 | 1,287 | Present | `0b476188f52a0862e71886eb31a81f6345fc6616403b52188484aef0438cfcfb` |
| 2023Q2 | 10,742,628 | 50,854 | 937 | Present | `7e636787231ae0f00accf5c3627298402dedd1aefffd7c50fb48292e5d3a8fbb` |
| 2025Q3 | 7,956,025 | 31,672 | 455 | Present | `9c57f272b7230500771f661bc1fe181527ed6b76a6f45d23a910c7fc7e9fcfa4` |
| 2026Q3 | 8,660,776 | 33,521 | 627 | Present | `a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3` |

The six quarters were selected to span early history, the 2023 Rule 10b5-1 checkbox era, the July 2025 archive update and the latest published quarter. They are a purposive schema sample, not a census of all 83 archives.

## Schema and data-contract findings

1. All eight documented TSV tables were present in each sampled archive. The table headers were stable across the sample except for SUBMISSION: `AFF10B5ONE` was absent in 2006Q1/2012Q1 and present in 2023Q1, 2023Q2, 2025Q3 and 2026Q3. Its absence in older archives is UNKNOWN, not false; it must not be used as a negative plan flag.
2. SEC bulk `FILING_DATE` values are formatted as `DD-MMM-YYYY` (for example, `31-MAR-2006`), not ISO dates. Phase 294 added explicit, locale-independent normalization. All 317,267 Form 4/4-A rows in the six archives received valid accession and normalized filing-date values.
3. SUBMISSION, REPORTINGOWNER, NONDERIV_TRANS and FOOTNOTES passed their required-field, row-width, non-null key, unique-key and cross-table accession checks in all six samples. The other transaction/holding tables also had no missing keys, duplicate keys, malformed rows or orphan accessions in these samples.
4. The documented OWNER_SIGNATURE key `ACCESSION_NUMBER + OWNERSIGNATURENAME` is not unique in the raw data. Across the six archives, 1,107 rows repeat that key: 1,055 are exact repeated rows and 52 have the same accession/name but a different signature date. This is a non-core-table warning, not a failure of the Form 4 transaction tables. Do not blindly deduplicate this table on the documented two-field key; retain source rows and inspect the signature date/row provenance.
5. Multiple reporting owners are common enough to be a material attribution constraint. The flattened NONDERIV_TRANS table has no reporting-owner CIK, so accession-only joins are prohibited.

## Disposition and next gates

**Passed:** authorized SEC contact injection; six raw ZIP downloads; ZIP integrity; immutable per-archive SHA-256; all eight table inventories; required schema and core key checks; date normalization; AFF10B5ONE era observation.

**Not admitted:** exact first-public receipt; acceptance-time join; strict point-in-time panel; multi-owner transaction attribution; effective-dated issuer/security-class identity; coverage against the frozen 335-name universe; signal prevalence; return predictability; alpha; chronological OOS; bootstrap/LOO.

The next gate is a stratified real-data join from selected Form 4 accessions to SEC daily `form.YYYYMMDD.idx` files and the complete submission text. Record every observed index date without backdating to FILING_DATE, reconcile the SEC-HEADER acceptance timestamp, and keep the first daily-index sighting distinct from exact first-public receipt. Only after those clocks, owner attribution and historical security identity are resolved should a broad event panel be considered.

No vendor was contacted, no paid data was purchased, no return test or bootstrap/LOO was run, no holdout was used, and no production, universe, capital or strategy parameter changed.
