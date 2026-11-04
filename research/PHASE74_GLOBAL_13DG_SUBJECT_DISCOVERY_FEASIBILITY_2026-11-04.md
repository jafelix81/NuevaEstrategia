# Phase 74 — Global SEC 13D/13G subject-issuer discovery feasibility

**Date:** 2026-11-04  
**Branch:** phase74-13dg-global-subject-discovery-audit  
**Scope:** index semantics, global discovery and identity feasibility only. No forward returns or alpha tests.

## Executive question

Can the SEC quarterly global master index identify Schedule 13D/13G filings by the subject issuer for the current 335-name candidate universe, without crawling every filer submission history?

This is necessary because Phase 35's 20,265-row input was retrieved by querying submissions for the current universe CIKs. It is a filer-universe-limited sample with a mixed heuristic CIK field, not a subject-issuer census. Parsing its documents cannot recover filings submitted by investors whose filer CIK is outside the current universe.

## Current evidence

- Phase 35 immutable artifact: 20,265 rows; its source CIK equals the accession-prefix CIK in 10,085/20,265 rows (49.77%). This is a role diagnostic, not subject-CIK accuracy.
- Phase 72 structured XML pilot: 0/80 parsed using the earlier direct primary-document retrieval route. All 80 errors were ElementTree mismatched-tag failures. This is a representation/transport failure, not evidence of absent filings.
- Phase 73 complete-submission extractor tests passed on 2026-11-04 (run 41868094850). Its stratified 80-filing pilot is running as run 41868352940; no final artifact is available yet. Do not start a duplicate SEC crawl while it is active.
- Phase 69: ten additional current fund registrant CIKs produced zero incremental Form 144 accessions in the 14-quarter sample. This does not resolve 13D/13G subject coverage.

## Phase 74 hypothesis

A global master-index accession may expose two distinct identity fields: the CIK value(s) in master-index row(s), and the CIK in the archive path embedded in Filename.

For Form 144, Phase 64 found two distinct master-index CIK associations per accession and validated a unique current-universe candidate as XML issuer in the tested sample. That result must not be extrapolated to 13D/13G. Phase 35's 13D/13G diagnosis warns that the master-index CIK column can be the filer. Phase 74 therefore preserves both fields and validates each against the complete-submission SEC-HEADER SUBJECT COMPANY and FILED BY blocks.

If a target CIK appears in the index pair/path and is the header subject, the global index can be filtered before downloading filings. If it is only the filer, it is a false target match. If the subject CIK is absent from both fields, a filing-detail index page or another discovery route is required.

## Implementation

- research/phase74_13dg_global_subject_audit.py: parses four 13D/13G variants; groups duplicate rows by accession; preserves master-index and archive-path CIKs separately; computes candidate overlap; stratifies by form, amendment, regulatory timing and candidate/control/ambiguous status; validates SEC header roles and optional XML concordance. Supports index-only and pilot modes.
- research/test_phase74_13dg_global_subject_audit.py: seven offline tests for form/accession parsing, duplicate rows, archive-path separation, subject/filer role, timing cutovers, URL construction and deterministic stratification.
- .github/workflows/phase74_13dg_global_subject_audit_tests.yml: offline tests only; it does not contact the SEC or start a data crawl.

## Preregistered gates

### Gate A — index completeness
- All 14 quarterly indexes (2023Q2–2026Q3) retrieved.
- Zero duplicate accessions across quarters.
- Zero unresolved form/date/path metadata conflicts, or every conflict explicitly quarantined.
- Separate counts for SC 13D, SC 13D/A, SC 13G and SC 13G/A.
- Preserve SHA-256 for each raw quarterly index.

### Gate B — subject identity pilot
- Up to 120 filings stratified across 13D/13G, original/amendment, form-specific deadline regimes and pre-/post-XML mandate.
- SEC-HEADER subject and filer CIK present in at least 99.5%.
- Header accession, form and filing date concordance at least 99.5%.
- Subject CIK appears in master-index CIK associations or archive path in at least 99.5%.
- Where structured XML exists, XML issuer/filer must match header subject/filer at least 99.5%.
- A unique target CIK in the index pair/path must resolve to header subject at least 99.5%; filer-only matches are excluded.
- Keep legacy HTML and structured XML strata separate.

### Gate C — coverage and economics (not authorized)
- Reconstruct historical target issuer CIK/security lineage and historical F80 membership.
- Resolve reporting-person identity, group membership, exact previousAccessionNumber chains and left-censored predecessors.
- Separate 13D activist/strategic filings from 13G QII/passive/exempt filings and regulatory deadline regimes.
- Use SEC filing/acceptance availability, never ownership event date, as KnowledgeDate.
- Only then may a preregistered ownership-change hypothesis be compared with frozen LTM/F80 using identical exposure/costs, chronological OOS, block bootstrap and issuer LOO.

## Decision

Phase 74 is an identity/discovery feasibility stage. It does not claim that the global index pair is a reliable subject-issuer filter for 13D/13G until the pilot proves it. No forward returns, alpha tests, data purchases or production changes are permitted.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
