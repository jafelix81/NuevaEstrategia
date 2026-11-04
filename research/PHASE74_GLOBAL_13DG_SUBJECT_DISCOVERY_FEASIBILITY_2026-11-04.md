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
- Phase 73 complete-submission extractor tests passed (run 41868094850), but the first 80-filing pilot (run 41868352940; artifact 13342854701) failed its data gate: 54/80 parsed, 26 HTTP 404 retrieval failures, and 0% acceptance-time concordance. The 26 were archive-path failures, not malformed XML. A separate corrected rerun (run 41872288761 on phase74-13dg-archive-path-and-utc-fix) is currently in progress; it tries the subject/archive CIK before the accession-prefix CIK and converts SEC header Eastern timestamps to UTC before comparison. Do not start a duplicate SEC crawl while it is active.
- Phase 69: ten additional current fund registrant CIKs produced zero incremental Form 144 accessions in the 14-quarter sample. This does not resolve 13D/13G subject coverage.

## Phase 74 hypothesis

A global master-index accession may expose two distinct identity fields: the CIK value(s) in master-index row(s), and the CIK in the archive path embedded in Filename.

For Form 144, Phase 64 found two distinct master-index CIK associations per accession and validated a unique current-universe candidate as XML issuer in the tested sample. That result must not be extrapolated to 13D/13G. Phase 35's 13D/13G diagnosis warns that the master-index CIK column can be the filer. Phase 74 therefore preserves both fields and validates each against the complete-submission SEC-HEADER SUBJECT COMPANY and FILED BY blocks.

If a target CIK appears in the index pair/path and is the header subject, the global index can be filtered before downloading filings. If it is only the filer, it is a false target match. If the subject CIK is absent from both fields, a filing-detail index page or another discovery route is required. A second candidate is the SEC Full-Text Search: the SEC says it searches electronic filings since 2001, supports CIK and form/date searches, and indexes XML element content (but not element names). Exact quoted subject-CIK text queries may therefore find cross-filer XML filings; this remains a hypothesis until positive controls and pagination are tested.

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


## 11. Phase 73 failure diagnosis and corrected retrieval path

Run 41868352940 completed with a failed data gate:
- 80 sampled filings; 54 parsed successfully; 26 retrieval failures.
- For the 54 retrieved filings, XML issuer vs SEC header SUBJECT COMPANY, XML filer vs FILED BY/accession prefix, accession, form and filing date all matched at 100%.
- Acceptance timestamp concordance was 0% because SEC-HEADER ACCEPTANCE-DATETIME is an Eastern wall-clock value without an offset, while submissions API acceptanceDateTime is UTC ISO-8601. Comparing digit strings is invalid.
- The 26 failures were HTTP 404 archive-path mismatches. The corrected branch phase74-13dg-archive-path-and-utc-fix (run 41872288761) now tries subject/archive path CIK first and accession-prefix CIK as fallback, and normalizes timestamps with America/New_York daylight-saving rules. That run remains the only active SEC pilot; Phase 74 does not launch another SEC crawl.

## 12. Additional discovery route — SEC Full-Text Search (EFTS)

The official SEC Full-Text Search page states that electronic filings have been searchable since 2001 and that users can search by keyword, ticker, company name, CIK and reporter name. The SEC Webmaster FAQ explicitly confirms that XML element content is indexed, although element names are not associated with the indexed text.

Official documentation:
- https://www.sec.gov/edgar/search/
- https://www.sec.gov/edgar/search/efts-faq.html
- https://www.sec.gov/about/webmaster-frequently-asked-questions

This creates a potentially much cheaper subject-side discovery route than downloading every global 13D/13G filing. The test must use exact quoted subject-CIK text, not assume the undocumented ciks parameter is subject-aware. Positive controls:
- Revance Therapeutics subject CIK 0001479290, filer JPMorgan Chase CIK 0000019617, accession 0000019617-25-000296 (SC 13G/A).
- Osisko Development subject CIK 0001431852, filer Double Zero Capital CIK 0002083861, accession 0001062993-25-015044 (SC 13D).

For each control, test zero-padded and unpadded CIK strings, all four form variants, narrow date windows, result pagination and document-level deduplication. Then retrieve the complete submission text and confirm header SUBJECT COMPANY, FILED BY, accession, form/date and primary XML issuer/filer identities. Exhibit-only hits do not count as primary ownership filings. The SEC's search endpoint implementation is not documented as a stable API; treat any direct JSON endpoint as experimental and retain raw query/response metadata and hashes.

A separate branch, phase74-sec-subject-side-13dg-discovery, contains the detailed EFTS/Entity Landing Page probe plan. It has not launched a data crawl. The SEC Entity Landing Page's Beneficial Ownership section is a secondary fallback if exact-CIK full-text search fails:
https://www.sec.gov/edgar/browse/?CIK=1479290

## 13. Updated next action

Wait for run 41872288761 to finish and inspect its artifact. Then run only a tiny EFTS positive-control probe (two known cross-filer filings plus controls) before any global subject-side crawl. Do not launch the 14-quarter master-index pilot or full 8,294-row filer-side corpus until archive path, timezone and subject discovery gates are resolved.
