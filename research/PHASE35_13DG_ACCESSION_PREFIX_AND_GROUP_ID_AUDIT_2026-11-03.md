> **SUPERSEDED (2026-11-03):** This audit's claim that row-level issuer/PIT extraction passed is invalidated by a later subject-issuer attribution audit. The 13G XML parser can fall back to the query/reporting-person CIK instead of the actual subject issuer CIK. Do not use the counts or conclusions below as issuer/group evidence. See research/PHASE35_13DG_ISSUER_ATTRIBUTION_FAILURE_2026-11-03.md.

# Phase 35 — accession-prefix and reporting-group identity correction

Date: 2026-11-03  
Branch: `phase35-event-normalization-audit`  
Scope: source/identity audit only; no forward-return test.

## Source artifact and row-level result

Latest completed corrected artifact inspected: run `41618946255`, artifact `13236177463` (`phase35-13dg-pit-event-crosswalk-audit`).

- 335 frozen-universe tickers; 307 selected CIKs; 27 unresolved tickers.
- 20,266 resolved filing rows; 303 subject issuers.
- 14,542 amendments (71.76%).
- 19,680 rows with parsed event date (97.11%).
- 0 submission errors and 0 resolution errors in this completed run.
- Extracted filing-date range: 2020-10-01 through 2026-09-25.
- `filing_date` remains the conservative KnowledgeDate. `event_date` is not KnowledgeDate.

This confirms row-level issuer/PIT extraction for the retrieved filings. It does not establish complete reporting-group lineage or true first events.

## Critical identity correction: accession prefix is not the beneficial owner

The prior provisional diagnostic used:

`issuer_cik + accession-prefix CIK + form family`

as a deterministic sequence key. The accession prefix is **not a reliable reporting-person or economic-group identifier**.

The SEC's official *Accessing EDGAR Data* guidance explains that the first ten digits of an accession number identify the entity that submitted the filing, which may be the company **or a third-party filing agent**:
https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data

A concrete SEC example is the Occidental Petroleum filing `0000928464-20-000057`:
- accession prefix: `0000928464`;
- subject issuer: Occidental Petroleum, CIK `0000797468`;
- SEC filing detail page identifies Carl C. Icahn, CIK `0000921669`, as “Filed by”.
https://www.sec.gov/Archives/edgar/data/797468/000092846420000057/0000928464-20-000057-index.htm

Thus the accession prefix can differ from the actual reporting person and can represent an agent. It may be retained as `submission_cik` for traceability, but it must **never** be used as a beneficial-owner, reporting-person, or group key.

## Consequence for the previous provisional counts

The earlier diagnostic produced 3,115 issuer/accession-prefix/form-family sequences, 1,823 (58.5%) provisional first rows that were amendments, and 360 issuer/family combinations with multiple accession prefixes.

Those counts are reproducible diagnostics of submission-prefix fragmentation only. They are **not** counts of economic groups, true first filings, or group-level amendment chains. The 58.5% amendment share cannot be interpreted as the fraction of genuine first events that are left-censored; it mixes left-censoring with filing-agent/submission-prefix identity error.

Likewise, the earlier increase/decrease/no-change counts derived from this provisional key are descriptive parser outputs only and are not valid group-level ownership transitions.

## Remaining data defects

- The extracted window starts 2020-10-01, so earlier original filings are absent. A first row in the current panel may be an amendment to a pre-window filing.
- `reporting_person` is populated on only 3,502/20,266 rows (17.3%); `purpose_text` on 261/20,266 (1.29%); `reporting_person_type` on 10,041/20,266 (49.5%).
- The current parser captures at most one reporting-person name and does not reconstruct all joint filers/group members.
- Raw `percent_class` is mechanically selected around the regulatory 5% reporting threshold and is not an independent alpha feature.

## Correct next gate

1. Keep `accession_prefix` only as `submission_cik`; never use it as group identity.
2. Extend the issuer filing history sufficiently far back to recover predecessor/original filings. Any event with incomplete predecessor history must be marked left-censored and excluded from initiation tests.
3. Parse the SEC filing detail/index metadata and the complete cover page/structured XML to capture the actual “Filed by” entity and **all** reporting persons, group checkboxes, and joint-filing evidence.
4. Build a deterministic reporting-group fingerprint only where the filing itself supports it. Keep ambiguous or incomplete groups excluded; do not fuzzy-merge.
5. Reconstruct ownership state only across sequential filings for the same verified issuer + reporting group, with `filing_date` as KnowledgeDate.
6. Re-run historical active-universe coverage and event counts before authorizing any forward-return test.

## Decision

**ROW-LEVEL ISSUER/PIT EXTRACTION: PASS.  
REPORTING-GROUP / ORIGINAL-AMENDMENT NORMALIZATION: FAIL / NOT AUTHORIZED.  
ECONOMIC TEST: BLOCKED.**

No forward returns, horizon selection, threshold optimization, or baseline change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
